import json
import os
from http import HTTPStatus
from api.utilities import get_logger, get_correlation_id, get_secret, get_start_time, get_elapsed_ms


def ping(event, context):
    start_time = get_start_time()
    logger = get_logger()

    region = ''
    aws = ''

    try:
        region = os.environ['AWS_REGION']
        aws = os.environ['AWS_EXECUTION_ENV']
    except:
        pass

    body = {
        "message": "Response from THIS Institute citizen science API",
        "region": region,
        "aws":aws,
        "input": event
    }

    response = {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(body)
    }

    correlation_id = get_correlation_id(event)
    logger.info('API call', extra={'correlation_id': correlation_id, 'event': event, 'elapsed_ms': get_elapsed_ms(start_time)})

    return response


def hubspot_entity_info(event, context):

    body = {
        "results": [
            {
                "objectId": 245,
                "title": "Eric's participation on Maternity care systematic review",
                "created": "2016-09-15",
                "study-id": "123abc",
                "reviews-completed": "234",
                "accuracy-percent": "56.7",
            },
        ]
    }

    response = {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(body)
    }

    return response


def connection_info(event, context):

    env_dict = get_secret('database-connection')
    t = str(type(env_dict))

    body = env_dict

    response = {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(body)
    }

    return response


if __name__ == "__main__":
    result = ping(None, None)
    # result = connection_info(None, None)
    print(result)