import json
import uuid
import datetime
from api.pg_utilities import execute_query, execute_non_query
from api.utilities import UserDoesNotExistError, DuplicateInsertError, DetailedIntegrityError, DetailedValueError, \
    validate_uuid, validate_utc_datetime, get_correlation_id, get_logger, error_as_response_body
from api.user import get_user_id


def validate_status(s):
    # todo figure out what valid statuses are
    return s


def check_user_id_and_external_account(user_uuid, external_system_id, correlation_id):

    base_sql = '''
      SELECT 
        COUNT(uea.id)
      FROM public.users_user u 
      JOIN public.projects_userexternalaccount uea ON u.id = uea.user_id
      WHERE
        uuid = ''' \
        + "\'" + str(user_uuid) + "\'" \
        + " AND external_system_id = \'" + str(external_system_id) + "\'"

    return execute_query(base_sql, correlation_id, False)


def create_user_external_account(uea_json, correlation_id):
    # json MUST contain: external_system_id, user_uuid, external_user_id, status
    # json may OPTIONALLY include: id, created,

    # extract mandatory data from json
    try:
        external_system_id = validate_uuid(uea_json['external_system_id'])
        user_uuid = validate_uuid(uea_json['user_id'])
        external_user_id = uea_json['external_user_id']
        status = validate_status(uea_json['status'])
    except :
        raise

    # now process optional json data
    if 'id' in uea_json:
        try:
            id = validate_uuid(uea_json['id'])
        except DetailedValueError:
            raise
    else:
        id = str(uuid.uuid4())
        uea_json['id'] = id

    if 'created' in uea_json:
        try:
            created = validate_utc_datetime(uea_json['created'])
        except DetailedValueError:
            raise
    else:
        created = str(datetime.datetime.utcnow())
        uea_json['created'] = created

    uea_json['modified'] = created

    # check external account does not already exist
    existing = check_user_id_and_external_account(user_uuid, external_system_id, correlation_id)
    if int(existing[0][0]) > 0:
        errorjson = {'user_uuid': user_uuid, 'external_system_id': external_system_id, 'correlation_id': str(correlation_id)}
        raise DuplicateInsertError('user_external_account already exists', errorjson)

    # lookup user id (needed for insert) for user uuid (supplied in json)
    user_id = get_user_id(user_uuid, correlation_id)
    if user_id is None:
        errorjson = {'user_uuid': user_uuid, 'correlation_id': str(correlation_id)}
        raise UserDoesNotExistError('user does not exist', errorjson)

    sql = '''INSERT INTO public.projects_userexternalaccount (
            id,
            created,
            modified,
            external_system_id,
            user_id,
            external_user_id,
            status
        ) VALUES ( %s, %s, %s, %s, %s, %s, %s );'''

    rowcount = execute_non_query(sql, (id, created, created, external_system_id, user_id, external_user_id, status), correlation_id)

    return rowcount


def create_user_external_account_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        uea_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'uea_json': uea_json, 'correlation_id': correlation_id, 'event': event})

        create_user_external_account(uea_json, correlation_id)

        response = {"statusCode": 201, "body": json.dumps(uea_json)}

    except DuplicateInsertError as err:
        response = {"statusCode": 409, "body": err.as_response_body()}

    except (UserDoesNotExistError, DetailedIntegrityError, DetailedValueError) as err:
        response = {"statusCode": 400, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


if __name__ == "__main__":
    uea_json = {
        'external_system_id': '4a7ceb98-888c-4e38-8803-4a25ddf64ef4',
        'user_id': '8e385316-5827-4c72-8d4b-af5c57ff4679',
        'external_user_id': 'cc02',
        'status': 'A',
        # 'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
        # 'created': '2018-06-13 14:15:16.171819+00'
    }
    correlation_id = None
    # print(create_user_external_account(uea_json), correlation_id)

    # print (check_user_id_and_external_account('81f56be3-14dd-4b23-8632-96d01aa46f1d', '0fd1c5cf-4c3c-4d57-8eee-0e2c5127e7f0'))