# {{cookiecutter.REPO_NAME}}

This project allows to deploy a serverless AWS Lambda Function (Docker
Image) with the AWS Cloud Development Kit (CDK).

The `input source` and the `destination (output)` are modular and controlled via the configuration
files `input.json` and `output.json` respectively.
Secrets are provided with a `secrets.json` config.
Transformations (JMESPath) are provided with the `transforms.json` config.
Data schemas & validations are provided with the `schemas` directory.

For more information, read [cdk-lambda](https://github.com/dmesh-io/cdk-lambda).

All configuration files are deployed as `profiles` in AWS AppConfig.

**Please note**: Do not provide any secrets in the config files!
Instead, add them in the AWS Secrets Manager and provide the corresponding ARNs of these secrets in the `secrets.json`.

## How to use

- Install [AWS CDK](https://aws.amazon.com/de/cdk/)
- Install [requirements.txt](requirements.txt):

```shell
pip install -r requirements.txt
```

- Deploy Lambda Function stack:

```shell
cdk deploy
```

## Multiple environments

Cookiecutter uses the [.env](.env) file to configure the AWS Lambda Function and all related resources.
If you want to create another environment,
change the `APP_CONFIG_ENV_NAME` value and optionally the path to your configurations `CONFIG_PATH`.
