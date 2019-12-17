#!/usr/bin/env python3

import json
import subprocess
import sys
import requests

from api.local.secrets import STACKERY_CREDENTIALS, SLACK_DEPLOYMENT_NOTIFIER_WEBHOOKS


def slack_message(environment, message="deploy_to_aws.py has just finished running!"):
    header = {
        'Content-Type': 'application/json'
    }
    payload = {
        "text": message
    }
    requests.post(SLACK_DEPLOYMENT_NOTIFIER_WEBHOOKS['stackery-deployments'], data=json.dumps(payload), headers=header)
    if 'afs25' in environment:
        requests.post(SLACK_DEPLOYMENT_NOTIFIER_WEBHOOKS['Andre'], data=json.dumps(payload), headers=header)


def stackery_deployment(environment, branch):
    try:
        subprocess.run(['stackery', 'deploy', '--stack-name=thiscovery-core', '--aws-profile=default',
                        f'--env-name={environment}', f'--git-ref={branch}'], check=True,
                       stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as err:
        print(err.stderr.decode('utf-8').strip())
        raise err


def stackery_login():
    try:
        subprocess.run(['stackery', 'login', '--email', STACKERY_CREDENTIALS['email'],
                        '--password', STACKERY_CREDENTIALS['password']],
                       check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as err:
        print(err.stderr.decode('utf-8').strip())
        raise err


def deploy(environment):
    branch = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, check=True,
                            text=True).stdout.strip()
    status = subprocess.run(['git', 'status'], capture_output=True, check=True, text=True).stdout.strip()
    if 'Your branch is ahead' in status:
        proceed = input('It looks like your local branch is ahead of remote. Continue anyway? [y/N]')
        if not proceed.lower() in ['y', 'yes']:
            sys.exit('Deployment aborted')

    try:
        stackery_deployment(environment, branch)
    except subprocess.CalledProcessError as err:
        if err.stderr.decode('utf-8').strip() == "Error: Failed to get settings: Attempting to access Stackery " \
                                                 "before logging in. Please run `stackery login` first.":
            stackery_login()
            stackery_deployment(environment, branch)
    slack_message(environment)


if __name__ == '__main__':
    deploy('dev-afs25')
    # deploy('test-afs25')

    # deploy('dev')
    # deploy('test')
