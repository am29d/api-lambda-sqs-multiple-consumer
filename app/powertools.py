from aws_lambda_powertools import Logger, Metrics, Tracer

tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")
