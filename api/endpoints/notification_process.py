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
    from .common.utilities import get_logger, DetailedValueError, new_correlation_id, now_with_tz
    from .common.hubspot import post_new_user_to_crm, post_task_signup_to_crm, TASK_SIGNUP_TLE_TYPE_NAME
    from .common.pg_utilities import execute_query
    from .common.dynamodb_utilities import scan, update_item
    from .common.notification_send import NOTIFICATION_TABLE_NAME, TASK_SIGNUP_NOTIFICATION, USER_REGISTRATION_NOTIFICATION, NOTIFICATION_PROCESSED_FLAG
    from .user import patch_user
else:
    from common.utilities import get_logger, DetailedValueError, new_correlation_id, now_with_tz
    from common.hubspot import post_new_user_to_crm, post_task_signup_to_crm, TASK_SIGNUP_TLE_TYPE_NAME
    from common.pg_utilities import execute_query
    from common.dynamodb_utilities import scan, update_item
    from common.notification_send import NOTIFICATION_TABLE_NAME, TASK_SIGNUP_NOTIFICATION, USER_REGISTRATION_NOTIFICATION, NOTIFICATION_PROCESSED_FLAG
    from user import patch_user


def process_notifications(event, context):
    logger = get_logger()
    notifications = scan(NOTIFICATION_TABLE_NAME, NOTIFICATION_PROCESSED_FLAG, False)
    logger.info('process_notifications', extra = {'count': str(len(notifications))})

    # note that we need to process all registrations first, then do task signups (otherwise we might try to process a signup for someone not yet registered)
    signup_notifications = []
    for notification in notifications:
        notification_type = notification['type']
        if notification_type == USER_REGISTRATION_NOTIFICATION:
            process_user_registration(notification)
        elif notification_type == TASK_SIGNUP_NOTIFICATION:
            # add to list for later processing
            signup_notifications.append(notification)

    for signup_notification in signup_notifications:
        process_task_signup(signup_notification)


def process_user_registration (notification):
    try:
        logger = get_logger()
        correlation_id = new_correlation_id()
        notification_id = notification['id']
        details = notification['details']
        user_id = details['id']
        logger.info('process_user_registration: post to hubspot', \
                    extra={'notification_id': str(notification_id), 'user_id': str(user_id), 'email': details['email'], 'correlation_id': str(correlation_id)})
        hubspot_id, isNew = post_new_user_to_crm(details, correlation_id)
        logger.info('process_user_registration: hubspot details', \
                    extra={'notification_id': str(notification_id), 'hubspot_id': str(hubspot_id), 'isNew': str(isNew), 'correlation_id': str(correlation_id)})

        if hubspot_id == -1:
            raise ValueError

        user_jsonpatch = [
            {'op': 'replace', 'path': '/crm_id', 'value': str(hubspot_id)},
        ]

        patch_user(user_id, user_jsonpatch, now_with_tz(), correlation_id)

        mark_notification_processed(notification_id, correlation_id)
    except Exception as ex:
        raise ex


def mark_notification_processed(notification_id, correlation_id):
    update_item(NOTIFICATION_TABLE_NAME, notification_id, NOTIFICATION_PROCESSED_FLAG, True, correlation_id)


SIGNUP_DETAILS_SELECT_SQL = '''
  SELECT 
    p.id as project_id,
    p.name as project_name,
    pt.id as task_id,
    pt.description as task_name,
    tt.id as task_type_id,
    tt.name as task_type_name,
    u.crm_id
  FROM 
    public.projects_project p
    JOIN projects_projecttask pt on p.id = pt.project_id
    JOIN projects_tasktype tt on pt.task_type_id = tt.id
    JOIN projects_usertask ut on pt.id = ut.project_task_id
    JOIN projects_userproject up on ut.user_project_id = up.id
    JOIN projects_user u on up.user_id = u.id
  WHERE
    ut.id = %s
    '''


def get_task_signup_data_for_crm(user_task_id, correlation_id):
    extra_data = execute_query(SIGNUP_DETAILS_SELECT_SQL, (str(user_task_id),), correlation_id)
    if len(extra_data) == 1:
        return extra_data[0]
    else:
        raise Exception


def process_task_signup(notification):
    logger = get_logger()
    correlation_id = new_correlation_id()

    # get basic data out of notification
    notification_id = notification['id']
    signup_details = notification['details']
    user_task_id = signup_details['id']

    # get additional data that hubspot needs from database
    extra_data = get_task_signup_data_for_crm(user_task_id, correlation_id)

    # put it all together for dispatch to HubSpot
    signup_details.update(extra_data)
    signup_details['signup_event_type'] = 'Sign-up'

    post_task_signup_to_crm(signup_details, correlation_id)
    mark_notification_processed(notification_id, correlation_id)


def dateformattest(event, context):
    logger = get_logger()
    logger.info('dateformattest', extra=event)
    try:
        test_json = json.loads(event['body'])
        logger.info('body:', extra=test_json)
        date_string = test_json['date']
        date_string = date_string[:19] # strip timezone and milliseconds
        format_string = test_json['format']
        logger.info('dateformattest', extra={'date_string': date_string, 'format_string': format_string})
        datetime_obj = datetime.strptime(date_string, format_string)
        created_timestamp = int(datetime_obj.timestamp() * 1000)

        response = {"statusCode": 200, "body": json.dumps({"created_timestamp": str(created_timestamp)})}
        return response
    except:
        logger.error(sys.exc_info()[0])


if __name__ == "__main__":

    result = process_notifications(None, None)
    # notifications = scan(NOTIFICATION_TABLE_NAME, NOTIFICATION_PROCESSED_FLAG, False)
    # print(str(notifications))
    # notification_id = notifications[0]['id']
    # update_item(NOTIFICATION_TABLE_NAME, notification_id, NOTIFICATION_PROCESSED_FLAG, True)

    # date_json = {
    #     "date": "2019-05-16 15:20:51.264658+00:00",
    #     "format": "%Y-%m-%d %H:%M:%S.%f%z"
    # }
    # ev = {'body': json.dumps(date_json)}
    # print(dateformattest(ev, None))

    # details = {'id': '010d3058-d329-448a-b155-4e574e9e2e57'}
    # result = get_task_signup_data_for_crm(details)
    print(result)
