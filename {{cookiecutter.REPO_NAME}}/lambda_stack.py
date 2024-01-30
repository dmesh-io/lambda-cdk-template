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
from config import Config, InputType, OutputType, read_json_config
from constructs import Construct


class LambdaStack(Stack):
    """
    Creates an AWS Lambda Function (Docker image) with an event source as input.
    Default: AWS Kinesis Stream.

    A Docker image (Dockerfile) is built and pushed to a private ECR.
    If the ECR does not exist, it is automatically created.
    Alternatively, an ECR image can be provided.

    The AWS Lambda Function uses AWS AppConfig to retrieve application information.
    For this to work, you either need to add the AWS AppConfig Agent to the Docker image:
    https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-integration-lambda-extensions-container-image.html
    OR use boto3 in your application code. The latter is used here.

    In the context of AWS AppConfig, these actions are performed:
    - Creating an application
    - Creating an environment
    - Creating a configuration profile
    - Creating a deployment strategy
    - Deploying the configuration

    Every config file is mapped to an AWS AppConfig Profile.

    The AWS Lambda Function is given the permission to retrieve provided secrets (ARNs) from the AWS Secrets Manager.

    """

    def __init__(self, scope: Construct, id: str, config: Config, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.config: Config = config

        self._build()

    def _build(self) -> None:
        # create new role for the lambda function
        lambda_role: Role = Role(
            self,
            f"LambdaRole{self.config.APP_CONFIG_ENV_NAME}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"),
        )

        # allow lambda function to log
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

        # aws app config application
        self.app_config: CfnApplication = CfnApplication(
            self,
            f"ApplicationConfig{self.config.APP_CONFIG_ENV_NAME}",
            name=f"{self.config.APP_CONFIG_NAME}_{self.config.APP_CONFIG_ENV_NAME}",
        )

        # aws app config env
        self.app_env: CfnEnvironment = CfnEnvironment(
            self,
            f"Environment{self.config.APP_CONFIG_ENV_NAME}",
            application_id=self.app_config.attr_application_id,
            name=f"{self.config.APP_CONFIG_ENV_NAME}",
        )

        # aws app config deployment strategy
        self.app_deployment_strategy: CfnDeploymentStrategy = CfnDeploymentStrategy(
            self,
            f"AppConfigDeploymentStrategy{self.config.APP_CONFIG_ENV_NAME}",
            deployment_duration_in_minutes=0,
            growth_factor=1.0,
            replicate_to="NONE",
            name=f"{self.config.APP_CONFIG_DEPLOYMENT_STRATEGY_NAME}_{self.config.APP_CONFIG_ENV_NAME}",
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

        # for each schema and config, we create & deploy an aws app config profile

        schema_paths: List[Path] = self.config.schema_paths

        for schema_path in schema_paths:
            self.deploy_app_env(schema_path)

        config_paths: List[Path] = [
            self.config.input_config_path,
            self.config.output_config_path,
            self.config.secrets_config_path,
            self.config.transform_config_path,
        ]

        for config_path in config_paths:
            self.deploy_app_env(config_path)

        # allow lambda function SP to retrieve secrets from the secrets manager
        for secret_name, secret_arn in self.config.secrets_config_data.items():
            # make sure the secret exists
            secret_ref: ISecret = Secret.from_secret_complete_arn(  # noqa: F841
                self, secret_name, secret_complete_arn=secret_arn
            )

            lambda_role.add_to_policy(
                statement=PolicyStatement(
                    effect=Effect.ALLOW,
                    actions=["secretsmanager:GetSecretValue"],
                    resources=[secret_arn],
                )
            )

        # Docker
        if self.config.DOCKER_IMAGE != "local":
            docker_image_repo, docker_image_tag = self.config.DOCKER_IMAGE.split(":")

            code: DockerImageCode = DockerImageCode.from_ecr(
                repository=Repository.from_repository_name(
                    self,
                    f"Repository{self.config.APP_CONFIG_ENV_NAME}",
                    repository_name=docker_image_repo,
                ),
                tag_or_digest=docker_image_tag,
            )
        else:
            code: DockerImageCode = DockerImageCode.from_image_asset(directory=".")

        # environment variables for the lambda function
        environment: dict = (
            {} if self.config.FUNCTION_ENV is None else self.config.FUNCTION_ENV
        )
        environment["app_config_app_name"] = self.app_config.name
        environment["app_config_environment_name"] = self.app_env.name
        environment["app_config_profile_input"] = "input"
        environment["app_config_profile_output"] = "output"
        environment["app_config_secrets"] = "secrets"
        environment["app_config_transform"] = "transform"

        # create lambda function with docker image
        lambda_function: DockerImageFunction = DockerImageFunction(
            self,
            f"LambdaFunction{self.config.APP_CONFIG_ENV_NAME}",
            function_name=f"{self.config.FUNCTION_NAME}_{self.config.APP_CONFIG_ENV_NAME}",
            code=code,
            architecture=Architecture.X86_64,
            description=self.config.FUNCTION_DESCRIPTION,
            memory_size=self.config.FUNCTION_MEMORY_SIZE,
            timeout=Duration.seconds(self.config.FUNCTION_TIMEOUT),
            vpc=self.config.FUNCTION_VPC,
            environment=environment,
            role=lambda_role,
        )

        # INPUT
        if self.config.INPUT_TYPE == InputType.KINESIS:
            arn_input: str = self.config.input_config_data["arn"]

            # get kinesis reference
            kinesis: IStream = Stream.from_stream_arn(
                self,
                f"KinesisInputEventSource{self.config.APP_CONFIG_ENV_NAME}",
                stream_arn=arn_input,
            )

            # add event source (kinesis)
            lambda_function.add_event_source(
                source=KinesisEventSource(
                    stream=kinesis, starting_position=StartingPosition.LATEST
                )
            )

        # OUTPUT
        if self.config.OUTPUT_TYPE == OutputType.KINESIS:
            arn_output: str = self.config.output_config_data["arn"]

            # get kinesis reference
            kinesis: IStream = Stream.from_stream_arn(
                self,
                f"KinesisOutputEventSource{self.config.APP_CONFIG_ENV_NAME}",
                stream_arn=arn_output,
            )

            # allow lambda function to put records
            lambda_role.add_to_policy(
                statement=PolicyStatement(
                    effect=Effect.ALLOW,
                    actions=["kinesis:PutRecord", "kinesis:PutRecords"],
                    resources=[arn_output],
                )
            )
        elif self.config.OUTPUT_TYPE == OutputType.POSTGRESQL:
            arn_output: str = self.config.output_config_data["arn"]

            # no need to do anything permission-wise
            # if the lambda has the master key of the postgresql database

    def deploy_app_env(self, path):
        json_data: dict = read_json_config(path)

        app_profile: CfnConfigurationProfile = CfnConfigurationProfile(
            self,
            f"Profile_{self.config.APP_CONFIG_ENV_NAME}_{path.stem}",
            application_id=self.app_config.attr_application_id,
            name=path.stem,
            location_uri="hosted",
        )

        hosted_configuration_version: CfnHostedConfigurationVersion = (
            CfnHostedConfigurationVersion(
                self,
                f"{self.config.APP_CONFIG_ENV_NAME}_{path.stem}",
                application_id=self.app_config.attr_application_id,
                configuration_profile_id=app_profile.attr_configuration_profile_id,
                content=json.dumps(json_data),
                content_type="application/json",
            )
        )

        app_deployment: CfnDeployment = CfnDeployment(  # noqa: F841
            self,
            f"Deployment_{self.config.APP_CONFIG_ENV_NAME}_{path.stem}",
            application_id=self.app_config.attr_application_id,
            configuration_profile_id=app_profile.attr_configuration_profile_id,
            configuration_version=hosted_configuration_version.ref,
            deployment_strategy_id=self.app_deployment_strategy.ref,
            environment_id=self.app_env.ref,
        )
