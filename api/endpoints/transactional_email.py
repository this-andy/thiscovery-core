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
import user as u
from common.dynamodb_utilities import Dynamodb
from common.notifications import get_notifications, NotificationType, NotificationStatus, NotificationAttributes, mark_notification_processed, mark_notification_failure
from common.pg_utilities import execute_query
from common.sql_queries import SIGNUP_DETAILS_SELECT_SQL
from common.utilities import get_logger, new_correlation_id, now_with_tz, DetailedValueError


class TransactionalEmail:
    templates_table = 'HubspotEmailTemplates'

    def __init__(self, email_dict, correlation_id=None):
        self.template_name = email_dict.get('template_name')
        self.to_recipient_id = email_dict.get('to_recipient_id')
        if None in [self.template_name, self.to_recipient_id]:
            raise utils.DetailedValueError('template_name and to_recipient_id must be present in email_dict',
                                           details={'email_dict': email_dict, 'correlation_id': correlation_id})

        self.email_dict = email_dict
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb(correlation_id=correlation_id)
        self.ss_client = hs.SingleSendClient(correlation_id=correlation_id)
        self.template = None

    def _get_template_details(self):
        self.template = self.ddb_client.get_item(
            table_name=self.templates_table,
            key=self.template_name,
            correlation_id=self.correlation_id
        )
        if self.template is None:
            raise utils.ObjectDoesNotExistError('Template not found', details={
                'template_name': self.template_name
            })
        return self.template

    def _validate_properties(self):
        for p_type in ['contact_properties', 'custom_properties']:
            type_name = p_type.split("_")[0]
            required_p_names = list()
            optional_p_names = list()
            for p in self.template[p_type]:
                if p['required'] is True:
                    required_p_names.append(p['name'])
                else:
                    optional_p_names.append(p['name'])
            for p_name in required_p_names:
                try:
                    self.email_dict[p_type][p_name]
                except KeyError:
                    raise utils.ObjectDoesNotExistError(f'Required {type_name} property {p_name} not found in call body',
                                                        details={
                                                            'email_dict': self.email_dict,
                                                            'correlation_id': self.correlation_id,
                                                        })

            p_names_in_call = [x['name'] for x in self.email_dict[p_type]]
            for p in p_names_in_call:
                if p not in [*required_p_names, *optional_p_names]:
                    raise utils.DetailedIntegrityError(f'Call {type_name} property {p} is not specified in email template',
                                                       details={
                                                           'email_dict': self.email_dict,
                                                           f'template_required_{type_name}_properties': self.template[p_type],
                                                           'correlation_id': self.correlation_id,
                                                       })

    def _get_user(self):
        try:
            user = u.get_user_by_id(self.to_recipient_id, correlation_id=self.correlation_id)[0]
        except IndexError:
            try:
                user = u.get_user_by_anon_project_specific_user_id(self.to_recipient_id, correlation_id=self.correlation_id)[0]
            except IndexError:
                raise utils.ObjectDoesNotExistError('Recipient id does not match any known user_id or anon_project_specific_user_id',
                                                    details={
                                                        'to_recipient_id': self.to_recipient_id,
                                                        'correlation_id': self.correlation_id,
                                                    })
        return user

    def send(self):
        self._get_template_details()
        self._validate_properties()
        user = self._get_user()
        if not user['crm_id']:
            raise utils.ObjectDoesNotExistError('Recipient does not have a HubSpot id',
                                                details={
                                                    'user': user,
                                                    'correlation_id': self.correlation_id,
                                                })
        self.ss_client.send_email(
            template_id=self.template['hs_template_id'],
            message={
                'to': user['email'],
                'cc': self.template['cc'],
                'bcc': self.template['bcc'],
                'sendId': self.correlation_id,
            },
            contactProperties=self.email_dict.get('contact_properties'),
            customProperties=self.email_dict.get('custom_properties'),
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