import json
import uuid
from http import HTTPStatus
from api.pg_utilities import execute_query, execute_non_query
from api.user import get_user_by_id
from api.utilities import ObjectDoesNotExistError, DuplicateInsertError, DetailedIntegrityError, DetailedValueError, \
    validate_uuid, validate_utc_datetime, get_correlation_id, get_logger, error_as_response_body, now_with_tz


STATUS_CHOICES = (
    'active',
    'closed',
)
DEFAULT_STATUS = 'active'


def validate_status(s):
    if s in STATUS_CHOICES:
        return s
    else:
        errorjson = {'status': s}
        raise DetailedValueError('invalid user_external_account status', errorjson)


def check_user_id_and_external_account(user_id, external_system_id, correlation_id):

    base_sql = '''
      SELECT 
        id
      FROM public.projects_userexternalaccount
      WHERE
        user_id = %s AND external_system_id = %s
    '''

    return execute_query(base_sql, (str(user_id), str(external_system_id)), correlation_id)


def create_user_external_account(uea_json, correlation_id, do_nothing_if_exists=False):
    # json MUST contain: external_system_id, user_id, external_user_id
    # json may OPTIONALLY include: id, created, status

    # extract mandatory data from json
    try:
        external_system_id = validate_uuid(uea_json['external_system_id'])
        user_id = validate_uuid(uea_json['user_id'])
        external_user_id = uea_json['external_user_id']
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err
    except KeyError as err:
        errorjson = {'parameter': err.args[0], 'correlation_id': str(correlation_id)}
        raise DetailedValueError('mandatory data missing', errorjson) from err


    # now process optional json data
    if 'id' in uea_json:
        try:
            id = validate_uuid(uea_json['id'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    if 'created' in uea_json:
        try:
            created = validate_utc_datetime(uea_json['created'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        created = str(now_with_tz())

    if 'status' in uea_json:
        try:
            status = validate_status(uea_json['status'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        status = DEFAULT_STATUS

    # check external account does not already exist
    existing = check_user_id_and_external_account(user_id, external_system_id, correlation_id)
    if len(existing) > 0:
        if do_nothing_if_exists:
            return existing[0]['id']
        else:
            errorjson = {'user_id': user_id, 'external_system_id': external_system_id, 'correlation_id': str(correlation_id)}
            raise DuplicateInsertError('user_external_account already exists', errorjson)

    # lookup user id (needed for insert) for user uuid (supplied in json)
    existing_user = get_user_by_id(user_id, correlation_id)
    if len(existing_user) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise ObjectDoesNotExistError('user does not exist', errorjson)

    sql = '''INSERT INTO public.projects_userexternalaccount (
            id,
            created,
            modified,
            external_system_id,
            user_id,
            external_user_id,
            status
        ) VALUES ( %s, %s, %s, %s, %s, %s, %s );'''

    execute_non_query(sql, (id, created, created, external_system_id, user_id, external_user_id, status), correlation_id)

    new_user_external_account = {
        'id': id,
        'created': created,
        'modified': created,
        'external_system_id': external_system_id,
        'user_id': user_id,
        'external_user_id': external_user_id,
        'status': status,
    }

    return new_user_external_account


def create_user_external_account_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        uea_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'uea_json': uea_json, 'correlation_id': correlation_id, 'event': event})

        new_user_external_account = create_user_external_account(uea_json, correlation_id)

        response = {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user_external_account)}

    except DuplicateInsertError as err:
        response = {"statusCode": HTTPStatus.CONFLICT, "body": err.as_response_body()}

    except (ObjectDoesNotExistError, DetailedIntegrityError, DetailedValueError) as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


def get_or_create_user_external_account(user_id, external_system_id, correlation_id):
    # see if it exists
    # if not then call extrenal system to get id and create record
    pass


if __name__ == "__main__":
    uea_json = {
        'external_system_id': 'e056e0bf-8d24-487e-a57b-4e812b40c4d8',
        'user_id': '35224bd5-f8a8-41f6-8502-f96e12d6ddde',
        'external_user_id': 'cc02'
        # 'status': 'active',
        # 'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
        # 'created': '2018-06-13 14:15:16.171819+00'
    }
    correlation_id = None
    print(create_user_external_account(uea_json, correlation_id, True))

    # ev = {'body': json.dumps(uea_json)}
    # print(create_user_external_account_api(ev, None))

    # print (check_user_id_and_external_account('35224bd5-f8a8-41f6-8502-f96e12d6ddde', 'e056e0bf-8d24-487e-a57b-4e812b40c4d8', correlation_id))

    # print(validate_status('active'))
