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

import api.endpoints.progress_process as prog_proc
import api.endpoints.project as p
import api.endpoints.user_task as ut
import common.pg_utilities as pg_utils
import common.sql_queries as sql_q
import testing_utilities as test_utils


class MyTestCase(test_utils.DbTestCase):
    def test_01_external_users_identity_length_matches_usertask_table(self):
        view_sql = "SELECT * FROM public.external_users_identity"
        table_sql = "SELECT * FROM public.projects_usertask"
        view_result, table_result = pg_utils.execute_query_multiple((view_sql, table_sql))
        self.assertEqual(len(view_result), len(table_result))







