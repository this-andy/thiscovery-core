import logging
import os
import sys
import time
import unittest
from copy import deepcopy

import api.local.deploy_to_aws as d2aws
import thiscovery_lib.utilities as utils


TARGET_ENV = 'test-afs25'
MAX_RETRIES = 5
MIN_EXPECTED_TESTS = 119

logger = utils.get_logger()
logger.setLevel(logging.WARNING)

test_modules = [
    'test_dynamodb',
    'test_entity_base',
    'test_hubspot',
    'test_misc',
    'test_notifications',
    'test_progress',
    'test_project',
    'test_project_status_for_user',
    'test_security',
    'test_user',
    'test_user_external_account',
    'test_user_group',
    'test_user_group_membership',
    'test_user_project',
    'test_user_task',
    'test_utilities',
]


total_number_of_tests_run = None


def _print_tracebacks(test_result_instance):
    """
    Args:
        test_result_instance: instance of unittest.TestResult (https://docs.python.org/3/library/unittest.html#unittest.TestResult)
    """
    def eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

    if test_result_instance.errors:
        eprint('----------------------\nTEST ERRORS:\n')
        for e in test_result_instance.errors:
            eprint(e[0])
            eprint(e[1])
    if test_result_instance.failures:
        eprint('----------------------\nTEST FAILURES:\n')
        for e in test_result_instance.failures:
            eprint(e[0])
            eprint(e[1])
        eprint('\n')


def run_and_retry(test_suite, on_aws=False, remaining_retries=MAX_RETRIES, failfast=False, _first_run=True):
    """
    Runs all tests in test_suite. If any fails, re-runs those remaining_retries times.

    Args:
        test_suite: instance of unittest.TestSuite (https://docs.python.org/3/library/unittest.html#unittest.TestSuite)
        on_aws: if True, runs test suite on AWS
        remaining_retries: number of attempts to run the test suite successfully
        failfast: option passed to unittest.TextTestRunner. If True, the runner raises an error as soon as a test fails
        _first_run: private variable set to False by this function after the first run

    Returns:
        Total number of tests run (i.e. number of tests discovered in test_suite
    """

    if on_aws:
        os.environ['TEST_ON_AWS'] = 'true'
    else:
        os.environ['TEST_ON_AWS'] = 'false'

    runner = unittest.TextTestRunner(
        sys.stdout,
        verbosity=2,
        failfast=failfast,
    )

    results = runner.run(test_suite)

    if _first_run:
        global total_number_of_tests_run
        total_number_of_tests_run = results.testsRun

    if results.wasSuccessful():
        assert total_number_of_tests_run >= MIN_EXPECTED_TESTS, \
            f'Passed {total_number_of_tests_run} rather than at least {MIN_EXPECTED_TESTS}. This probably means that some tests failed to load.'
        return total_number_of_tests_run
    else:
        if (results.failures or results.errors) and remaining_retries:
            failed_tests_names = [x[0].id() for x in results.failures]
            failed_tests_names += [x[0].id() for x in results.errors]
            new_suite = unittest.TestLoader().loadTestsFromNames(failed_tests_names)
            remaining_retries = remaining_retries - 1
            run_and_retry(new_suite, on_aws=on_aws, remaining_retries=remaining_retries, _first_run=False, failfast=failfast)
        else:
            _print_tracebacks(results)
            print('len(results.errors):', len(results.errors))
            print('len(results.failures):', len(results.failures))
            number_of_failed_tests = len(results.errors) + len(results.failures)
            raise utils.DetailedValueError(f'Ran {total_number_of_tests_run} tests; {number_of_failed_tests} failed (after '
                                           f'{MAX_RETRIES} attempts); {total_number_of_tests_run - number_of_failed_tests} passed.',
                                           details={'errors': results.errors, 'failures': results.failures})


def main():
    target_branch = d2aws.get_git_branch()
    d2aws.deployment_confirmation(TARGET_ENV, target_branch)
    suite = unittest.TestLoader().loadTestsFromNames(test_modules)
    aws_suite = deepcopy(suite)
    print(f'All tests passed locally: {run_and_retry(test_suite=suite)} ran')
    d2aws.deploy(TARGET_ENV, target_branch)
    time.sleep(10)
    print(f'All tests passed on AWS: {run_and_retry(test_suite=aws_suite, on_aws=True)} ran')
    d2aws.slack_message(TARGET_ENV, target_branch, message=f':tada: Branch {target_branch} passed all tests locally and on AWS!')


if __name__ == "__main__":
    main()
