import logging


def handler(event, context):
    print(f"This is the context {context}")
    logging.info(event)
    logging.info(context)
    return "my return value"
