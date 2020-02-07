from jinja2 import Environment, PackageLoader, select_autoescape, Template


def where_equals(where_dict, value=None, indent=None):
    """
    Inspired by name_column function in https://medium.com/analytics-and-data/jinja-the-sql-way-of-the-ninja-9a64fc815564
    """
    return ',\n'.join([k + " = " + v for k, v in where_dict.items()])


env = Environment(
    loader=PackageLoader('common', 'sql_templates'),
)

env.filters['where_equals'] = where_equals

project_tasks_by_external_id = env.get_template('project_tasks_by_external_id.jinja2')

project_tasks_select_where = env.get_template('project_tasks_select_where.jinja2')


# project_tasks_by_project_id = Template(
# )
#
#
# project_tasks_by_external_id = Template(
#     """
#     {% extends project_tasks_select %}
#
#     {% block join_clause %}
#         JOIN projects_externalsystem es on pt.external_system_id = es.id
#     {% endblock %}
#
#     {% block where_clause %}
#         WHERE
#             external_task_id = (%s)
#     {% endblock %}
#     """
# )
#
#
# update_user_task = Template(
#     """
#
#     """
# )



