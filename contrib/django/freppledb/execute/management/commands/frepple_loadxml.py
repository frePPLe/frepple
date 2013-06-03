#
# Copyright (C) 2011-2012 by Johan De Taeye, frePPLe bvba
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
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _
from django.db import transaction, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.execute.models import log
from freppledb import VERSION


class Command(BaseCommand):
  help = "Loads an XML file into the frePPLe database"
  option_list = BaseCommand.option_list + (
    make_option('--user', dest='user', type='string',
      help='User running the command'),
    make_option('--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS, help='Nominates a specific database to load data from and export results into'),
    make_option('--nonfatal', action="store_true", dest='nonfatal',
      default=False, help='Dont abort the execution upon an error'),
  )
  args = 'XMLfile(s)'
  
  requires_model_validation = False

  def get_version(self):
    return VERSION

  def handle(self, *args, **options):
    # Pick up the options
    if 'nonfatal' in options: nonfatal = options['nonfatal']
    else: nonfatal = False
    if 'user' in options: user = options['user'] or ''
    else: user = ''
    if 'database' in options: database = options['database'] or DEFAULT_DB_ALIAS
    else: database = DEFAULT_DB_ALIAS
    if not database in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % database )
    if not args: 
      raise CommandError("No XML input file given")

    transaction.enter_transaction_management(managed=False, using=database)
    transaction.managed(False, using=database)
    try:
      # Log message
      log(category='LOAD XML', theuser=user,
        message=_('Loading XML data file in the database')).save(using=database)
      transaction.commit(using=database)

      # Execute
      # TODO: if frePPLe is available as a module, we don't really need to spawn another process.
      os.environ['FREPPLE_HOME'] = settings.FREPPLE_HOME.replace('\\','\\\\')
      os.environ['FREPPLE_APP'] = settings.FREPPLE_APP
      os.environ['FREPPLE_DATABASE'] = database
      os.environ['PATH'] = settings.FREPPLE_HOME + os.pathsep + os.environ['PATH'] + os.pathsep + settings.FREPPLE_APP
      os.environ['LD_LIBRARY_PATH'] = settings.FREPPLE_HOME
      if 'DJANGO_SETTINGS_MODULE' not in os.environ.keys():
        os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
      if os.path.exists(os.path.join(os.environ['FREPPLE_HOME'],'python27.zip')):
        # For the py2exe executable
        os.environ['PYTHONPATH'] = os.path.join(os.environ['FREPPLE_HOME'],'python27.zip') + ';' + os.path.normpath(os.environ['FREPPLE_APP'])
      else:
        # Other executables
        os.environ['PYTHONPATH'] = os.path.normpath(os.environ['FREPPLE_APP'])
      cmdline = [ '"%s"' % i for i in args ]
      cmdline.insert(0, 'frepple')
      cmdline.append( '"%s"' % os.path.join(settings.FREPPLE_APP,'freppledb','execute','loadxml.py') ) 
      ret = os.system(' '.join(cmdline))
      if ret: raise Exception('Exit code of the batch run is %d' % ret)

      # Log message
      log(category='LOAD XML', theuser=user,
        message=_('Finished loading XML data file in the database')).save(using=database)
    except Exception as e:
      try: log(category='LOAD XML', theuser=user,
        message=u'%s: %s' % (_('Failure loading XML data file in the database'),e)).save(using=database)
      except: pass
      if nonfatal: raise e
      else: raise CommandError(e)
    finally:
      transaction.commit(using=database)
      transaction.leave_transaction_management(using=database)
