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

from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

import common.utilities as utils


STACK_NAME = 'thiscovery-core'


class Dynamodb(utils.BaseClient):
    def __init__(self, correlation_id=None):
        super().__init__('dynamodb', client_type='resource', correlation_id=correlation_id)
        super().get_namespace()

    def get_table(self, table_name):
        table_full_name = '-'.join([STACK_NAME, self.aws_namespace, table_name])
        self.logger.debug('Table full name', extra={'table_full_name': table_full_name})
        return self.client.Table(table_full_name)

    def put_item(self, table_name: str, key, item_type: str, item_details, item=dict(), update_allowed=False, correlation_id=None):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Table.put_item
        Args:
            table_name:
            key:
            item_type:
            item_details:
            item:
            update_allowed:
            correlation_id:

        Returns:
        """
        try:
            table = self.get_table(table_name)

            item['id'] = str(key)
            item['type'] = item_type
            item['details'] = item_details
            now = str(utils.now_with_tz())
            item['created'] = now
            item['modified'] = now

            self.logger.info('dynamodb put', extra={'table_name': table_name, 'item': item, 'correlation_id': self.correlation_id})
            if update_allowed:
                return table.put_item(Item=item)
            else:
                return table.put_item(Item=item, ConditionExpression='attribute_not_exists(id)')
        except ClientError as ex:
            error_code = ex.response['Error']['Code']
            errorjson = {'error_code': error_code, 'table_name': table_name, 'item_type': item_type, 'id': str(key), 'correlation_id': self.correlation_id}
            raise utils.DetailedValueError('Dynamodb raised an error', errorjson)

    def update_item(self, table_name: str, key: str, name_value_pairs: dict, correlation_id=None, **kwargs):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Table.update_item

        Args:
            table_name:
            key:
            name_value_pairs:
            correlation_id:
            **kwargs: use ReturnValues to get the item attributes as they appear before or after the update

        Returns:
            Only response metadata such as status code, unless the parameter ReturnValues is specified in **kwargs

        Notes:
            US 2951 proposes adding support for partial map updates to this function.
        """
        if correlation_id is None:
            correlation_id = utils.new_correlation_id()

        table = self.get_table(table_name)
        key_json = {'id': key}
        update_expr = 'SET #modified = :m '
        values_expr = {
            ':m': name_value_pairs.pop(
                'modified', str(utils.now_with_tz())
            )
        }
        attr_names_expr = {'#modified': 'modified'}  # not strictly necessary, but allows easy addition of names later
        param_count = 1
        for name,  value in name_value_pairs.items():
            param_name = ':p' + str(param_count)
            if name == 'status':   # todo generalise this to other reserved words, and ensure it only catches whole words
                attr_name = '#a' + str(param_count)
                attr_names_expr[attr_name] = 'status'
            else:
                attr_name = name
            update_expr += ', ' + attr_name + ' = ' + param_name

            values_expr[param_name] = value

            param_count += 1

        self.logger.info('dynamodb update', extra={'table_name': table_name, 'key': key, 'update_expr': update_expr, 'values_expr': values_expr,
                                                   'correlation_id': correlation_id})
        return table.update_item(
            Key=key_json,
            UpdateExpression=update_expr,
            ExpressionAttributeValues=values_expr,
            ExpressionAttributeNames=attr_names_expr,
            **kwargs,
        )

    def scan(self, table_name: str, filter_attr_name: str = None, filter_attr_values=None):
        table = self.get_table(table_name)

        # accept string but make it into a list for later processing
        if isinstance(filter_attr_values, str):
            filter_attr_values = [filter_attr_values]
        self.logger.info('dynamodb scan', extra={
            'table_name': table_name,
            'filter_attr_name': filter_attr_name,
            'filter_attr_value': str(filter_attr_values),
            'correlation_id': self.correlation_id})
        if filter_attr_name is None:
            response = table.scan()
        else:
            filter_expr = Attr(filter_attr_name).eq(filter_attr_values[0])
            for value in filter_attr_values[1:]:
                filter_expr = filter_expr | Attr(filter_attr_name).eq(value)
            response = table.scan(FilterExpression=filter_expr)
        items = response['Items']
        self.logger.info('dynamodb scan result', extra={'count': str(len(items)), 'correlation_id': self.correlation_id})
        return items

    def get_item(self, table_name: str, key: str, correlation_id=None):
        if correlation_id is None:
            correlation_id = utils.new_correlation_id()
        table = self.get_table(table_name)
        key_json = {'id': key}
        self.logger.info('dynamodb get', extra={'table_name': table_name, 'key': key, 'correlation_id': correlation_id})
        response = table.get_item(Key=key_json)
        if 'Item' in response:
            return response['Item']
        else:
            # not found
            return None

    def delete_item(self, table_name: str, key: str, correlation_id=None):
        if correlation_id is None:
            correlation_id = utils.new_correlation_id()
        table = self.get_table(table_name)
        key_json = {'id': key}
        self.logger.info('dynamodb delete', extra={'table_name': table_name, 'key': key, 'correlation_id': correlation_id})
        return table.delete_item(Key=key_json)

    def delete_all(self, table_name: str, correlation_id=None):
        if correlation_id is None:
            correlation_id = utils.new_correlation_id()
        table = self.get_table(table_name)
        items = self.scan(table_name)
        for item in items:
            key = item['id']
            key_json = {'id': key}
            self.logger.info('dynamodb delete_all', extra={'table_name': table_name, 'key': key, 'correlation_id': correlation_id})
            table.delete_item(Key=key_json)
