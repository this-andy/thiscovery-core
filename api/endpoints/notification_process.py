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

import http
import sys
import json
from datetime import datetime, timedelta
from dateutil import parser, tz

import thiscovery_lib.notifications as c_notif
import common.pg_utilities as pg_utils
import thiscovery_lib.utilities as utils
from thiscovery_lib.dynamodb_utilities import Dynamodb
from common.hubspot import HubSpotClient
from thiscovery_lib.notifications import get_notifications, NotificationType, NotificationStatus, NotificationAttributes, mark_notification_processed, mark_notification_failure
from common.pg_utilities import execute_query
from common.sql_queries import SIGNUP_DETAILS_SELECT_SQL
from thiscovery_lib.utilities import get_logger, new_correlation_id, now_with_tz, DetailedValueError
from user import patch_user


# region processing
def process_notifications(event, context):
    logger = get_logger()
    notifications = c_notif.get_notifications_to_process()
    # notifications = get_notifications(NotificationAttributes.STATUS.value, [NotificationStatus.NEW.value, NotificationStatus.RETRYING.value])
    logger.info('process_notifications', extra={'count': str(len(notifications))})

    # note that we need to process all registrations first, then do task signups (otherwise we might try to process a signup for someone not yet registered)
    signup_notifications = list()
    login_notifications = list()
    transactional_emails = list()
    for notification in notifications:
        notification_type = notification['type']
        if notification_type == NotificationType.USER_REGISTRATION.value:
            process_user_registration(notification)
        elif notification_type == NotificationType.TASK_SIGNUP.value:
            # add to list for later processing
            signup_notifications.append(notification)
        elif notification_type == NotificationType.USER_LOGIN.value:
            # add to list for later processing
            login_notifications.append(notification)
        elif notification_type == NotificationType.TRANSACTIONAL_EMAIL.value:
            transactional_emails.append(notification)
        else:
            error_message = f'Processing of {notification_type} notifications not implemented yet'
            logger.error(error_message)
            raise NotImplementedError(error_message)

    for signup_notification in signup_notifications:
        process_task_signup(signup_notification)

    for login_notification in login_notifications:
        process_user_login(login_notification)

    for email in transactional_emails:
        process_transactional_email(email)


def process_user_registration(notification):
    logger = get_logger()
    correlation_id = new_correlation_id()
    try:
        notification_id = notification['id']
        details = notification['details']
        user_id = details['id']
        logger.info('process_user_registration: post to hubspot',
                    extra={'notification_id': str(notification_id), 'user_id': str(user_id), 'email': details['email'], 'correlation_id': str(correlation_id)})
        hs_client = HubSpotClient(correlation_id=correlation_id)
        hubspot_id, is_new = hs_client.post_new_user_to_crm(details)
        logger.info('process_user_registration: hubspot details',
                    extra={'notification_id': str(notification_id), 'hubspot_id': str(hubspot_id), 'isNew': str(is_new), 'correlation_id': str(correlation_id)})

        if hubspot_id == -1:
            errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
            raise DetailedValueError('could not find user in HubSpot', errorjson)

        user_jsonpatch = [
            {'op': 'replace', 'path': '/crm_id', 'value': str(hubspot_id)},
        ]

        number_of_updated_rows_in_db = patch_user(user_id, user_jsonpatch, now_with_tz(), correlation_id)
        marking_result = mark_notification_processed(notification, correlation_id)
        return number_of_updated_rows_in_db, marking_result

    except Exception as ex:
        error_message = str(ex)
        mark_notification_failure(notification, error_message, correlation_id)


def get_task_signup_data_for_crm(user_task_id, correlation_id):
    extra_data = execute_query(SIGNUP_DETAILS_SELECT_SQL, (str(user_task_id),), correlation_id)
    pg_utils.close_connection()
    if len(extra_data) == 1:
        return extra_data[0]
    else:
        errorjson = {'user_task_id': user_task_id, 'correlation_id': str(correlation_id)}
        raise DetailedValueError('could not load details for user task', errorjson)


