#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

#  file     : $URL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$

import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _
from django.db import transaction, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.common.models import Parameter
from freppledb.execute.models import log


class Command(BaseCommand):
  option_list = BaseCommand.option_list + (
    make_option('--user', dest='user', type='string',
      help='User running the command'),
    make_option('--constraint', dest='constraint', type='choice',
      choices=['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15'], default='15',
      help='Constraints: 1=lead time, 2=capacity, 4=material, 8=release fence'),
    make_option('--plantype', dest='plantype', type='choice', choices=['1','2'],
      default='1', help='Plan type: 1=constrained, 2=unconstrained'),
    make_option('--nonfatal', action="store_true", dest='nonfatal',
      default=False, help='Dont abort the execution upon an error'),
    make_option('--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS, help='Nominates a specific database to load data from and export results into'),
  )
  help = "Runs frePPLe to generate a plan"

  requires_model_validation = False

  def handle(self, **options):
    # Pick up the options    
    if 'nonfatal' in options: nonfatal = options['nonfatal']
    else: nonfatal = False
    if 'user' in options: user = options['user'] or ''
    else: user = ''
    if 'constraint' in options:
      constraint = int(options['constraint'])
      if constraint < 0 or constraint > 15:
        raise ValueError("Invalid constraint: %s" % options['constraint'])
    else: constraint = 15
    if 'plantype' in options:
      plantype = int(options['plantype'])
      if plantype < 1 or plantype > 2:
        raise ValueError("Invalid plan type: %s" % options['plantype'])
    else: plantype = 1
    if 'database' in options: database = options['database'] or DEFAULT_DB_ALIAS
    else: database = DEFAULT_DB_ALIAS
    if not database in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % database )

    transaction.enter_transaction_management(managed=False, using=database)
    transaction.managed(False, using=database)
    try:
      # Check if already running
      param = Parameter.objects.using(database).get_or_create(name="Plan executing")[0]
      if param.value == 'True': raise Exception('Plan is already running')
      param.value = 'True'
      param.description = 'If this parameter exists, it indicates that the plan is currently being generated.'
      param.save(using=database)
      
      # Log message
      log(category='RUN', theuser=user,
        message=_('Start creating frePPLe plan of type %(plantype)d and constraints %(constraint)d') % {'plantype': plantype, 'constraint': constraint}).save(using=database)
      transaction.commit(using=database)

      # Execute
      os.environ['PLANTYPE'] = str(plantype)
      os.environ['CONSTRAINT'] = str(constraint)
      os.environ['FREPPLE_HOME'] = settings.FREPPLE_HOME.replace('\\','\\\\')
      os.environ['FREPPLE_APP'] = settings.FREPPLE_APP
      os.environ['FREPPLE_DATABASE'] = database
      os.environ['PATH'] = settings.FREPPLE_HOME + os.pathsep + os.environ['PATH'] + os.pathsep + settings.FREPPLE_APP
      os.environ['LD_LIBRARY_PATH'] = settings.FREPPLE_HOME
      if 'DJANGO_SETTINGS_MODULE' not in os.environ.keys():
        os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
      if os.path.exists(os.path.join(os.environ['FREPPLE_HOME'],'python27.zip')):
        # For the py2exe executable
        os.environ['PYTHONPATH'] = os.path.join(os.environ['FREPPLE_HOME'],'python27.zip') + os.pathsep + os.path.normpath(os.environ['FREPPLE_APP'])
      else:
        # Other executables
        os.environ['PYTHONPATH'] = os.path.normpath(os.environ['FREPPLE_APP'])
      ret = os.system('frepple "%s"' % os.path.join(settings.FREPPLE_APP,'freppledb','execute','commands.py').replace('\\','\\\\'))
      if ret: 
        Parameter.objects.using(database).filter(name="Plan executing").delete()
        raise Exception('Exit code of the batch run is %d' % ret)

      # Log message
      log(category='RUN', theuser=user,
        message=_('Finished creating frePPLe plan')).save(using=database)

      # Remove flag of running plan
      Parameter.objects.using(database).filter(name="Plan executing").delete()

    except Exception as e:
      try: log(category='RUN', theuser=user,
        message=u'%s: %s' % (_('Failure when creating frePPLe plan'),e)).save(using=database)
      except: pass
      if nonfatal: raise e
      else: raise CommandError(e)
    finally:
      transaction.commit(using=database)
      transaction.leave_transaction_management(using=database)
