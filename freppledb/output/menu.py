# Copyright (C) 2013 by frePPLe bv
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

from freppledb.menu import menu
from freppledb.input.models import OperationPlanMaterial, OperationPlanResource
from freppledb.input.models import (
    Item,
    Location,
    Customer,
    OperationPlan,
    Operation,
    Resource,
    DistributionOrder,
    PurchaseOrder,
)
from freppledb.input.models import ManufacturingOrder, ItemDistribution, ItemSupplier
import freppledb.output.views.buffer
import freppledb.output.views.demand
import freppledb.output.views.problem
import freppledb.output.views.constraint
import freppledb.output.views.resource
import freppledb.output.views.operation


# Adding reports. We use an index value to keep the same order of the entries in all languages.
menu.addItem(
    "sales",
    "demand report",
    url="/demand/",
    report=freppledb.output.views.demand.OverviewReport,
    index=200,
    dependencies=[Item, Location, Customer, OperationPlan],
)
menu.addItem(
    "sales",
    "problem report",
    url="/problem/?entity__in=demand,forecast",
    report=freppledb.output.views.problem.Report,
    index=400,
    dependencies=[Item, Location, Customer, OperationPlan],
)
menu.addItem(
    "sales",
    "constraint report",
    url="/constraint/",
    report=freppledb.output.views.constraint.BaseReport,
    index=500,
    dependencies=[Item, Location, Customer, OperationPlan],
)
menu.addItem(
    "inventory",
    "distribution order summary",
    url="/distribution/",
    report=freppledb.output.views.operation.DistributionReport,
    index=90,
    dependencies=[DistributionOrder, ItemDistribution],
)
menu.addItem(
    "inventory",
    "inventory report",
    url="/buffer/",
    report=freppledb.output.views.buffer.OverviewReport,
    index=100,
    dependencies=[OperationPlanMaterial],
)
menu.addItem(
    "inventory",
    "problem report",
    url="/problem/?entity=material",
    report=freppledb.output.views.problem.Report,
    index=300,
    dependencies=[OperationPlanMaterial],
)
menu.addItem(
    "capacity",
    "resource report",
    url="/resource/",
    report=freppledb.output.views.resource.OverviewReport,
    index=100,
    dependencies=[OperationPlanResource],
)
menu.addItem(
    "capacity",
    "problem report",
    url="/problem/?entity=capacity",
    report=freppledb.output.views.problem.Report,
    index=300,
    dependencies=[Resource],
)
menu.addItem(
    "purchasing",
    "purchase order summary",
    url="/purchase/",
    report=freppledb.output.views.operation.PurchaseReport,
    index=200,
    dependencies=[PurchaseOrder, ItemSupplier],
)
menu.addItem(
    "manufacturing",
    "manufacturing order summary",
    url="/operation/",
    report=freppledb.output.views.operation.OverviewReport,
    index=160,
    dependencies=[ManufacturingOrder, Operation],
)
menu.addItem(
    "manufacturing",
    "problem report",
    url="/problem/?entity=operation",
    report=freppledb.output.views.problem.Report,
    index=200,
    dependencies=[Operation],
)
menu.addItem(
    "admin",
    "problem report",
    url="/problem/?name=invalid%20data",
    report=freppledb.output.views.problem.Report,
    index=400,
)
