import json
import os

import boto3
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.exceptions import (
    BadRequestError,
    InternalServerError,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import validate
from powertools import logger, metrics, tracer
from schema import SCHEMA

app = APIGatewayRestResolver()
sqs_client = boto3.client("sqs")


@app.post("/")
@tracer.capture_method
def process() -> dict:
    if app.current_event["headers"].get("Content-Type") == "application/json":
        return process_order_json(app.current_event.json_body)
    elif app.current_event["headers"].get("Content-Type") == "application/xml":
        return process_order_xml(app.current_event.body)  # Changed from json_body
    else:
        raise BadRequestError("Unsupported media type")


@tracer.capture_method
def send_to_sqs(queue_url: str, message_body: str | dict, event_type: str) -> bool:
    logger.info(f"Sending message to SQS: {queue_url}")
    try:
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body,
            MessageAttributes={
                "eventType": {"DataType": "String", "StringValue": event_type}
            },
        )
        return {"message": "Order processed successfully"}
    except Exception as e:
        logger.error(f"Failed to send message to SQS: {str(e)}")
        raise InternalServerError("Failed to process order")


@tracer.capture_method
def process_order_json(order: dict) -> dict:
    logger.info("Processing JSON order")
    validate(event=order, schema=SCHEMA)
    return send_to_sqs(os.environ["ORDERS_QUEUE_URL"], json.dumps(order), "json_order")


@tracer.capture_method
def process_order_xml(order: str) -> dict:
    logger.info("Processing XML order")
    if not order:
        raise BadRequestError("Empty XML body")
    return send_to_sqs(os.environ["ORDERS_QUEUE_URL"], order, "xml_order")


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True
)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
