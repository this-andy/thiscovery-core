from pprint import pprint
from thiscovery_lib.hubspot_utilities import HubSpotClient, SingleSendClient


def setup_app(client_class):
    hs_client = client_class()
    pprint(hs_client.get_initial_token_from_hubspot())


if __name__ == '__main__':
    target_app = ''
    while target_app.lower() not in ['d', 'e']:
        target_app = input("What HubSpot app are you setting up?\nd = default (thiscovery)\ne = transactional emails (thiscovery emails)")
    if target_app == 'd':
        setup_app(HubSpotClient)
    elif target_app == 'e':
        setup_app(SingleSendClient)
