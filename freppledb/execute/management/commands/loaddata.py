import datetime
import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import loaddata
from django.db import connections, transaction


class Command(loaddata.Command):

  def handle(self, *args, **options):
    super(Command, self).handle(*args, **options)
    
    # if the fixture doesn't contain the 'demo' word, let's not apply loaddata post-treatments
    if 'demo' not in (args[0]).lower():
      return
    
    # get the database object
    database = options['database']
    if database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % database )
    
    with transaction.atomic(using=database, savepoint=False):
      print('updating fixture to current date')
      
      
      cursor = connections[database].cursor()
      cursor.execute('''
        select to_timestamp(value,'YYYY-MM-DD hh24:mi:ss') from common_parameter where name = 'currentdate'
      ''')
      currentDate = cursor.fetchone()[0]
      now = datetime.datetime.now()
      offset = (now - currentDate).days
      
      #update currentdate to now
      cursor.execute('''
        update common_parameter set value = 'now' where name = 'currentdate'
      ''')
      
      #update demand due dates
      cursor.execute('''
        update demand set due = due + %s * interval '1 day'
      ''', (offset,))
      
      #update PO/DO/MO due dates
      cursor.execute('''
        update operationplan set startdate = startdate + %s * interval '1 day', enddate = enddate + %s * interval '1 day'
      ''', 2 * (offset,))
      
    #run the workflow
    print('Running workflow...')
    active_modules = 'supply'
    if 'invplan' in os.environ:
      active_modules = 'invplan, balancing, ' + active_modules
    if "fcst" in os.environ:
       active_modules = 'fcst, ' + active_modules
    
    call_command(
          'runplan',
          database=database,
          env=active_modules
          )