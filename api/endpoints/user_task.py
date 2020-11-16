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
import functools
import json
import uuid
from http import HTTPStatus

import common.sql_queries as sql_q
import thiscovery_lib.utilities as utils
from thiscovery_lib.dynamodb_utilities import Dynamodb
from common.pg_utilities import execute_query, execute_non_query
from common.sql_queries import GET_USER_TASK_SQL, UPDATE_USER_TASK_PROGRESS_INFO_SQL, CHECK_IF_USER_TASK_EXISTS_SQL, \
    CREATE_USER_TASK_SQL
from user import get_user_by_id
from project import get_project_task
from user_project import create_user_project_if_not_exists
from common.notification_send import notify_new_task_signup

STATUS_CHOICES = (
    'active',
    'complete',
    'withdrawn',
)
DEFAULT_STATUS = 'active'


class UserTask:
    user_specific_url_table = "UserSpecificUrls"

    def __init__(self, correlation_id=None, ddb_client=None):
        self.id = None
        self.user_project = None
        self.project_task = None
        self.status = None
        self.consented = None
        self.progress_info = None
        self.ext_user_task_id = None
        self.anon_user_task_id = None
        self.user_task_url = None

        self._correlation_id = correlation_id
        self.user_id = None
        self.first_name = None
        self.last_name = None
        self.email = None
        # this is the same as project_task above
        self.project_task_id = None
        self.anon_user_task_id = None
        self.created = None
        self.project_id = None
        self.base_url = None
        self.task_provider_name = None
        self.external_task_id = None
        self.user_specific_url = None
        self.anonymise_url = None
        # this is the same as user_project above
        self.user_project_id = None
        self.anon_project_specific_user_id = None
        self.task_type_name = None

        self._ddb_client = ddb_client

    def __repr__(self):
        return str(self.__dict__)

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if (k[0] != "_")}

    def from_dict(self, ut_dict):
        self.__dict__.update(ut_dict)

    @staticmethod
    def _validate_status(status):
        if status in STATUS_CHOICES:
            return status
        else:
            errorjson = {
                'status': status
            }
            raise utils.DetailedValueError('invalid user_task status', errorjson)

    def _create_user_task_validate_mandatory_data(self):
        for param in ['user_id', 'project_task_id', 'consented']:
            if self.__dict__[param] is None:
                errorjson = {
                    'parameter': param,
                    'correlation_id': str(self._correlation_id)
                }
                raise utils.DetailedValueError('mandatory data missing', details=errorjson)
        try:
            utils.validate_uuid(self.user_id)
            utils.validate_uuid(self.project_task_id)
            utils.validate_utc_datetime(self.consented)
        except utils.DetailedValueError as err:
            err.add_correlation_id(self._correlation_id)
            raise err

    def _create_user_task_process_optional_data(self, ut_dict):
        optional_fields_name_default_and_validator = [
            ('id', str(uuid.uuid4()), utils.validate_uuid),
            ('anon_user_task_id', str(uuid.uuid4()), utils.validate_uuid),
            ('created', str(utils.now_with_tz()), utils.validate_utc_datetime),
            ('status', DEFAULT_STATUS, self._validate_status),
        ]
        for variable_name, default_value, validating_func in optional_fields_name_default_and_validator:
            if variable_name in ut_dict:
                try:
                    self.__dict__[variable_name] = validating_func(ut_dict[variable_name])  # https://stackoverflow.com/a/4687672
                except utils.DetailedValueError as err:
                    err.add_correlation_id(self._correlation_id)
                    raise err
            else:
                self.__dict__[variable_name] = default_value

    def _get_project_task(self):
        project_task = get_project_task(self.project_task_id, self._correlation_id)
        try:
            pt_ = project_task[0]
        except IndexError:
            errorjson = {
                'user_id': self.user_id,
                'project_task_id': self.project_task_id,
                'correlation_id': str(self._correlation_id)
            }
            raise utils.DetailedIntegrityError('project_task does not exist', errorjson)

        self.project_id = pt_['project_id']
        self.base_url = pt_['base_url']
        self.task_provider_name = pt_['task_provider_name']
        self.external_task_id = pt_['external_task_id']
        self.user_specific_url = pt_['user_specific_url']
        self.anonymise_url = pt_['anonymise_url']
        self.task_type_name = pt_['task_type_name']

    def _create_user_task_abort_if_exists(self):
        existing = check_if_user_task_exists(self.user_id, self.project_task_id, self._correlation_id)
        if len(existing) > 0:
            errorjson = {
                'user_id': self.user_id,
                'project_task_id': self.project_task_id,
                'existing_user_task': existing[0][0],
                'correlation_id': str(self._correlation_id)
            }
            raise utils.DuplicateInsertError('user_task already exists', errorjson)

    def _get_user_info(self):
        # get user info if not received from calling process
        if None in [self.first_name, self.last_name, self.email]:
            try:
                user = get_user_by_id(self.user_id, correlation_id=self._correlation_id)[0]
            except IndexError:
                errorjson = {
                    'user_id': self.user_id,
                    'correlation_id': str(self._correlation_id)
                }
                return utils.ObjectDoesNotExistError('User does not exist', errorjson)
            self.first_name = user['first_name']
            self.last_name = user['last_name']
            self.email = user['email']

    def calculate_url(self):
        if self.user_specific_url:
            self.base_url = self.user_task_url

        if self.base_url:
            if self.anonymise_url:
                params = utils.create_anonymous_url_params(
                    base_url=self.base_url,
                    anon_project_specific_user_id=self.anon_project_specific_user_id,
                    user_first_name=self.first_name,
                    anon_user_task_id=self.anon_user_task_id,
                    external_task_id=self.external_task_id,
                    project_task_id=self.project_task_id,
                )
            else:
                params = utils.create_url_params(
                    base_url=self.base_url,
                    user_id=self.user_id,
                    user_first_name=self.first_name,
                    user_task_id=self.id,
                    external_task_id=self.external_task_id
                )

            if self.task_type_name is None:
                self._get_project_task()
            if self.task_type_name == 'interview':
                # add last name and email for use with Acuity Scheduler
                params = f"{params}" \
                         f"&last_name={self.last_name}" \
                         f"&email={self.email}"

            return "{}{}{}".format(
                self.base_url,
                params,
                utils.non_prod_env_url_param()
            )

    def _get_ddb_client(self):
        if self._ddb_client is None:
            self._ddb_client = Dynamodb(correlation_id=self._correlation_id)

    def _get_user_specific_task_url_from_ddb(self):
        if self.user_specific_url:
            self._get_ddb_client()
            item_key = f"{self.project_task_id}_{self.user_id}"
            item = self._ddb_client.get_item(
                table_name=self.user_specific_url_table,
                key=item_key,
                correlation_id=self._correlation_id,
            )
            try:
                self.user_task_url = item['user_specific_url']
            except TypeError:
                errorjson = {
                    'user_id': self.user_id,
                    'project_task_id': self.project_task_id,
                    'correlation_id': str(self._correlation_id)
                }
                raise utils.ObjectDoesNotExistError('User specific url not found', errorjson)
            return item_key

    def thiscovery_db_dump(self):
        row_count = execute_non_query(
            sql=CREATE_USER_TASK_SQL,
            params=(
                self.id,
                self.created,
                self.created,
                self.user_project_id,
                self.project_task_id,
                self.status,
                self.consented,
                self.anon_user_task_id,
                self.user_task_url,
            ),
            correlation_id=self._correlation_id
        )
        return row_count

    def _mark_user_specific_url_as_processed_in_ddb(self, item_key):
        self._get_ddb_client()
        self._ddb_client.update_item(
            table_name=self.user_specific_url_table,
            key=item_key,
            name_value_pairs={
                'status': 'processed'
            },
            correlation_id=self._correlation_id,
        )

    def create_user_task(self, ut_dict):
        """
        Inserts new UserTask row in thiscovery db

        Args:
            ut_dict: must contain user_id, project_task_id and consented; may optionally include id, created,
                    status, anon_user_task_id, first_name, last_name, email

        Returns:
            Dictionary representation of new user task
        """
        self.from_dict(ut_dict=ut_dict)
        self._create_user_task_validate_mandatory_data()
        self._create_user_task_process_optional_data(ut_dict=ut_dict)
        self._get_project_task()
        user_project = create_user_project_if_not_exists(self.user_id, self.project_id, self._correlation_id)
        self.user_project_id = user_project['id']
        self.anon_project_specific_user_id = user_project['anon_project_specific_user_id']
        self._create_user_task_abort_if_exists()
        self._get_user_info()
        item_key = self._get_user_specific_task_url_from_ddb()
        row_count = self.thiscovery_db_dump()
        if self.user_specific_url and row_count:
            self._mark_user_specific_url_as_processed_in_ddb(item_key=item_key)
        url = self.calculate_url()

        new_user_task = {
            'id': self.id,
            'created': self.created,
            'modified': self.created,
            'user_id': self.user_id,
            'user_project_id': self.user_project_id,
            'project_task_id': self.project_task_id,
            'task_provider_name': self.task_provider_name,
            'url': url,
            'status': self.status,
            'consented': self.consented,
            'anon_user_task_id': self.anon_user_task_id,
        }

        notify_new_task_signup(new_user_task, self._correlation_id)

        return new_user_task


