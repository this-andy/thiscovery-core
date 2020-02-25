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
import common.utilities as utils


class Ssm(utils.BaseClient):

    def __init__(self):
        super().__init__('ssm')

    def _prefix_name(self, name, prefix):
        if prefix is None:
            prefix = f"/{super().get_namespace()}/"
        return prefix + name

    def get_parameter(self, name, prefix=None):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameter
        """
        parameter_name = self._prefix_name(name, prefix)
        self.logger.debug(f'Getting SSM parameter {parameter_name}')
        response = self.client.get_parameter(
            Name=parameter_name,
        )
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f'call to boto3.client.get_parameter failed with response: {response}'
        return response['Parameter']['Value']

    def put_parameter(self, name, value, prefix=None):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.put_parameter
        """
        parameter_name = self._prefix_name(name, prefix)
        self.logger.debug(f'Adding or updating SSM parameter {parameter_name}')
        response = self.client.put_parameter(
            Name=parameter_name,
            Value=value,
            Type='String',
            Overwrite=True,
        )
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f'call to boto3.client.put_parameter failed with response: {response}'
        return response
