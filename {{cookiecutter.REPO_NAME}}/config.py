import json
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


def read_json_config(path: Path):
    with open(path, "r") as fh:
        data: dict = json.load(fh)
        return data


def get_filenames_of_path(path: Path, ext: str = "*") -> List[Path]:
    """
    Returns a list of files in a directory/path. Uses pathlib.
    """
    filenames = [file for file in path.glob(ext) if file.is_file()]
    assert len(filenames) > 0, f"No files found in path: {path}"
    return filenames


class InputType(str, Enum):
    KINESIS: str = "kinesis"


class OutputType(str, Enum):
    POSTGRESQL: str = "postgresql"
    KINESIS: str = "kinesis"


class Config(BaseSettings):
    # AWS Account
    ACCOUNT_ID: str
    REGION: str

    # CONFIGS
    CONFIG_PATH: str  # location of the configs directory

    # Input
    INPUT_TYPE: InputType

    # Output
    OUTPUT_TYPE: OutputType

    # AppConfig
    APP_CONFIG_NAME: str
    APP_CONFIG_ENV_NAME: str
    APP_CONFIG_DEPLOYMENT_STRATEGY_NAME: str

    # Secrets
    SECRETS: List[str]

    # Lambda
    FUNCTION_NAME: str = "LambdaFunctionKinesis"
    FUNCTION_DESCRIPTION: str = "Lambda Function description"
    FUNCTION_MEMORY_SIZE: int = 128  # in MB
    FUNCTION_TIMEOUT: int = 60  # in seconds
    FUNCTION_VPC: Optional[str] = None
    FUNCTION_ENV: Optional[dict] = None

    # Docker (optional)
    DOCKER_IMAGE: str = "local"

    @cached_property
    def input_config_path(self) -> Path:
        return Path(self.CONFIG_PATH) / "input.json"

    @cached_property
    def output_config_path(self) -> Path:
        return Path(self.CONFIG_PATH) / "output.json"

    @cached_property
    def secrets_config_path(self) -> Path:
        return Path(self.CONFIG_PATH) / "secret.json"

    @cached_property
    def transform_config_path(self) -> Path:
        return Path(self.CONFIG_PATH) / "transform.json"

    @cached_property
    def input_config_data(self) -> dict:
        data: dict = read_json_config(self.input_config_path)
        self.validate_input_config_data()
        return data

    @cached_property
    def output_config_data(self) -> dict:
        data: dict = read_json_config(self.output_config_path)
        self.validate_output_config_data()
        return data

    @cached_property
    def secrets_config_data(self) -> dict:
        data: dict = read_json_config(self.secrets_config_path)
        self.validate_output_config_data()
        return data

    @cached_property
    def transform_config_data(self) -> dict:
        data: dict = read_json_config(self.transform_config_path)
        self.validate_transform_config_data()
        return data

    def validate_output_config_data(self):
        ...

    def validate_input_config_data(self):
        ...

    def validate_secrets_config_data(self):
        ...

    def validate_transform_config_data(self):
        ...

    @cached_property
    def schema_paths(self):
        files: List[Path] = get_filenames_of_path(
            path=Path(self.CONFIG_PATH) / "schemas", ext="*.json"
        )
        return files
