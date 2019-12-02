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
from http import HTTPStatus

import sys
import json
from datetime import datetime

if 'api.endpoints' in __name__:
    from .common.cloudwatch_utilities import get_thiscovery_log_groups, set_log_group_retention_policy
    from .common.utilities import get_logger
else:
    from common.cloudwatch_utilities import get_thiscovery_log_groups, set_log_group_retention_policy
    from common.utilities import get_logger


def set_new_log_groups_retention_policy(event, context):
    """
    Fetches all CloudWatch log groups and sets the default retention policy (30 days) only for those groups in which
    the parameter "retentionInDays" is not present (new groups).
    """
    logger = get_logger()
    log_groups = get_thiscovery_log_groups()
    response = {
        'updated_log_groups': [],
    }
    for lg in log_groups:
        if 'retentionInDays' not in lg.keys():
            log_group_name = lg['logGroupName']
            set_log_group_retention_policy(log_group_name)
            response['updated_log_groups'].append(log_group_name)

    return response
