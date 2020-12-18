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

import uuid
from jsonpatch import JsonPatch

import common.pg_utilities as pg_utils
from common.pg_utilities import execute_non_query, execute_query
from common.sql_queries import SAVE_ENTITY_UPDATE_SQL, GET_ENTITY_UPDATES_FOR_ENTITY_SQL


class EntityUpdate:

    def __init__(self, entity_name, entity, json_patch: JsonPatch, modified, correlation_id):
        self.entity_name = entity_name
        self.entity_id = entity['id']
        self.json_patch = json_patch
        self.reverse_json_patch = self.create_reverse_jsonpatch(entity)
        self.modified = modified
        self.correlation_id = correlation_id


    def __str__(self):
        path_list = ''
        for patch in self.json_patch.patch:
            path_list += patch['path']
        return '{}:{} ({})'.format(self.entity_name, self.entity_id, path_list)


    def create_reverse_jsonpatch(self, original_entity):
        patched_entity = self.json_patch.apply(original_entity, False)
        return JsonPatch.from_diff(patched_entity, original_entity)


    def save(self):
        id = str(uuid.uuid4())
        rowcount = execute_non_query(SAVE_ENTITY_UPDATE_SQL, (id, self.modified, self.modified, self.entity_name, self.entity_id, self.json_patch.to_string(),
                                           self.reverse_json_patch.to_string()), self.correlation_id)
        return rowcount

    @staticmethod
    @pg_utils.db_connection_handler
    def get_entity_updates_for_entity(entity_name:str, entity_id:uuid, correlation_id):
        return execute_query(GET_ENTITY_UPDATES_FOR_ENTITY_SQL, (entity_name, str(entity_id)), correlation_id)
