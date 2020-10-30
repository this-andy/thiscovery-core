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
Creates and exports to S3 a snapshot of the staging RDS database.

WARNING: At the time of writing, it is not possible to import data back into RDS (restore the db) from snapshots created by this script
"""
from datetime import datetime
from time import sleep

from api.local.secrets import THISCOVERY_STAGING_PROFILE, THISCOVERY_STAGING_DELETION_AND_REBUILD
from api.endpoints.common.rds_utilities import RdsClient


rds_client = RdsClient(profile_name=THISCOVERY_STAGING_PROFILE)


def create_new_db_snapshot():
    db_instances = rds_client.describe_db_instances()['DBInstances']
    assert len(db_instances) == 1, "Found more than 1 RDS instance in target AWS account"
    db_instance_id = db_instances[0]['DBInstanceIdentifier']
    snapshot_name = f"{db_instance_id}-{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
    snapshot_response = rds_client.create_db_snapshot(snapshot_name, db_instance_id)
    assert snapshot_response['ResponseMetadata']['HTTPStatusCode'] == 200, f"Error creating snapshot: {snapshot_response}"
    print(f"Successfully initialised creation of RDS snapshot {snapshot_name}")
    return snapshot_name


def check_db_snapshot_is_ready(snapshot_name):
    snapshots_response = rds_client.describe_db_snapshots(DBSnapshotIdentifier=snapshot_name)
    assert snapshots_response['ResponseMetadata']['HTTPStatusCode'] == 200, f"Error fetching snapshots: {snapshots_response}"
    snapshots = snapshots_response['DBSnapshots']
    assert len(snapshots) == 1, f"More than one snapshot matches name {snapshot_name}"
    snap = snapshots[0]
    snap_arn = snap['DBSnapshotArn']
    snap_status = snapshots[0]['Status']
    if snap_status == 'available':
        return snap_arn
    else:
        print(f"Snapshot is not ready yet (status is {snap_status}); trying again in 1 minute")
        sleep(60)
        return check_db_snapshot_is_ready(snapshot_name)


def start_db_dump_to_s3(snapshot_name):
    export_task_id = f"export-task-{snapshot_name}"
    snapshot_arn = check_db_snapshot_is_ready(snapshot_name)
    export_task_response = rds_client.start_export_task(
        export_task_id,
        snapshot_arn,
        THISCOVERY_STAGING_DELETION_AND_REBUILD['db_dumps_s3'],
        THISCOVERY_STAGING_DELETION_AND_REBUILD['rds2s3_export_role_arn'],
        THISCOVERY_STAGING_DELETION_AND_REBUILD['rds2s3_kms_key_id'],
        S3Prefix="rds"
    )
    assert export_task_response['ResponseMetadata']['HTTPStatusCode'] == 200, f"Error starting export task: {export_task_response}"
    export_task_id = export_task_response['ExportTaskIdentifier']
    return export_task_id


def monitor_progress_of_export_task(export_task_id):
    status = None
    while status != 'COMPLETE':
        response = rds_client.describe_export_tasks(ExportTaskIdentifier=export_task_id)
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200, f"Error monitoring export task: {response}"
        export_task_info = response['ExportTasks'][0]
        status = export_task_info['Status']
        print(f"Export task {export_task_id} status: {status})")
        sleep(60)
    print(f"Export task {export_task_id} completed successfully!")


def main(snapshot_name=None):
    """
    Args:
        snapshot_name: Name of the RDS snapshot to use; if None, a new snapshot will be created and used, but this will take a long time
    """
    if snapshot_name is None:
        snapshot_name = create_new_db_snapshot()
    export_task_id = start_db_dump_to_s3(snapshot_name)
    monitor_progress_of_export_task(export_task_id)


if __name__ == "__main__":
    main()
