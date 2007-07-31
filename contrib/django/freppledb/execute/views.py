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

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$
# email : jdetaeye@users.sourceforge.net


from django import template
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.management import load_data
from django.db.models.fields.related import ForeignKey, AutoField
from django.db import models, transaction
from django.views.generic.simple import direct_to_template
import os, os.path

from freppledb.execute.create import erase_model, create_model
from freppledb.execute.models import log


@staff_member_required
def main(request):
  '''
  This view implements the overview screen with all execution
  actions.
  '''
  return direct_to_template(request,  template='execute/execute.html',
        extra_context={'title': 'Execute', 'reset_crumbs': True} )


@staff_member_required
@never_cache
def rundb(request):
    '''
    Database execution button.
    '''
    # Decode form attributes
    try: action = request.POST['action']
    except KeyError: raise Http404

    # Execute appropriate action
    if action == 'erase':
      # Erase the database contents
      try:
        log(category='ERASE', message='Start erasing the database').save()
        erase_model()
        request.user.message_set.create(message='Erased the database')
        log(category='ERASE', message='Finished erasing the database').save()
      except Exception, e:
        request.user.message_set.create(message='Failure during database erasing:%s' % e)
        log(category='RUN', message='Failed erasing the database: %s' % e).save()

      # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
      return HttpResponseRedirect('/execute/execute.html')

    elif action == 'create':
      # Populate the database with a sample model
      # Validate the data
      try:
        clusters = int(request.POST['clusters'])
        demands = int(request.POST['demands'])
        levels = int(request.POST['levels'])
        resources = int(request.POST['resources'])
        utilization = int(request.POST['utilization'])
        if clusters>=100000 or demands>=10000 or levels>=100 or resources>=1000:
          raise ValueError("Invalid parameters")
        if clusters<=0 or demands<=0 or levels<=0 or utilization<1:
          raise ValueError("Invalid parameters")
      except KeyError:
        raise Http404
      except ValueError, e:
        request.user.message_set.create(message='Invalid input field')
      else:
        # Execute
        try:
          log(
            category = 'CREATE',
            message = 'Start creating sample model with parameters: %d %d %d %d %d' \
              % (clusters, demands, levels, resources, utilization)
            ).save()
          create_model(clusters, demands, levels, resources, utilization)
          request.user.message_set.create(message='Created sample model in the database')
          log(category='CREATE', message='Finished creating sample model').save()
        except Exception, e:
          request.user.message_set.create(message='Failure during sample model creation: %s' % e)
          log(category='CREATE', message='Failed creating sample model: %s' % e).save()

      # Show the main screen again
      # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
      return HttpResponseRedirect('/execute/')

    else:
      # No valid action found
      raise Http404


@staff_member_required
@never_cache
def runfrepple(request):
    '''
    FrePPLe execution button.
    '''
    # Decode form attributes
    try: action = request.POST['action']
    except KeyError: raise Http404
    try: type = request.POST['type']
    except: type = 7   # Default plan is fully constrained

    if action == 'run':
      # Run frepple
      try:
        log(category='RUN', message='Start running frepple').save()
        os.environ['PLAN_TYPE'] = type
        os.environ['FREPPLE_HOME'] = settings.FREPPLE_HOME.replace('\\','\\\\')
        os.environ['FREPPLE_APP'] = settings.FREPPLE_APP
        os.environ['PATH'] = settings.FREPPLE_HOME + os.pathsep + os.environ['PATH'] + os.pathsep + '.'
        os.environ['LD_LIBRARY_PATH'] = settings.FREPPLE_HOME
        os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
        if os.path.exists(os.path.join(os.environ['FREPPLE_APP'],'library.zip')):
          # For the py2exe executable
          os.environ['PYTHONPATH'] = os.path.join(os.environ['FREPPLE_APP'],'library.zip')
        else:
          # Other executables
          os.environ['PYTHONPATH'] = os.path.normpath(os.path.join(os.environ['FREPPLE_APP'],'..'))
        ret = os.system('frepple "%s"' % os.path.join(settings.FREPPLE_APP,'execute','commands.xml'))
        if ret: raise Exception('exit code of the batch run is %d' % ret)
        request.user.message_set.create(message='Successfully ran frepple')
        log(category='RUN', message='Finished running frepple').save()
      except Exception, e:
        request.user.message_set.create(message='Failure when running frepple: %s' % e)
        log(category='RUN', message='Failed running frepple: %s' % e).save()
      # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
      return HttpResponseRedirect('/execute/execute.html')

    else:
      # No valid action found
      raise Http404


