#
# Copyright (C) 2007-2017 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from datetime import datetime
import os
import logging

from django.conf import settings
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
        return -1 if Bucket.objects.all().using(database).exists() else 0.1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        from django.core import management

        management.call_command("createbuckets", database=database, task=-1)


@PlanTaskRegistry.register
class UpdateLastCurrentDate(PlanTask):
    description = "Updates last_currentdate parameter"
    sequence = 450

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return -1 if "loadplan" in os.environ or "noexport" in os.environ else 0.1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        try:
            p, created = Parameter.objects.using(database).get_or_create(
                pk="last_currentdate"
            )
            newval = frepple.settings.current.strftime("%Y-%m-%d %H:%M:%S")
            if p.value == newval:
                return
            p.value = newval
            if created:
                p.description = "This parameter is automatically populated. It stores the date of the last plan execution"
            p.save(using=database)
        except Exception:
            logger.warning("Failed to set last_currentdate parameter")


@PlanTaskRegistry.register
class MakePlanFeasible(PlanTask):
    description = "Initial plan problems"
    sequence = 199

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if "supply" in os.environ or (
            "nowebservice" not in os.environ
            and Parameter.getValue("plan.webservice", database, "true").lower()
            == "true"
        ):
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        # Determine log level
        loglevel = int(Parameter.getValue("plan.loglevel", database, 0))

        # Clear previous info messages
        if "supply" in os.environ:
            for oper in frepple.operations():
                for opplan in oper.operationplans:
                    if opplan.info:
                        opplan.info = ""

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
    label = (
        "supply",
        _("Generate supply plan"),
        _(
            "Compute finite material and finite capacity purchasing, inventory and resource plans."
        ),
    )

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
        print("=> Situation on resource %s" % res.name)
        for j in res.loadplans:
            print(
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
            print("=> Starting to plan demand %s" % dem.name)
            cls.solver.loglevel = 2
        else:
            cls.solver.loglevel = 0

    # Auxiliary functions for debugging
    # Rename to activate
    @classmethod
    def DISABLED_nextDemand(cls, cluster):
        # Build the list of demands to plan when accessed for the first time
        if not hasattr(cls, "demandlist"):
            import frepple

            cls.demandlist = {}
            for d in frepple.demands():
                if d.quantity > 0 and d.status in ("open", "quote"):
                    if d.cluster in cls.demandlist:
                        cls.demandlist[d.cluster].append(d)
                    else:
                        cls.demandlist[d.cluster] = [d]
            for cl in cls.demandlist:
                cls.demandlist[cl].sort(
                    key=lambda d: (d.priority, d.due, d.quantity, d.name)
                )
                for d in cls.demandlist[cl]:
                    print("sorted", cl, d.priority, d.due, d.quantity, d.name)

        # Pop a demand from the list on every call
        print("asked next demand for", cls.demandlist[cluster])
        if cls.demandlist.get(cluster, None):
            return cls.demandlist[cluster].pop(0)
        else:
            return None

    # Auxiliary functions for debugging
    # Rename to activate
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
        except Exception:
            plantype = 1  # Default is a constrained plan
        try:
            from freppledb.execute.management.commands.runplan import parseConstraints

            constraint = parseConstraints(os.environ["FREPPLE_CONSTRAINT"])
        except Exception:
            constraint = 4 + 16 + 32  # Default is with all constraints enabled
        cls.solver = frepple.solver_mrp(
            constraints=constraint,
            plantype=plantype,
            loglevel=loglevel,
            lazydelay=int(Parameter.getValue("lazydelay", database, "86400")),
            minimumdelay=int(Parameter.getValue("plan.minimumdelay", database, "3600")),
            rotateresources=(
                Parameter.getValue("plan.rotateResources", database, "true").lower()
                == "true"
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
            if hasattr(cls, "nextDemand"):
                cls.solver.userexit_nextdemand = cls.nextDemand
        logger.info("Plan type: %s" % plantype)
        constraint_str = []
        if constraint & 4:
            constraint_str.append("capa")
        if constraint & 16:
            constraint_str.append("mfg_lt")
        if constraint & 32:
            constraint_str.append("po_lt")
        if not constraint_str:
            constraint_str.append("-")
        logger.info("Constraints: %s" % ",".join(constraint_str))
        try:
            if loglevel <= 2 and not settings.DEBUG:
                # Solver output is limited to 300000 lines
                frepple.settings.loglimit = 300000
            cls.solver.solve()
        finally:
            frepple.settings.loglimit = 0
        frepple.printsize()


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


@PlanTaskRegistry.register
class ActivatePythonDebugger(PlanTask):
    description = "Activate Python debugger"
    sequence = 50

    @classmethod
    def getWeight(cls, **kwargs):
        try:
            import debugpy

            return 0.1 if "debugpy" in os.environ else -1
        except ImportError:
            return -1

    @classmethod
    def run(cls, **kwargs):
        import debugpy

        debugpy.configure()
        debugpy.listen(("0.0.0.0", 17999))
