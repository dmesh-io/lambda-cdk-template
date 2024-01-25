import logging
import os

import boto3


def handler(event, context):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=os.getenv("postgres_secret_arn"))
    print(response)
    logging.info(response)
    logging.info(event)
    # write to kinesis stream
    kinesis_client = boto3.client('kinesis')
    kinesis_client.put_record(Data=b'some value', PartitionKey='1', StreamARN=os.getenv("kinesis_arn_output"))
    return "my return value"
