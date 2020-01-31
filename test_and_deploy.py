import logging
import os
import subprocess
import sys
import time

import api.local.deploy_to_aws as d2aws
import api.common.utilities as utils

TARGET_ENV = 'test-afs25'
MAX_RETRIES = 1

logger = utils.get_logger()
logger.setLevel(logging.WARNING)

def run_all_tests(on_aws=False):
    if on_aws:
        os.environ['TEST_ON_AWS'] = 'true'
    else:
        os.environ['TEST_ON_AWS'] = 'false'

    retries = 0
    while True:
        try:
            subprocess.run(
                ['python', '-m', 'unittest', 'discover', '-b', '-c', '-f',
                 '-v',
                 '-s', './api/tests/test_scripts', '-t', './api/tests/test_scripts'],
                stdout=sys.stdout,
                stderr=sys.stderr,
                check=True,
            )
            logger.info('Tests passed!')
            break

        except subprocess.SubprocessError as err:
            if retries > MAX_RETRIES:
                raise err
            else:
                logger.error(f'Tests failed after {retries + 1} attempts. Trying again...')
                retries += 1


def main():
    target_branch = d2aws.get_git_branch()
    d2aws.deployment_confirmation(TARGET_ENV, target_branch)

    run_all_tests()
    d2aws.deploy(TARGET_ENV, target_branch)
    time.sleep(10)
    run_all_tests(on_aws=True)
    d2aws.slack_message(TARGET_ENV, target_branch, message=f':tada: Branch {target_branch} passed all tests locally and on AWS!')


if __name__ == "__main__":
    main()
