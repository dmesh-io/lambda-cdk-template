from aws_cdk import Duration, Stack
from aws_cdk.aws_appconfig import (
    CfnApplication,
    CfnConfigurationProfile,
    CfnDeploymentStrategy,
    CfnEnvironment,
    CfnHostedConfigurationVersion,
)
from aws_cdk.aws_iam import Effect, PolicyStatement, Role, ServicePrincipal
from aws_cdk.aws_kinesis import IStream, Stream
from aws_cdk.aws_lambda import (
    Architecture,
    DockerImageCode,
    DockerImageFunction,
    StartingPosition,
)
from aws_cdk.aws_lambda_event_sources import KinesisEventSource
from config import Config
from constructs import Construct


class LambdaStack(Stack):
    """
    Creates an AWS Lambda Function (Docker image) with AWS Kinesis Stream as the event source.

    A Docker image is built and pushed to a private ECR. If the ECR does not exist, it is automatically created.

    The AWS Lambda Function uses AWS AppConfig to retrieve application information.
    For this to work, you need to add the AWS AppConfig Agent to the Docker image: https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-integration-lambda-extensions-container-image.html


    In the context of AWS AppConfig, these actions are performed:
    - Creating an application
    - Creating an environment
    - Creating a configuration profile
    - Creating a deployment strategy
    - Deploying the configuration
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

        app_env: CfnEnvironment = CfnEnvironment(
            self,
            "Environment",
            application_id=app_config.attr_application_id,
            name=self.config.APP_CONFIG_ENV_NAME,
        )

        app_profile: CfnConfigurationProfile = CfnConfigurationProfile(
            self,
            "Profile",
            application_id=app_config.attr_application_id,
            name=self.config.APP_CONFIG_PROFILE_NAME,
            location_uri="hosted",
        )

        app_deployment_strategy: CfnDeploymentStrategy = CfnDeploymentStrategy(
            self,
            "DeploymentStrategy",
            deployment_duration_in_minutes=1,
            growth_factor=1.0,
            replicate_to="NONE",
            name=self.config.APP_CONFIG_DEPLOYMENT_STRAT_NAME,
        )

        hosted_configuration_version: CfnHostedConfigurationVersion = (
            CfnHostedConfigurationVersion(
                self,
                "HostedConfiguration",
                application_id=app_config.attr_application_id,
                configuration_profile_id=app_profile.attr_configuration_profile_id,
                content="abc",
                content_type="text/plain",  # use json as an alternative
            )
        )

        # get kinesis reference
        kinesis: IStream = Stream.from_stream_arn(
            self, "KinesisEventSource", stream_arn=self.config.KINESIS_ARN
        )

        # create new role for the lambda function
        lambda_role: Role = Role(
            self, "LambdaRole", assumed_by=ServicePrincipal("lambda.amazonaws.com")
        )

        lambda_role.add_to_policy(
            statement=PolicyStatement(
                effect=Effect.ALLOW,
                actions=["appconfig:GetConfiguration"],
                resources=[
                    "*"
                ],  # TODO: restrict access to the app config (requires ARN)
            )
        )

        # create lambda function with docker
        lambda_function: DockerImageFunction = DockerImageFunction(
            self,
            "LambdaFunction",
            function_name=self.config.FUNCTION_NAME,
            code=DockerImageCode.from_image_asset(directory="."),
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

        # TODO: Make the lambda function use app config (add AWS AppConfig Agent to the Docker image: https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-integration-lambda-extensions-container-image.html)

        # TODO: Test if the lambda can retrieve the app config data

        # TODO: Find out how to make the deployment work

        # from aws_cdk.aws_appconfig import (
        #     CfnDeployment
        # )
        #
        # app_deployment: CfnDeployment = CfnDeployment(
        #     self,
        #     "AppDeployment",
        #     application_id=app_config.attr_application_id,
        #     configuration_profile_id=app_profile.attr_configuration_profile_id,
        #     configuration_version=hosted_configuration_version.logical_id,
        #     deployment_strategy_id=app_deployment_strategy.logical_id,
        #     environment_id=app_env.logical_id,
        # )

        # permission
        # lambda_function.add_permission # TODO
        # allow the lambda function to write on the table in postgreSQL database
        # allow the lambda function to access secrets (always aws secrets manager) -> create manually


# 2. aws config with permissions
# 2.5 configure lambda to retrieve app config data
# 3. aws secrets manager with permissions
# 4. cookie cutter magic
