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
import json
from http import HTTPStatus

import common.hubspot as hs
import thiscovery_lib.utilities as utils
import notification_process as np
import user as u
from thiscovery_lib.dynamodb_utilities import Dynamodb
from common.notification_send import new_transactional_email_notification


class TransactionalEmail:
    templates_table = 'HubspotEmailTemplates'

    def __init__(self, email_dict, correlation_id=None):
        self.template_name = email_dict.get('template_name')
        self.to_recipient_id = email_dict.get('to_recipient_id')
        if None in [self.template_name, self.to_recipient_id]:
            raise utils.DetailedValueError('template_name and to_recipient_id must be present in email_dict',
                                           details={'email_dict': email_dict, 'correlation_id': correlation_id})

        self.email_dict = email_dict
        self.logger = utils.get_logger()
        self.correlation_id = str(correlation_id)
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
        if self.template is None:
            self._get_template_details()
        for p_type in ['contact_properties', 'custom_properties']:
            type_name = p_type.split("_")[0]
            required_p_names = list()
            optional_p_names = list()
            # check all required properties are present in body of call
            for p in self.template[p_type]:
                if p['required'] is True:
                    required_p_names.append(p['name'])
                else:
                    optional_p_names.append(p['name'])
            self.logger.debug(f'{type_name} properties in template', extra={'required_p_names': required_p_names, 'optional_p_names': optional_p_names})

            for p_name in required_p_names:
                try:
                    p_value = self.email_dict[p_type][p_name]
                except KeyError:
                    raise utils.DetailedValueError(f'Required {type_name} property {p_name} not found in call body',
                                                        details={
                                                            'email_dict': self.email_dict,
                                                            'correlation_id': self.correlation_id,
                                                        })
                if not p_value:
                    raise utils.DetailedValueError(f'Required {type_name} property {p_name} cannot be null',
                                                        details={
                                                            'email_dict': self.email_dict,
                                                            'correlation_id': self.correlation_id,
                                                        })

            # check all properties in body of call are specified in template
            properties_in_call = self.email_dict.get(p_type)
            if properties_in_call is not None:
                p_names_in_call = self.email_dict.get(p_type).keys()
                for p in p_names_in_call:
                    if p not in [*required_p_names, *optional_p_names]:
                        raise utils.DetailedIntegrityError(f'Call {type_name} property {p} is not specified in email template',
                                                           details={
                                                               'email_dict': self.email_dict,
                                                               f'template_required_{type_name}_properties': self.template[p_type],
                                                               'correlation_id': self.correlation_id,
                                                           })
        return True

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

    @staticmethod
    def _format_properties_to_name_value(properties_dict):
        if properties_dict:
            output_list = list()
            for k, v in properties_dict.items():
                output_list.append(
                    {
                        'name': k,
                        'value': v,
                    }
                )
            return output_list

    def send(self, mock_server=False):
        if mock_server:
            self.ss_client.mock_server = True
        self._get_template_details()
        self._validate_properties()
        user = self._get_user()
        if not user['crm_id']:
            raise utils.ObjectDoesNotExistError('Recipient does not have a HubSpot id',
                                                details={
                                                    'user': user,
                                                    'correlation_id': self.correlation_id,
                                                })
        return self.ss_client.send_email(
            template_id=self.template['hs_template_id'],
            message={
                'from': self.template['from'],
                'to': user['email'],
                'cc': self.template['cc'],
                'bcc': self.template['bcc'],
                'sendId': self.correlation_id,
            },
            contactProperties=self._format_properties_to_name_value(self.email_dict.get('contact_properties')),
            customProperties=self._format_properties_to_name_value(self.email_dict.get('custom_properties')),
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
    new_transactional_email_notification(email_dict, correlation_id)
    np.process_notifications(event, context)
    return {
        "statusCode": HTTPStatus.NO_CONTENT,
    }
