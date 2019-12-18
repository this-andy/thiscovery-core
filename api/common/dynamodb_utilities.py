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
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from common.utilities import get_aws_region, get_environment_name, get_logger, DuplicateInsertError, now_with_tz, new_correlation_id


STACK_NAME = 'thiscovery-core'


def get_table(table_name):
    try:
        environment_name = get_environment_name()
        dynamodb = boto3.resource('dynamodb', region_name=get_aws_region())
        table = dynamodb.Table('-'.join([STACK_NAME, environment_name, table_name]))
        return table
    except Exception as ex:
        raise ex


def put_item(table_name: str, key, item_type: str, item_details, item: dict, update_allowed=False, correlation_id=new_correlation_id()):
    try:
        logger = get_logger()
        table = get_table(table_name)

        item['id'] = str(key)
        item['type'] = item_type
        item['details'] = item_details
        now = str(now_with_tz())
        item['created'] = now
        item['modified'] = now

        logger.info('dynamodb put', extra={'table_name': table_name, 'item': item, 'correlation_id': correlation_id})
        if update_allowed:
            response = table.put_item(Item=item)
        else:
            response = table.put_item(Item=item, ConditionExpression='attribute_not_exists(id)')
    except ClientError as ex:
        error_code = ex.response['Error']['Code']
        errorjson = {'error_code': error_code, 'table_name': table_name, 'item_type': item_type, 'id': str(key), 'correlation_id': correlation_id}
        raise DuplicateInsertError('item already exists', errorjson)


def update_item_old(table_name: str, key: str, attr_name: str, attr_value, correlation_id=new_correlation_id()):
    try:
        logger = get_logger()
        table = get_table(table_name)
        key_json = {'id': key}
        update = 'SET ' + attr_name + ' = :new_value, modified = :m'
        expression_json = {':new_value': attr_value, ':m': str(now_with_tz())}

        logger.info('dynamodb update', extra={'table_name': table_name, 'key': key, 'attr_name': attr_name, 'attr_value': attr_value, 'correlation_id': correlation_id})
        response = table.update_item(
            Key=key_json,
            UpdateExpression = update,
            ExpressionAttributeValues = expression_json
        )
    except Exception as ex:
        raise ex


def update_item(table_name: str, key: str, name_value_pairs: dict, correlation_id=new_correlation_id()):
    try:
        logger = get_logger()
        table = get_table(table_name)
        key_json = {'id': key}
        update_expr = 'SET #modified = :m '
        values_expr = {':m': str(now_with_tz())}
        attr_names_expr = {'#modified': 'modified'}  # not strictly necessary, but allows easy addition of names later
        param_count = 1
        for name,  value in name_value_pairs.items():
            param_name = ':p' + str(param_count)
            map_name = None
            if name == 'status':   # todo generalise this to other reserved words, and ensure it only catches whole words
                if '.' in name:
                    map_name = name.split('.')[0]
                attr_name = '#a' + str(param_count)
                attr_names_expr[attr_name] = 'status'
            else:
                attr_name = name
            if map_name is not None:
                attr_name = map_name + '.' + attr_name
            update_expr += ', ' + attr_name + ' = ' + param_name

            values_expr[param_name] = str(value)

            param_count += 1

        logger.info('dynamodb update', extra={'table_name': table_name, 'key': key, 'update_expr': update_expr, 'values_expr': values_expr, 'correlation_id': correlation_id})
        response = table.update_item(
            Key=key_json,
            UpdateExpression = update_expr,
            ExpressionAttributeValues = values_expr,
            ExpressionAttributeNames = attr_names_expr,
        )
        return response
    except Exception as ex:
        raise ex


def scan_old(table_name: str, filter_attr_name: str = None, filter_attr_value=None, correlation_id=new_correlation_id()):
    try:
        logger = get_logger()
        table = get_table(table_name)
        logger.info('dynamodb scan', extra={'table_name': table_name, 'filter_attr_name': filter_attr_name, 'filter_attr_value': filter_attr_value, 'correlation_id': correlation_id})
        if filter_attr_name is None:
            response = table.scan()
        else:
            response = table.scan(FilterExpression=Attr(filter_attr_name).eq(filter_attr_value))
        items = response['Items']
        logger.info('dynamodb scan result', extra={'count': str(len(items)), 'correlation_id': correlation_id})
        return items
    except Exception as ex:
        raise ex


def scan(table_name: str, filter_attr_name: str = None, filter_attr_values=None, correlation_id=new_correlation_id()):
    try:
        logger = get_logger()
        table = get_table(table_name)

        # accept string but make it into a list for later processing
        if isinstance(filter_attr_values, str):
            filter_attr_values = [filter_attr_values]
        logger.info('dynamodb scan', extra={
            'table_name': table_name,
            'filter_attr_name': filter_attr_name,
            'filter_attr_value': str(filter_attr_values),
            'correlation_id': correlation_id})
        if filter_attr_name is None:
            response = table.scan()
        else:
            filter_expr = Attr(filter_attr_name).eq(filter_attr_values[0])
            for value in filter_attr_values[1:]:
                filter_expr = filter_expr | Attr(filter_attr_name).eq(value)
            response = table.scan(FilterExpression=filter_expr)
        items = response['Items']
        logger.info('dynamodb scan result', extra={'count': str(len(items)), 'correlation_id': correlation_id})
        return items
    except Exception as ex:
        raise ex


def get_item(table_name: str, key: str, correlation_id=new_correlation_id()):
    try:
        logger = get_logger()
        table = get_table(table_name)
        key_json = {'id': key}
        logger.info('dynamodb get', extra={'table_name': table_name, 'key': key, 'correlation_id': correlation_id})
        response = table.get_item(Key=key_json)
        if 'Item' in response:
            return response['Item']
        else:
            # not found
            return None
    except Exception as ex:
        raise ex


def delete_item(table_name: str, key: str, correlation_id=new_correlation_id()):
    try:
        logger = get_logger()
        table = get_table(table_name)
        key_json = {'id': key}
        logger.info('dynamodb delete', extra={'table_name': table_name, 'key': key, 'correlation_id': correlation_id})
        response = table.delete_item(Key=key_json)
    except Exception as err:
        raise err


def delete_all(table_name: str, correlation_id=new_correlation_id()):
    try:
        logger = get_logger()
        table = get_table(table_name)
        items = scan(table_name)
        for item in items:
            key = item['id']
            key_json = {'id': key}
            logger.info('dynamodb delete_all', extra={'table_name': table_name, 'key': key, 'correlation_id': correlation_id})
            table.delete_item(Key=key_json)
    except Exception as err:
        raise err


if __name__ == "__main__":
    pass
    # item_details = {'hello': 'world'}
    # put_item('notifications', 'abd', 'test', item_details, {})


    # print(str(read()))
    # delete('e847d0e6-8c08-4ffd-bade-dc55196b51a4')
    # print(get('notifications', '821ee279-18d5-4873-ba94-81c39b932a81'))

    # update_item('notifications', 'abd', 'details', {"hello": "world", "more": "data!"})

    result = scan('notifications', 'processing_status', ['new', 'retrying'])
    print(len(result))
    print(result)

    # av_pairs = {
    #     'label': 'there',
    #     'status': 'not updated',
    #     'processing.status': 'testing done?!'
    # }
    # result = update_item('notifications', '8345331b-9416-45bc-9223-01435e45d36e', av_pairs )
