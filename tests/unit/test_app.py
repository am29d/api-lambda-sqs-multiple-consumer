import json
import os
import unittest
from unittest.mock import MagicMock, patch

# Mock environment variables before importing the handler
os.environ["ORDERS_XML_QUEUE_URL"] = (
    "https://sqs.eu-west-1.amazonaws.com/123456789012/OrdersXMLQueue"
)
os.environ["ORDERS_JSON_QUEUE_URL"] = (
    "https://sqs.eu-west-1.amazonaws.com/123456789012/OrdersJsonQueue"
)

# Mock the parameters and schema validation with correct path
with patch(
    "aws_lambda_powertools.utilities.parameters.get_parameter"
) as mock_get_parameter:
    mock_get_parameter.side_effect = lambda param: "mocked_value"
    from app.app import handler


class TestApp(unittest.TestCase):
    def setUp(self):
        # Create mock Lambda context
        self.context = MagicMock()
        self.context.function_name = "test-function"
        self.context.function_version = "$LATEST"
        self.context.invoked_function_arn = (
            "arn:aws:lambda:eu-west-1:123456789012:function:test-function"
        )
        self.context.memory_limit_in_mb = 128
        self.context.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"
        self.context.log_group_name = "/aws/lambda/test-function"
        self.context.log_stream_name = "2020/01/31/[$LATEST]52fdfc07"
        self.context.get_remaining_time_in_millis = lambda: 1000

        # Mock SQS client
        self.sqs_patcher = patch("boto3.client")
        self.mock_sqs = self.sqs_patcher.start()
        self.mock_sqs_client = MagicMock()
        self.mock_sqs.return_value = self.mock_sqs_client

        # Load test data from API Gateway event files
        with open("events/api_order_json.json", "r") as f:
            self.json_event = json.load(f)

        with open("events/api_order_xml.json", "r") as f:
            self.xml_event = json.load(f)

    def tearDown(self):
        self.sqs_patcher.stop()

    def test_process_order_json(self):
        self.mock_sqs_client.send_message.return_value = {"MessageId": "12345"}
        response = handler(self.json_event, self.context)
        self.assertEqual(response["statusCode"], 200)
        self.mock_sqs_client.send_message.assert_called_once()

    def test_process_order_xml(self):
        self.mock_sqs_client.send_message.return_value = {"MessageId": "12345"}
        response = handler(self.xml_event, self.context)
        self.assertEqual(response["statusCode"], 200)
        self.mock_sqs_client.send_message.assert_called_once()

    def test_process_unsupported_media_type(self):
        unsupported_event = self.json_event.copy()
        unsupported_event["headers"] = {"Content-Type": "text/plain"}
        response = handler(unsupported_event, self.context)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Unsupported media type", response["body"])
