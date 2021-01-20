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
import thiscovery_lib.utilities as utils
from http import HTTPStatus

from common.notification_send import notify_new_task_signup


@utils.lambda_wrapper
def record_new_task_signup(event, context):
    event_id = event['id']   # note that event id will be used as correlation id for subsequent processing
    new_user_task = event['detail']
    notify_new_task_signup(task_signup=new_user_task, correlation_id=event_id)
    return {"statusCode": HTTPStatus.OK, "body": json.dumps('')}