# region decorators
def anon_user_task_id_support(default_parameter_name, lookup_func):
    """
    Extends api endpoints to support anon_user_task_id as parameter

    Args:
        default_parameter_name (str): The default parameter anon_user_task_id will be an alternative to (e.g. 'user_id')
        lookup_func (function): The function that converts anon_user_task_id to the default parameter

    Notes:
        Use with lambda_wrapper api_error_handler as outer decorators. E.g.:
            @lambda_wrapper
            @api_error_handler
            @anon_user_task_id_support
            def decorated_function():

    """
    def inner_function(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            event = args[0]
            correlation_id = event['correlation_id']
            logger = event['logger']
            parameters = event['queryStringParameters']
            default_parameter = parameters.get(default_parameter_name)
            anon_user_task_id = parameters.get('anon_user_task_id')

            if default_parameter and anon_user_task_id:
                errorjson = {
                    'queryStringParameters': parameters,
                    'correlation_id': str(correlation_id)
                }
                raise utils.DetailedValueError(f'This endpoint requires parameter {default_parameter_name} or anon_user_task_id, not both', errorjson)
            elif default_parameter:
                logger.info('API call', extra={
                    default_parameter_name: default_parameter,
                    'anon_user_task_id': anon_user_task_id,
                    'correlation_id': correlation_id,
                    'event': args[0]
                })
            elif anon_user_task_id:
                logger.info('API call', extra={
                    default_parameter_name: default_parameter,
                    'anon_user_task_id': anon_user_task_id,
                    'correlation_id': correlation_id,
                    'event': args[0]
                })
                parameters[default_parameter_name] = lookup_func(anon_user_task_id, correlation_id)
            else:  # e.g. parameters is None or an empty dict
                errorjson = {
                    'queryStringParameters': parameters,
                    'correlation_id': str(correlation_id)
                }
                raise utils.DetailedValueError('This endpoint requires parameter user_task_id or anon_user_task_id; none were given', errorjson)

            updated_args = (event, *args[1:])
            result = func(*updated_args, **kwargs)
            return result
        return wrapper
    return inner_function
# endregion


def get_user_task(ut_id, correlation_id=None):
    result = execute_query(GET_USER_TASK_SQL, (str(ut_id),), correlation_id)
    return result


def filter_user_tasks_by_project_task_id(user_id, project_task_id, correlation_id=None):
    """
    Returns user_task related to user_id and project_task_id or None
    """
    result = [t for t in list_user_tasks_by_user(user_id, correlation_id) if t['project_task_id'] == project_task_id]
    return result


def list_user_tasks_by_user(user_id, correlation_id=None):
    try:
        user_id = utils.validate_uuid(user_id)
    except utils.DetailedValueError:
        raise

    # check that user exists
    try:
        user_result = get_user_by_id(user_id, correlation_id)[0]
    except IndexError:
        errorjson = {
            'user_id': user_id,
            'correlation_id': str(correlation_id)
        }
        raise utils.ObjectDoesNotExistError('user does not exist', errorjson)

    result = execute_query(sql_q.LIST_USER_TASKS_SQL, (str(user_id),), correlation_id)

    # add url field to each user_task in result
    edited_result = list()
    for ut in result:
        user_task = UserTask(correlation_id=correlation_id)
        user_task.from_dict(ut_dict=ut)
        user_task.id = ut['user_task_id']
        user_task.first_name = user_result['first_name']
        user_task.last_name = user_result['last_name']
        user_task.email = user_result['email']
        ut['url'] = user_task.calculate_url()
        del ut['base_url']
        del ut['external_task_id']
        del ut['user_specific_url']
        del ut['user_task_url']
        del ut['anon_project_specific_user_id']
        del ut['anonymise_url']
        edited_result.append(ut)

    return edited_result


def clear_user_tasks_for_project_task_id(project_task_id):
    return execute_non_query(
        sql=sql_q.DELETE_USER_TASKS_FOR_PROJECT_TASK_SQL,
        params=(project_task_id,),
    )


def anon_user_task_id_2_parameter(anon_ut_id, parameter_name, correlation_id=None):
    try:
        return execute_query(
            sql_q.ANON_USER_TASK_ID_2_ID_SQL,
            [anon_ut_id],
            correlation_id,
        )[0][parameter_name]
    except IndexError:
        errorjson = {
            'anon_ut_id': anon_ut_id,
            'correlation_id': str(correlation_id)
        }
        raise utils.ObjectDoesNotExistError('user task does not exist', errorjson)


def anon_user_task_id_2_user_id(anon_ut_id, correlation_id=None):
    return anon_user_task_id_2_parameter(anon_ut_id, 'user_id', correlation_id=correlation_id)


@utils.lambda_wrapper
@utils.api_error_handler
@anon_user_task_id_support('user_id', anon_user_task_id_2_user_id)
def list_user_tasks_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    parameters = event['queryStringParameters']
    user_id = parameters.get('user_id')

    if not user_id:  # e.g. parameters is None or an empty dict
        errorjson = {
            'queryStringParameters': parameters,
            'correlation_id': str(correlation_id)
        }
        raise utils.DetailedValueError('This endpoint requires parameter user_id', errorjson)

    project_task_id = parameters.get('project_task_id')

    if project_task_id:
        logger.info('API call', extra={
            'user_id': user_id,
            'project_task_id': project_task_id,
            'correlation_id': correlation_id,
            'event': event
        })
        result = filter_user_tasks_by_project_task_id(user_id, project_task_id, correlation_id)
    else:
        logger.info('API call', extra={
            'user_id': user_id,
            'correlation_id': correlation_id,
            'event': event
        })
        result = list_user_tasks_by_user(user_id, correlation_id)

    # todo: this was added here as a way of quickly fixing an issue with the thiscovery frontend; review what to do for the longer term
    if len(result) == 1:
        result = result[0]

    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(result)
    }


