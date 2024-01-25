import json
from pathlib import Path
from typing import List

from aws_cdk import Duration, Stack
from aws_cdk.aws_appconfig import (
    CfnApplication,
    CfnConfigurationProfile,
    CfnDeployment,
    CfnDeploymentStrategy,
    CfnEnvironment,
    CfnHostedConfigurationVersion,
)
from aws_cdk.aws_ecr import Repository
from aws_cdk.aws_iam import Effect, PolicyStatement, Role, ServicePrincipal
from aws_cdk.aws_kinesis import IStream, Stream
from aws_cdk.aws_lambda import (
    Architecture,
    DockerImageCode,
    DockerImageFunction,
    StartingPosition,
)
from aws_cdk.aws_lambda_event_sources import KinesisEventSource
from aws_cdk.aws_secretsmanager import ISecret, Secret
from config import Config
from constructs import Construct


def get_filenames_of_path(path: Path, ext: str = "*") -> List[Path]:
    """
    Returns a list of files in a directory/path. Uses pathlib.
    """
    filenames = [file for file in path.glob(ext) if file.is_file()]
    assert len(filenames) > 0, f"No files found in path: {path}"
    return filenames


def read_json_config(path: Path):
    with open(path, "r") as fh:
        data: dict = json.load(fh)
        return data


