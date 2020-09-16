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

from common.notifications import NotificationStatus, NotificationType, save_notification, create_notification


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


def new_transactional_email_notification(email_dict, correlation_id=None):
    try:
        user_label = email_dict['to_recipient_id']
    except KeyError:
        user_label = email_dict.get('to_recipient_email')
    notification_item = create_notification(f"{email_dict['template_name']}_{user_label}")
    key = str(uuid.uuid4())
    save_notification(key, NotificationType.TRANSACTIONAL_EMAIL.value, email_dict, notification_item, correlation_id)
