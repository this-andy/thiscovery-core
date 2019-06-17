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

if __name__ == "__main__":
    from api.common.dynamodb_utilities import put_item
    from api.common.notifications import NotificationStatus, NotificationType, NOTIFICATION_TABLE_NAME, create_notification
else:
    from .dynamodb_utilities import put_item
    from .notifications import NotificationStatus, NotificationType, NOTIFICATION_TABLE_NAME, create_notification


def notify_new_user_registration(new_user, correlation_id):
    notification_item = create_notification(new_user['email'])
    key = new_user['id']
    put_item(NOTIFICATION_TABLE_NAME, key, NotificationType.USER_REGISTRATION.value, new_user, notification_item, correlation_id)


def notify_new_task_signup(task_signup, correlation_id):
    notification_item = create_notification(task_signup['user_id'])
    # use existing user_task id as notification id
    key = task_signup['id']
    put_item(NOTIFICATION_TABLE_NAME, key, NotificationType.TASK_SIGNUP.value, task_signup, notification_item, correlation_id)


if __name__ == "__main__":
    pass
    print(NotificationStatus.NEW.value)