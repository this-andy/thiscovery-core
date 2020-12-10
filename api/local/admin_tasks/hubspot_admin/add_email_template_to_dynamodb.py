#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by th e Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#
"""
This script parses a transactional email template preview page and adds the template to Dynamodb table HubspotEmailTemplates
"""
import api.local.dev_config  # env variables
import api.local.secrets  # env variables
import re
import requests
import sys

from thiscovery_lib.dynamodb_utilities import Dynamodb
from api.local.secrets import TRANSACTIONAL_EMAILS_FROM_ADDRESS


def get_html(url):
    r = requests.get(url)
    return r.text


def extract_template_id_from_url(url):
    p = re.compile(r"content/(\d+)\?portalId=")
    m = p.search(url)
    return m.group(1)


def extract_custom_properties(string):
    p = re.compile(r"\{\{custom\.(\w+)\}\}")
    return p.findall(string)


def format_custom_properties(custom_properties_list):
    return [{"name": x, "required": False} for x in custom_properties_list]


def add_template_to_ddb(template_id, template_name, template_type, formatted_custom_properties, preview_url):
    ddb_client = Dynamodb()
    ddb_client.put_item(
        table_name="HubspotEmailTemplates",
        key=template_name,
        item_type=template_type,
        item_details={
            "preview_url": preview_url,
        },
        item={
              "bcc": [],
              "cc": [],
              "contact_properties": [],
              "custom_properties": formatted_custom_properties,
              "from": TRANSACTIONAL_EMAILS_FROM_ADDRESS,
              "hs_template_id": template_id,
        }
    )


def main():
    preview_url = input("Please enter the url of the template preview page:")
    # page_html = get_html(preview_url)
    input("Please paste the template text in file hubspot_email_template_text.txt, save it and press return to continue.")
    with open('hubspot_email_template_text.txt') as f:
        page_html = f.read()
    custom_properties = extract_custom_properties(page_html)
    template_id = extract_template_id_from_url(preview_url)
    if not template_id:
        sys.exit(f"No template id could be found in url {preview_url}")
    if not custom_properties:
        confirmation = input(f"No custom properties found in preview page. Are you sure you want to add this template to Dynamodb? (y/n)")
        if confirmation not in ['y', 'Y']:
            print('Import aborted')
            sys.exit(0)
    formatted_custom_properties = format_custom_properties(custom_properties_list=custom_properties)
    template_name = ""
    while not template_name:
        template_name = input("Please enter the new template name:")
    template_type = input("Please enter the type of the new template (or leave blank to use the default type 'transactional-email-template'):")
    if not template_type.strip():
        template_type = "transactional-email-template"
    add_template_to_ddb(
        template_id=template_id,
        template_name=template_name,
        template_type=template_type,
        formatted_custom_properties=formatted_custom_properties,
        preview_url=preview_url,
    )


if __name__ == "__main__":
    main()
