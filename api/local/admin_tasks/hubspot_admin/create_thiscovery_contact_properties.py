from http import HTTPStatus
from thiscovery_lib.hubspot_utilities import HubSpotClient
from thiscovery_lib.utilities import DetailedValueError


class ContactPropertyAndGroupManager:
    hs_client = HubSpotClient()

    @classmethod
    def create_object(cls, url, object_definition):
        try:
            r = cls.hs_client.post(url, object_definition, None)
        except DetailedValueError as err:
            if err.details['result'].status_code == HTTPStatus.CONFLICT:
                return HTTPStatus.CONFLICT
            else:
                raise err
        return r.status_code

    @classmethod
    def create_group(cls, group_definition):
        url = '/properties/v1/contacts/groups'
        return cls.create_object(url, group_definition)

    @classmethod
    def create_contact_property(cls, property_definition):
        url = '/properties/v1/contacts/properties'
        return cls.create_object(url, property_definition)

    @classmethod
    def create_thiscovery_contact_properties(cls):
        group_definition = {
            "name": "thiscovery",
            "displayName": "Thiscovery"
        }
        status = cls.create_group(group_definition)
        message_base = "Group named '" + group_definition["name"] + "' "
        if status == HTTPStatus.CONFLICT:
            print(message_base + 'already exists - no action taken')
        else:
            print(message_base + 'created')

        property_definition = {
            "name": "thiscovery_id",
            "label": "Thiscovery ID",
            "description": "Contact's unique user ID in Thiscovery API",
            "groupName": "thiscovery",
            "type": "string",
            "fieldType": "text",
            "formField": False
        }
        status = cls.create_contact_property(property_definition)
        message_base = "Property named '" + property_definition["name"] + "' "
        if status == HTTPStatus.CONFLICT:
            print(message_base + 'already exists - no action taken')
        else:
            print(message_base + 'created')

        property_definition = {
            "name": "thiscovery_registered_date",
            "label": "Registered on Thiscovery date",
            "description": "The date on which a person first registered on Thiscovery.  Automatically set when someone registers.",
            "groupName": "thiscovery",
            "type": "datetime",
            "fieldType": "text",
            "formField": False
        }
        status = cls.create_contact_property(property_definition)
        message_base = "Property named '" + property_definition["name"] + "' "
        if status == HTTPStatus.CONFLICT:
            print(message_base + 'already exists - no action taken')
        else:
            print(message_base + 'created')

        property_definition = {
            "name": "thiscovery_last_login_date",
            "label": "Last login on Thiscovery date",
            "description": "The date on which a person last logged in to Thiscovery.",
            "groupName": "thiscovery",
            "type": "datetime",
            "fieldType": "text",
            "formField": False
        }
        status = cls.create_contact_property(property_definition)
        message_base = "Property named '" + property_definition["name"] + "' "
        if status == HTTPStatus.CONFLICT:
            print(message_base + 'already exists - no action taken')
        else:
            print(message_base + 'created')


if __name__ == "__main__":
    ContactPropertyAndGroupManager.create_thiscovery_contact_properties()
