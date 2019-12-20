import api.common.hubspot as hs


def create_timeline_event_type_for_task_signup():
    tle_type_manager = hs.TimelineEventTypeManager()

    type_defn = {
        "name": hs.TASK_SIGNUP_TLE_TYPE_NAME,
        "objectType": "CONTACT",
        "headerTemplate": "{{signup_event_type}} for {{task_name}}",
        "detailTemplate": "Project: {{project_name}}  {{project_id}}\nTask type: {{task_type_name}}  {{task_type_id}}"
    }

    tle_type_id = tle_type_manager.create_timeline_event_type(type_defn)

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

    tle_type_manager.create_timeline_event_type_properties(tle_type_id, properties)

    tle_type_manager.save_timeline_event_type_id(hs.TASK_SIGNUP_TLE_TYPE_NAME, tle_type_id, None)


if __name__ == '__main__':
    create_timeline_event_type_for_task_signup()