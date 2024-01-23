from aws_cdk import Stack
from aws_cdk.aws_lambda import Function, Runtime, Code
from constructs import Construct


class LambdaStack(Stack):
    """
    TODO: Description
    """

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self._build()

    def _build(self) -> None:
        lambda_function = Function(
            self,
            "LambdaFunction",
            code=Code.from_asset("lambda"),
            handler="lambda_function.handler",
            runtime=Runtime.PYTHON_3_10
        )
