import boto3

import api.local.secrets as secrets


def main(source_account_credentials, target_account_credentials, source_table_name, target_table_name=None):
    """
    Modified from https://stackoverflow.com/a/43612035
    Args:
        source_account_credentials:
        target_account_credentials:
        source_table_name:
        target_table_name:

    Returns:
    """
    if target_table_name is None:
        target_table_name = source_table_name

    dynamoclient = boto3.client('dynamodb', region_name='eu-west-1',
                                aws_access_key_id=source_account_credentials['aws_access_key_id'],
                                aws_secret_access_key=source_account_credentials['aws_secret_access_key'],
                                aws_session_token=source_account_credentials['aws_session_token'])

    dynamotargetclient = boto3.client('dynamodb', region_name='eu-west-1',
                                      aws_access_key_id=target_account_credentials['aws_access_key_id'],
                                      aws_secret_access_key=target_account_credentials['aws_secret_access_key'],
                                      aws_session_token=target_account_credentials['aws_session_token'])

    dynamopaginator = dynamoclient.get_paginator('scan')
    dynamoresponse = dynamopaginator.paginate(
        TableName=source_table_name,
        Select='ALL_ATTRIBUTES',
        ReturnConsumedCapacity='NONE',
        ConsistentRead=True
    )
    for page in dynamoresponse:
        for item in page['Items']:
            dynamotargetclient.put_item(
                TableName=target_table_name,
                Item=item
            )


if __name__ == "__main__":
    tables = ['lookups', 'notifications', 'tokens']
    source = secrets.PROD_ACCOUNT
    target = secrets.STAGING_ACCOUNT

    tables_fullnames = [f'thiscovery-core-staging-{x}' for x in tables]

    response = input(f"About to copy data in Dynamodb tables {', '.join(tables_fullnames)} from {source['account_name']} to {target['account_name']}. "
                     f"Proceed? [y/N]")

    if response.lower() == 'y':
        for table in tables_fullnames:
            main(
                source_account_credentials=source,
                target_account_credentials=target,
                source_table_name=table,
            )
    else:
        print('Script aborted; nothing was done')
