#!/usr/bin/env python3

import subprocess
import sys


def deploy(environment):
    branch = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, check=True, text=True).stdout.strip()
    status = subprocess.run(['git', 'status'], capture_output=True, check=True, text=True).stdout.strip()
    if 'Your branch is ahead' in status:
        proceed = input('It looks like your local branch is ahead of remote. Continue anyway? [y/N]')
        if not proceed.lower() in ['y', 'yes']:
            sys.exit('Deployment aborted')

    return subprocess.run(['stackery', 'deploy', '--stack-name=thiscovery-core', '--aws-profile default',
                           f'--env-name={environment}', f'--git-ref={branch}'], check=True)


if __name__ == '__main__':
    deployment = deploy('dev-afs25')
    # deployment = deploy('test-afs25')
    print(deployment)
