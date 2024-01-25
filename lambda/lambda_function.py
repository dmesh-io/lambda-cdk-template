import logging
import os

import boto3


def handler(event, context):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=os.getenv("postgres_secret_arn"))
    print(response)
    logging.info(response)
    logging.info(event)
    return "my return value"