def check_if_user_task_exists(user_id, project_task_id, correlation_id):
    return execute_query(CHECK_IF_USER_TASK_EXISTS_SQL, (str(user_id), str(project_task_id)), correlation_id, False)


@utils.lambda_wrapper
@utils.api_error_handler
def create_user_task_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    ut_json = json.loads(event['body'])
    logger.info('API call', extra={
        'ut_json': ut_json,
        'correlation_id': correlation_id
    })
    ut = UserTask(correlation_id=correlation_id)
    new_user_task = ut.create_user_task(ut_json)
    return {
        "statusCode": HTTPStatus.CREATED,
        "body": json.dumps(new_user_task)
    }


def anon_user_task_id_2_user_task_id(anon_ut_id, correlation_id=None):
    return anon_user_task_id_2_parameter(anon_ut_id, 'id', correlation_id=correlation_id)


def set_user_task_completed(ut_id, correlation_id=None):
    utils.validate_uuid(ut_id)
    # check that user_task exists
    result = get_user_task(ut_id, correlation_id)
    if len(result) == 0:
        errorjson = {
            'user_task_id': ut_id,
            'correlation_id': str(correlation_id)
        }
        raise utils.ObjectDoesNotExistError('user task does not exist', errorjson)

    updated_rows_count = execute_non_query(
        sql_q.UPDATE_USER_TASK_STATUS,
        (
            'complete',
            str(utils.now_with_tz()),
            str(ut_id),
        ),
        correlation_id
    )

    assert updated_rows_count == 1, f"Failed to update status of user task {ut_id}; updated_rows_count: {updated_rows_count}"


@utils.lambda_wrapper
@utils.api_error_handler
@anon_user_task_id_support('user_task_id', anon_user_task_id_2_user_task_id)
def set_user_task_completed_api(event, context):
    """
    Third party systems (eg Qualtrics) use this endpoint to inform Thiscovery that a user has completed a task.

    Note that the standard way to do this would be create a json patch entity and implement full patch functionality in
    user_task as in other patchable entities.  We do not have time to develop and test that right now, so please omit this.
    We can come back to it.

    Also, this is fundamentally the wrong approach to be taking to this problem.  We need to be posting events to Thiscovery.
    So this code will be completely superseded in the medium term.
    """
    correlation_id = event['correlation_id']

    parameters = event['queryStringParameters']
    user_task_id = parameters.get('user_task_id')

    set_user_task_completed(user_task_id, correlation_id)
    return {
        "statusCode": HTTPStatus.NO_CONTENT
    }
