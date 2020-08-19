from api.common.hubspot import HubSpotClient, SingleSendClient


def renew_token(client_class):
    hs_client = client_class()
    hs_client.get_new_token_from_hubspot()
    print('New token:')
    print(hs_client.access_token)


if __name__ == '__main__':
    target_app = ''
    while target_app.lower() not in ['d', 'e']:
        target_app = input("What HubSpot app are you renewing the token for?\nd = default (thiscovery)\ne = transactional emails (thiscovery emails)")
    if target_app == 'd':
        renew_token(HubSpotClient)
    elif target_app == 'e':
        renew_token(SingleSendClient)
