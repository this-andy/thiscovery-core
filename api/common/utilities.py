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
import boto3
import datetime
import epsagon
import functools
import json
import logging
import os
import re
import requests
import sys
import uuid
import validators

from botocore.exceptions import ClientError
from dateutil import parser, tz
from http import HTTPStatus
from pythonjsonlogger import jsonlogger
from timeit import default_timer as timer


# region constants
def name2namespace(name):
    return f'/{name}/'


def namespace2name(namespace):
    return namespace[1:-1]


def namespace2profile(namespace):
    """
    Maps namespaces in dev_config.py to profiles in ~/.aws/credentials
    """
    if not running_on_aws():
        from api.local.secrets import THISCOVERY_PROD_PROFILE, THISCOVERY_STAGING_PROFILE, THISCOVERY_AFS25_PROFILE, THISCOVERY_AMP205_PROFILE

        namespace2profile_map = {
            '/prod/': THISCOVERY_PROD_PROFILE,
            '/staging/': THISCOVERY_STAGING_PROFILE,
            '/dev-afs25/': THISCOVERY_AFS25_PROFILE,
            '/test-afs25/': THISCOVERY_AFS25_PROFILE,
            '/dev-amp205/': THISCOVERY_AMP205_PROFILE,
            '/test-amp205/': THISCOVERY_AMP205_PROFILE,
        }

        return namespace2profile_map.get(namespace)


PRODUCTION_ENV_NAME = 'prod'
STAGING_ENV_NAME = 'staging'

PRODUCTION_NAMESPACE = name2namespace(PRODUCTION_ENV_NAME)
STAGING_NAMESPACE = name2namespace(STAGING_ENV_NAME)
# endregion


# region Custom error classes and handling
class DetailedValueError(ValueError):
    def __init__(self, message, details):
        self.message = message
        self.details = details

    def as_response_body(self):
        try:
            return json.dumps({'message': self.message, **self.details})
        except TypeError:
            print(f"message: {self.message}; details: {self.details}")
            return json.dumps({'message': self.message, **self.details})

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
    return json.dumps({'error': error_msg, 'correlation_id': str(correlation_id)})


def log_exception_and_return_edited_api_response(exception, status_code, logger_instance, correlation_id):
    if isinstance(exception, DetailedValueError):
        exception.add_correlation_id(correlation_id)
        logger_instance.error(exception)
        return {"statusCode": status_code, "body": exception.as_response_body()}

    else:
        error_message = exception.args[0]
        logger_instance.error(error_message, extra={'correlation_id': correlation_id})
        return {"statusCode": status_code, "body": error_as_response_body(error_message, correlation_id)}
# endregion


# region unit test methods
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
    """
    Checks if calling code is running on an AWS machine
    """
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


def obfuscate_data(input, item_key_path):
    try:
        key = item_key_path[0]
        if key in input:
            if len(item_key_path) == 1:
                input[key] = '*****'
            else:
                obfuscate_data(input[key], item_key_path[1:])
    except TypeError:
        # if called with None or non-subscriptable arguments then do nothing
        pass
# endregion


# region Validation methods
def null_validator(s):
    """
    A validator that doesn't do anything. For use for optional parameters of create_user_task that do not require validation
    """
    return s


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


def validate_url(s):
    if validators.url(s):
        return s
    else:
        errorjson = {'url': s}
        raise DetailedValueError('invalid url', errorjson)


def validate_boolean(s):
    if s in ['true', 'True', 'false', 'False', '0', '1']:
        return s
    else:
        errorjson = {'boolean': s}
        raise DetailedValueError('invalid boolean', errorjson)
# endregion


# region boto3
# The default Boto3 session; autoloaded when needed.
DEFAULT_SESSION = None


def setup_default_session(profile_name):
    """
    Set up a default boto3 session, which sets profile_name and region_name if running locally
    """
    global DEFAULT_SESSION
    if running_on_aws():
        DEFAULT_SESSION = boto3.Session()
    else:
        DEFAULT_SESSION = boto3.Session(profile_name=profile_name, region_name=DEFAULT_AWS_REGION)


def _get_default_session(profile_name):
    """
    Get the default session, creating one if needed.
    """
    if DEFAULT_SESSION is None:
        setup_default_session(profile_name)
    return DEFAULT_SESSION


