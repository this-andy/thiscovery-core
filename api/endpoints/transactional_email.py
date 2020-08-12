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
import sys
import json
from datetime import datetime, timedelta
from dateutil import parser, tz
from http import HTTPStatus

import common.hubspot as hs
import common.notifications as c_notif
import common.utilities as utils
from common.dynamodb_utilities import Dynamodb
from common.notifications import get_notifications, NotificationType, NotificationStatus, NotificationAttributes, mark_notification_processed, mark_notification_failure
from common.pg_utilities import execute_query
from common.sql_queries import SIGNUP_DETAILS_SELECT_SQL
from common.utilities import get_logger, new_correlation_id, now_with_tz, DetailedValueError
from user import patch_user


class TransactionalEmail:
    templates_table = 'HubspotEmailTemplates'

    def __init__(self, email_dict, correlation_id=None):
        self.template_name = email_dict.get('template_name')
        self.to_user_id = email_dict.get('to_user_id')
        if None in [self.template_name, self.to_user_id]:
            raise utils.DetailedValueError('template_name and to_user_id must be present in email_dict',
                                           details={'email_dict': email_dict, 'correlation_id': correlation_id})

        self.email_dict = email_dict
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb(correlation_id=correlation_id)
        self.ss_client = hs.SingleSendClient(correlation_id=correlation_id)

    def get_template_details(self):
        template = self.ddb_client.get_item(
            table_name=self.templates_table,
            key=self.template_name,
            correlation_id=self.correlation_id
        )
        try:
            return template
        except KeyError:
            raise utils.ObjectDoesNotExistError('Template not found', details={
                'template_name': self.template_name
            })

    def send(self):
        template = self.get_template_details()




        self.ss_client.send_email(

        )




@utils.lambda_wrapper
@utils.api_error_handler
def send_transactional_email_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    email_dict = json.loads(event['body'])
    logger.info('API call', extra={
        'email_dict': email_dict,
        'correlation_id': correlation_id,
        'event': event
    })
    email = TransactionalEmail(email_dict, correlation_id)
    email.send()
    return {
        "statusCode": HTTPStatus.OK,
    }