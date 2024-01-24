from typing import List, Optional

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    ACCOUNT_ID: str
    REGION: str

    # Kinesis
    KINESIS_ARN: str

    # AppConfig
    APP_CONFIG_NAME: str
    APP_CONFIG_ENV_NAME: str
    APP_CONFIG_PROFILE_NAME: str
    APP_CONFIG_DEPLOYMENT_STRAT_NAME: str

    # SECRETS
    SECRETS: List[str]

    # Lambda
    FUNCTION_NAME: str = "LambdaFunctionKinesis"
    FUNCTION_LOCATION: str = "lambda"
    FUNCTION_DESCRIPTION: str = "Lambda Function Kinesis"
    FUNCTION_MEMORY_SIZE: int = 128  # in MB
    FUNCTION_TIMEOUT: int = 60  # in seconds
    FUNCTION_VPC: Optional[str] = None
    FUNCTION_ENV: Optional[dict] = None
