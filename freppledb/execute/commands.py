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
from django.utils.translation import gettext_lazy as _

from freppledb.common.commands import PlanTaskRegistry, PlanTask
from freppledb.common.models import Parameter, Bucket

logger = logging.getLogger(__name__)


@PlanTaskRegistry.register
class CheckBuckets(PlanTask):
    description = "Generation of time buckets"
    sequence = 3

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if Bucket.objects.all().using(database).exists():
            return -1
        else:
            return 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        from django.core import management

        management.call_command("createbuckets", database=database, task=-1)


@PlanTaskRegistry.register
class MakePlanFeasible(PlanTask):

    description = "Initial plan problems"
    sequence = 199

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        # Determine log level
        loglevel = int(Parameter.getValue("plan.loglevel", database, 0))

        # Propagate the operationplan status
        logger.info("Propagating work-in-progress status information")
        frepple.solver_propagateStatus(loglevel=loglevel).solve()

        # Update the feasibility flag of all operationplans
        for oper in frepple.operations():
            for opplan in oper.operationplans:
                opplan.updateFeasible()

        # Report the result
        print("Initial problems:")
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
    label = ("supply", _("Generate supply plan"))

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
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
            logger.debug(
                "=>  %s %s %s %s %s %s %s"
                % (
                    j.quantity,
                    j.onhand,
                    j.startdate,
                    j.enddate,
                    j.operation.name,
                    j.operationplan.quantity,
                    j.setup,
                )
            )

    # Auxiliary functions for debugging
    # Rename to activate
    @classmethod
    def DISABLED_debugDemand(cls, dem, mode):
        if dem.name == "my favorite demand":
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

        # Determine log level
        loglevel = int(Parameter.getValue("plan.loglevel", database, 0))

        # Create a solver where the plan type are defined by an environment variable
        try:
            plantype = int(os.environ["FREPPLE_PLANTYPE"])
        except:
            plantype = 1  # Default is a constrained plan
        try:
            constraint = int(os.environ["FREPPLE_CONSTRAINT"])
        except:
            constraint = 15  # Default is with all constraints enabled
        cls.solver = frepple.solver_mrp(
            constraints=constraint,
            plantype=plantype,
            loglevel=loglevel,
            lazydelay=int(Parameter.getValue("lazydelay", database, "86400")),
            allowsplits=(
                Parameter.getValue("allowsplits", database, "true").lower() == "true"
            ),
            minimumdelay=int(Parameter.getValue("plan.minimumdelay", database, "3600")),
            rotateresources=(
                Parameter.getValue("plan.rotateResources", database, "true").lower()
                == "true"
            ),
            plansafetystockfirst=(
                Parameter.getValue(
                    "plan.planSafetyStockFirst", database, "false"
                ).lower()
                != "false"
            ),
            iterationmax=int(Parameter.getValue("plan.iterationmax", database, "0")),
            resourceiterationmax=int(
                Parameter.getValue("plan.resourceiterationmax", database, "500")
            ),
            administrativeleadtime=86400
            * float(Parameter.getValue("plan.administrativeLeadtime", database, "0")),
            autofence=86400
            * float(Parameter.getValue("plan.autoFenceOperations", database, "0")),
        )
        if hasattr(cls, "debugResource"):
            cls.solver.userexit_resource = cls.debugResource
        if hasattr(cls, "debugDemand"):
            cls.solver.userexit_demand = cls.debugDemand
        if hasattr(cls, "debugOperation"):
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
class EraseModel(PlanTask):

    description = "Erase model"
    sequence = 700

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        # Task not active!
        return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        frepple.erase(True)
        frepple.printsize()
