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


class RdsClient(utils.BaseClient):

    def __init__(self, profile_name=None):
        super().__init__('rds', profile_name=profile_name)

    def describe_db_instances(self, **kwargs):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html#RDS.Client.describe_db_instances
        """
        return self.client.describe_db_instances(**kwargs)

    def describe_db_snapshots(self, **kwargs):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html#RDS.Client.describe_db_snapshots
        """
        return self.client.describe_db_snapshots(**kwargs)

    def describe_export_tasks(self, **kwargs):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html#RDS.Client.describe_export_tasks
        """
        return self.client.describe_export_tasks(**kwargs)

    def create_db_snapshot(self, db_snapshot_identifier, db_instance_identifier, **kwargs):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html#RDS.Client.create_db_snapshot
        """
        return self.client.create_db_snapshot(
            DBSnapshotIdentifier=db_snapshot_identifier,
            DBInstanceIdentifier=db_instance_identifier,
            **kwargs
        )

    def start_export_task(self, export_task_identifier, source_arn, s3_bucket_name, iam_role_arn, kms_key_id, **kwargs):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html#RDS.Client.start_export_task
        """
        return self.client.start_export_task(
            ExportTaskIdentifier=export_task_identifier,
            SourceArn=source_arn,
            S3BucketName=s3_bucket_name,
            IamRoleArn=iam_role_arn,
            KmsKeyId=kms_key_id,
            **kwargs
        )
