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
from api.pg_utilities import execute_non_query, execute_query


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

        sql = '''INSERT INTO public.projects_entityupdate (
                id,
                created,
                modified,
                entity_name,
                entity_id,
                json_patch,
                json_reverse_patch
            ) VALUES ( %s, %s, %s, %s, %s, %s, %s);'''

        rowcount = execute_non_query(sql, (id, self.modified, self.modified, self.entity_name, self.entity_id, self.json_patch.to_string(),
                                           self.reverse_json_patch.to_string()), self.correlation_id)

        return rowcount

    @staticmethod
    def get_entity_updates_for_entity(entity_name:str, entity_id:uuid, correlation_id):

        select_sql = '''
            SELECT
                id,
                created,
                modified,
                entity_name,
                entity_id,
                json_patch,
                json_reverse_patch
            FROM public.projects_entityupdate 
            WHERE entity_name = %s 
                AND entity_id = %s
            ORDER BY created
        '''

        return execute_query(select_sql, (entity_name, str(entity_id)), correlation_id)


if __name__ == "__main__":
    # user_json = {
    #     "id": "48e30e54-b4fc-4303-963f-2943dda2b139",
    #     "created": "2018-08-21T11:16:56+01:00",
    #     "email": "sw@email.addr",
    #     "title": "Mr",
    #     "first_name": "Steven",
    #     "last_name": "Walcorn",
    #     "auth0_id": "1234abcd",
    #     "status": "new"}
    # jp = [
    #     {'op': 'replace', 'path': '/first_name', 'value': 'zahra'},
    #     {'op': 'replace', 'path': '/last_name', 'value': 'hhyth'},
    #     {'op': 'replace', 'path': '/email', 'value': 'zahra@somewhere.com'}
    # ]
    # jp = JsonPatch(jp)
    # eu = EntityUpdate('user', user_json, jp, '1234abcd')
    # eu.save()
    # print(eu)

    result = EntityUpdate.get_entity_updates_for_entity('user', '48e30e54-b4fc-4303-963f-2943dda2b139', '1234567ab')
    print(result)