#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#

import os
import uuid
import logging
import re
import sys
import datetime
from timeit import default_timer as timer
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


# region unit test methods

UNIT_TEST_NAMESPACE = '/test/'

def set_running_unit_tests(flag):
    if flag:
        os.environ["TESTING"] = 'true'
    else:
        os.unsetenv("TESTING")


def running_unit_tests():
    testing = os.getenv("TESTING")
    return testing == 'true'

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


def get_start_time():
    return timer()


def get_elapsed_ms(start_time):
    elapsed_ms = int((timer() - start_time) * 1000)
    return elapsed_ms


def triggered_by_heartbeat(event):
    # return ('detail-type' in event and event['detail-type'] == 'Scheduled Event')
    return (event is not None and 'heartbeat' in event)


def obfuscate_data(input, item_key_path):
    key = item_key_path[0]
    if key in input:
        if len(item_key_path) == 1:
            input[key] = '*****'
        else:
            obfuscate_data(input[key], item_key_path[1:])

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
        logger = logging.getLogger('thiscovery')
        # print('creating logger')
        log_handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter('%(asctime)s %(module)s %(funcName)s %(lineno)d %(name)-2s %(levelname)-8s %(message)s')
        formatter.default_msec_format = '%s.%03d'
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
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

DEFAULT_AWS_REGION = 'eu-west-1'


def get_aws_region():
    try:
        region = os.environ['AWS_REGION']
    except:
        region = DEFAULT_AWS_REGION
    return region


def get_aws_namespace():
    if running_unit_tests():
        return UNIT_TEST_NAMESPACE
    else:
        try:
            secrets_namespace = os.environ['SECRETS_NAMESPACE']
        except:
            # secrets_namespace = '/dev/'
            secrets_namespace = '/exp/'
            # secrets_namespace = '/test/'
            # secrets_namespace = '/staging/'
            # secrets_namespace = '/prod/'
        return secrets_namespace


def get_environment_name():
    namespace = get_aws_namespace()
    # strip leading and trailing '/' chars
    return namespace[1:-1]


def get_secret(secret_name, namespace_override=None):
    logger = get_logger()
    # need to prepend secret name with namespace...
    if namespace_override is None:
        namespace = get_aws_namespace()
    else:
        namespace = namespace_override

    if namespace is not None:
        secret_name = namespace + secret_name

    region = get_aws_region()
    endpoint_url = "https://secretsmanager." + region + ".amazonaws.com"

    logger.info('get_aws_secret: ' + secret_name)

    session = boto3.session.Session()
    # logger.info('get_aws_secret:session created')
    client = session.client(
        service_name='secretsmanager',
        region_name=region,
        endpoint_url=endpoint_url
    )

    secret = None

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


# region System parameter methods

    ssm = boto3.client('ssm', get_aws_region())

    response = ssm.get_parameters(
        Names=['/dev/feature-flags']
    )
    for parameter in response['Parameters']:
        print (parameter['Value'])

# endregion


# region System parameter methods

# def load_system_params():
#     ssm = boto3.client('ssm', get_aws_region())
#
#     flags_list = ssm.get_parameters(Names=[get_aws_namespace() + 'feature-flags'])
#
#     params = json.loads(flags_list['Parameters'][0]['Value'])
#
#     return params


def feature_flag(name: str) -> bool:
    # return name in system_parameters and system_parameters[name]
    return False


# system_parameters = load_system_params()

# endregion


# region Country code/name processing

def append_country_name_to_list(entity_list):
    for entity in entity_list:
        append_country_name(entity)
    return entity_list


def append_country_name(entity):
    country_code = entity['country_code']
    entity['country_name'] = get_country_name(country_code)


def load_countries():
    # import os
    country_list_filename = 'countries.json'

    # print('dir:' + os.getcwd())
    # print('files:' + str(os.listdir('./common')))

    if running_unit_tests():
        country_list_filename = '../../common/' + country_list_filename

    if running_on_aws():
        country_list_filename = './common/' + country_list_filename

    try:
        country_list = json.loads(get_file_as_string(country_list_filename))
    except FileNotFoundError:
        try:
            country_list_filename = '../common/' + country_list_filename
            country_list = json.loads(get_file_as_string(country_list_filename))
        except FileNotFoundError as err:
            try:
                country_list_filename = '../' + country_list_filename
                country_list = json.loads(get_file_as_string(country_list_filename))
            except FileNotFoundError as err:
                raise err

    countries_dict = {}
    for country in country_list:
        countries_dict[country['Code']] = country['Name']
    return countries_dict


def get_country_name(country_code):
    try:
        return countries[country_code]
    except KeyError as err:
        errorjson = {'country_code': country_code}
        raise DetailedValueError('invalid country code', errorjson)


countries = load_countries()

# endregion


if __name__ == "__main__":
    # result = get_aws_secret('database-connection')
    # result = {"dbname": "citsci_platform", **result}
    # result = now_with_tz()
    # result = str(result)
    # result = get_country_name('US')
    # print(result)

    print(feature_flag('hubspot-tle'))
    print(feature_flag('hubspot-contacts'))
