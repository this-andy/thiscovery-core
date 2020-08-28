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
import thiscovery_lib.utilities as utils


class Lambda(utils.BaseClient):

    def __init__(self):
        super().__init__('lambda')

    def list_functions(self):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.list_functions
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Paginator.ListFunctions

        Returns:
        """
        funcs = list()
        paginator = self.client.get_paginator('list_functions')
        for response in paginator.paginate():
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f'call to boto3.client.list_functions failed with response: {response}'
            funcs += response['Functions']
        return funcs
