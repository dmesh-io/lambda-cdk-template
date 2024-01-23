from typing import Optional

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    ACCOUNT_ID: str
    REGION: str

    # Kinesis
    KINESIS_ARN: str

    # Lambda
    FUNCTION_NAME: str = "LambdaFunctionKinesis"
    FUNCTION_LOCATION: str = "lambda"
    FUNCTION_DESCRIPTION: str = "Lambda Function Kinesis"
    FUNCTION_MEMORY_SIZE: int = 128  # in MB
    FUNCTION_TIMEOUT: int = 60  # in seconds
    FUNCTION_VPC: Optional[str] = None
    FUNCTION_ENV: Optional[dict] = None
