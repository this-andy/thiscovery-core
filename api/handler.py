import json
from api.utilities import get_logger, get_correlation_id


def ping(event, context):
    logger = get_logger()

    body = {
        "message": "Response from THIS Institute citizen science API",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    correlation_id = get_correlation_id(event)
    logger.info('API call', extra={'correlation_id': correlation_id, 'event': event})

    return response
