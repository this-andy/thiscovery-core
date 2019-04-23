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
import boto3
from botocore.exceptions import ClientError

from api.common.hubspot import post_new_user_to_crm
from api.common.utilities import feature_flag

def notify_new_user_event (new_user):
    # this will eventually post new user to SQS queue

    # for now it just calls hubspot
    if feature_flag('hubspot-contacts'):
        post_new_user_to_crm(new_user)