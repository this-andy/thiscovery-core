import logging
from pythonjsonlogger import jsonlogger
import re
import json
import uuid
import os
from dateutil import parser



# region Custom error classes and handling

class DetailedValueError(ValueError):
    def __init__(self, message, details):
        self.message = message
        self.details = details

    def as_response_body(self):
        return json.dumps({**{'message': self.message}, **self.details})


class UserDoesNotExistError(DetailedValueError):
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


# removes newlines and multiple spaces
def minimise_white_space(s):
    return re.sub(' +', ' ', s.replace('\n', ' '))


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


def get_file_as_string(path):
    """ Reads and returns the entire contents of a file """
    with open(path, 'r') as f:
        return f.read()


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


# region Secret settings handling

secrets_filename = 'secret-settings.json'
try:
    secrets = json.loads(get_file_as_string(secrets_filename))
except FileNotFoundError:
    # legitimate reason for file not being found is that we are running test scripts from different directory
    secrets_filename = '../' + secrets_filename
    secrets = json.loads(get_file_as_string(secrets_filename))


def get_secret(secret_name):
    try:
        return secrets[secret_name]
    except KeyError:
        errorjson = {'secret_name': secret_name}
        raise DetailedValueError('Secret key not found', errorjson)

# endregion


if __name__ == "__main__":
    result = get_secret('aws_rds_connection')
    print(result)
