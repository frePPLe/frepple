#
# Copyright (C) 2007-2016 by frePPLe bvba
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

from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _

from freppledb.common.commands import PlanTaskRegistry, PlanTask
from freppledb.common.models import Parameter


@PlanTaskRegistry.register
class LoadData(PlanTask):

  description = "Load static data"
  sequence = 100
  filter = None

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple
    from freppledb.execute.load import loadData
    loadData(database=database, filter=cls.filter).runStatic()


@PlanTaskRegistry.register
class LoadDynamicData(PlanTask):

  description = "Load dynamic data"
  sequence = 110
  filter = None

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple
    from freppledb.execute.load import loadData
    loadData(database=database, filter=cls.filter).runDynamic()
    frepple.printsize()


@PlanTaskRegistry.register
class SupplyPlanning(PlanTask):

  description = "Generate supply plan"
  sequence = 200
  label = ('supply', _("Generate supply plan"))

  @classmethod
  def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    if 'supply' in os.environ:
      return 1
    else:
      return -1

  @staticmethod
  def run(database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple
    # Auxiliary functions for debugging
    def debugResource(res, mode):
      # if res.name != 'my favorite resource': return
      print("=> Situation on resource", res.name)
      for j in res.loadplans:
        print("=>  ", j.quantity, j.onhand, j.startdate, j.enddate, j.operation.name, j.operationplan.quantity, j.setup)

    def debugDemand(dem, mode):
      if dem.name == 'my favorite demand':
        print("=> Starting to plan demand ", dem.name)
        solver.loglevel = 2
      else:
        solver.loglevel = 0

    # Create a solver where the plan type are defined by an environment variable
    try:
      plantype = int(os.environ['FREPPLE_PLANTYPE'])
    except:
      plantype = 1  # Default is a constrained plan
    try:
      constraint = int(os.environ['FREPPLE_CONSTRAINT'])
    except:
      constraint = 15  # Default is with all constraints enabled
    solver = frepple.solver_mrp(
      constraints=constraint,
      plantype=plantype,
      loglevel=int(Parameter.getValue('plan.loglevel', database, 0)),
      lazydelay=int(Parameter.getValue('lazydelay', database, '86400')),
      allowsplits=(Parameter.getValue('allowsplits', database, 'true').lower() == "true"),
      rotateresources=(Parameter.getValue('plan.rotateResources', database, 'true').lower() == "true"),
      plansafetystockfirst=(Parameter.getValue('plan.planSafetyStockFirst', database, 'false').lower() != "false"),
      iterationmax=int(Parameter.getValue('plan.iterationmax', database, '0'))
      #userexit_resource=debugResource,
      #userexit_demand=debugDemand
      )
    print("Plan type: ", plantype)
    print("Constraints: ", constraint)
    solver.solve()
    frepple.printsize()


@PlanTaskRegistry.register
class ExportStatic(PlanTask):

  description = "Export static data"
  sequence = 300

  @classmethod
  def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    # Task not active!
    return -1

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    from freppledb.execute.export_database_static import exportStaticModel
    exportStaticModel(database=database, source=None).run()


@PlanTaskRegistry.register
class ExportPlan(PlanTask):

  description = "Export plan"
  sequence = 400

  @classmethod
  def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    if 'supply' in os.environ:
      return 1
    else:
      return -1

  @staticmethod
  def run(database=DEFAULT_DB_ALIAS, **kwargs):
    from freppledb.execute.export_database_plan import export
    export(database=database).run()


@PlanTaskRegistry.register
class ExportPlanToFile(PlanTask):

  description = "Export plan to file"
  sequence = 500

  @staticmethod
  def getWeight(database=DEFAULT_DB_ALIAS, **kwargs):
    # Task not active!
    return -1

  @staticmethod
  def run(database=DEFAULT_DB_ALIAS, **kwargs):
    from freppledb.execute.export_file_plan import exportfrepple as export_plan_to_file
    export_plan_to_file()


@PlanTaskRegistry.register
class ExportPlanToXML(PlanTask):

  description = "Export plan to XML files"
  sequence = 600

  @staticmethod
  def getWeight(database=DEFAULT_DB_ALIAS, **kwargs):
    # Task not active!
    return -1

  @staticmethod
  def run(database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple
    frepple.saveXMLfile("output.1.xml","BASE")
    #frepple.saveXMLfile("output.2.xml","PLAN")
    #frepple.saveXMLfile("output.3.xml","PLANDETAIL")


@PlanTaskRegistry.register
class EraseModel(PlanTask):

  description = "Erase model"
  sequence = 600

  @staticmethod
  def getWeight(database=DEFAULT_DB_ALIAS, **kwargs):
    # Task not active!
    return -1

  @staticmethod
  def run(database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple
    frepple.erase(True)
    frepple.printsize()
