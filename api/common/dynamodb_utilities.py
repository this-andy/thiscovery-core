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
import uuid

# from .utilities import get_aws_region, get_environment_name, get_logger
from .utilities import get_aws_region, get_environment_name, get_logger, DuplicateInsertError

STACK_NAME = 'thiscovery-core'


def get_table(table_name):
    try:
        environment_name = get_environment_name()
        dynamodb = boto3.resource('dynamodb', region_name=get_aws_region())
        table = dynamodb.Table('-'.join([STACK_NAME, environment_name, table_name]))
        return table
    except Exception as ex:
        raise ex


def put_item(table_name: str, item_type: str, item_details, item: dict, id, update_allowed=False):
    try:
        logger = get_logger()
        table = get_table(table_name)

        item['id'] = str(id)
        item['type'] = item_type
        item['details'] = item_details

        logger.info('dynamodb put', extra = {'table_name': table_name,'item': item})
        if update_allowed:
            response = table.put_item(Item=item)
        else:
            response = table.put_item(Item=item, ConditionExpression='attribute_not_exists(id)')
    except ClientError as ex:
        error_code = ex.response['Error']['Code']
        errorjson = {'error_code': error_code, 'table_name': table_name, 'item_type': item_type, 'id': str(id)}
        raise DuplicateInsertError('item already exists', errorjson)


def update_item(table_name: str, key: str, attr_name: str, attr_value):
    try:
        logger = get_logger()
        table = get_table(table_name)
        key_json = {'id': key}
        update = 'SET ' + attr_name + ' = :new_value'
        expression_json = {':new_value': attr_value}

        logger.info('dynamodb update', extra = {'table_name': table_name,'key': key, 'attr_name': attr_name, 'attr_value': attr_value})
        response = table.update_item(
            Key=key_json,
            UpdateExpression = update,
            ExpressionAttributeValues = expression_json
        )
    except Exception as ex:
        raise ex


def scan(table_name: str, filter_attr_name: str = None, filter_attr_value=None):
    try:
        logger = get_logger()
        table = get_table(table_name)
        logger.info('dynamodb scan', extra = {'table_name': table_name,'filter_attr_name': filter_attr_name, 'filter_attr_value': filter_attr_value})
        if filter_attr_name is None:
            response = table.scan()
        else:
            response = table.scan(FilterExpression=Attr(filter_attr_name).eq(filter_attr_value))
        items = response['Items']
        logger.info('dynamodb scan result', extra = {'count': str(len(items))})
        return items
    except Exception as ex:
        raise ex


def get_item(table_name: str, key: str):
    try:
        logger = get_logger()
        table = get_table(table_name)
        key_json = {'id': key}
        logger.info('dynamodb get', extra = {'table_name': table_name,'key': key})
        response = table.get_item(Key=key_json)
        item = response['Item']
        return item
    except Exception as ex:
        raise ex


def delete_item(table_name: str, key: str):
    try:
        logger = get_logger()
        table = get_table(table_name)
        key_json = {'id': key}
        logger.info('dynamodb delete', extra = {'table_name': table_name,'key': key})
        response = table.delete_item(Key=key_json)
    except Exception as err:
        raise err


if __name__ == "__main__":
    item_details = {'hello': 'world'}
    put_item('notifications', 'test', item_details, {}, 'abd')


    # write(item_details)
    # print(str(read()))
    # delete('e847d0e6-8c08-4ffd-bade-dc55196b51a4')
    # print(get('notifications', '821ee279-18d5-4873-ba94-81c39b932a81'))

    # update_item('tokens', 'abc', {"hello": "world", "more": "data!"})