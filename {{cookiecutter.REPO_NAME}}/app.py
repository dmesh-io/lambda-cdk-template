from aws_cdk import App, Environment
from config import Config
from lambda_stack import LambdaStack

config: Config = Config(_env_file=".env")

app: App = App()

LambdaStack(
    scope=app,
    id=f"LambdaStack{config.APP_CONFIG_ENV_NAME}",
    env=Environment(account=config.ACCOUNT_ID, region=config.REGION),
    config=config,
)

if __name__ == "__main__":
    app.synth()
