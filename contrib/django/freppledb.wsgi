# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

#
# These are the extra settings to add to your apache httpd.conf configuration
# file for deploying frePPLe as a django application.
# See the Django website http://www.djangoproject.com/documentation/modpython/
# for more information.
#

import os, sys

sys.path.append('/home/frepple/workspace/frepple/contrib/django')

os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['FREPPLE_HOME'] = '/home/frepple/workspace/frepple/bin'
os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
#os.environ['NUMBER_OF_PROCESSORS'] = '2'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
