import boto3
import pytest
import requests
from typing import Generator

class TestConfig:
    """Test configuration with environment-specific values"""
    STACK_NAME = "api-lambda-sqs-multiple-consumer"  # Replace with your stack name
    DYNAMODB_TABLE = "Orders"
    AWS_REGION = "eu-west-1"

    @classmethod
    def get_api_url(cls) -> str:
        """Get API Gateway URL from CloudFormation stack outputs"""
        cfn = boto3.client('cloudformation', region_name=cls.AWS_REGION)
        try:
            response = cfn.describe_stacks(StackName=cls.STACK_NAME)
            outputs = response['Stacks'][0]['Outputs']
            for output in outputs:
                if output['OutputKey'] == 'OrderApi':
                    return output['OutputValue']
            raise ValueError("OrderApi URL not found in stack outputs")
        except Exception as e:
            raise Exception(f"Failed to get API URL from CloudFormation: {str(e)}")

    @classmethod
    def _check_dynamodb_table_exists(cls, table_name: str) -> bool:
        """Check if DynamoDB table exists"""
        try:
            dynamodb = boto3.client('dynamodb', region_name=cls.AWS_REGION)
            response = dynamodb.describe_table(TableName=table_name)
            return response['Table']['TableStatus'] == 'ACTIVE'
        except dynamodb.exceptions.ResourceNotFoundException:
            return False

@pytest.fixture(scope="session")
def dynamodb_client():
    return boto3.client("dynamodb", region_name=TestConfig.AWS_REGION)

@pytest.fixture(scope="session")
def dynamodb_table(dynamodb_client) -> Generator:
    """Create and delete test table"""
    try:
        dynamodb_client.create_table(
            TableName=TestConfig.DYNAMODB_TABLE,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        dynamodb_client.get_waiter("table_exists").wait(TableName=TestConfig.DYNAMODB_TABLE)
        yield TestConfig.DYNAMODB_TABLE
    finally:
        dynamodb_client.delete_table(TableName=TestConfig.DYNAMODB_TABLE)
        dynamodb_client.get_waiter("table_not_exists").wait(TableName=TestConfig.DYNAMODB_TABLE)

@pytest.fixture(scope="session")
def http_client():
    """Session-scoped requests session"""
    with requests.Session() as session:
        yield session
