import json
import logging
import os
import time
import unittest
import uuid
import xml.etree.ElementTree as ET

import boto3
import requests

from .test_fixtures import TestConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestOrdersApi(unittest.TestCase):
    @classmethod
    def _check_dynamodb_table_exists(cls, table_name: str) -> bool:
        """Check if DynamoDB table exists"""
        try:
            response = cls.dynamodb_client.describe_table(TableName=table_name)
            return response["Table"]["TableStatus"] == "ACTIVE"
        except cls.dynamodb_client.exceptions.ResourceNotFoundException:
            return False

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are shared across all tests"""
        try:
            logger.info("Setting up test environment")
            cls.dynamodb_client = boto3.client(
                "dynamodb", region_name=TestConfig.AWS_REGION
            )
            cls.http_client = requests.Session()
            cls.api_url = TestConfig.get_api_url()
            logger.info(f"Using API URL: {cls.api_url}")

            if not cls._check_dynamodb_table_exists(TestConfig.DYNAMODB_TABLE):
                logger.error(f"Table {TestConfig.DYNAMODB_TABLE} does not exist")
                raise ValueError(
                    f"DynamoDB table {TestConfig.DYNAMODB_TABLE} does not exist"
                )
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}", exc_info=True)
            raise

    @classmethod
    def tearDownClass(cls):
        pass

    def _read_file(self, filename: str) -> str:
        """Helper method to read file content"""
        file_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "events", filename
        )
        with open(file_path, "r") as f:
            return f.read()

    def _verify_order_in_dynamodb(
        self, order_id: str, expected_email: str, expected_format: str
    ):
        """Helper method to verify order in DynamoDB with retries"""
        logger.info(f"Verifying order in DynamoDB: {order_id}")
        for attempt in range(5):
            result = self.dynamodb_client.get_item(
                TableName=TestConfig.DYNAMODB_TABLE, Key={"id": {"S": order_id}}
            )
            if "Item" in result:
                break
            wait_time = 2**attempt
            logger.info(f"Order not found, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            self.fail(
                f"Order not found in DynamoDB after multiple attempts: {order_id}"
            )

        stored_order = result["Item"]
        self.assertEqual(stored_order["id"]["S"], order_id, "Order ID mismatch")
        self.assertEqual(
            stored_order["customer_email"]["S"],
            expected_email,
            "Customer email mismatch",
        )
        self.assertEqual(
            stored_order["format"]["S"],
            expected_format,
            f"Format should be {expected_format}",
        )
        return stored_order

    def _send_order(self, content_type: str, data: dict | str) -> requests.Response:
        """Helper method to send order to API"""
        logger.info(f"Sending {content_type} request to {self.api_url}")
        return self.http_client.post(
            self.api_url,
            headers={"Content-Type": content_type},
            json=data if content_type == "application/json" else None,
            data=data if content_type == "application/xml" else None,
            timeout=10,
        )

    def _replace_json_ids(self, order_data: dict) -> tuple[str, str]:
        """Replace order and customer IDs with new UUIDs in JSON data"""
        new_order_id = str(uuid.uuid4())
        new_customer_id = str(uuid.uuid4())

        order_data["id"] = new_order_id
        order_data["customer_id"] = new_customer_id

        return new_order_id, new_customer_id

    def _replace_xml_ids(self, xml_content: str) -> tuple[str, str, ET.Element]:
        """Replace order and customer IDs with new UUIDs in XML content"""
        root = ET.fromstring(xml_content)
        new_order_id = str(uuid.uuid4())
        new_customer_id = str(uuid.uuid4())

        id_elem = root.find("id")
        customer_id_elem = root.find("customer_id")

        if id_elem is not None:
            id_elem.text = new_order_id
        if customer_id_elem is not None:
            customer_id_elem.text = new_customer_id

        return new_order_id, new_customer_id, root

    def test_create_json_order(self):
        try:
            # Read and modify test JSON order
            json_content = self._read_file("order.json")
            order = json.loads(json_content)
            order_id, customer_id = self._replace_json_ids(order)

            logger.info(
                f"Testing with JSON order ID: {order_id}, customer ID: {customer_id}"
            )

            # Send order through API
            response = self._send_order("application/json", order)
            self.assertEqual(
                response.status_code,
                200,
                f"API request failed with status {response.status_code}",
            )

            # Verify in DynamoDB
            self._verify_order_in_dynamodb(
                order_id=order_id,
                expected_email=order["customer_email"],
                expected_format="json",
            )

        except Exception as e:
            logger.error(f"Test failed: {str(e)}", exc_info=True)
            raise

    def test_create_xml_order(self):
        try:
            # Read and modify test XML order
            xml_content = self._read_file("order.xml")
            order_id, customer_id, root = self._replace_xml_ids(xml_content)
            modified_xml = ET.tostring(root, encoding="unicode")

            logger.info(
                f"Testing with XML order ID: {order_id}, customer ID: {customer_id}"
            )

            # Send order through API
            response = self._send_order("application/xml", modified_xml)
            self.assertEqual(
                response.status_code,
                200,
                f"API request failed with status {response.status_code}",
            )

            # Verify in DynamoDB
            self._verify_order_in_dynamodb(
                order_id=order_id,
                expected_email=root.find("customer_email").text,
                expected_format="xml",
            )

        except Exception as e:
            logger.error(f"XML test failed: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    unittest.main()
