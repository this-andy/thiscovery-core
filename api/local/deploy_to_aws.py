#!/usr/bin/env python3

import json
import subprocess
import sys
import requests

import api.common.utilities as utils
from api.local.secrets import STACKERY_CREDENTIALS, SLACK_DEPLOYMENT_NOTIFIER_WEBHOOKS


def slack_message(environment, branch, message=None):
    if not message:
        message = f"{branch} has just been deployed to {environment}."
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
    profile = utils.namespace2profile(utils.name2namespace(environment))
    try:
        subprocess.run(['stackery', 'deploy', '--stack-name=thiscovery-core', f'--aws-profile={profile}',
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


def get_git_branch():
    branch = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, check=True,
                            text=True).stdout.strip()
    status = subprocess.run(['git', 'status'], capture_output=True, check=True, text=True).stdout.strip()
    if ('Your branch is ahead' in status) or ('Changes not staged for commit' in status):
        while True:
            proceed = input('It looks like your local branch is out of sync with remote. Continue anyway? [y/N] (or "s" to show "git status")')
            if proceed.lower() == 's':
                print(status)
                print("--------------------------")
            elif proceed.lower() not in ['y', 'yes']:
                sys.exit('Deployment aborted')
            else:
                break
    return branch


def deployment_confirmation(environment, branch):
    proceed = input(f'About to deploy branch {branch} to {environment}. Continue? [y/N]')
    if not proceed.lower() in ['y', 'yes']:
        sys.exit('Deployment aborted')


def deploy(environment, branch=None):
    if branch is None:
        branch = get_git_branch()
    try:
        stackery_deployment(environment, branch)
    except subprocess.CalledProcessError as err:
        if err.stderr.decode('utf-8').strip() == "Error: Failed to get settings: Attempting to access Stackery " \
                                                 "before logging in. Please run `stackery login` first.":
            stackery_login()
            stackery_deployment(environment, branch)
        else:
            raise err


def main(environment):
    target_branch = get_git_branch()
    deployment_confirmation(environment, target_branch)
    deploy(environment, target_branch)
    slack_message(environment, target_branch)


if __name__ == '__main__':

    # target_environment = 'test-afs25'
    target_environment = 'dev-afs25'
    # target_environment = 'staging'

    main(environment=target_environment)

