#
# Copyright (C) 2007-2017 by frePPLe bvba
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
import os
import logging

from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _

from freppledb.common.commands import PlanTaskRegistry, PlanTask
from freppledb.common.models import Parameter

logger = logging.getLogger(__name__)


@PlanTaskRegistry.register
class MakePlanFeasible(PlanTask):

  description = "Initial plan problems"
  sequence = 199

  @classmethod
  def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    if 'supply' in os.environ:
      return 1
    else:
      return -1

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    # Update the feasibility flag of all operationplans
    for oper in frepple.operations():
      for opplan in oper.operationplans:
        opplan.updateFeasible()

    # Report the result
    print ("Initial problems:")
    probs = {}
    for i in frepple.problems():
      if i.name in probs:
        probs[i.name] += 1
      else:
        probs[i.name] = 1
    for i in sorted(probs.keys()):
      print("     %s: %s" % (i, probs[i]))


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

  # Auxiliary functions for debugging
  # Rename to activate
  @classmethod
  def DISABLED_debugResource(cls, res, mode):
    # if res.name != 'my favorite resource': return
    logger.debug("=> Situation on resource %s" % res.name)
    for j in res.loadplans:
      logger.debug("=>  %s %s %s %s %s %s %s" % (j.quantity, j.onhand, j.startdate, j.enddate, j.operation.name, j.operationplan.quantity, j.setup))

  # Auxiliary functions for debugging
  # Rename to activate
  @classmethod
  def DISABLED_debugDemand(cls, dem, mode):
    if dem.name == 'my favorite demand':
      logger.debug("=> Starting to plan demand %s" % dem.name)
      cls.solver.loglevel = 2
    else:
      cls.solver.loglevel = 0

  @classmethod
  def DISABLED_debugOperation(cls, oper, mode):
    return

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    # Create a solver where the plan type are defined by an environment variable
    try:
      plantype = int(os.environ['FREPPLE_PLANTYPE'])
    except:
      plantype = 1  # Default is a constrained plan
    try:
      constraint = int(os.environ['FREPPLE_CONSTRAINT'])
    except:
      constraint = 15  # Default is with all constraints enabled
    cls.solver = frepple.solver_mrp(
      constraints=constraint,
      plantype=plantype,
      loglevel=int(Parameter.getValue('plan.loglevel', database, 0)),
      lazydelay=int(Parameter.getValue('lazydelay', database, '86400')),
      allowsplits=(Parameter.getValue('allowsplits', database, 'true').lower() == "true"),
      minimumdelay=int(Parameter.getValue('plan.minimumdelay', database, '0')),
      rotateresources=(Parameter.getValue('plan.rotateResources', database, 'true').lower() == "true"),
      plansafetystockfirst=(Parameter.getValue('plan.planSafetyStockFirst', database, 'false').lower() != "false"),
      iterationmax=int(Parameter.getValue('plan.iterationmax', database, '0')),
      administrativeleadtime=86400 * float(Parameter.getValue('plan.administrativeLeadtime', database, '0')),
      autofence=86400 * float(Parameter.getValue("plan.autoFenceOperations", database, '0'))
      )
    if hasattr(cls, 'debugResource'):
      cls.solver.userexit_resource = cls.debugResource
    if hasattr(cls, 'debugDemand'):
      cls.solver.userexit_demand = cls.debugDemand
    if hasattr(cls, 'debugOperation'):
      cls.solver.userexit_operation = cls.debugOperation
    logger.info("Plan type: %s" % plantype)
    logger.info("Constraints: %s" % constraint)
    cls.solver.solve()
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
    frepple.saveXMLfile("output.1.xml", "BASE")
    # frepple.saveXMLfile("output.2.xml","PLAN")
    # frepple.saveXMLfile("output.3.xml","PLANDETAIL")


@PlanTaskRegistry.register
class EraseModel(PlanTask):

  description = "Erase model"
  sequence = 700

  @staticmethod
  def getWeight(database=DEFAULT_DB_ALIAS, **kwargs):
    # Task not active!
    return -1

  @staticmethod
  def run(database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple
    frepple.erase(True)
    frepple.printsize()