@transaction.commit_manually
def parseUpload(data, entity):
    '''
    This method reads CSV data from a string (in memory) and creates or updates
    the database records.
    The data must follow the following format:
      - the first row contains a header, listing all field names
      - a first character # marks a comment line
      - empty rows are skipped
    '''
    import csv
    from django.db import models
    from django.db.models import get_model
    headers = []
    rownumber = 0
    warnings = []
    has_pk_field = False

    # Find model class
    entityclass = get_model("input",entity)
    if not entityclass: raise TypeError, 'Invalid entity type %s' % entity

    # Loop through the data records
    for row in csv.reader(data.splitlines()):
      rownumber += 1
      # The first line is read as a header line
      if rownumber == 1:
        for col in row:
          col = col.strip().strip('#').lower()
          ok = False
          for i in entityclass._meta.fields:
            if i.name == col:
              headers.append(i)
              ok = True
              break
          if ok == False: raise TypeError, 'Incorrect field %s' % col
          if col == entityclass._meta.pk.name: has_pk_field = True
        if not has_pk_field and notisinstance(entityclass._meta.pk, AutoField):
          # The primary key is not an auto-generated id and it is not mapped in the input...
          raise TypeError, 'Missing primary key field %s' % entityclass._meta.pk.name

      # Skip empty rows and comments rows
      elif len(row) == 0 or row[0].startswith('#'):
        continue

      # Process a data row
      else:
        cnt = 0
        d = {}
        try:
          for col in row:
            # More fields in data row than headers. Move on to the next row
            if cnt >= len(headers): break
            if isinstance(headers[cnt], ForeignKey):
              try: d[headers[cnt].name] = headers[cnt].rel.to.objects.get(pk=col)
              except Exception, e: warnings.append('row %d: %s' % (rownumber,e))
            else:
              d[headers[cnt].name] = col
            cnt += 1
          if has_pk_field:
            # A primary key is part of the input fields
            try:
              it = entityclass.objects.get(pk=d[entityclass._meta.pk.name])
              del d[entityclass._meta.pk.name]
              for x in d: it.__setattr__ (x,d[x])
            except:
              it = entityclass(**d)
          else:
            # The primary key is autogenerated
            it = entityclass(**d)
          it.save()
          transaction.commit()
        except Exception, e:
          warnings.append('row %d: %s' % (rownumber,e))
          transaction.rollback()

    # Report all failed records
    return warnings


@staff_member_required
def upload(request):
    """
    Upload function for bulk data in CSV format.
    """
    # Validate request method
    if request.method != 'POST':
        request.user.message_set.create(message='Only POST method allowed')
        # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
        return HttpResponseRedirect('/execute/execute.html')

    # Validate uploaded file is present
    if "csv_file" not in request.FILES:
        request.user.message_set.create(message='No file uploaded')
        return HttpResponseRedirect('/execute/execute.html')

    # Validate entity type. It needs to be a valid model in the input application.
    try: entity = request.POST['entity']
    except: entity = None
    if not entity:
        request.user.message_set.create(message='Missing entity type')
        return HttpResponseRedirect('/execute/execute.html')

    # Parse the uploaded file
    try:
        log(
          category='LOAD',
          message='Start loading %s data file "%s"' % (entity, request.FILES['csv_file']['filename'])
          ).save()
        warnings = parseUpload(request.FILES['csv_file']['content'], entity)
        if len(warnings) > 0:
          request.user.message_set.create(message='Uploaded file processed with warnings')
          for i in warnings: request.user.message_set.create(message=i)
        else:
          request.user.message_set.create(message='Uploaded file processed')
        log(
          category='LOAD',
          message='Finished loading %s data file "%s"' % (entity, request.FILES['csv_file']['filename'])
          ).save()
        return HttpResponseRedirect('/execute/execute.html')
    except TypeError, e:
        request.user.message_set.create(message='Error while parsing %s' % e)
        log(
          category='LOAD',
          message='Failed loading %s data file "%s": %s' % (entity, request.FILES['csv_file']['filename'], e)
          ).save()
        return HttpResponseRedirect('/execute/execute.html')


@staff_member_required
def fixture(request):
    """
    Load a dataset stored in a django fixture file.
    """

    # Validate the request
    if request.method != 'POST':
      request.user.message_set.create(message='Only POST method allowed')
      # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
      return HttpResponseRedirect('/execute/execute.html')
    try:
      fixture = request.POST['datafile']
      if fixture == '-': raise
    except:
      request.user.message_set.create(message='Missing fixture attribute')
      return HttpResponseRedirect('/execute/execute.html')

    # Load the fixture
    # The fixture loading code is unfornately such that no exceptions are
    # or any error status returned when it fails...
    try:
        log(category='LOAD', message='Start loading fixture "%s"' % fixture).save()
        load_data([fixture], verbosity=1)
        request.user.message_set.create(message='Loaded fixture')
        log(category='LOAD', message='Finished loading fixture "%s"' % fixture).save()
        return HttpResponseRedirect('/execute/execute.html')
    except Exception, e:
        request.user.message_set.create(message='Error while loading fixture: %s' % e)
        log(category='LOAD', message='Failed loading fixture "%s": %s' % (fixture,e)).save()
        return HttpResponseRedirect('/execute/execute.html')