class BaseClient:
    def __init__(self, service_name, profile_name=None, client_type='low-level'):
        """
        Args:
            service_name (str): AWS service name (e.g. dynamodb, lambda, etc)
            profile_name (str): Profile in ~/.aws/credentials
            client_type (str): 'low-level' to create a boto3 low-level service client; or 'resource' to create a boto3 resource service client.
        """
        if (profile_name is None) and not running_on_aws():
            profile_name = namespace2profile(get_aws_namespace())
        session = _get_default_session(profile_name)
        if client_type == 'low-level':
            self.client = session.client(service_name)
        elif client_type == 'resource':
            self.client = session.resource(service_name)
        else:
            raise NotImplementedError(f"client_type can only be 'low-level' or 'resource', not {client_type}")
        self.logger = get_logger()
        self.aws_namespace = None

    def get_namespace(self):
        if self.aws_namespace is None:
            self.aws_namespace = get_aws_namespace()[1:-1]
        return self.aws_namespace


class SsmClient(BaseClient):
    def __init__(self):
        super().__init__('ssm')

    def _prefix_name(self, name, prefix):
        if prefix is None:
            prefix = f"/{super().get_namespace()}/"
        return prefix + name

    def get_parameter(self, name, prefix=None):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameter
        """
        parameter_name = self._prefix_name(name, prefix)
        self.logger.debug(f'Getting SSM parameter {parameter_name}')
        response = self.client.get_parameter(
            Name=parameter_name,
        )
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f'call to boto3.client.get_parameter failed with response: {response}'
        return response['Parameter']['Value']

    def put_parameter(self, name, value, prefix=None):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.put_parameter
        """
        parameter_name = self._prefix_name(name, prefix)
        self.logger.debug(f'Adding or updating SSM parameter {parameter_name} with value {value}')
        response = self.client.put_parameter(
            Name=parameter_name,
            Value=value,
            Type='String',
            Overwrite=True,
        )
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f'call to boto3.client.put_parameter failed with response: {response}'
        return response


