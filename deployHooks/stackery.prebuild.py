#!/usr/bin/env python3

#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/

import os
import re


BASE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')  # thiscovery-core/
template_file = os.path.join(BASE_FOLDER, '.stackery', 'template.yaml')
template_contents = str()

with open(template_file) as f:
    template_contents = f.read()


env_p = re.compile(r"EnvironmentTagName:"
                   r"\s+Default: (.+)"
                   r"\s+Description: Environment Name \(injected by Stackery at deployment time\)"
                   r"\s+Type: String")
env_m = env_p.search(template_contents)

try:
    env_name = env_m.group(1)
except AttributeError:
    print(f"Couldn't find any match of pattern {env_p} in file {template_file}")
    print(f"template_contents: {template_contents}")
    raise AttributeError

if env_name in ['prod', 'staging']:
    print(f'Deploying to {env_name}; {template_file} left untouched')
else:
    p_conc_config_p = re.compile(r"\s+ProvisionedConcurrencyConfig:"
                                 r"\s*ProvisionedConcurrentExecutions: \d+"
                                 r"\s+AutoPublishAlias: live"
                                 r"\s+DeploymentPreference:"
                                 r"\s+Type: AllAtOnce")

    template_contents_without_concurrency = re.sub(p_conc_config_p, "", template_contents)

    assert template_contents_without_concurrency != template_contents, "Failed to strip provisioned concurrency from template " \
                                                                       f"(or template does not define provisioned concurrency)\n" \
                                                                       f"template_contents: {template_contents}"
    with open(template_file, 'w') as f:
        f.write(template_contents_without_concurrency)
