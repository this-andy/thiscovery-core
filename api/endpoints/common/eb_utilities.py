#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2021 THIS Institute
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
import boto3
import datetime
import epsagon
import json
import logging
import os
import uuid
from copy import deepcopy

import thiscovery_lib.utilities as utils
from common.entity_base import EntityBase

class EventbridgeClient(utils.BaseClient):

    def __init__(self, profile_name=None):
        super().__init__('events', profile_name=profile_name)

    def put_event(self, thiscovery_event, event_source='thiscovery', event_bus_name='thiscovery-event-bus'):
        """
        Args:
            thiscovery_event (ThiscoveryEvent): instance of ThiscoveryEvent
            event_source:
            event_bus_name:

        Returns:
        """
        event_json = thiscovery_event.to_json()
        entries = [
            {
                'Source': event_source,
                'Resources': [],
                'Time': thiscovery_event.event_time,
                'DetailType': thiscovery_event.detail_type,
                'Detail': thiscovery_event.detail,
                'EventBusName': event_bus_name
            }
        ]
        return self.client.put_events(Entries=entries)


class ThiscoveryEvent(EntityBase):
    def __init__(self, event):
        """

        Args:
            event (dict): must contain detail_type, user_id and detail (a json-serializable version of event details). It can optionally contain:
                            event_time (string in iso format) - if this is omitted creation time of entity will be used
                            id - uuid for event - if this is omitted it will be created
                            user_email - no action if this is omitted
                            further eventtype-specific details
        """
        # self.logger = utils.get_logger()

        if 'user_id' not in event or 'detail_type' not in event:
            # raise error
            raise utils.DetailedValueError('mandatory event data not provided','')

        # todo - validate type

        if 'id' in event:
            self.id = event['id']
        else:
            self.id = uuid.uuid4()

        if 'event_time' in event:
            self.event_time = event['event_time']
        else:
            self.event_time = utils.now_with_tz().isoformat()

        if 'user_email' in event:
            self.user_email = event['user_email']
        else:
            self.user_email = ''

        self.user_id = event['user_id']
        self.detail_type = event['detail_type']
        self.detail = json.dumps(event)

    def put_event(self):
        ebc = EventbridgeClient()
        return ebc.put_event(self)

