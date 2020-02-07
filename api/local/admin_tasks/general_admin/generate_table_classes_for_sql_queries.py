import sys
PATH_TO_THISCOVERY_ADMIN = '/Users/afs25/GitHub/thiscovery_admin'
sys.path.append(PATH_TO_THISCOVERY_ADMIN)

import django
from django.conf import settings
from thiscovery_admin.settings import base
from django.conf.global_settings import *

settings.configure(default_settings=django.conf.global_settings, DEBUG=True)
django.setup()

from thiscovery_admin.projects import models

user = models.User()

