#
# Copyright (C) 2010 by Johan De Taeye
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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

#  file     : $URL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$

import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.template.loader import render_to_string

from execute.models import log
from input.models import Operation, Resource, Buffer, Load, Flow

#TODO handling of suboperations!!!

@transaction.commit_manually
class Command(BaseCommand):
  help = "Generates output in the DOT language to visualize the network"

  requires_model_validation = False

  @transaction.autocommit
  def handle(self, **options):
    try:
      print render_to_string(
        "input/path.gv", 
        { 'supplypath': {
            'buffers': Buffer.objects.all(),
            'operations': Operation.objects.all(),
            'resources': Resource.objects.all(),
            'flows': Flow.objects.all(),
            'loads': Load.objects.all(),
        }})
    except Exception, e:
      raise CommandError(e)
