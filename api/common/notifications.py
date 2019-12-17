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

from enum import Enum
if 'api.endpoints' in __name__:
    from api.common.dynamodb_utilities import scan, update_item, delete_all, put_item
else:
    from .dynamodb_utilities import scan, update_item, delete_all, put_item


NOTIFICATION_TABLE_NAME = 'notifications'
MAX_RETRIES = 2


class NotificationType(Enum):
    USER_REGISTRATION = 'user-registration'
    TASK_SIGNUP = 'task-signup'
    USER_LOGIN = 'user-login'


class NotificationStatus(Enum):
    NEW = 'new'
    PROCESSED = 'processed'
    RETRYING = 'retrying'
    DLQ = 'dlq'


class NotificationAttributes(Enum):
    STATUS = 'processing_status'
    FAIL_COUNT = 'processing_fail_count'
    ERROR_MESSAGE = 'processing_error_message'
    TYPE = 'type'


def get_notifications(filter_attr_name: str = None, filter_attr_values=None, correlation_id=None):
    notifications = scan(NOTIFICATION_TABLE_NAME, filter_attr_name, filter_attr_values, correlation_id)
    return notifications


def delete_all_notifications():
    delete_all(NOTIFICATION_TABLE_NAME)


def create_notification(label: str):
    notification_item = {
        NotificationAttributes.STATUS.value: NotificationStatus.NEW.value,
        'label': label
    }
    return notification_item


def save_notification(key, task_type, task_signup, notification_item, correlation_id):
    put_item(NOTIFICATION_TABLE_NAME, key, task_type, task_signup, notification_item, False, correlation_id)


def get_fail_count(notification):
    if NotificationAttributes.FAIL_COUNT.value in notification:
        return int(notification[NotificationAttributes.FAIL_COUNT.value])
    else:
        return 0


def set_fail_count(notification, new_value):
    notification[NotificationAttributes.FAIL_COUNT.value] = new_value


def mark_notification_processed(notification, correlation_id):
    notification_id = notification['id']
    notification_updates = {
        NotificationAttributes.STATUS.value: NotificationStatus.PROCESSED.value
    }
    return update_item(NOTIFICATION_TABLE_NAME, notification_id, notification_updates, correlation_id)


def mark_notification_failure(notification, error_message, correlation_id):
    notification_id = notification['id']
    fail_count = get_fail_count(notification) + 1
    set_fail_count(notification, fail_count)
    if fail_count > MAX_RETRIES:
        status = NotificationStatus.DLQ.value
    else:
        status = NotificationStatus.RETRYING.value
    notification_updates = {
        NotificationAttributes.STATUS.value: status,
        NotificationAttributes.FAIL_COUNT.value: fail_count,
        NotificationAttributes.ERROR_MESSAGE.value: error_message
    }
    update_item(NOTIFICATION_TABLE_NAME, notification_id, notification_updates, correlation_id)
