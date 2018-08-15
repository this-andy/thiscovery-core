import uuid
import json
import datetime
from api.pg_utilities import execute_query, execute_non_query
from api.utilities import UserDoesNotExistError, DuplicateInsertError, DetailedIntegrityError, DetailedValueError, \
    validate_uuid, validate_utc_datetime, get_correlation_id, get_logger, error_as_response_body
from api.user import get_user_id


def validate_status(s):
    return s


def list_user_projects(user_uuid, correlation_id):

    try:
        user_uuid = validate_uuid(user_uuid)
    except DetailedValueError:
        raise

    # check that user exists
    user_id = get_user_id(user_uuid, correlation_id)
    if user_id is None:
        errorjson = {'user_uuid': user_uuid, 'correlation_id': str(correlation_id)}
        raise UserDoesNotExistError('user does not exist', errorjson)

    base_sql = '''
        SELECT 
            up.id,
            u.uuid as user_id,
            up.project_id,
            up.created,
            up.modified,               
            up.status                
        FROM 
            public.projects_userproject up
            inner join public.users_user u on u.id = up.user_id
        WHERE u.uuid = ''' \
            + "'" + str(user_uuid) + "'"

    return execute_query(base_sql, correlation_id)


def list_user_projects_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        params = event['queryStringParameters']
        user_uuid = params['user_id']  # all public id are uuids
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_uuid': user_uuid, 'correlation_id': correlation_id, 'event': event})

        response = {
            "statusCode": 200,
            "body": json.dumps(list_user_projects(user_uuid, correlation_id))
        }

    except UserDoesNotExistError as err:
        response = {"statusCode": 404, "body": err.as_response_body()}

    except DetailedValueError as err:
        response = {"statusCode": 400, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


def get_existing_user_project_count(user_uuid, project_id, correlation_id):

    base_sql = '''
      SELECT 
        COUNT(up.id)
      FROM public.projects_userproject up
        INNER JOIN public.users_user u ON up.user_id = u.id
      WHERE
        up.project_id = ''' \
        + "'" + str(project_id) + "'" \
        + " AND u.uuid = '" + str(user_uuid) + "'"

    return execute_query(base_sql, correlation_id, False)


def create_user_project(up_json, correlation_id):
    # json MUST contain: user_uuid, project_id, status
    # json may OPTIONALLY include: id, created,

    # extract mandatory data from json
    try:
        user_uuid = validate_uuid(up_json['user_id'])    # all public id are uuids
        project_id = validate_uuid(up_json['project_id'])
        status = validate_status(up_json['status'])
    except DetailedValueError:
        raise

    # now process optional json data
    if 'id' in up_json:
        try:
            id = validate_uuid(up_json['id'])
        except DetailedValueError:
            raise
    else:
        id = str(uuid.uuid4())
        up_json['id'] = id

    if 'created' in up_json:
        try:
            created = validate_utc_datetime(up_json['created'])
        except DetailedValueError:
            raise
    else:
        created = str(datetime.datetime.utcnow())
        up_json['created'] = created

    up_json['modified'] = created

    # check external account does not already exist
    existing = get_existing_user_project_count(user_uuid, project_id, correlation_id)
    if int(existing[0][0]) > 0:
        errorjson = {'user_uuid': user_uuid, 'project_id': project_id, 'correlation_id': str(correlation_id)}
        raise DuplicateInsertError('user_project already exists', errorjson)

    # lookup user id (needed for insert) for user uuid (supplied in json)
    user_id = get_user_id(user_uuid, correlation_id)
    if user_id is None:
        errorjson = {'user_uuid': user_uuid, 'correlation_id': str(correlation_id)}
        raise UserDoesNotExistError('user does not exist', errorjson)

    sql = '''INSERT INTO public.projects_userproject (
        id,
        created,
        modified,
        user_id,
        project_id,
        status
    ) VALUES ( %s, %s, %s, %s, %s, %s );'''

    rowcount = execute_non_query(sql, (id, created, created, user_id, project_id, status), correlation_id)

    dbdata = list_user_projects(user_uuid, correlation_id)

    return rowcount


def create_user_project_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        up_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'up_json': up_json, 'correlation_id': correlation_id, 'event': event})

        create_user_project(up_json, correlation_id)

        response = {"statusCode": 201, "body": json.dumps(up_json)}

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
    print('running user_project')
    up_json = {
        'user_id': "e8d6b60f-9b99-4dfa-89d4-2ec7b2038b41",
        'project_id': "21c0779a-5fc2-4b72-8a88-0ba31456b563",
        'status': 'A',
        'id': '9620089b-e9a4-46fd-bb78-091c8449d778',
        'created': '2018-06-13 14:15:16.171819+00'
    }
    # print(up_json)

    ev = {'body': json.dumps(up_json)}
    print(create_user_project_api(ev, None))

    # ev = {}
    # print(list_user_projects("e8d6b60f-9b99-4dfa-89d4-2ec7b2038b41", None))