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
import yaml


def extract_environment_name_from_template(template_contents_):
    """
    Args:
        template_contents_ (str): the full contents of template.yaml

    Returns:
        The environment name as a string

    """
    env_p = re.compile(r"EnvironmentTagName:"
                   r"\s+Default: (.+)"
                   r"\s+Description: Environment Name \(injected by Stackery at deployment time\)"
                   r"\s+Type: String")
    env_m = env_p.search(template_contents_)
    try:
        return env_m.group(1)
    except AttributeError:
        print(f"Couldn't find any match of pattern {env_p} in template file")
        print(f"template_contents: {template_contents_}")
        raise AttributeError


def strip_provisioned_concurrency_config(template_contents_):
    """
    Args:
        template_contents_ (str): the full contents of template.yaml

    Returns:
        template_contents_ with all settings related to provisioned concurrency removed

    """
    p_conc_config_p = re.compile(r"\s+ProvisionedConcurrencyConfig:"
                                 r"\s*ProvisionedConcurrentExecutions:"
                                 r"\s+Ref: EnvConfiglambdaprovisionedconcurrencyAsString")

    edited_template = re.sub(p_conc_config_p, "", template_contents_)
    assert "ProvisionedConcurrencyConfig" not in edited_template, "Failed to strip provisioned concurrency from template; " \
                                                                                        f"template_contents_: {template_contents_}"
    return edited_template


def remove_additional_subnets(template_contents_):
    """
    Args:
        template_contents_ (str): the full contents of template.yaml

    Returns:
        template_contents with only one private and one public subnet configured (all additional subnets removed)

    """
    template_as_dict = yaml.load(template_contents_, Loader=yaml.Loader)

    subnet_p = re.compile(
        r"(VirtualNetwork(?:Public|Private)Subnet(\d+)):"
    )

    # delete resources
    for name, number in subnet_p.findall(template_contents_):
        if not number == "1":
            for resource in ['', 'NatGateway', 'NatGatewayEIP', 'NatGatewayRoute', 'RouteTable', 'RouteTableAssociation']
                del template_as_dict['Resources'][f'{name}{resource}']
    edited_template = yaml.dump(template_as_dict)

    # delete references
    for name, number in subnet_p.findall(edited_template):
        if not number == "1":
            ref_p = re.compile(fr"\s+- Ref: {name}\n")
            edited_template = re.sub(ref_p, "", edited_template)

    assert "Subnet2" not in edited_template, "Failed to strip subnets from template; " \
                                             f"template_contents_: {template_contents_}"
    return edited_template


def main():
    """
    The main script routine
    """
    base_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')  # thiscovery-core/
    template_file = os.path.join(base_folder, '.stackery', 'template.yaml')
    template_contents = str()
    with open(template_file) as f:
        template_contents = f.read()
    env_name = extract_environment_name_from_template(template_contents)

    if env_name in ['prod', 'staging']:
        print(f'Deploying to {env_name}; {template_file} left untouched')
    else:
        edited_template = strip_provisioned_concurrency_config(template_contents)
        edited_template = remove_additional_subnets(edited_template)
        with open(template_file, 'w') as f:
            f.write(edited_template)
        print(f"Edited template:\n{edited_template}")


if __name__ == "__main__":
    main()
