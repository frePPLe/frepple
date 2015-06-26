#
# Copyright (C) 2007-2013 by frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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
  frepple.settings.logfile = os.path.join(settings.FREPPLE_LOGDIR, 'frepple.log')
else:
  frepple.settings.logfile = os.path.join(settings.FREPPLE_LOGDIR, 'frepple_%s.log' % db)

# Use the test database if we are running the test suite
if 'FREPPLE_TEST' in os.environ:
  settings.DATABASES[db]['NAME'] = settings.DATABASES[db]['TEST']['NAME']

# Welcome message
print("frePPLe on %s using %s database '%s' as '%s' on '%s:%s'" % (
  sys.platform,
  settings.DATABASES[db].get('ENGINE', ''),
  settings.DATABASES[db].get('NAME', ''),
  settings.DATABASES[db].get('USER', ''),
  settings.DATABASES[db].get('HOST', ''),
  settings.DATABASES[db].get('PORT', '')
  ))

print("\nStart exporting static model to the database at", datetime.now().strftime("%H:%M:%S"))
from freppledb.execute.export_database_static import exportStaticModel
exportStaticModel(database=db).run()

print("\nFinished loading XML data at", datetime.now().strftime("%H:%M:%S"))