class SecretsManager(BaseClient):
    def __init__(self):
        super().__init__('secretsmanager')

    def _prefix_name(self, name, prefix):
        if prefix is None:
            prefix = f"/{super().get_namespace()}/"
        return prefix + name

    def _create_secret(self, secret_id, value):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html#SecretsManager.Client.create_secret
        """
        return self.client.create_secret(
            Name=secret_id,
            SecretString=value,
        )

    def _update_secret(self, secret_id, value):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html#SecretsManager.Client.update_secret
        """
        return self.client.update_secret(
            SecretId=secret_id,
            SecretString=value,
        )

    def get_secret_value(self, secret_id):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html#SecretsManager.Client.get_secret_value
        """
        return self.client.get_secret_value(
            SecretId=secret_id,
        )

    def create_or_update_secret(self, name, value, prefix=None):
        """
        Creates or updates a secret in AWS Secrets Manager.

        Args:
            name (str): the secret name, excluding an environment prefix
            value (json or dict): key/value pairs in either dict or JSON string format
            prefix (str): if None, environment name will be used as prefix; use an empty string in calls where no prefix is required

        """
        secret_id = self._prefix_name(name, prefix)
        if isinstance(value, dict):
            value = json.dumps(value)
        self.logger.debug(f'Adding or updating Secret {secret_id} with value {value}')
        try:
            response = self._update_secret(secret_id, value)
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f'Call to boto3.client.update_secret failed with response: {response}'
        except Exception as exception:
            error_message = exception.args[0]
            self.logger.error(error_message)
            response = self._create_secret(secret_id, value)
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f'Call to boto3.client.create_secret failed with response: {response}'
        return response
# endregion


# region Logging
class _AnsiColorizer(object):
    """
    A colorizer is an object that loosely wraps around a stream, allowing
    callers to write text to the stream in a particular color.

    Colorizer classes must implement C{supported()} and C{write(text, color)}.
    """
    _colors = dict(black=30, red=31, green=32, yellow=33,
                   blue=34, magenta=35, cyan=36, white=37)

    def __init__(self, stream):
        self.stream = stream

    @classmethod
    def supported(cls, stream=sys.stdout):
        """
        A class method that returns True if the current platform supports
        coloring terminal output using this method. Returns False otherwise.
        """
        if not stream.isatty():
            return False  # auto color only on TTYs
        try:
            import curses
        except ImportError:
            return False
        else:
            try:
                try:
                    return curses.tigetnum("colors") > 2
                except curses.error:
                    curses.setupterm()
                    return curses.tigetnum("colors") > 2
            except:
                raise
                # guess false in case of error
                return False

    def write(self, text, color):
        """
        Write the given text to the stream in the given color.

        @param text: Text to be written to the stream.

        @param color: A string label for a color. e.g. 'red', 'white'.
        """
        color = self._colors[color]
        self.stream.write('\x1b[%s;1m%s\x1b[0m' % (color, text))


class ColorHandler(logging.StreamHandler):

    def __init__(self, stream=sys.stderr):
        super(ColorHandler, self).__init__(_AnsiColorizer(stream))

    def emit(self, record):
        msg_colors = {
            logging.DEBUG: "green",
            logging.INFO: "blue",
            logging.WARNING: "yellow",
            logging.ERROR: "red"
        }

        color = msg_colors.get(record.levelno, "blue")
        self.stream.write(self.format(record) + "\n", color)


class EpsagonHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        try:
            self.running_tests = get_secret('runtime-parameters')['running-tests']
        except TypeError:  # get_secret('runtime-parameters') is None
            self.running_tests = 'false'

    def emit(self, exception_instance):
        if (self.running_tests == 'false') or (get_aws_namespace() in [PRODUCTION_NAMESPACE, STAGING_NAMESPACE]):
            epsagon.error(exception_instance)
        elif self.running_tests == 'true':
            pass
        else:
            raise AttributeError(f'Secret runtime-parameters.running-tests is neither "true" nor "false": {self.running_tests}')


logger = None


def get_logger():
    global logger
    if logger is None:
        logger = logging.getLogger('thiscovery')
        formatter = jsonlogger.JsonFormatter('%(asctime)s %(module)s %(funcName)s %(lineno)d %(name)-2s %(levelname)-8s %(message)s')
        formatter.default_msec_format = '%s.%03d'

        log_handler = ColorHandler()
        log_handler.setLevel(logging.DEBUG)
        log_handler.setFormatter(formatter)

        epsagon_handler = EpsagonHandler()
        epsagon_handler.setLevel(logging.ERROR)
        epsagon_handler.setFormatter(formatter)

        for handler in [log_handler, epsagon_handler]:
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
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
    return str(correlation_id)
# endregion


# region Secrets processing
DEFAULT_AWS_REGION = 'eu-west-1'


def get_aws_region():
    try:
        region = os.environ['AWS_REGION']
    except KeyError:
        region = DEFAULT_AWS_REGION
    return region


def get_aws_namespace():
    if running_on_aws():
        try:
            secrets_namespace = os.environ['SECRETS_NAMESPACE']
        except KeyError:
            raise DetailedValueError('SECRETS_NAMESPACE environment variable not defined', {})
    else:
        from common.dev_config import UNIT_TEST_NAMESPACE, SECRETS_NAMESPACE
        if running_unit_tests():
            secrets_namespace = UNIT_TEST_NAMESPACE
        else:
            secrets_namespace = SECRETS_NAMESPACE
    return secrets_namespace


def get_environment_name():
    namespace = get_aws_namespace()
    # strip leading and trailing '/' chars
    return namespace[1:-1]


# this belongs in user_task class as a property - moved here to avoid circular includes
def create_anonymous_url_params(base_url, ext_user_project_id, ext_user_task_id, external_task_id):
    assert ext_user_project_id, 'ext_user_project_id is null'
    assert ext_user_task_id, 'ext_user_task_id is null'
    if "?" in base_url:
        params = f'&ext_user_project_id={ext_user_project_id}&ext_user_task_id={ext_user_task_id}'
    else:
        params = f'?ext_user_project_id={ext_user_project_id}&ext_user_task_id={ext_user_task_id}'
    if external_task_id is not None:
        params += f'&external_task_id={external_task_id}'
    return params


def create_url_params(base_url, user_id, user_first_name, user_task_id, external_task_id=None):
    if "?" in base_url:
        params = f'&user_id={user_id}&first_name={user_first_name}&user_task_id={user_task_id}'
    else:
        params = f'?user_id={user_id}&first_name={user_first_name}&user_task_id={user_task_id}'
    if external_task_id is not None:
        params += f'&external_task_id={str(external_task_id)}'
    return params


def non_prod_env_url_param(target_env='prod'):
    if get_environment_name() == target_env:
        return ''
    else:
        return '&env=' + get_environment_name()


def get_secret(secret_name, namespace_override=None):
    logger = get_logger()
    # need to prepend secret name with namespace...
    if namespace_override is None:
        namespace = get_aws_namespace()
    else:
        namespace = namespace_override

    if namespace is not None:
        secret_name = namespace + secret_name

    logger.info('get_aws_secret: ' + secret_name)

    secret = None
    client = SecretsManager()

    try:
        get_secret_value_response = client.get_secret_value(secret_name)
        # logger.info('get_aws_secret:secret retrieved')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.error("The requested secret " + secret_name + " was not found")
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            logger.error("The request was invalid due to:" + str(e))
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            logger.error("The request had invalid params:" + str(e))
        else:
            logger.error("An unexpected exception occurred:" + str(e), exc_info=True)
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


# region Country code/name processing
def append_country_name_to_list(entity_list):
    for entity in entity_list:
        append_country_name(entity)
    return entity_list


def append_country_name(entity):
    country_code = entity['country_code']
    entity['country_name'] = get_country_name(country_code)


def load_countries():
    country_list_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'countries.json')
    country_list = json.loads(get_file_as_string(country_list_filename))
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


# region decorators
def api_error_handler(func):
    """
    Error handler decorator for thiscovery API endpoints. Use with lambda_wrapper as the outer decorator. E.g.:
        @lambda_wrapper
        @api_error_handler
        def decorated_function():
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        correlation_id = args[0]['correlation_id']
        try:
            return func(*args, **kwargs)
        except DuplicateInsertError as err:
            return log_exception_and_return_edited_api_response(err, HTTPStatus.CONFLICT, logger, correlation_id)
        except ObjectDoesNotExistError as err:
            return log_exception_and_return_edited_api_response(err, HTTPStatus.NOT_FOUND, logger, correlation_id)
        except (PatchAttributeNotRecognisedError, PatchOperationNotSupportedError, PatchInvalidJsonError, DetailedIntegrityError, DetailedValueError) as err:
            return log_exception_and_return_edited_api_response(err, HTTPStatus.BAD_REQUEST, logger, correlation_id)
        except Exception as err:
            return log_exception_and_return_edited_api_response(err, HTTPStatus.INTERNAL_SERVER_ERROR, logger, correlation_id)
    return wrapper


