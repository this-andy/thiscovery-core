from api.common.hubspot import HubSpotClient

hs_client = HubSpotClient()
hs_client.get_new_token_from_hubspot()
print('New token:')
print(hs_client.access_token)
