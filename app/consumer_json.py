import json
import os
from decimal import Decimal

import boto3
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
from powertools import logger, metrics, tracer

processor = BatchProcessor(event_type=EventType.SQS)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["ORDERS_TABLE"])

def float_to_decimal(obj):
    """Convert float values to Decimal for DynamoDB"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [float_to_decimal(item) for item in obj]
    return obj

@tracer.capture_method
def record_handler(record: SQSRecord) -> str:
    """Process individual SQS record and return success/failure"""
    try:
        # Parse message body as JSON and convert floats to Decimals
        payload = json.loads(record.body, parse_float=Decimal)

        # Add format information to the payload
        payload["format"] = "json"

        # Store in DynamoDB
        table.put_item(Item=payload)

        # Add your business logic here
        logger.info(f"Processing order: {payload.get('id', 'unknown')}")

        # Increment successful processing metric
        metrics.add_metric(name="SuccessfulOrdersProcessed", unit="Count", value=1)

        return f"Processed order {payload.get('id', 'unknown')}"
    except Exception as e:
        # Log error and increment failure metric
        logger.error(f"Error processing record: {e}")
        metrics.add_metric(name="FailedOrdersProcessed", unit="Count", value=1)
        raise


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    # Add custom metrics for total records
    metrics.add_metric(
        name="TotalOrdersReceived", unit="Count", value=len(event["Records"])
    )

    # Process partial failures if any
    return process_partial_response(
        event=event, processor=processor, record_handler=record_handler, context=context
    )
