# api-lambda-sqs-multiple-consumer

This project demonstrates a serverless architecture for handling multi-format order processing using AWS services. It consists of:

- An API Gateway endpoint that accepts both JSON and XML order payloads
- A Lambda function that validates and routes orders to SQS based on their format
- Two specialized Lambda consumers that process JSON and XML orders respectively
- A DynamoDB table for storing processed orders

## Architecture

1. API Gateway accepts POST requests with either `application/json` or `application/xml` content types
2. The ingestion Lambda function validates the payload and sends it to an SQS queue
3. Two separate Lambda functions consume from the queue:
   - JSON consumer processes and stores JSON formatted orders
   - XML consumer processes and stores XML formatted orders
4. Both consumers store the processed orders in a DynamoDB table with a format indicator

## Powertools features

Powertools provides three core utilities:

- **[Tracing](https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/)** - Decorators and utilities to trace Lambda function handlers, and both synchronous and asynchronous functions
- **[Logging](https://awslabs.github.io/aws-lambda-powertools-python/latest/core/logger/)** - Structured logging made easier, and decorator to enrich structured logging with key Lambda context details
- **[Metrics](https://awslabs.github.io/aws-lambda-powertools-python/latest/core/metrics/)** - Custom Metrics created asynchronously via CloudWatch Embedded Metric Format (EMF)

Find the complete project's [documentation here](https://awslabs.github.io/aws-lambda-powertools-python).

### Installing AWS Lambda Powertools for Python

With [pip](https://pip.pypa.io/en/latest/index.html) installed, run:

```bash
pip install aws-lambda-powertools
```

### Powertools Examples

- [Tutorial](https://awslabs.github.io/aws-lambda-powertools-python/latest/tutorial)
- [Serverless Shopping cart](https://github.com/aws-samples/aws-serverless-shopping-cart)
- [Serverless Airline](https://github.com/aws-samples/aws-serverless-airline-booking)
- [Serverless E-commerce platform](https://github.com/aws-samples/aws-serverless-ecommerce-platform)
- [Serverless GraphQL Nanny Booking Api](https://github.com/trey-rosius/babysitter_api)
