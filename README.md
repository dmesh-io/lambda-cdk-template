# Lambda Function Template with AWS CDK

This is ready-to-use cookiecutter template to create a project that deploys a serverless AWS Lambda Function (Docker
Image) with the AWS Cloud Development Kit (CDK).

## Requirements

- [Python 3.10](https://www.python.org/downloads/)
- [Cookiecutter](https://github.com/cookiecutter/cookiecutter)
- [Configs](#configs)

## Configs

You must provide a config path that contains this directory structure:

```text
.
├── schemas
│       ├── schema-v1.json
│       ├── schema-v1.json
│       ├── ...
├── input.json
├── output.json
└── secrets.json
```

### input.json

...

### output.json

...

### secrets.json

...

## How to use

Clone and change to this repository. Execute cookiecutter and follow the input directions.

```shell
git clone git@github.com:dmesh-io/cdk-lambda.git
cd cdk-lambda
cookiecutter .
```

OR do this in one step:

```shell
cookiecutter git@github.com:dmesh-io/cdk-lambda.git
```
