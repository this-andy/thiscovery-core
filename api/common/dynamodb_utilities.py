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
import uuid
import json

from api.common.utilities import get_aws_region

dynamodb = boto3.resource('dynamodb',region_name=get_aws_region())

notifications_table = dynamodb.Table('thiscovery-core-dev-notifications')

def write(item_details):
    item = {
        'id': str(uuid.uuid4()),
        'type': 'user-registration',
        'details': item_details,
    }

    response = notifications_table.put_item(Item=item)

    print(str(response))

def read():
    response = notifications_table.scan()
    items = response['Items']
    return items

def delete(id):
    response = notifications_table.delete_item(Key={'id':id})
    pass


if __name__ == "__main__":
    # item_details = {'hello': 'world'}
    # write(item_details)
    # print(str(read()))
    delete('e847d0e6-8c08-4ffd-bade-dc55196b51a4')