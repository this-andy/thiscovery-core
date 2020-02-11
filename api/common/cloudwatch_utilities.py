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

from common.aws_common import BaseClient
from common.utilities import get_logger, get_aws_namespace


ALARM_PREFIX_LAMBDA_DURATION = 'LambdaDuration'


class CloudWatch(BaseClient):

    def __init__(self):
        super().__init__('cloudwatch')

    def get_alarms(self, prefix=None):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.describe_alarms
        """
        if prefix is None:
            prefix = f"thiscovery-core-{super().get_namespace()}"
        try:
            self.logger.info('Getting cloudwatch alarms', extra={'prefix': prefix})
            response = self.client.describe_alarms(
                AlarmNamePrefix=prefix,
            )
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f'call to boto3.client.describe_alarms failed with response: {response}'
            return response['MetricAlarms']
        except Exception as err:
            raise err

    def get_lambda_duration_alarms(self):
        return self.get_alarms(prefix=f"thiscovery-core-{super().get_namespace()}-{ALARM_PREFIX_LAMBDA_DURATION}")

    def create_or_update_lambda_duration_alarm(self, function_name, **kwargs):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_alarm

        Args:
            function_name (str): The name of the lambda function the alarm relates to (e.g. 'thiscovery-core-test-afs25-UpdateCochraneProgress')
            **kwargs: Parameters that will be passed to put_metric_alarm; MUST contain AlarmName; MAY contain Threshold

        Returns:
        """
        # set different defaults for production and staging
        actions_enabled_default = False
        alarm_actions_default = list()
        if ('thiscovery-core-prod' in kwargs['AlarmName']) or ('thiscovery-core-staging' in kwargs['AlarmName']):
            actions_enabled_default = True
            alarm_actions_default = ['arn:aws:sns:eu-west-1:595383251813:AWS-Alerts']

        # if parameters below not in kwargs, set default
        kwargs['Threshold'] = kwargs.get('Threshold', 1.5)
        kwargs['ActionsEnabled'] = kwargs.get('ActionsEnabled', actions_enabled_default)
        kwargs['AlarmActions'] = kwargs.get('AlarmActions', alarm_actions_default)

        try:
            response = self.client.put_metric_alarm(
                AlarmName=kwargs['AlarmName'],
                Dimensions=[{
                    'Name': 'FunctionName',
                    'Value': function_name,
                }],
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='Duration',
                Namespace='AWS/Lambda',
                Period=300,
                Statistic='Maximum',
                Threshold=kwargs['Threshold'],
                TreatMissingData='notBreaching',
                Unit='Seconds',
                ActionsEnabled=kwargs['ActionsEnabled'],
                AlarmActions=kwargs['AlarmActions'],
            )

            assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f'call to boto3.client.put_metric_alarm failed with response: {response}'
            return response['ResponseMetadata']['HTTPStatusCode']
        except Exception as err:
            raise err

    # def create_lambda_duration_alarm(self, environment):
    #     pass


class CloudWatchLogs(BaseClient):

    def __init__(self):
        super().__init__('logs')

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
