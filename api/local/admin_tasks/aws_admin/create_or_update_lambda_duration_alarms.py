from api.common.cloudwatch_utilities import CloudWatch, ALARM_PREFIX_LAMBDA_DURATION
from api.common.lambda_utilities import Lambda
from api.common.utilities import get_aws_namespace

cw_client = CloudWatch()
lambda_client = Lambda()
aws_namespace = get_aws_namespace()[1:-1]

# process alarms for all lambdas in current namespace
env_lambda_names = [x['FunctionName'] for x in lambda_client.list_functions() if aws_namespace in x['FunctionName']]
for n in env_lambda_names:
    kwargs = {'AlarmName': n}
    cw_client.create_or_update_lambda_duration_alarm(**kwargs)


# alter alarms requiring custom thresholds (specified in seconds)
custom_lambda_thresholds = [
    {'Lambda': 'UpdateCochraneProgress', 'Threshold': 5.5},
]

custom_alarms = [
    {
        'AlarmName': f"thiscovery-core-{aws_namespace}-{ALARM_PREFIX_LAMBDA_DURATION}-{x['Lambda']}",
        'Threshold': x['Threshold']
    } for x in custom_lambda_thresholds
]

for kwargs in custom_alarms:
    cw_client.create_or_update_lambda_duration_alarm(**kwargs)

