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

import os
import uuid
import logging
from pythonjsonlogger import jsonlogger
import json

if 'api.endpoints' in __name__:
    from .common.utilities import get_logger, DetailedValueError
    from .common.hubspot import post_new_user_to_crm
    from .common.dynamodb_utilities import read, delete
else:
    from common.utilities import get_logger, DetailedValueError
    from common.hubspot import post_new_user_to_crm
    from common.dynamodb_utilities import read, delete


def process_new_user_event ():

    new_users = read()
    for new_user_notification in new_users:
        details = new_user_notification['details']
        post_new_user_to_crm(details)
        notification_id = new_user_notification['id']
        delete(notification_id)
    pass


if __name__ == "__main__":

    process_new_user_event()