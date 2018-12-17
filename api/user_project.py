import uuid
import json
from http import HTTPStatus
from api.pg_utilities import execute_query, execute_non_query
from api.utilities import ObjectDoesNotExistError, DuplicateInsertError, DetailedIntegrityError, DetailedValueError, \
    validate_uuid, validate_utc_datetime, get_correlation_id, get_logger, error_as_response_body, now_with_tz
from api.user import get_user_by_id


def validate_status(s):
    return s


def list_user_projects(user_id, correlation_id):

    try:
        user_id = validate_uuid(user_id)
    except DetailedValueError:
        raise

    # check that user exists
    result = get_user_by_id(user_id, correlation_id)
    if len(result) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise ObjectDoesNotExistError('user does not exist', errorjson)

    base_sql = '''
        SELECT 
            id,
            user_id,
            project_id,
            created,
            modified,               
            status                
        FROM 
            public.projects_userproject
        WHERE user_id = %s
    '''

    return execute_query(base_sql, (str(user_id),), correlation_id)


def list_user_projects_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        params = event['queryStringParameters']
        user_id = params['user_id']  # all public id are uuids
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})

        response = {
            "statusCode": HTTPStatus.OK,
            "body": json.dumps(list_user_projects(user_id, correlation_id))
        }

    except ObjectDoesNotExistError as err:
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    except DetailedValueError as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


def get_existing_user_project_id(user_id, project_id, correlation_id):

    base_sql = """
      SELECT 
        id
      FROM public.projects_userproject
      WHERE 
        project_id = %s
        AND user_id = %s
    """

    return execute_query(base_sql, (str(project_id), str(user_id)), correlation_id)


def create_user_project(up_json, correlation_id, do_nothing_if_exists=False):
    # json MUST contain: user_id, project_id, status
    # json may OPTIONALLY include: id, created,

    # extract mandatory data from json
    try:
        user_id = validate_uuid(up_json['user_id'])    # all public id are uuids
        project_id = validate_uuid(up_json['project_id'])
        status = validate_status(up_json['status'])
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err

    # now process optional json data
    if 'id' in up_json:
        try:
            id = validate_uuid(up_json['id'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    if 'created' in up_json:
        try:
            created = validate_utc_datetime(up_json['created'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        created = str(now_with_tz())

    # check external account does not already exist
    existing = get_existing_user_project_id(user_id, project_id, correlation_id)
    # if int(existing[0][0]) > 0:
    if len(existing) > 0:
        if do_nothing_if_exists:
            return existing[0]
        else:
            errorjson = {'user_id': user_id, 'project_id': project_id, 'correlation_id': str(correlation_id)}
            raise DuplicateInsertError('user_project already exists', errorjson)

    # lookup user id (needed for insert) for user uuid (supplied in json)
    result = get_user_by_id(user_id, correlation_id)
    if len(result) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise ObjectDoesNotExistError('user does not exist', errorjson)

    sql = '''INSERT INTO public.projects_userproject (
        id,
        created,
        modified,
        user_id,
        project_id,
        status
    ) VALUES ( %s, %s, %s, %s, %s, %s );'''

    execute_non_query(sql, (id, created, created, user_id, project_id, status), correlation_id)

    new_user_project = {
        'id': id,
        'created': created,
        'modified': created,
        'user_id': user_id,
        'project_id': project_id,
        'status': status,
    }

    return new_user_project


def create_user_project_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        up_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'up_json': up_json, 'correlation_id': correlation_id, 'event': event})

        new_user_project = create_user_project(up_json, correlation_id)

        response = {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user_project)}

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


def create_user_project_if_not_exists(user_id, project_id, correlation_id):
    up_json = {
        'user_id': user_id,
        'project_id': project_id,
        'status': 'active'
    }
    return create_user_project(up_json, correlation_id, True)


if __name__ == "__main__":
    # print('running user_project')
    up_json = {
        'user_id': "0bef3b7e-ab4a-437e-936a-6b7b557fb059",
        'project_id': "0c137d9d-e087-448b-ba8d-24141b6ceecd",
        'status': 'active'
    }
    # # print(up_json)
    #
    ev = {'body': json.dumps(up_json)}
    print(create_user_project_if_not_exists("0bef3b7e-ab4a-437e-936a-6b7b557fb059", "0c137d9d-e087-448b-ba8d-24141b6ceecd", 'abc'))
    # print(create_user_project_api(ev, None))
    #
    # # ev = {}
    # print(list_user_projects("851f7b34-f76c-49de-a382-7e4089b744e2", None))
