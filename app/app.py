import json
import os

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.exceptions import (
    BadRequestError,
    InternalServerError,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import validate

from app import schema

app = APIGatewayRestResolver()
tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")

params_for_xml = parameters.get_parameter("/orders-server/xml")
params_for_json = parameters.get_parameter("/orders-server/json")


@app.put("/")
@tracer.capture_method
def process() -> dict:
    if app.current_event["headers"].get("Content-Type") == "application/json":
        return process_order_json(app.current_event.json_body)
    elif app.current_event["headers"].get("Content-Type") == "application/xml":
        return process_order_xml(app.current_event.decoded_body)  # Changed from json_body
    else:
        raise BadRequestError("Unsupported media type")


def send_to_sqs(queue_url: str, message_body: str | dict, event_type: str) -> bool:
    sqs_client = boto3.client("sqs")
    try:
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageAttributes={
                "event_type": {"DataType": "String", "StringValue": event_type}
            },
        )
        return {"message": "Order processed successfully"}
    except Exception as e:
        logger.error(f"Failed to send message to SQS: {str(e)}")
        return InternalServerError("Failed to process order")


def process_order_json(order: dict) -> dict:
    validate(event=order, schema=schema.INPUT)  # No formats needed

    return send_to_sqs(os.environ["ORDERS_JSON_QUEUE_URL"], order, "json_event")


def process_order_xml(order: str) -> dict:
    if not order:
        raise BadRequestError("Empty XML body")
    
    if send_to_sqs(os.environ["ORDERS_XML_QUEUE_URL"], order, "xml_event"):
        return {"message": "Order processed successfully as XML"}
    return InternalServerError("Failed to process XML order")  # Changed to be consistent with error handling


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
