import json
import uuid
from http import HTTPStatus
from datetime import timedelta
from jsonpatch import JsonPatch, JsonPatchException
from api.pg_utilities import execute_query, execute_jsonpatch, execute_non_query
from api.utilities import validate_uuid, get_correlation_id, get_logger, DetailedValueError, DuplicateInsertError, ObjectDoesNotExistError, \
    PatchInvalidJsonError, PatchAttributeNotRecognisedError, PatchOperationNotSupportedError, error_as_response_body, validate_utc_datetime, \
    now_with_tz
from api.entity_update import EntityUpdate


BASE_USER_SELECT_SQL = '''
  SELECT 
    id, 
    created, 
    modified, 
    email, 
    email_address_verified,
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
        user_id = validate_uuid(user_id)
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err

    sql_where_clause = " WHERE id = %s"

    return execute_query(BASE_USER_SELECT_SQL + sql_where_clause, (str(user_id),), correlation_id)


def get_user_by_id_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        correlation_id = get_correlation_id(event)
        user_id = event['pathParameters']['id']
        logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})

        result = get_user_by_id(user_id, correlation_id)

        if len(result) > 0:
            response = {"statusCode": HTTPStatus.OK, "body": json.dumps(result)}
        else:
            errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
            raise ObjectDoesNotExistError('user does not exist', errorjson)

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


def get_user_by_email(user_email, correlation_id):

    sql_where_clause = " WHERE email = %s"

    return execute_query(BASE_USER_SELECT_SQL + sql_where_clause, (str(user_email),), correlation_id)


def get_user_by_email_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        user_email = event['queryStringParameters']['email']
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_email': user_email, 'correlation_id': correlation_id, 'event': event})

        result = get_user_by_email(user_email, correlation_id)

        if len(result) > 0:
            response = {"statusCode": HTTPStatus.OK, "body": json.dumps(result)}
        else:
            errorjson = {'user_email': user_email, 'correlation_id': str(correlation_id)}
            raise ObjectDoesNotExistError('user does not exist', errorjson)

    except ObjectDoesNotExistError as err:
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


def patch_user(id_to_update, patch_json, modified, correlation_id):
    mappings = {
        'email': {'table_name': 'public.projects_user', 'column_name': 'email'},
        'email_address_verified': {'table_name': 'public.projects_user', 'column_name': 'email_address_verified'},
        'title': {'table_name': 'public.projects_user', 'column_name': 'title'},
        'first_name': {'table_name': 'public.projects_user', 'column_name': 'first_name'},
        'last_name': {'table_name': 'public.projects_user', 'column_name': 'last_name'},
        'auth0_id': {'table_name': 'public.projects_user', 'column_name': 'auth0_id'},
        'status': {'table_name': 'public.projects_user', 'column_name': 'status'},
    }

    id_column = 'id'

    execute_jsonpatch(id_column, id_to_update, mappings, patch_json, modified, correlation_id)


def create_user_entity_update(user_id, user_jsonpatch, modified, correlation_id):
    try:
        original_user_list = get_user_by_id(user_id, correlation_id)
        original_user = original_user_list[0]
        return EntityUpdate('user', original_user, user_jsonpatch, modified, correlation_id)
    except IndexError as ex:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise ObjectDoesNotExistError('user does not exist', errorjson)
    except JsonPatchException as ex:
        errorjson = {'user_jsonpatch': user_jsonpatch.to_string(), 'correlation_id': str(correlation_id)}
        raise PatchInvalidJsonError('invalid jsonpatch', errorjson)


def patch_user_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        correlation_id = get_correlation_id(event)
        # get info supplied to api call
        user_id = event['pathParameters']['id']
        user_jsonpatch = JsonPatch.from_string(event['body'])

        logger.info('API call', extra={'user_id': user_id, 'user_jsonpatch': user_jsonpatch, 'correlation_id': correlation_id, 'event': event})

        modified = now_with_tz()

        # create an audit record of update, inc 'undo' patch
        entity_update = create_user_entity_update(user_id, user_jsonpatch, modified, correlation_id)

        patch_user(user_id, user_jsonpatch, modified, correlation_id)

        response = {"statusCode": HTTPStatus.NO_CONTENT, "body": json.dumps('')}

        # on successful update save audit record
        entity_update.save()

    except ObjectDoesNotExistError as err:
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    except (PatchAttributeNotRecognisedError, PatchOperationNotSupportedError, PatchInvalidJsonError, DetailedValueError) as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})

    return response


# User create JSON should look like this:
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
    # note that users will always be created with email_address_verified = false

    # extract mandatory data from json
    try:
        email = user_json['email']
        title = user_json['title']
        first_name = user_json['first_name']
        last_name = user_json['last_name']
        status = validate_status(user_json['status'])
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err


    # now process optional json data
    if 'id' in user_json:
        try:
            id = validate_uuid(user_json['id'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    if 'created' in user_json:
        try:
            created = validate_utc_datetime(user_json['created'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        created = str(now_with_tz())

    if 'auth0_id' in user_json:
        auth0_id = user_json['auth0_id']
    else:
        auth0_id = None

    # set up default values
    email_address_verified = False
    email_verification_token = str(uuid.uuid4())
    email_verification_expiry = str(now_with_tz() + timedelta(hours=24))

    existing_user = get_user_by_id(id, correlation_id)
    if len(existing_user) > 0:
        errorjson = {'id': id, 'correlation_id': str(correlation_id)}
        raise DuplicateInsertError('user already exists', errorjson)

    sql = '''INSERT INTO public.projects_user (
            id,
            created,
            modified,
            email,
            email_address_verified,
            email_verification_token,
            email_verification_expiry,
            title,
            first_name,
            last_name,
            auth0_id,
            status
        ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s );'''

    params = (id, created, created, email, email_address_verified, email_verification_token, email_verification_expiry, title, first_name, last_name, auth0_id, status)
    execute_non_query(sql, params, correlation_id)

    new_user = {
        'id': id,
        'created': created,
        'modified': created,        
        'email': email,
        'email_address_verified': email_address_verified,
        'email_verification_token': email_verification_token,
        'email_verification_expiry': email_verification_expiry,
        'title': title,
        'first_name': first_name,
        'last_name': last_name,
        'auth0_id': auth0_id,
        'status': status,
    }
    
    return new_user


def create_user_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        user_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_json': user_json, 'correlation_id': correlation_id, 'event': event})

        new_user = create_user(user_json, correlation_id)

        response = {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user)}

    except DuplicateInsertError as err:
        response = {"statusCode": HTTPStatus.CONFLICT, "body": err.as_response_body()}

    except DetailedValueError as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


def validate_user_email(user_id, email_verification_token_to_check, correlation_id):
    sql = """
        SELECT 
            email_verification_token, email_verification_expiry
        FROM 
            public.projects_user
        WHERE
            id = %s
    """
    result = execute_query(sql, (str(user_id),), correlation_id)



if __name__ == "__main__":
    # qsp = {'email': 'andy.paterson@thisinstitute.cam.ac.uk'}
    # ev = {'queryStringParameters': qsp}
    # result = get_user_by_email_api(ev, None)
    # print(result)

    # pp = {'id': "1cbe9aad-b29f-46b5-920e-b4c496d42515"}
    # ev = {'pathParameters': pp}
    # print(get_user_by_id_api(ev, None))

    # jp = [{'op': 'replace', 'path': '/first_name', 'value': '1555'}, {'op': 'replace', 'path': '/last_name', 'value': '11345'}, {'op': 'replace', 'path': '/email', 'value': '1234@somewhere.com'}]
    # # jp = [{'op': 'replace', 'path': '/email_address_verified', 'value': 'True'}]
    #
    # ev = {'body': json.dumps(jp)}
    # ev['pathParameters'] = {'id': '48e30e54-b4fc-4303-963f-2943dda2b139'}
    #
    # r = patch_user_api(ev, None)
    #
    # print(r)

    # sql_updates = jsonpatch_to_sql(jp, '8e385316-5827-4c72-8d4b-af5c57ff4679')

    # print(sql_updates)
    # for (sql_update, params) in sql_updates:
    #     execute_non_query(sql_update, params, None)

    user_json = {
        "email": "an@email.addr",
        "title": "Mr",
        "first_name": "Albert",
        "last_name": "Narlcorn",
        "status": "new"}

    correlation_id = None
    print(create_user(user_json,correlation_id))

    # ev = {'body': json.dumps(user_json)}
    # print(create_user_api(ev, None))