def process_task_signup(notification):
    logger = get_logger()
    correlation_id = new_correlation_id()
    logger.info('Processing task signup notification', extra={'notification': notification, 'correlation_id': correlation_id})
    posting_result = None
    marking_result = None
    try:
        # get basic data out of notification
        signup_details = notification['details']
        user_task_id = signup_details['id']

        # get additional data that hubspot needs from database
        extra_data = get_task_signup_data_for_crm(user_task_id, correlation_id)

        # put it all together for dispatch to HubSpot
        signup_details.update(extra_data)
        signup_details['signup_event_type'] = 'Sign-up'

        # check here that we have a hubspot id
        if signup_details['crm_id'] is None:
            errorjson = {'user_task_id': user_task_id, 'correlation_id': str(correlation_id)}
            raise DetailedValueError('user does not have crm_id', errorjson)
        else:
            hs_client = HubSpotClient(correlation_id=correlation_id)
            posting_result = hs_client.post_task_signup_to_crm(signup_details)
            logger.debug('Response from HubSpot API', extra={'posting_result': posting_result, 'correlation_id': correlation_id})
            if posting_result == http.HTTPStatus.NO_CONTENT:
                marking_result = mark_notification_processed(notification, correlation_id)
    except Exception as ex:
        error_message = str(ex)
        marking_result = mark_notification_failure(notification, error_message, correlation_id)
    finally:
        return posting_result, marking_result


def process_user_login(notification):
    logger = get_logger()
    correlation_id = new_correlation_id()
    logger.info('Processing user login notification', extra={'notification': notification, 'correlation_id': correlation_id})
    posting_result = None
    marking_result = None
    try:
        # get basic data out of notification
        login_details = notification['details']
        hs_client = HubSpotClient(correlation_id=correlation_id)
        posting_result = hs_client.post_user_login_to_crm(login_details)
        logger.debug('Response from HubSpot API', extra={'posting_result': posting_result, 'correlation_id': correlation_id})
        if posting_result == http.HTTPStatus.NO_CONTENT:
            marking_result = mark_notification_processed(notification, correlation_id)
    except Exception as ex:
        error_message = str(ex)
        marking_result = mark_notification_failure(notification, error_message, correlation_id)
    finally:
        return posting_result, marking_result


def process_transactional_email(notification, mock_server=False):
    logger = get_logger()
    correlation_id = new_correlation_id()
    logger.info('Processing transactional email', extra={'notification': notification, 'correlation_id': correlation_id})
    posting_result = None
    marking_result = None
    try:
        from transactional_email import TransactionalEmail
        email = TransactionalEmail(
            email_dict=notification['details'],
            send_id=notification['id'],
            correlation_id=correlation_id
        )
        posting_result = email.send(mock_server=mock_server)
        logger.debug('Response from HubSpot API', extra={'posting_result': posting_result, 'correlation_id': correlation_id})
        if posting_result.status_code == http.HTTPStatus.OK:
            marking_result = mark_notification_processed(notification, correlation_id)
    except Exception as ex:
        error_message = str(ex)
        marking_result = mark_notification_failure(notification, error_message, correlation_id)
    finally:
        return posting_result, marking_result
# endregion


# region cleanup
@utils.lambda_wrapper
def clear_notification_queue(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    seven_days_ago = now_with_tz() - timedelta(days=7)
    # processed_notifications = get_notifications('processing_status', ['processed'])
    processed_notifications = c_notif.get_notifications_to_clear(datetime_threshold=seven_days_ago)
    notifications_to_delete = [
        x for x in processed_notifications if 
        (parser.isoparse(x['modified']) < seven_days_ago) and 
        (x[NotificationAttributes.TYPE.value] != NotificationType.TRANSACTIONAL_EMAIL.value)
    ]
    deleted_notifications = list()
    ddb_client = Dynamodb()
    for n in notifications_to_delete:
        response = ddb_client.delete_item(c_notif.NOTIFICATION_TABLE_NAME, n['id'], correlation_id=correlation_id)
        if response['ResponseMetadata']['HTTPStatusCode'] == http.HTTPStatus.OK:
            deleted_notifications.append(n)
        else:
            logger.info(f'Notifications deleted before an error occurred', extra={'deleted_notifications': deleted_notifications,
                                                                                  'correlation_id': correlation_id})
            logger.error('Failed to delete notification', extra={'notification': n, 'response': response})
            raise Exception(f'Failed to delete notification {n}; received response: {response}')
    return deleted_notifications
# endregion
