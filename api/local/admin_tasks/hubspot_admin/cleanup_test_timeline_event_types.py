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
This script fetches all timeline event types associated with an environment and deletes all event types whose name == "Test timeline type"
"""
from api.endpoints.common.hubspot import HubSpotClient

if __name__ == "__main__":
    hs_client = HubSpotClient()
    ets = hs_client.list_timeline_event_types()
    for et in ets:
        if et['name'] == "Test timeline type":
            response = hs_client.delete_timeline_event_type(et['id'])
            assert response == 204, f"HubSpot API returned an unexpected response: {response}"
