from aws_cdk import App, Environment

from config import Config
from lambda_stack import LambdaStack

config: Config = Config(_env_file=".env")

app: App = App()

LambdaStack(
    scope=app,
    id="LambdaStack",
    env=Environment(account=config.ACCOUNT_ID, region=config.REGION)
)

if __name__ == "__main__":
    app.synth()
