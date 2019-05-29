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

from .utilities import feature_flag, get_logger, now_with_tz
from .dynamodb_utilities import put_item
import uuid

NOTIFICATION_TABLE_NAME = 'notifications'
USER_REGISTRATION_NOTIFICATION = 'user-registration'
TASK_SIGNUP_NOTIFICATION = 'task-signup'
NOTIFICATION_PROCESSED_FLAG = 'notification_processed'


# def sqs_send_DNU(message_body, message_attributes):
#     logger = get_logger()
#
#     logger.info('sqs_send: init')
#
#     sqs = boto3.client('sqs')
#
#     queue_url = 'https://sqs.eu-west-1.amazonaws.com/595383251813/thiscovery-core-dev-HubSpotEventQueue'
#
#     logger.info('sqs_send: about to send')
#
#     response = sqs.send_message(
#         QueueUrl=queue_url,
#         DelaySeconds=10,
#         MessageAttributes=message_attributes,
#         MessageBody=message_body
#     )
#
#     return response['MessageId']


def create_notification(label: str):
    notification_item = {
        NOTIFICATION_PROCESSED_FLAG: False,
        'label': label
    }
    return notification_item


def notify_new_user_registration(new_user, correlation_id):
    notification_item = create_notification(new_user['email'])
    key = new_user['id']
    put_item(NOTIFICATION_TABLE_NAME, key, USER_REGISTRATION_NOTIFICATION, new_user, notification_item, correlation_id)


def notify_new_task_signup(task_signup, correlation_id):
    notification_item = create_notification(task_signup['user_id'])
    # use existing user_task id as notification id
    key = task_signup['id']
    put_item(NOTIFICATION_TABLE_NAME, key, TASK_SIGNUP_NOTIFICATION, task_signup, notification_item, correlation_id)
