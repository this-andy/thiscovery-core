import os
import uuid
import logging
import re
import sys
import datetime
from dateutil import parser, tz
from pythonjsonlogger import jsonlogger
import json
import boto3
from botocore.exceptions import ClientError


# region Custom error classes and handling

class DetailedValueError(ValueError):
    def __init__(self, message, details):
        self.message = message
        self.details = details

    def as_response_body(self):
        return json.dumps({**{'message': self.message}, **self.details})

    def add_correlation_id(self, correlation_id):
        self.details['correlation_id'] = str(correlation_id)


class ObjectDoesNotExistError(DetailedValueError):
    pass


class DuplicateInsertError(DetailedValueError):
    pass


class PatchOperationNotSupportedError(DetailedValueError):
    pass


class PatchAttributeNotRecognisedError(DetailedValueError):
    pass


class PatchInvalidJsonError(DetailedValueError):
    pass


class DetailedIntegrityError(DetailedValueError):
    pass


def error_as_response_body(error_msg, correlation_id):
    return json.dumps({'error:': error_msg, 'correlation_id': str(correlation_id)})

# endregion


# region Misc utilities
# removes newlines and multiple spaces
def minimise_white_space(s):
    return re.sub(' +', ' ', s.replace('\n', ' '))


# Reads and returns the entire contents of a file
def get_file_as_string(path):
    with open(path, 'r') as f:
        return f.read()


def running_on_aws():
    try:
        region = os.environ['AWS_REGION']
    except:
        region = None

    return region is not None


def now_with_tz():
    return datetime.datetime.now(tz.tzlocal())

# endregion


# region Validation methods

def validate_int(s):
    try:
        int(s)
        return s
    except ValueError:
        errorjson = {'int': s}
        raise DetailedValueError('invalid integer', errorjson)


def validate_uuid(s):
    try:
        uuid.UUID(s, version=4)
        if uuid.UUID(s).version != 4:
            errorjson = {'uuid': s}
            raise DetailedValueError('uuid is not version 4', errorjson)
        return s
    except ValueError:
        errorjson = {'uuid': s}
        raise DetailedValueError('invalid uuid', errorjson)


def validate_utc_datetime(s):
    try:
        # date format should be like '2018-06-12 16:16:56.087895+01'
        parser.isoparse(s)
        return s
    except ValueError:
        errorjson = {'datetime': s}
        raise DetailedValueError('invalid utc format datetime', errorjson)

# endregion


# region Logging

logger = None

def get_logger():
    global logger
    if logger is None:
        logger = logging.getLogger()
        # print('creating logger')
        log_handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter('%(asctime)s %(module)s %(funcName)s %(lineno)d %(name)-2s %(levelname)-8s %(message)s')
        formatter.default_msec_format = '%s.%03d'
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
        logger.setLevel(logging.INFO)
    return logger

# endregion


# region Correlation id

def new_correlation_id():
    return uuid.uuid4()


def get_correlation_id(event):
    try:
        http_header = event['headers']
        correlation_id = http_header['Correlation_Id']
    except (KeyError, TypeError):  # KeyError if no correlation_id in headers, TypeError if no headers
        correlation_id = new_correlation_id()
    return correlation_id

# endregion

# region Secrets processing

secrets_filename = 'secret-settings.json'

try:
    secrets = json.loads(get_file_as_string(secrets_filename))
except FileNotFoundError:
    # legitimate reason for file not being found is that we are running test scripts from different directory or we are running on AWS
    secrets_filename = '../' + secrets_filename
    try:
        secrets = json.loads(get_file_as_string(secrets_filename))
    except FileNotFoundError:
        pass


def get_local_secret(secret_name):
    try:
        return secrets[secret_name]
    except KeyError:
        errorjson = {'secret_name': secret_name}
        raise DetailedValueError('Secret key not found', errorjson)


def get_secret(secret_name):
    if running_on_aws():
        return get_aws_secret(secret_name)
    else:
        return get_local_secret(secret_name)


def get_aws_secret(secret_name):
    logger = get_logger()
    secret_name = "database-connection"
    endpoint_url = "https://secretsmanager.eu-west-2.amazonaws.com"
    region_name = "eu-west-2"

    logger.info('get_aws_secret: ' + secret_name)

    session = boto3.session.Session()
    # logger.info('get_aws_secret:session created')
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
        endpoint_url=endpoint_url
    )

    secret= {"No": "secrets"}

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        # logger.info('get_aws_secret:secret retrieved')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.error("The requested secret " + secret_name + " was not found")
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            logger.error("The request was invalid due to:" + str(e))
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            logger.error("The request had invalid params:" + str(e))
        raise
    except:
        logger.error(sys.exc_info()[0])
    else:
        # logger.info('get_aws_secret:secret about to decode')
        # Decrypted secret using the associated KMS CMK
        # Depending on whether the secret was a string or binary, one of these fields will be populated
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            binary_secret_data = get_secret_value_response['SecretBinary']
        # logger.info('get_aws_secret:secret decoded')
        # logger.info('secret:' + secret)

        secret = json.loads(secret)
    finally:
        return secret

# endregion


if __name__ == "__main__":
    result = get_aws_secret('database-connection')
    # result = {"dbname": "citsci_platform", **result}
    print(result)

