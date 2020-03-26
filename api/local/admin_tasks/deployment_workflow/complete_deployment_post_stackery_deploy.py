from api.endpoints.log_groups import set_new_log_groups_retention_policy
from api.local.admin_tasks.aws_admin.create_or_update_lambda_duration_alarms import main as create_or_update_lambda_duration_alarms
from api.local.admin_tasks.aws_admin.create_or_update_general_alarms import main as create_or_update_general_alarms


def main():
    print(f'Created or updated general CloudWatch alarms: {create_or_update_general_alarms()}')
    print(f'Created or updated CloudWatch lambda duration alarms: {create_or_update_lambda_duration_alarms()}')
    print(f'Updated CloudWatch log groups: {set_new_log_groups_retention_policy(event=None, context=None)["updated_log_groups"]}')


if __name__ == "__main__":
    main()
