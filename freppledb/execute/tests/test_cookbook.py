#
# Copyright (C) 2007-2013 by frePPLe bv
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

import unittest

from django.conf import settings
from django.core import management

from . import cookbooktest


class cookbook_input(cookbooktest):
    def test_calendar_working_hours(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "calendar",
            "calendar-working-hours.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "calendar",
            "calendar-working-hours.expect",
        )

    def test_resource_type(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-type.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-type.expect",
        )

    def test_resource_skills(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-skills.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-skills.expect",
        )

    def test_resource_tool(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-tool.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-tool.expect",
        )

    def test_demand_priorities(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "demand",
            "demand-priorities.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "demand",
            "demand-priorities.expect",
        )

    def test_demand_policies(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "demand",
            "demand-policies.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "demand",
            "demand-policies.expect",
        )

    def test_operation_type(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-type.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-type.expect",
        )

    def test_operation_posttime(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-posttime.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-posttime.expect",
        )

    def test_operation_dependency(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-dependency.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-dependency.expect",
        )

    def test_operation_autofence(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-autofence.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-autofence.expect",
        )

    def test_operation_routing(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-routing.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-routing.expect",
        )

    def test_make_to_order(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "make-to-order.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "make-to-order.expect",
        )

    @unittest.skip("Feature is deprecated")
    def test_buffer_transfer_batch(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "transfer-batch.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "transfer-batch.expect",
        )

    def test_supplier_capacity(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "supplier",
            "supplier-capacity.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "supplier",
            "supplier-capacity.expect",
        )

    def test_alternate_materials(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "alternate-materials.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "alternate-materials.expect",
        )

    def test_resource_efficiency(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-efficiency.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-efficiency.expect",
        )

    def test_operation_alternate(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-alternate.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-alternate.expect",
        )

    def test_resource_alternate(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-alternate.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-alternate.expect",
        )

    def test_operation_alternate(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-alternate.xlsx",
        )
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-alternate.expect",
        )
