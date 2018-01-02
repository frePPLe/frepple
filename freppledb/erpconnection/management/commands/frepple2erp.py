#
# Copyright (C) 2017 by frePPLe bvba
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

from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections
from django.template import Template, RequestContext
from django.utils.translation import ugettext_lazy as _

from freppledb import VERSION
from freppledb.common.models import User
from freppledb.execute.models import Task

from ...utils import getERPconnection


class Command(BaseCommand):
  help = '''
  Update the ERP system with frePPLe planning information.
  '''
  # For the display in the execution screen
  title = _('Export data to %(erp)s') % {'erp': 'erp'}

  # For the display in the execution screen
  index = 1500

  requires_system_checks = False

  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      '--user', help='User running the command'
      )
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates the frePPLe database to load'
      )
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )


  @ staticmethod
  def getHTML(request):
    if 'freppledb.erpconnection' in settings.INSTALLED_APPS:
      context = RequestContext(request)

      template = Template('''
        {% load i18n %}
        <form role="form" method="post" action="{{request.prefix}}/execute/launch/erp2frepple/">{% csrf_token %}
        <table>
          <tr>
            <td style="vertical-align:top; padding: 15px">
               <button  class="btn btn-primary"  type="submit" value="{% trans "launch"|capfirst %}">{% trans "launch"|capfirst %}</button>
            </td>
            <td  style="padding: 0px 15px;">{% trans "Export erp data to frePPLe." %}
            </td>
          </tr>
        </table>
        </form>
      ''')
      return template.render(context)
    else:
      return None


  def handle(self, **options):
    '''
    Uploads approved operationplans to the ERP system.
    '''

    # Select the correct frePPLe scenario database
    self.database = options['database']
    if self.database not in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % self.database)
    self.cursor_frepple = connections[self.database].cursor()

    # FrePPle user running this task
    if options['user']:
      try:
        self.user = User.objects.all().using(self.database).get(username=options['user'])
      except:
        raise CommandError("User '%s' not found" % options['user'] )
    else:
      self.user = None

    # FrePPLe task identifier
    if options['task']:
      try:
        self.task = Task.objects.all().using(self.database).get(pk=options['task'])
      except:
        raise CommandError("Task identifier not found")
      if self.task.started or self.task.finished or self.task.status != "Waiting" or self.task.name != 'frepple2erp':
        raise CommandError("Invalid task identifier")
    else:
      now = datetime.now()
      self.task = Task(name='frepple2erp', submitted=now, started=now, status='0%', user=self.user)
    self.task.save(using=self.database)

    try:
      # Open database connection
      print("Connecting to the ERP database")
      with getERPconnection() as erp_connection:
        self.cursor_erp = erp_connection.cursor(self.database)
        try:
          self.extractPurchaseOrders()
          self.task.status = '33%'
          self.task.save(using=self.database)

          self.extractDistributionOrders()
          self.task.status = '66%'
          self.task.save(using=self.database)

          self.extractManufacturingOrders()
          self.task.status = '100%'
          self.task.save(using=self.database)
          
          # Optional extra planning output the ERP might be interested in:
          #  - planned delivery date of sales orders
          #  - safety stock (Enterprise Edition only)
          #  - reorder quantities (Enterprise Edition only)
          #  - forecast (Enterprise Edition only)
          self.task.status = 'Done'
        finally:
          self.cursor_erp.close()
    except Exception as e:
      self.task.status = 'Failed'
      self.task.message = 'Failed: %s' % e
    self.task.finished = datetime.now()
    self.task.save(using=self.database)
    self.cursor_frepple.close()


  def extractPurchaseOrders(self):
    '''
    Export purchase orders from frePPle.
    We export:
      - approved purchase orders.
      - proposed purchase orders that start within the next day and with a total cost less than 500$.
    '''
    print("Start exporting purchase orders")
    self.cursor_frepple.execute('''
      select
        item_id, location_id, supplier_id, quantity, startdate, enddate
      from operationplan
      inner join item on item_id = item.name
      where type = 'PO'
        and (
          status = 'approved'
          or (status = 'proposed' and quantity * cost < 500 and startdate < now() + interval '1 day')
          )
      order by supplier_id
      ''')
    output = [ i for i in self.cursor_frepple.fetchall()]
    self.cursor_erp.executemany('''
      insert into test
      (item, location, location2, quantity, startdate, enddate)
      values (?, ?, ?, ?, ?, ?)
      ''', output)


  def extractDistributionOrders(self):
    '''
    Export distribution orders from frePPle.
    We export:
      - approved distribution orders.
      - proposed distribution orders that start within the next day and with a total cost less than 500$.
    '''
    print("Start exporting distribution orders")
    self.cursor_frepple.execute('''
      select
        item_id, destination_id, origin_id, quantity, startdate, enddate
      from operationplan
      inner join item on item_id = item.name
      where type = 'DO'
        and (
          status = 'approved' 
          or (status = 'proposed' and quantity * cost < 500 and startdate < now() + interval '1 day')
          )
      order by origin_id, destination_id
      ''')
    output = [ i for i in self.cursor_frepple.fetchall()]
    self.cursor_erp.executemany('''
      insert into test
      (item, location, location2, quantity, startdate, enddate)
      values (?, ?, ?, ?, ?, ?)
      ''', output)


  def extractManufacturingOrders(self):
    '''
    Export manufacturing orders from frePPle.
    We export:
      - approved manufacturing orders.
      - proposed manufacturing orders that start within the next day.
    '''
    print("Start exporting manufacturing orders")
    self.cursor_frepple.execute('''
      select
        item_id, location_id, operation_id, quantity, startdate, enddate
      from operationplan
      where type = 'MO'
        and (
          status = 'approved'
          or (status = 'proposed' and startdate < now() + interval '1 day')
          )
      order by operation_id
      ''')
    output = [ i for i in self.cursor_frepple.fetchall()]
    self.cursor_erp.executemany('''
      insert into test
      (item, location, location2, quantity, startdate, enddate)
      values (?, ?, ?, ?, ?, ?)
      ''', output)
