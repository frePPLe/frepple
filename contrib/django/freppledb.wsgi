# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

#
# These are the extra settings to add to your apache httpd.conf configuration
# file for deploying frePPLe as a django application.
# See the Django website https://docs.djangoproject.com/en/dev/howto/deployment/modwsgi/
# for more information.
#


# Assure frepple and django are found in the Python path.
import os, sys
sys.path.append('/home/frepple/workspace/frepple/contrib/django')

os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['FREPPLE_HOME'] = '/home/frepple/workspace/frepple/bin'
os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
