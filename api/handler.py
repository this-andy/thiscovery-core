import json
import os
from api.utilities import get_logger, get_correlation_id


def ping(event, context):
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
        "statusCode": 200,
        "body": json.dumps(body)
    }

    correlation_id = get_correlation_id(event)
    logger.info('API call', extra={'correlation_id': correlation_id, 'event': event})

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
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response


if __name__ == "__main__":
    result = hubspot_entity_info(None, None)
    print(result)