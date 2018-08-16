import json
from jsonpatch import JsonPatch
from api.pg_utilities import execute_query, execute_jsonpatch
from api.utilities import validate_uuid, get_correlation_id, get_logger, DetailedValueError, UserDoesNotExistError, \
    PatchInvalidJsonError, PatchAttributeNotRecognisedError, PatchOperationNotSupportedError, error_as_response_body


BASE_USER_SELECT_SQL = '''
  SELECT 
    username, 
    name,
    first_name,
    last_name,
    email,
    uuid 
  FROM 
    public.users_user
    '''


def get_user_id(user_uuid, correlation_id):

    base_sql = '''
      SELECT 
        id 
      FROM 
        public.users_user
      WHERE
        uuid = ''' \
        + "\'" + str(user_uuid) + "\'"

    try:
        result = int(execute_query(base_sql, correlation_id, False)[0][0])
    except IndexError:
        result = None

    return result


def get_user_by_uuid(user_uuid, correlation_id):

    try:
        user_uuid = validate_uuid(user_uuid)
    except DetailedValueError as err:
        raise err

    sql_where_clause = " WHERE uuid = \'" + str(user_uuid) + "\'"

    return execute_query(BASE_USER_SELECT_SQL + sql_where_clause, correlation_id)


def get_user_by_uuid_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        correlation_id = get_correlation_id(event)
        user_uuid = event['pathParameters']['id']
        logger.info('API call', extra={'user_uuid': user_uuid, 'correlation_id': correlation_id, 'event': event})

        result = get_user_by_uuid(user_uuid, correlation_id)

        if len(result) > 0:
            response = {"statusCode": 200, "body": json.dumps(result)}
        else:
            errorjson = {'user_uuid': user_uuid, 'correlation_id': str(correlation_id)}
            raise UserDoesNotExistError('user does not exist', errorjson)

    except UserDoesNotExistError as err:
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
            raise UserDoesNotExistError('user does not exist', errorjson)

    except UserDoesNotExistError as err:
        response = {"statusCode": 404, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


def patch_user(id_to_update, patch_json, correlation_id):
    mappings = {
        'email': {'table_name': 'public.users_user', 'column_name': 'email'},
        'first_name': {'table_name': 'public.users_user', 'column_name': 'first_name'},
        'last_name': {'table_name': 'public.users_user', 'column_name': 'last_name'},
    }

    id_column = 'uuid'

    execute_jsonpatch(id_column, id_to_update, mappings, patch_json, correlation_id)


def patch_user_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        correlation_id = get_correlation_id(event)
        user_uuid = event['pathParameters']['id']
        # user_jsonpatch = json.loads(event['body'])
        user_jsonpatch = JsonPatch.from_string(event['body'])

        logger.info('API call', extra={'user_uuid': user_uuid, 'user_jsonpatch': user_jsonpatch, 'correlation_id': correlation_id, 'event': event})

        patch_user(user_uuid, user_jsonpatch, correlation_id)

        response = {"statusCode": 204, "body": json.dumps('')}

    except UserDoesNotExistError as err:
        response = {"statusCode": 404, "body": err.as_response_body()}

    except (PatchAttributeNotRecognisedError, PatchOperationNotSupportedError, PatchInvalidJsonError, DetailedValueError) as err:
        response = {"statusCode": 400, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})

    return response


if __name__ == "__main__":
    qsp = {'email': 'andy.paterson@thisinstitute.cam.ac.uk'}
    ev = {'queryStringParameters': qsp}
    result = get_user_by_email_api(ev, None)
    print(result)

    # pp = {'id': "23e38ff4-1483-408a-ad58-d08cb5a34038"}
    # ev = {'pathParameters': pp}
    # print(get_user_by_uuid_api(ev, None))

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
