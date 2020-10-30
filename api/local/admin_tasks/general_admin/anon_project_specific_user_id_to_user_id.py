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
"""
This script converts anon_project_specific_user_ids into user_ids.
Input format: string of anon_project_specific_user_ids separated by commas (and optionally a space) (,)
Ouput format: prints to stdout a string containing user_ids separated by ;\n
"""
import api.local.dev_config  # sets env variables
import api.local.secrets  # sets env variables
import api.endpoints.common.pg_utilities as pg_utils
import api.endpoints.common.sql_queries as sql_q



if __name__ == '__main__':
    user_input = input("Please paste list of anon_project_specific_user_ids separated by commas:")
    anon_ids = user_input.split(',')
    anon_ids = [x.strip() for x in anon_ids]
    user_ids = list()
    for anon_project_specific_user_id in anon_ids:
        user_ids.append(pg_utils.execute_query(sql_q.GET_USER_BY_ANON_PROJECT_SPECIFIC_USER_ID_SQL, [str(anon_project_specific_user_id)])[0]['id'])
    print(';\n'.join(user_ids))
