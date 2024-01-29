import shutil
from pathlib import Path


def remove_dir(path: str) -> None:
    dir_to_remove: Path = Path(path)
    if dir_to_remove.exists() and dir_to_remove.is_dir():
        shutil.rmtree(dir_to_remove)


def remove_file(path: str) -> None:
    file_to_remove: Path = Path(path)
    if file_to_remove.exists() and file_to_remove.is_file():
        file_to_remove.unlink()


def validate_account_id() -> bool:
    # TODO: we can validate if the account_id exists
    if not isinstance("{{cookiecutter.ACCOUNT_ID}}", str):
        raise ValueError("{{cookiecutter.ACCOUNT_ID}} must be a string")
    return True


def validate_configs():
    # TODO: validate that configs are all valid and contain the correct set of variables:
    #  schemas, input.json, output.json, secrets.json
    return True


def validate_docker_image() -> True:
    # TODO: we should validate the docker image
    if not isinstance("{{cookiecutter.DOCKER_IMAGE}}", str):
        raise ValueError("{{cookiecutter.DOCKER_IMAGE}} must be a string")

    if ":" not in "{{cookiecutter.DOCKER_IMAGE}}":
        raise ValueError("Incorrect value for 'DOCKER_IMAGE'. Missing ':' character!")


if __name__ == "__main__":
    validate_account_id()
    validate_configs()
    remove_dir("configs-kinesis")
    remove_dir("configs-postgresql")
    if not "{{cookiecutter.DOCKER_IMAGE}}" == "local":
        remove_dir("lambda")
        remove_file("Dockerfile")
