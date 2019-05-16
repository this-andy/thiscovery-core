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
import uuid

from .utilities import get_aws_region, get_environment_name

STACK_NAME = 'thiscovery-core'
environment_name = get_environment_name()
dynamodb = boto3.resource('dynamodb',region_name=get_aws_region())


def get_table(table_name):
    table = dynamodb.Table('-'.join([STACK_NAME, environment_name, table_name]))
    return table


def put_item(table_name: str, item_type: str, item_details, item: dict = {}, id=uuid.uuid4()):
    try:
        table = get_table(table_name)
        # item = {
        #     'id': str(id),
        #     'type': item_type,
        #     'details': item_details,
        # }

        item['id'] = str(id)
        item['type'] = item_type
        item['details'] = item_details

        response = table.put_item(Item=item)
    except Exception as err:
        raise err

    print(str(response))


def update_item(table_name: str, key: str, attr_name: str, attr_value):
    try:
        table = get_table(table_name)
        key_json = {'id': key}
        update = 'SET ' + attr_name + ' = :new_value'
        expression_json = {':new_value': attr_value}

        response = table.update_item(
            Key=key_json,
            UpdateExpression = update,
            ExpressionAttributeValues = expression_json
        )
    except Exception as err:
        raise err


def scan(table_name: str, filter_attr_name: str = None, filter_attr_value=None):
    try:
        table = get_table(table_name)
        if filter_attr_name is None:
            response = table.scan()
        else:
            response = table.scan(FilterExpression=Attr(filter_attr_name).eq(filter_attr_value))
        items = response['Items']
        return items
    except Exception as err:
        raise err


def get_item(table_name: str, key: str):

    try:
        table = get_table(table_name)
        key_json = {'id': key}
        response = table.get_item(Key=key_json)
        item = response['Item']
        return item
    except Exception as err:
        raise err


def delete_item(table_name: str, key: str):
    try:
        table = get_table(table_name)
        key_json = {'id': key}
        response = table.delete_item(Key=key_json)
    except Exception as err:
        raise err


if __name__ == "__main__":
    # item_details = {'hello': 'world'}
    # write(item_details)
    # print(str(read()))
    # delete('e847d0e6-8c08-4ffd-bade-dc55196b51a4')
    # print(get('notifications', '821ee279-18d5-4873-ba94-81c39b932a81'))

    update_item('tokens', 'abc', {"hello": "world", "more": "data!"})