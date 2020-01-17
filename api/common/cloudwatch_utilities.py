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

from common.utilities import get_logger, get_aws_namespace


class BaseClient:
    def __init__(self):
        self.logger = get_logger()


class CloudWatch(BaseClient):
    def __init__(self):
        super().__init__()
        self.client = boto3.client('cloudwatch')


class CloudWatchLogs(BaseClient):
    def __init__(self):
        super().__init__()
        self.client = boto3.client('logs')

    def get_thiscovery_log_groups(self, prefix=f"/aws/lambda/thiscovery-core-{get_aws_namespace()[1:-1]}"):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html#CloudWatchLogs.Client.describe_log_groups
        """
        try:
            self.logger.info('Getting log groups', extra={'prefix': prefix})
            response = self.client.describe_log_groups(
                logGroupNamePrefix=prefix,
                limit=50,
            )
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f'call to boto3.client.describe_log_groups failed with response: {response}'
            return response['logGroups']
        except Exception as err:
            raise err

    def set_log_group_retention_policy(self, log_group_name, retention_in_days=30):
        """
        Wrapper for boto3.client('logs').put_retention_policy(**kwargs) documented at
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html#CloudWatchLogs.Client.put_retention_policy

        Args:
            log_group_name (str): name of target log group
            retention_in_days: retention policy in days. Possible values are: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, and 3653.

        Returns:
        """
        try:
            self.logger.info('Setting log group retention policy', extra={'log_group_name': log_group_name, 'retention_in_days': retention_in_days})
            response = self.client.put_retention_policy(
                logGroupName=log_group_name,
                retentionInDays=retention_in_days
            )
            return response
        except Exception as err:
            raise err


if __name__ == "__main__":
    pass
    # response = get_thiscovery_log_groups()
    # print(response)
    # target_group_name = response[0]['logGroupName']
    # print(set_log_group_retention_policy(target_group_name))
