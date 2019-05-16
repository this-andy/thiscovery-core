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
import sys
import json
from datetime import datetime

if 'api.endpoints' in __name__:
    from .common.utilities import get_logger, DetailedValueError
    from .common.hubspot import post_new_user_to_crm
    from .common.dynamodb_utilities import scan, update_item
    from .common.notification_send import NOTIFICATION_TABLE_NAME, TASK_SIGNUP_NOTIFICATION, USER_REGISTRATION_NOTIFICATION, NOTIFICATION_PROCESSED_FLAG
    from .user import patch_user
else:
    from common.utilities import get_logger, DetailedValueError
    from common.hubspot import post_new_user_to_crm
    from common.dynamodb_utilities import scan, update_item
    from common.notification_send import NOTIFICATION_TABLE_NAME, TASK_SIGNUP_NOTIFICATION, USER_REGISTRATION_NOTIFICATION, NOTIFICATION_PROCESSED_FLAG
    from user import patch_user


def process_notifications(event, context):
    print ('hello from def process_notifications')

    logger = get_logger()
    logger.info('process_notifications')
    notifications = scan(NOTIFICATION_TABLE_NAME)
    for notification in notifications:
        notification_type = notification['type']
        if notification_type == USER_REGISTRATION_NOTIFICATION:
            process_user_registration(notification)
        elif notification_type == TASK_SIGNUP_NOTIFICATION:
            process_task_signup(notification)


def process_user_registration (notification):
    logger = get_logger()
    notification_id = notification['id']
    details = notification['details']
    user_id = details['id']
    logger.info('process_user_registration', extra={'user_id': str(user_id)})
    hubspot_id, isNew = post_new_user_to_crm(details)
    logger.info('process_user_registration', extra={'hubspot_id': str(hubspot_id)})

    if hubspot_id == -1:
        raise ValueError

    user_jsonpatch = [
        {'op': 'replace', 'path': '/crm_id', 'value': str(hubspot_id)},
    ]

    patch_user(user_id, user_jsonpatch)

    update_item(NOTIFICATION_TABLE_NAME, notification_id, NOTIFICATION_PROCESSED_FLAG, True)


def process_task_signup(notification):
    notification_id = notification['id']
    details = notification['details']
    # post_task_signup_to_crm(details)
    # delete(notification_id)


def dateformattest(event, context):
    logger = get_logger()
    logger.info('dateformattest')
    # try:
    #     test_json = json.loads(event['body'])
    #     date_string = test_json['date']
    #     format_string = test_json['format']
    #     logger.info('dateformattest', extra={'date_string': date_string, 'format_string': format_string})
    #     datetime_obj = datetime.strptime(date_string, format_string)
    #     created_timestamp = int(datetime_obj.timestamp() * 1000)
    #     return created_timestamp
    # except:
    #     logger.error(sys.exc_info()[0])


if __name__ == "__main__":

    # process_notifications(None, None)
    # notifications = scan(NOTIFICATION_TABLE_NAME, NOTIFICATION_PROCESSED_FLAG, False)
    # print(str(notifications))
    # notification_id = notifications[0]['id']
    # update_item(NOTIFICATION_TABLE_NAME, notification_id, NOTIFICATION_PROCESSED_FLAG, True)

    date_json = {
        "date": "2019-05-16 15:20:51.264658+00:00",
        "format": "%Y-%m-%d %H:%M:%S.%f%z"
    }

    ev = {'body': json.dumps(date_json)}
    print(dateformattest(ev, None))
