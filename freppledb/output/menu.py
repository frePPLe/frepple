# Copyright (C) 2013 by frePPLe bvba
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

from freppledb.menu import menu
from freppledb.input.models import OperationPlanMaterial, OperationPlanResource
from freppledb.input.models import Demand, Operation, Resource, DistributionOrder, PurchaseOrder
from freppledb.input.models import ManufacturingOrder, ItemDistribution, ItemSupplier
import freppledb.output.views.buffer
import freppledb.output.views.demand
import freppledb.output.views.problem
import freppledb.output.views.constraint
import freppledb.output.views.resource
import freppledb.output.views.operation
import freppledb.output.views.kpi


# Adding reports. We use an index value to keep the same order of the entries in all languages.
menu.addItem(
  "sales", "demand report", url="/demand/",
  report=freppledb.output.views.demand.OverviewReport, index=200,
  dependencies=[Demand]
  )
menu.addItem(
  "sales", "problem report", url="/problem/?entity=demand",
  report=freppledb.output.views.problem.Report, index=400,
  dependencies=[Demand]
  )
menu.addItem(
  "sales", "constraint report", url="/constraint/",
  report=freppledb.output.views.constraint.BaseReport, index=500,
  dependencies=[Demand]
  )
menu.addItem(
  "admin", "kpi report", url="/kpi/",
  report=freppledb.output.views.kpi.Report, index=200
  )
menu.addItem(
  "inventory", "distribution order summary", url="/distribution/",
  report=freppledb.output.views.operation.DistributionReport, index=90,
  dependencies=[DistributionOrder, ItemDistribution]
  )
menu.addItem(
  "inventory", "inventory report", url="/buffer/",
  report=freppledb.output.views.buffer.OverviewReport, index=100,
  dependencies=[OperationPlanMaterial]
  )
menu.addItem(
  "inventory", "inventory detail report", url="/flowplan/",
  report=freppledb.output.views.buffer.DetailReport, index=200,
  dependencies=[OperationPlanMaterial]
  )
menu.addItem(
  "inventory", "problem report", url="/problem/?entity=material",
  report=freppledb.output.views.problem.Report, index=300,
  dependencies=[OperationPlanMaterial]
  )
menu.addItem(
  "capacity", "resource report", url="/resource/",
  report=freppledb.output.views.resource.OverviewReport, index=100,
  dependencies=[OperationPlanResource]
  )
menu.addItem(
  "capacity", "resource detail report", url="/loadplan/",
  report=freppledb.output.views.resource.DetailReport, index=200,
  dependencies=[OperationPlanResource])
menu.addItem(
  "capacity", "problem report", url="/problem/?entity=capacity",
  report=freppledb.output.views.problem.Report, index=300,
  dependencies=[Resource]
  )
menu.addItem(
  "purchasing", "purchase order summary", url="/purchase/",
  report=freppledb.output.views.operation.PurchaseReport, index=200,
  dependencies=[PurchaseOrder, ItemSupplier]
  )
menu.addItem(
  "manufacturing", "manufacturing order summary", url="/operation/",
  report=freppledb.output.views.operation.OverviewReport, index=110,
  dependencies=[ManufacturingOrder, Operation]
  )
menu.addItem(
  "manufacturing", "problem report", url="/problem/?entity=operation",
  report=freppledb.output.views.problem.Report, index=200,
  dependencies=[Operation]
  )
menu.addItem(
  "admin", "problem report", url="/problem/?name=invalid%20data",
  report=freppledb.output.views.problem.Report, index=400,
  )