def lambda_wrapper(func):
    @functools.wraps(func)
    def thiscovery_lambda_wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = get_start_time()

        # check if the lambda event dict includes a correlation id; if it does not, add one and pass it to the wrapped lambda
        # also add a logger to the event dict
        event = args[0]
        correlation_id = get_correlation_id(event)
        event['correlation_id'] = correlation_id
        event['logger'] = logger
        updated_args = (event, *args[1:])

        result = func(*updated_args, **kwargs)
        logger.info('Decorated function result and execution time', extra={'decorated func module': func.__module__, 'decorated func name': func.__name__,
                                                                           'result': result, 'func args': args, 'func kwargs': kwargs,
                                                                           'elapsed_ms': get_elapsed_ms(start_time), 'correlation_id': correlation_id})
        return result
    return thiscovery_lambda_wrapper
# endregion


# region aws api requests
def aws_request(method, endpoint_url, base_url, params=None, data=None, aws_api_key=None):
    full_url = base_url + endpoint_url
    headers = {'Content-Type': 'application/json'}

    if aws_api_key is None:
        headers['x-api-key'] = get_secret('aws-connection')['aws-api-key']
    else:
        headers['x-api-key'] = aws_api_key

    try:
        response = requests.request(
            method=method,
            url=full_url,
            params=params,
            headers=headers,
            data=data,
        )
        return {'statusCode': response.status_code, 'body': response.text}
    except Exception as err:
        raise err


def aws_get(endpoint_url, base_url, params):
    return aws_request(method='GET', endpoint_url=endpoint_url, base_url=base_url, params=params)


def aws_post(endpoint_url, base_url, params=None, request_body=None):
    return aws_request(method='POST', endpoint_url=endpoint_url, base_url=base_url, params=params, data=request_body)


def aws_patch(endpoint_url, base_url, request_body):
    return aws_request(method='PATCH', endpoint_url=endpoint_url, base_url=base_url, data=request_body)
# endregion
