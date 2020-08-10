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

import unittest
from http import HTTPStatus
from pprint import pprint

import api.common.qualtrics as qualtrics
from api.common.dev_config import QUALTRICS_TEST_OBJECTS
from api.common.utilities import set_running_unit_tests, now_with_tz, new_correlation_id


class TestDistributionsClient(unittest.TestCase):
    test_survey_id = QUALTRICS_TEST_OBJECTS['unittest-survey-1']['id']
    test_contact_list_id = QUALTRICS_TEST_OBJECTS['unittest-contact-list-1']['id']

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        cls.dist_client = qualtrics.DistributionsClient()
        # cls.created_distributions = list()

    @classmethod
    def tearDownClass(cls):
        # for dist in cls.created_distributions:
        #     cls.dist_client.delete_distribution(dist)
        set_running_unit_tests(False)

    def test_dist_01_create_retrieve_and_delete_individual_links_ok(self):
        r = self.dist_client.create_individual_links(survey_id=self.test_survey_id, contact_list_id=self.test_contact_list_id)
        self.assertEqual('200 - OK', r['meta']['httpStatus'])


        distribution_id = r['result']['id']
        # self.created_distributions.append(distribution_id)
        r = self.dist_client.list_distribution_links(distribution_id, self.test_survey_id)
        self.assertEqual('200 - OK', r['meta']['httpStatus'])
        rows = r['result']['elements']
        anon_ids = [x['externalDataReference'] for x in rows]
        expected_ids = [
            '1a03cb39-b669-44bb-a69e-98e6a521d758',
            '754d3468-f6f9-46ba-8e30-e29132b925b4',
            'd4714343-305d-40b7-adc1-1b50f5575983',
            '73527dd8-6067-448a-8cd7-481a970a6a13',
            '7e6e4bca-4f0b-4f71-8660-790c1baf3b11',
            '2dc6f2c8-84d9-4705-88e9-d95731c794c9',
            'bfecaf5e-52e5-4307-baa8-7e5208ca3451',
            '922d2b14-554f-42b5-bd20-d024b5ac7214',
            '1406c523-6d12-4510-a745-271ddd9ad3e2',
            '2c8bba57-58a9-4ac7-98e8-beb34f0692c1',
            '82ca200e-66d6-455d-95bc-617f974bcb26',
            'e132c198-06d3-4200-a6c0-cc3bc7991828',
            '87b8f9a8-2400-4259-a8d9-a2f0b16d9ea1',
            'a7a8e630-cb7e-4421-a9b2-b8bad0298267',
            '3b76f205-762d-4fad-a06f-60f93bfbc5a9',
            '64cdc867-e53d-40c9-adda-f0271bcf1063',
        ]
        self.assertCountEqual(expected_ids, anon_ids)


