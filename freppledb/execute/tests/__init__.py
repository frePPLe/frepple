#
# Copyright (C) 2023 by frePPLe bv
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

import os

from django.conf import settings
from django.core import management
from django.http.response import StreamingHttpResponse
from django.test import TransactionTestCase

from freppledb.common.models import User, Notification
import freppledb.input


class cookbooktest(TransactionTestCase):
    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        super().setUp()

    def tearDown(self):
        Notification.wait()
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def loadExcel(self, *filepath, webservice=False):
        # Login
        if webservice:
            os.environ["FREPPLE_TEST"] = "webservice"
            if "nowebservice" in os.environ:
                del os.environ["nowebservice"]
        else:
            os.environ["FREPPLE_TEST"] = "YES"
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        self.client.login(username="admin", password="admin")
        try:
            with open(os.path.join(*filepath), "rb") as myfile:
                response = self.client.post(
                    "/execute/launch/importworkbook/", {"spreadsheet": myfile}
                )
                if not isinstance(response, StreamingHttpResponse):
                    raise Exception("expected a streaming response")
                for rec in response.streaming_content:
                    rec
        except Exception as e:
            self.fail("Can't load excel file: %s" % e)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        if webservice:
            management.call_command("stopwebservice", wait=True, force=True)

    def writeResults(self, resultpath, opplans):
        basename = resultpath[-1].replace(".expect", ".out")
        with open(os.path.join(settings.FREPPLE_LOGDIR, basename), "wt") as outputfile:
            print("\n  Wrote results to logs/%s" % basename)
            for i in opplans:
                print(i.strip(), file=outputfile)

    def assertOperationplans(self, *resultpath):
        opplans = sorted(
            [
                "%s,%s,%s,%s%s"
                % (
                    i.name,
                    i.startdate,
                    i.enddate,
                    round(i.quantity, 1),
                    ",%s " % i.batch if i.batch else "",
                )
                for i in freppledb.input.models.OperationPlan.objects.order_by(
                    "name", "startdate", "quantity", "batch"
                ).only("name", "startdate", "enddate", "quantity", "batch")
            ],
            key=lambda s: s.lower(),
        )
        row = 0
        maxrow = len(opplans)
        with open(os.path.join(*resultpath), "r") as f:
            for line in f:
                if not line.strip():
                    continue
                if row >= maxrow or opplans[row].strip() != line.strip():
                    self.writeResults(resultpath, opplans)
                    if row < maxrow:
                        self.fail(
                            "Difference in expected results on line %s" % (row + 1)
                        )
                    else:
                        self.fail("Less output rows than expected")
                row += 1
        if row != maxrow:
            self.writeResults(resultpath, opplans)
            self.fail("More output rows than expected")
