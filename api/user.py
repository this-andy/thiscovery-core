import datetime
import json
import uuid

from jsonpatch import JsonPatch
from api.pg_utilities import execute_query, execute_jsonpatch, execute_non_query
from api.utilities import validate_uuid, get_correlation_id, get_logger, DetailedValueError, DuplicateInsertError, ObjectDoesNotExistError, \
    PatchInvalidJsonError, PatchAttributeNotRecognisedError, PatchOperationNotSupportedError, error_as_response_body, validate_utc_datetime


BASE_USER_SELECT_SQL = '''
  SELECT 
    id, 
    created, 
    modified, 
    email, 
    title, 
    first_name, 
    last_name, 
    auth0_id, 
    status
  FROM 
    public.projects_user
    '''


def validate_status(s):
    return s


def get_user_by_id(user_id, correlation_id):

    try:
        user_uuid = validate_uuid(user_id)
    except DetailedValueError as err:
        raise err

    sql_where_clause = " WHERE id = \'" + str(user_id) + "\'"

    return execute_query(BASE_USER_SELECT_SQL + sql_where_clause, correlation_id)


def get_user_by_id_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        correlation_id = get_correlation_id(event)
        user_id = event['pathParameters']['id']
        logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})

        result = get_user_by_id(user_id, correlation_id)

        if len(result) > 0:
            response = {"statusCode": 200, "body": json.dumps(result)}
        else:
            errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
            raise ObjectDoesNotExistError('user does not exist', errorjson)

    except ObjectDoesNotExistError as err:
        response = {"statusCode": 404, "body": err.as_response_body()}

    except DetailedValueError  as err:
        response = {"statusCode": 400, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


def get_user_by_email(user_email, correlation_id):

    sql_where_clause = " WHERE email = \'" + str(user_email) + "\'"

    return execute_query(BASE_USER_SELECT_SQL + sql_where_clause, correlation_id)


def get_user_by_email_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        user_email = event['queryStringParameters']['email']
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_email': user_email, 'correlation_id': correlation_id, 'event': event})

        result = get_user_by_email(user_email, correlation_id)

        if len(result) > 0:
            response = {"statusCode": 200, "body": json.dumps(result)}
        else:
            errorjson = {'user_email': user_email, 'correlation_id': str(correlation_id)}
            raise ObjectDoesNotExistError('user does not exist', errorjson)

    except ObjectDoesNotExistError as err:
        response = {"statusCode": 404, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


def patch_user(id_to_update, patch_json, correlation_id):
    mappings = {
        'email': {'table_name': 'public.projects_user', 'column_name': 'email'},
        'first_name': {'table_name': 'public.projects_user', 'column_name': 'first_name'},
        'last_name': {'table_name': 'public.projects_user', 'column_name': 'last_name'},
    }

    id_column = 'id'

    execute_jsonpatch(id_column, id_to_update, mappings, patch_json, correlation_id)


def patch_user_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        correlation_id = get_correlation_id(event)
        user_id = event['pathParameters']['id']
        # user_jsonpatch = json.loads(event['body'])
        user_jsonpatch = JsonPatch.from_string(event['body'])

        logger.info('API call', extra={'user_id': user_id, 'user_jsonpatch': user_jsonpatch, 'correlation_id': correlation_id, 'event': event})

        patch_user(user_id, user_jsonpatch, correlation_id)

        response = {"statusCode": 204, "body": json.dumps('')}

    except ObjectDoesNotExistError as err:
        response = {"statusCode": 404, "body": err.as_response_body()}

    except (PatchAttributeNotRecognisedError, PatchOperationNotSupportedError, PatchInvalidJsonError, DetailedValueError) as err:
        response = {"statusCode": 400, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})

    return response

# User JSON should look like this:
#   {
#     "id": "48e30e54-b4fc-4303-963f-2943dda2b139",
#     "created": "2018-08-21T11:16:56+01:00",
#     "email": "sw@email.addr",
#     "title": "Mr",
#     "first_name": "Steven",
#     "last_name": "Walcorn",
#     "auth0_id": "1234abcd",
#     "status": "new"
#   }

def create_user(user_json, correlation_id):
    # json MUST contain: email, title, first_name, last_name, status
    # json may OPTIONALLY include: id, created, auth0_id

    # extract mandatory data from json
    try:
        email = user_json['email']
        title = user_json['title']
        first_name = user_json['first_name']
        last_name = user_json['last_name']
        status = validate_status(user_json['status'])
    except :
        raise

    # now process optional json data
    if 'id' in user_json:
        try:
            id = validate_uuid(user_json['id'])
        except DetailedValueError:
            raise
    else:
        id = str(uuid.uuid4())
        user_json['id'] = id

    if 'created' in user_json:
        try:
            created = validate_utc_datetime(user_json['created'])
        except DetailedValueError:
            raise
    else:
        created = str(datetime.datetime.utcnow())
        user_json['created'] = created

    auth0_id = user_json['auth0_id']

    user_json['modified'] = created

    existing_user = get_user_by_id(id, correlation_id)
    if len(existing_user) > 0:
        errorjson = {'id': id, 'correlation_id': str(correlation_id)}
        raise DuplicateInsertError('user already exists', errorjson)

    sql = '''INSERT INTO public.projects_user (
            id,
            created,
            modified,
            email,
            title,
            first_name,
            last_name,
            auth0_id,
            status
        ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s );'''

    rowcount = execute_non_query(sql, (id, created, created, email, title, first_name, last_name, auth0_id, status), correlation_id)

    return rowcount


def create_user_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        user_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_json': user_json, 'correlation_id': correlation_id, 'event': event})

        create_user(user_json, correlation_id)

        response = {"statusCode": 201, "body": json.dumps(user_json)}

    except DuplicateInsertError as err:
        response = {"statusCode": 409, "body": err.as_response_body()}

    except DetailedValueError as err:
        response = {"statusCode": 400, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


if __name__ == "__main__":
    # qsp = {'email': 'andy.paterson@thisinstitute.cam.ac.uk'}
    # ev = {'queryStringParameters': qsp}
    # result = get_user_by_email_api(ev, None)
    # print(result)

    # pp = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}
    # ev = {'pathParameters': pp}
    # print(get_user_by_id_api(ev, None))

    # jp = [{'op': 'replace', 'path': 'first_name', 'value': 'zahra'}, {'op': 'replace', 'path': 'last_name', 'value': 'hhyth'}, {'op': 'replace', 'path': '/email', 'value': 'zahra@somewhere.com'}]
    #
    # ev = {'body': json.dumps(jp)}
    # ev['pathParameters'] = {'id': '8e385316-5827-4c72-8d4b-af5c57ff4670'}
    #
    # r = patch_user_api(ev, None)
    #
    # print(r)

    # sql_updates = jsonpatch_to_sql(jp, '8e385316-5827-4c72-8d4b-af5c57ff4679')

    # print(sql_updates)
    # for (sql_update, params) in sql_updates:
    #     execute_non_query(sql_update, params, None)

    user_json = {
        "id": "48e30e54-b4fc-4303-963f-2943dda2b139",
        "created": "2018-08-21T11:16:56+01:00",
        "email": "sw@email.addr",
        "title": "Mr",
        "first_name": "Steven",
        "last_name": "Walcorn",
        "auth0_id": "1234abcd",
        "status": "new"}

    correlation_id = None
    # print(create_user(user_json,correlation_id))

    ev = {'body': json.dumps(user_json)}
    print(create_user_api(ev, None))
