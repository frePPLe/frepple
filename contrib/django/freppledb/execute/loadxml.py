from __future__ import print_function
import os
import sys
from datetime import datetime

from django.db import DEFAULT_DB_ALIAS
from django.conf import settings

# Send the output to a logfile
try:
  db = os.environ['FREPPLE_DATABASE'] or DEFAULT_DB_ALIAS
except:
  db = DEFAULT_DB_ALIAS
if db == DEFAULT_DB_ALIAS:
  frepple.settings.logfile = os.path.join(settings.FREPPLE_LOGDIR,'frepple.log')
else:
  frepple.settings.logfile = os.path.join(settings.FREPPLE_LOGDIR,'frepple_%s.log' % db)

# Use the test database if we are running the test suite
if 'FREPPLE_TEST' in os.environ:
  settings.DATABASES[db]['NAME'] = settings.DATABASES[db]['TEST_NAME']
  if 'TEST_CHARSET' in os.environ:
    settings.DATABASES[db]['CHARSET'] = settings.DATABASES[db]['TEST_CHARSET']
  if 'TEST_COLLATION' in os.environ:
    settings.DATABASES[db]['COLLATION'] = settings.DATABASES[db]['TEST_COLLATION']
  if 'TEST_USER' in os.environ:
    settings.DATABASES[db]['USER'] = settings.DATABASES[db]['TEST_USER']

# Welcome message
if settings.DATABASES[db]['ENGINE'] == 'django.db.backends.sqlite3':
  print("frePPLe on %s using sqlite3 database '%s'" % (
    sys.platform,
    'NAME' in settings.DATABASES[db] and settings.DATABASES[db]['NAME'] or ''
    ))
else:
  print("frePPLe on %s using %s database '%s' as '%s' on '%s:%s'" % (
    sys.platform,
    'ENGINE' in settings.DATABASES[db] and settings.DATABASES[db]['ENGINE'] or '',
    'NAME' in settings.DATABASES[db] and settings.DATABASES[db]['NAME'] or '',
    'USER' in settings.DATABASES[db] and settings.DATABASES[db]['USER'] or '',
    'HOST' in settings.DATABASES[db] and settings.DATABASES[db]['HOST'] or '',
    'PORT' in settings.DATABASES[db] and settings.DATABASES[db]['PORT'] or ''
    ))

print("\nStart exporting static model to the database at", datetime.now().strftime("%H:%M:%S"))
from freppledb.execute.export_database_static import exportfrepple as export_static_to_database
export_static_to_database()

print("\nFinished loading XML data at", datetime.now().strftime("%H:%M:%S"))
