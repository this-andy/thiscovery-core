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
import uuid

if __name__ == "__main__":
    from api.common.notifications import NotificationStatus, NotificationType, save_notification, create_notification
else:
    from .notifications import NotificationStatus, NotificationType, save_notification, create_notification


def notify_new_user_registration(new_user, correlation_id):
    notification_item = create_notification(new_user['email'])
    key = new_user['id']
    save_notification(key, NotificationType.USER_REGISTRATION.value, new_user, notification_item, correlation_id)


def notify_new_task_signup(task_signup, correlation_id):
    notification_item = create_notification(task_signup['user_id'])
    # use existing user_task id as notification id
    key = task_signup['id']
    save_notification(key, NotificationType.TASK_SIGNUP.value, task_signup, notification_item, correlation_id)


def notify_user_login(login_info, correlation_id):
    assert 'login_datetime' in login_info.keys(), f"login_datetime not present in notification body ({login_info})"
    notification_item = create_notification(login_info['email'])
    key = str(uuid.uuid4())
    save_notification(key, NotificationType.USER_LOGIN.value, login_info, notification_item, correlation_id)


if __name__ == "__main__":
    pass
    print(NotificationStatus.NEW.value)