import sys
PATH_TO_THISCOVERY_ADMIN = '/Users/afs25/GitHub/thiscovery_admin'
sys.path.append(PATH_TO_THISCOVERY_ADMIN)

import django
from django.conf import settings
from thiscovery_admin.settings import test

settings.configure(default_settings=test, DEBUG=True)
django.setup()

from thiscovery_admin.projects import models

user1 = models.User.objects.get(id='d1070e81-557e-40eb-a7ba-b951ddb7ebdc')
user1_projects = user1.user_project.all()
print(user1)
print(user1_projects)

user1_projects_in_one_query = models.User.objects.get(id='d1070e81-557e-40eb-a7ba-b951ddb7ebdc').user_project.all()
print('user1_projects_in_one_query:', user1_projects_in_one_query)

print('\nuser1_projects_in_one_query SQL:\n\t', user1_projects_in_one_query.query)

user = models.User()

