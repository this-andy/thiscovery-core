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
"""
This script creates or updates CloudWatch alarms that monitor more than one resource and
that trigger an SNS notification if state is not OK
"""
import thiscovery_lib.utilities as utils
from api.common.cloudwatch_utilities import CloudWatch
from api.local.secrets import ACCOUNT_MAP


def get_db_instance_identifier():
    host = utils.get_secret('database-connection')['host']
    return host.split('.')[0]


env_name = utils.get_environment_name()
account_number = ACCOUNT_MAP.get(env_name)

base_template = {
    'ActionsEnabled': True,
    'AlarmActions': [f'arn:aws:sns:eu-west-1:{account_number}:AWS-Alerts'],
    'InsufficientDataActions': [],
    'OKActions': [],
}

api_template = {
    **base_template,
    'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
    'Dimensions': [{'Name': 'ApiName', 'Value': f'Core Thiscovery API Env {env_name}'},
                   {'Name': 'Stage', 'Value': f'{env_name}'}],
    'Namespace': 'AWS/ApiGateway',
    'TreatMissingData': 'notBreaching',
}

rds_template = {
    **base_template,
    'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': f'{get_db_instance_identifier()}'}],
    'Namespace': 'AWS/RDS',
}

general_alarms = {
    'API 5xx errors': {
        **api_template,
        'AlarmName': 'API 5xx errors',
        'DatapointsToAlarm': 1,
        'EvaluationPeriods': 5,
        'MetricName': '5XXError',
        'Period': 60,
        'Statistic': 'Sum',
        'Threshold': 1.0,
    },
    'API latency': {
        **api_template,
        'AlarmName': 'API latency',
        'DatapointsToAlarm': 4,
        'EvaluationPeriods': 5,
        'MetricName': 'Latency',
        'Period': 300,
        'Statistic': 'Average',
        'Threshold': 500.0,
    },
    'RDS CPU high': {
        **rds_template,
        'AlarmName': 'RDS CPU high',
        'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
        'DatapointsToAlarm': 4,
        'EvaluationPeriods': 5,
        'MetricName': 'CPUUtilization',
        'Period': 60,
        'Statistic': 'Average',
        'Threshold': 75.0,
        'TreatMissingData': 'notBreaching',
    },
    'RDS DB connections': {
        **rds_template,
        'AlarmName': 'RDS DB connections',
        'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
        'DatapointsToAlarm': 1,
        'EvaluationPeriods': 5,
        'MetricName': 'DatabaseConnections',
        'Period': 60,
        'Statistic': 'Maximum',
        'Threshold': 150.0,
        'TreatMissingData': 'missing'
    },
    'RDS storage low': {
        **rds_template,
        'AlarmName': 'RDS storage low',
        'ComparisonOperator': 'LessThanOrEqualToThreshold',
        'DatapointsToAlarm': 4,
        'EvaluationPeriods': 5,
        'MetricName': 'FreeStorageSpace',
        'Period': 300,
        'Statistic': 'Average',
        'Threshold': 1.0,
        'TreatMissingData': 'missing'
    },
    'notification processing errors': {
        **base_template,
        'AlarmName': 'notification processing errors',
        'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
        'DatapointsToAlarm': 1,
        'Dimensions': [{'Name': 'FunctionName',
                        'Value': f'thiscovery-core-{env_name}-processnotifications'}],
        'EvaluationPeriods': 5,
        'MetricName': 'Errors',
        'Namespace': 'AWS/Lambda',
        'Period': 60,
        'Statistic': 'Average',
        'Threshold': 1.0,
        'TreatMissingData': 'notBreaching'
    },
}


def main():
    created_or_updated_alarms = list()
    cw_client = CloudWatch()

    for alarm_name, alarm_definition in general_alarms.items():
        cw_client.logger.info(f'About to create or update CloudWatch alarm {alarm_name} on {env_name}')
        if cw_client.put_metric_alarm(**alarm_definition) == 200:
            created_or_updated_alarms.append(alarm_name)
    return created_or_updated_alarms


if __name__ == "__main__":
    print(f'Created or updated CloudWatch alarms in {env_name}: {main()}')
