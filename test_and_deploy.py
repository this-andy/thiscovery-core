import os
import subprocess
import sys
import time

from api.local.deploy_to_aws import deploy


TARGET_ENV = 'test-afs25'


def run_all_tests(on_aws=False):
    if on_aws:
        os.environ['TEST_ON_AWS'] = 'true'
    else:
        os.environ['TEST_ON_AWS'] = 'false'

    subprocess.run(
        ['python', '-m', 'unittest', 'discover', '-s' './api/tests/test_scripts', '-t', './api/tests/test_scripts'],
        stdout=sys.stdout,
        stderr=sys.stderr,
        check=True,
    )


if __name__ == "__main__":
    run_all_tests()
    deploy()
    time.sleep(10)
    run_all_tests(on_aws=True)
