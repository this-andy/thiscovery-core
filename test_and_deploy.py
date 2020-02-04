import logging
import os
import subprocess
import sys
import time
import unittest

import api.local.deploy_to_aws as d2aws
import api.common.utilities as utils

TARGET_ENV = 'test-afs25'
MAX_RETRIES = 5

logger = utils.get_logger()
logger.setLevel(logging.WARNING)

test_modules = [
    # 'test_dynamodb',
    # 'test_entity_base',
    'test_hubspot',
    'test_misc',
    'test_notifications',
    'test_progress',
    'test_project',
    # 'test_project_status_for_user',
    # 'test_user',
    # 'test_user_external_account',
    # 'test_user_group',
    # 'test_user_group_membership',
    # 'test_user_project',
    # 'test_user_task',
    # 'test_utilities',
]


suite = unittest.TestLoader().loadTestsFromNames(test_modules)
runner = unittest.TextTestRunner(
    sys.stdout,
    verbosity=2,
    # failfast=True,
)


def run_and_retry(test_suite=suite, on_aws=False, remaining_retries=MAX_RETRIES):

    if on_aws:
        os.environ['TEST_ON_AWS'] = 'true'
    else:
        os.environ['TEST_ON_AWS'] = 'false'

    results = runner.run(test_suite)
    if results.wasSuccessful():
        return
    else:
        print('results.errors:', results.errors)
        print('results.failures:', results.failures)
        if (results.failures or results.errors) and remaining_retries:
            failed_tests_names = [x[0].id() for x in results.failures]
            failed_tests_names += [x[0].id() for x in results.errors]
            new_suite = unittest.TestLoader().loadTestsFromNames(failed_tests_names)
            remaining_retries = remaining_retries - 1
            run_and_retry(new_suite, remaining_retries=remaining_retries)
        else:
            raise utils.DetailedValueError(f'Tests failed after {MAX_RETRIES} attempts')


def main():
    target_branch = d2aws.get_git_branch()
    d2aws.deployment_confirmation(TARGET_ENV, target_branch)

    run_and_retry()
    d2aws.deploy(TARGET_ENV, target_branch)
    time.sleep(10)
    run_and_retry(on_aws=True)
    d2aws.slack_message(TARGET_ENV, target_branch, message=f':tada: Branch {target_branch} passed all tests locally and on AWS!')


if __name__ == "__main__":
    main()
