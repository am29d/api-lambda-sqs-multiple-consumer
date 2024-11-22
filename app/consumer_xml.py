import os
import xml.etree.ElementTree as ET
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


def xml_to_dict(element):
    """Convert XML to dictionary format with numeric values as Decimal"""
    result = {}
    for child in element:
        if len(child) > 0:
            if child.tag == "items":
                result[child.tag] = [xml_to_dict(item) for item in child]
            else:
                result[child.tag] = xml_to_dict(child)
        else:
            # Convert numeric values to Decimal
            if child.tag in ["unit_price", "subtotal", "total_amount", "quantity"]:
                try:
                    result[child.tag] = Decimal(child.text)
                except (ValueError, TypeError):
                    result[child.tag] = child.text
            else:
                result[child.tag] = child.text
    return result


@tracer.capture_method
def record_handler(record: SQSRecord) -> str:
    """Process individual SQS record containing XML data"""
    try:
        # Parse XML from message body
        root = ET.fromstring(record.body)

        # Convert XML to dictionary
        payload = xml_to_dict(root)

        # Add format information
        payload["format"] = "xml"

        # Store in DynamoDB
        table.put_item(Item=payload)

        order_id = payload.get("id", "unknown")
        logger.info(f"Processing XML order: {order_id}")

        # Increment successful processing metric
        metrics.add_metric(name="SuccessfulXMLOrdersProcessed", unit="Count", value=1)

        return f"Processed XML order {order_id}"
    except ET.ParseError as e:
        logger.error(f"XML parsing error: {e}")
        metrics.add_metric(name="XMLParsingErrors", unit="Count", value=1)
        raise
    except Exception as e:
        logger.error(f"Error processing XML record: {e}")
        metrics.add_metric(name="FailedXMLOrdersProcessed", unit="Count", value=1)
        raise


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    # Add custom metrics for total records
    metrics.add_metric(
        name="TotalXMLOrdersReceived", unit="Count", value=len(event["Records"])
    )

    # Process partial failures if any
    return process_partial_response(
        event=event, processor=processor, record_handler=record_handler, context=context
    )
