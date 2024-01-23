from aws_cdk import Duration, Stack
from aws_cdk.aws_kinesis import IStream, Stream
from aws_cdk.aws_lambda import Architecture, Code, Function, Runtime, StartingPosition
from aws_cdk.aws_lambda_event_sources import KinesisEventSource
from config import Config
from constructs import Construct


class LambdaStack(Stack):
    """
    TODO: Description
    """

    def __init__(self, scope: Construct, id: str, config: Config, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.config: Config = config

        self._build()

    def _build(self) -> None:
        environment: dict = (
            {} if self.config.FUNCTION_ENV is None else self.config.FUNCTION_ENV
        )

        # get kinesis reference
        kinesis: IStream = Stream.from_stream_arn(
            self, "KinesisEventSource", stream_arn=self.config.KINESIS_ARN
        )

        # create lambda function
        lambda_function: Function = Function(
            self,
            "LambdaFunction",
            function_name=self.config.FUNCTION_NAME,
            code=Code.from_asset(self.config.FUNCTION_LOCATION),
            handler="lambda_function.handler",
            runtime=Runtime.PYTHON_3_10,
            architecture=Architecture.X86_64,
            description=self.config.FUNCTION_DESCRIPTION,
            memory_size=self.config.FUNCTION_MEMORY_SIZE,
            timeout=Duration.seconds(self.config.FUNCTION_TIMEOUT),
            vpc=self.config.FUNCTION_VPC,
            environment=environment,
            # role="TODO",
        )

        # add event source (kinesis)
        lambda_function.add_event_source(
            source=KinesisEventSource(
                stream=kinesis, starting_position=StartingPosition.LATEST
            )
        )

        # layers
        # lambda_function.add_layers()

        # permission
        # lambda_function.add_permission