class LambdaStack(Stack):
    """
    Creates an AWS Lambda Function (Docker image) with AWS Kinesis Stream as the event source.

    A Docker image is built and pushed to a private ECR. If the ECR does not exist, it is automatically created.
    If an ECR image is given in the config this will be used otherwise the local Dockerfile is used as the image

    The AWS Lambda Function uses AWS AppConfig to retrieve application information.
    For this to work, you either need to add the AWS AppConfig Agent to the Docker image: https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-integration-lambda-extensions-container-image.html
    OR use boto3 in your application code.

    In the context of AWS AppConfig, these actions are performed:
    - Creating an application
    - Creating an environment
    - Creating a configuration profile
    - Creating a deployment strategy
    - Deploying the configuration

    The AWS lambda function is given the permission to retrieve provided secrets (ARNs) from the secrets manager.

    """

    def __init__(self, scope: Construct, id: str, config: Config, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.config: Config = config

        self._build()

    def _build(self) -> None:
        environment: dict = (
            {} if self.config.FUNCTION_ENV is None else self.config.FUNCTION_ENV
        )

        # create aws app config
        app_config: CfnApplication = CfnApplication(
            self, "ApplicationConfig", name=self.config.APP_CONFIG_NAME
        )

        environment["app_config_app_name"] = app_config.name

        app_env: CfnEnvironment = CfnEnvironment(
            self,
            "Environment",
            application_id=app_config.attr_application_id,
            name=self.config.APP_CONFIG_ENV_NAME,
        )

        environment["app_config_environment_name"] = app_env.name

        app_deployment_strategy: CfnDeploymentStrategy = CfnDeploymentStrategy(
            self,
            "DeploymentStrategy",
            deployment_duration_in_minutes=0,
            growth_factor=1.0,
            replicate_to="NONE",
            name=self.config.APP_CONFIG_DEPLOYMENT_STRAT_NAME,
        )

        destination_path: Path = (
            Path(self.config.CONFIG_PATH) / "destination-config.json"
        )

        paths: List[Path] = get_filenames_of_path(
            path=Path(self.config.CONFIG_PATH) / "schemas", ext="*.json"
        ) + [destination_path]

        for path in paths:
            json_data: dict = read_json_config(path)

            app_profile: CfnConfigurationProfile = CfnConfigurationProfile(
                self,
                f"Profile-{path.stem}",
                application_id=app_config.attr_application_id,
                name=path.stem,
                location_uri="hosted",
            )

            hosted_configuration_version: CfnHostedConfigurationVersion = (
                CfnHostedConfigurationVersion(
                    self,
                    path.stem,
                    application_id=app_config.attr_application_id,
                    configuration_profile_id=app_profile.attr_configuration_profile_id,
                    content=json.dumps(json_data),
                    content_type="application/json",
                )
            )
            app_deployment: CfnDeployment = CfnDeployment(
                self,
                f"AppDeployment-{path.stem}",
                application_id=app_config.attr_application_id,
                configuration_profile_id=app_profile.attr_configuration_profile_id,
                configuration_version=hosted_configuration_version.ref,
                deployment_strategy_id=app_deployment_strategy.ref,
                environment_id=app_env.ref,
            )

        # get kinesis reference
        kinesis: IStream = Stream.from_stream_arn(
            self, "KinesisEventSource", stream_arn=self.config.KINESIS_ARN_INPUT
        )

        # create new role for the lambda function
        lambda_role: Role = Role(
            self, "LambdaRole", assumed_by=ServicePrincipal("lambda.amazonaws.com")
        )

        # allow lambda function SP to retrieve secrets from the secrets manager
        for secret in self.config.SECRETS:
            # make sure the secret exists
            secret_ref: ISecret = Secret.from_secret_complete_arn(
                self, secret, secret_complete_arn=secret
            )

        # make sure the secret exists
        secret_postgresql_ref: ISecret = Secret.from_secret_complete_arn(
            self,
            self.config.SECRET_POSTGRESQL,
            secret_complete_arn=self.config.SECRET_POSTGRESQL,
        )

        environment["postgres_secret_arn"] = self.config.SECRET_POSTGRESQL
        environment["kinesis_arn_output"] = self.config.KINESIS_ARN_OUTPUT

        lambda_role.add_to_policy(
            statement=PolicyStatement(
                effect=Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=self.config.SECRETS,
            )
        )
        lambda_role.add_to_policy(
            statement=PolicyStatement(
                effect=Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[self.config.SECRET_POSTGRESQL],
            )
        )

        lambda_role.add_to_policy(
            statement=PolicyStatement(
                effect=Effect.ALLOW,
                actions=[
                    "appconfig:GetConfiguration",
                    "appconfig:GetApplication",
                    "appconfig:GetLatestConfiguration",
                    "appconfig:StartConfigurationSession",
                ],
                resources=[
                    f"arn:aws:appconfig:*:{self.config.ACCOUNT_ID}:application/*",
                ],
            )
        )

        lambda_role.add_to_policy(
            statement=PolicyStatement(
                effect=Effect.ALLOW,
                actions=["logs:CreateLogGroup"],
                resources=[
                    f"arn:aws:logs:{self.config.REGION}:{self.config.ACCOUNT_ID}:*"
                ],
            )
        )

        lambda_role.add_to_policy(
            statement=PolicyStatement(
                effect=Effect.ALLOW,
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[
                    f"arn:aws:logs:{self.config.REGION}:{self.config.ACCOUNT_ID}:log-group:/aws/lambda/{self.config.FUNCTION_NAME}"
                ],
            )
        )

        lambda_role.add_to_policy(
            statement=PolicyStatement(
                effect=Effect.ALLOW,
                actions=["kinesis:PutRecord", "kinesis:PutRecords"],
                resources=[self.config.KINESIS_ARN_OUTPUT],
            )
        )

        if self.config.DOCKER_IMAGE_TAG and self.config.DOCKER_IMAGE_TAG:
            code: DockerImageCode = DockerImageCode.from_ecr(
                repository=Repository.from_repository_name(
                    self, "Repository", repository_name=self.config.DOCKER_IMAGE_REPO
                ),
                tag_or_digest=self.config.DOCKER_IMAGE_TAG,
            )
        else:
            code: DockerImageCode = DockerImageCode.from_image_asset(directory=".")

        # create lambda function with docker
        lambda_function: DockerImageFunction = DockerImageFunction(
            self,
            "LambdaFunction",
            function_name=self.config.FUNCTION_NAME,
            code=code,
            architecture=Architecture.X86_64,
            description=self.config.FUNCTION_DESCRIPTION,
            memory_size=self.config.FUNCTION_MEMORY_SIZE,
            timeout=Duration.seconds(self.config.FUNCTION_TIMEOUT),
            vpc=self.config.FUNCTION_VPC,
            environment=environment,
            role=lambda_role,
        )

        # add event source (kinesis)
        lambda_function.add_event_source(
            source=KinesisEventSource(
                stream=kinesis, starting_position=StartingPosition.LATEST
            )
        )

        # TODO: better solution for tags (julia)

        # PostgreSQL permission
        # lambda_function.add_permission()
        # TODO: allow the lambda function to write on the table in postgreSQL database
        # TODO: cookie cutter magic
