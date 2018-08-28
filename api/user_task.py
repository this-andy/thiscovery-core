import uuid
import json
import datetime
from api.pg_utilities import execute_query, execute_non_query
from api.utilities import DuplicateInsertError, ObjectDoesNotExistError, DetailedValueError, DetailedIntegrityError, \
    validate_uuid, validate_utc_datetime, get_correlation_id, get_logger, error_as_response_body
from api.user import get_user_by_id


def validate_status(s):
    return s


def list_user_tasks(user_id, correlation_id):

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
            up.user_id,
            ut.user_project_id,
            up.status as user_project_status,
            ut.project_task_id,
            pt.description as task_description,
            ut.id as user_task_id,
            ut.created,
            ut.modified,               
            ut.status,
            ut.consented                
        FROM 
            public.projects_usertask ut
            inner join public.projects_projecttask pt on pt.id = ut.project_task_id
            inner join public.projects_userproject up on up.id = ut.user_project_id
        WHERE up.user_id = ''' \
            + "\'" + str(user_id) + "\' " \
            + "ORDER BY ut.created"

    return execute_query(base_sql, correlation_id)


def list_user_tasks_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        params = event['queryStringParameters']
        user_uuid = params['user_id']
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_uuid': user_uuid, 'correlation_id': correlation_id})

        response = {
            "statusCode": 200,
            "body": json.dumps(list_user_tasks(user_uuid, correlation_id))
        }

    except ObjectDoesNotExistError as err:
        response = {"statusCode": 404, "body": err.as_response_body()}

    except DetailedValueError as err:
        response = {"statusCode": 400, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id, 'event': event})
    return response


def check_if_user_task_exists(user_project_id, project_task_id, correlation_id):

    base_sql = '''
      SELECT 
        COUNT(id)
      FROM public.projects_usertask 
      WHERE
        user_project_id = ''' \
               + "\'" + str(user_project_id) + "\'" \
               + " AND project_task_id = \'" + str(project_task_id) + "\'"

    return execute_query(base_sql, correlation_id, False)


def create_user_task(ut_json, correlation_id):
    # json MUST contain: user_project_id, project_task_id, ut_status, ut_consented
    # json may OPTIONALLY include: id, created,

    # extract mandatory data from json
    try:
        user_project_id = validate_uuid(ut_json['user_project_id'])
        project_task_id = validate_uuid(ut_json['project_task_id'])
        ut_status = validate_status(ut_json['status'])
        ut_consented = validate_utc_datetime(ut_json['consented'])
    except DetailedValueError:
        raise

    # now process optional json data
    if 'id' in ut_json:
        try:
            id = validate_uuid(ut_json['id'])
        except DetailedValueError:
            raise
    else:
        id = str(uuid.uuid4())
        ut_json['id'] = id

    if 'created' in ut_json:
        try:
            created = validate_utc_datetime(ut_json['created'])
        except DetailedValueError:
            raise
    else:
        created = str(datetime.datetime.utcnow())
        ut_json['created'] = created

    ut_json['modified'] = created

    # check external account does not already exist
    existing = check_if_user_task_exists(user_project_id, project_task_id, correlation_id)
    if int(existing[0][0]) > 0:
        errorjson = {'user_project_id': user_project_id, 'project_task_id': project_task_id, 'correlation_id': str(correlation_id)}
        raise DuplicateInsertError('user_task already exists', errorjson)

    sql = '''INSERT INTO public.projects_usertask (
            id,
            created,
            modified,
            user_project_id,
            project_task_id,
            status,
            consented
        ) VALUES ( %s, %s, %s, %s, %s, %s, %s );'''

    rowcount = execute_non_query(sql, (id, created, created, user_project_id, project_task_id, ut_status, ut_consented), correlation_id)

    return rowcount


def create_user_task_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        ut_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'ut_json': ut_json, 'correlation_id': correlation_id})

        create_user_task(ut_json, correlation_id)

        response = {"statusCode": 201, "body": json.dumps(ut_json)}

    except DuplicateInsertError as err:
        response = {"statusCode": 409, "body": err.as_response_body()}

    except (DetailedIntegrityError, DetailedValueError) as err:
        response = {"statusCode": 400, "body": err.as_response_body()}

    except Exception as ex:
        error_msg = ex.args[0]
        logger.error(error_msg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(error_msg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id, 'event': event})
    return response


if __name__ == "__main__":
    # print('hello')
    # ut_json = {
    #     'user_project_id': 'a55c9adc-bc5a-4e1b-be4b-e68db1a01c43',
    #     'project_task_id': 'ebd5f57b-e77c-4f26-9ae4-b65cdabaf018',
    #     'status': 'A',
    #     'consented': '2018-06-12 16:16:56.087895+01',
    #     'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
    #     'created': '2018-06-13 14:15:16.171819+00'
    # }
    # # print(ut_json)
    #
    # ev = {'body': json.dumps(ut_json)}
    # print(create_user_task_api(ev, None))

    print(list_user_tasks("851f7b34-f76c-49de-a382-7e4089b744e2", None))