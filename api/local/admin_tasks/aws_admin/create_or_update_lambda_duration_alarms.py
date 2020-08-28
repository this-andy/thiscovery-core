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
from api.common.cloudwatch_utilities import CloudWatch, ALARM_PREFIX_LAMBDA_DURATION
from api.common.lambda_utilities import Lambda
from thiscovery_lib.utilities import get_aws_namespace, get_logger


def main():
    created_or_updated_alarms = list()

    cw_client = CloudWatch()
    lambda_client = Lambda()
    aws_namespace = get_aws_namespace()[1:-1]
    logger = get_logger()

    # Lambdas requiring custom thresholds (specified in seconds)
    custom_thresholds = [
        {'Lambda': 'UpdateCochraneProgress', 'Threshold': 5.5},
    ]

    # process custom alarms for lambdas in current namespace
    custom_lambdas = list()
    for x in custom_thresholds:
        function_name = f"thiscovery-core-{aws_namespace}-{x['Lambda']}"
        custom_lambdas.append(function_name)
        alarm_name = f"thiscovery-core-{aws_namespace}-{ALARM_PREFIX_LAMBDA_DURATION}-{x['Lambda']}"
        custom_threshold = x['Threshold']
        logger.info(f'About to create or update CloudWatch alarm {alarm_name} with custom threshold {custom_threshold}')
        kwargs = {'AlarmName': alarm_name, 'Threshold': custom_threshold}
        cw_client.create_or_update_lambda_duration_alarm(function_name, **kwargs)

    # process default alarms for lambdas in current namespace
    env_lambda_names = [x['FunctionName'] for x in lambda_client.list_functions() if
                        (x['FunctionName'] not in custom_lambdas) and (aws_namespace in x['FunctionName'])]
    for n in env_lambda_names:
        alarm_name = n.replace(f'{aws_namespace}-', f'{aws_namespace}-{ALARM_PREFIX_LAMBDA_DURATION}-')
        kwargs = {'AlarmName': alarm_name}
        logger.info(f'About to create or update CloudWatch alarm {alarm_name} with default settings')
        if cw_client.create_or_update_lambda_duration_alarm(function_name=n, **kwargs) == 200:
            created_or_updated_alarms.append(alarm_name)

    return created_or_updated_alarms


if __name__ == "__main__":
    print(f'Created or updated CloudWatch alarms: {main()}')
