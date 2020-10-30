#!/usr/bin/env python3

import api.endpoints.common.dev_config  # set environment variables
import api.local.secrets  # set environment variables
from thiscovery_dev_tools.deploy_to_aws import AwsDeployer


if __name__ == '__main__':
    deployer = AwsDeployer(stack_name='thiscovery-core')
    deployer.main()
