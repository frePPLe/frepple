#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

#  file     : $URL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$

import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _
from django.db import transaction
from django.conf import settings

from execute.models import log
from input.models import Plan


class Command(BaseCommand):
  option_list = BaseCommand.option_list + (
    make_option('--user', dest='user', type='string',
      help='User running the command'),
    make_option('--type', dest='type', type='choice',
      choices=['0','1','2','3','4','5','6','7'],
      help='Plan type: 0=unconstrained, 7=fully constrained'),
  )
  help = "Runs frePPLe to generate a plan"

  requires_model_validation = False

  @transaction.autocommit
  def handle(self, **options):
    try:
      # Pick up the options
      user = options.get('user','')
      type = int(options.get('type','7') or '7')

      # Log message
      log(category='RUN', user=user,
        message=_('Start creating frePPLe plan of type ') + str(type)).save()

      # Execute
      os.environ['PLAN_TYPE'] = str(type)
      os.environ['FREPPLE_HOME'] = settings.FREPPLE_HOME.replace('\\','\\\\')
      os.environ['FREPPLE_APP'] = settings.FREPPLE_APP
      os.environ['PATH'] = settings.FREPPLE_HOME + os.pathsep + os.environ['PATH'] + os.pathsep + settings.FREPPLE_APP
      os.environ['LD_LIBRARY_PATH'] = settings.FREPPLE_HOME
      os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
      if os.path.exists(os.path.join(os.environ['FREPPLE_APP'],'library.zip')):
        # For the py2exe executable
        os.environ['PYTHONPATH'] = os.path.join(os.environ['FREPPLE_APP'],'library.zip')
      else:
        # Other executables
        os.environ['PYTHONPATH'] = os.path.normpath(os.path.join(os.environ['FREPPLE_APP'],'..'))
      ret = os.system('frepple "%s"' % os.path.join(settings.FREPPLE_APP,'execute','commands.xml'))
      if ret: raise Exception('Exit code of the batch run is %d' % ret)

      # Mark the last-modified field of the plan. This is used to force
      # browser clients to refresh any cached reports.
      Plan.objects.all()[0].save()

      # Log message
      log(category='RUN', user=user,
        message=_('Finished creating frePPLe plan')).save()
    except Exception, e:
      try: log(category='RUN', user=user,
        message=u'%s: %s' % (_('Failure when creating frePPLe plan'),e)).save()
      except: pass
      raise CommandError(e)
