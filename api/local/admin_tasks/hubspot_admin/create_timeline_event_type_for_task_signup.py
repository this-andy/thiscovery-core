import thiscovery_lib.dynamodb_utilities as ddb
import thiscovery_lib.hubspot_utilities as hs
from thiscovery_lib.utilities import get_aws_namespace


def save_timeline_event_type_id(name: str, hubspot_id, correlation_id):
    table_id = get_aws_namespace() + name
    details = {
        'hubspot_id': str(hubspot_id),
        'name': str(name),
    }
    ddb.put_item('lookups', table_id, 'tle_type', details, {}, True, correlation_id)


def main():
    hs_client = hs.HubSpotClient()

    type_defn = {
        "name": hs.TASK_SIGNUP_TLE_TYPE_NAME,
        "objectType": "CONTACT",
        "headerTemplate": "{{signup_event_type}} for {{task_name}}",
        "detailTemplate": "Project: {{project_name}}  {{project_id}}\nTask type: {{task_type_name}}  {{task_type_id}}"
    }

    tle_type_id = hs_client.create_timeline_event_type(type_defn)

    properties = [
        {
            "name": "project_id",
            "label": "Project Id",
            "propertyType": "String"
        },
        {
            "name": "project_name",
            "label": "Project Name",
            "propertyType": "String"
        },
        {
            "name": "task_id",
            "label": "Task Id",
            "propertyType": "String"
        },
        {
            "name": "task_name",
            "label": "Task Name",
            "propertyType": "String"
        },
        {
            "name": "task_type_id",
            "label": "Task Type Id",
            "propertyType": "String"
        },
        {
            "name": "task_type_name",
            "label": "Task Type",
            "propertyType": "String"
        },
        {
            "name": "signup_event_type",
            "label": "Event Type",
            "propertyType": "String"
        },
    ]

    hs_client.create_timeline_event_type_properties(tle_type_id, properties)

    save_timeline_event_type_id(hs.TASK_SIGNUP_TLE_TYPE_NAME, tle_type_id, None)


if __name__ == '__main__':
    main()
