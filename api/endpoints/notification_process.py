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

# import os
# import uuid
# import logging
# from pythonjsonlogger import jsonlogger
# import json

if 'api.endpoints' in __name__:
    from .common.utilities import get_logger, DetailedValueError
#     from .common.hubspot import post_new_user_to_crm, post_task_signup_to_crm
    from .common.dynamodb_utilities import scan
#     from .common.notification_send import TASK_SIGNUP_NOTIFICATION, USER_REGISTRATION_NOTIFICATION
#     from .user import patch_user
else:
    from common.utilities import get_logger, DetailedValueError
#     from common.hubspot import post_new_user_to_crm
    from common.dynamodb_utilities import scan
#     from common.notification_send import TASK_SIGNUP_NOTIFICATION, USER_REGISTRATION_NOTIFICATION
#     from user import patch_user
#
#
NOTIFICATION_TABLE_NAME = 'notifications'


def process_notifications(event, context):
    print ('hello from def process_notifications')

    logger = get_logger()
    logger.info('process_notifications')
    notifications = scan(NOTIFICATION_TABLE_NAME)
    # for notification in notifications:
    #     notification_type = notification['type']
    #     if notification_type == USER_REGISTRATION_NOTIFICATION:
    #         process_user_registration(notification)
    #     elif notification_type == TASK_SIGNUP_NOTIFICATION:
    #         process_task_signup(notification)


# def process_user_registration (notification):
#     notification_id = notification['id']
#     details = notification['details']
#     user_id = details['id']
#     hubspot_id, isNew = post_new_user_to_crm(details)
#
#     if hubspot_id == -1:
#         raise ValueError
#
#     user_jsonpatch = [
#         {'op': 'replace', 'path': '/crm_id', 'value': str(hubspot_id)},
#     ]
#
#     patch_user(user_id, user_jsonpatch)
#     # delete(notification_id)


# def process_task_signup(notification):
#     notification_id = notification['id']
#     details = notification['details']
#     # post_task_signup_to_crm(details)
#     # delete(notification_id)


if __name__ == "__main__":

    process_notifications(None, None)