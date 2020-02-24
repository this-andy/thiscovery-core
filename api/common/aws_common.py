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

from common.utilities import get_logger, get_aws_namespace, DEFAULT_AWS_REGION


ALARM_PREFIX_LAMBDA_DURATION = 'LambdaDuration'


class BaseClient:
    def __init__(self, service_name):
        self.client = boto3.client(service_name, region_name=DEFAULT_AWS_REGION)
        self.logger = get_logger()
        self.aws_namespace = None

    def get_namespace(self):
        if self.aws_namespace is None:
            self.aws_namespace = get_aws_namespace()[1:-1]
        return self.aws_namespace
