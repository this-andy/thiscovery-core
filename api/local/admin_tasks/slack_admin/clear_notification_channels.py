import subprocess

from api.local.secrets import SLACK_TOKEN


def delete_bot_messages_from_channels(channel_list):
    for channel in channel_list:
        subprocess.run(['slack-cleaner', '--token', SLACK_TOKEN, '--message', '--channel', channel, '--bot', '--perform', '--rate=1'], check=True)


if __name__ == "__main__":
    delete_bot_messages_from_channels(
        [
            'epsagon-afs25-test-dev',
            'stackery-deployments',
        ]
    )