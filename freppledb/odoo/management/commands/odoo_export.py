#
# Copyright (C) 2016 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import base64
from datetime import datetime, timedelta
import email
import json
import jwt
import time
from xml.sax.saxutils import quoteattr
from urllib.request import urlopen, Request

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _
from django.template import Template, RequestContext

from freppledb import __version__
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User, Parameter
from freppledb.execute.models import Task
from freppledb.input.models import PurchaseOrder, DistributionOrder, ManufacturingOrder


class Command(BaseCommand):

    help = "Loads data from an Odoo instance into the frePPLe database"

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument("--user", help="User running the command")
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates the frePPLe database to export",
        )
        parser.add_argument(
            "--task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )

    def handle(self, **options):
        self.verbosity = int(options["verbosity"])
        self.database = options["database"]
        if self.database not in settings.DATABASES.keys():
            raise CommandError("No database settings known for '%s'" % self.database)

        if options["user"]:
            try:
                user = (
                    User.objects.all()
                    .using(self.database)
                    .get(username=options["user"])
                )
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None

        now = datetime.now()
        task = None
        old_thread_locals = getattr(_thread_locals, "database", None)
        try:
            # Initialize the task
            setattr(_thread_locals, "database", self.database)
            if "task" in options and options["task"]:
                try:
                    task = (
                        Task.objects.all().using(self.database).get(pk=options["task"])
                    )
                except Exception:
                    raise CommandError("Task identifier not found")
                if (
                    task.started
                    or task.finished
                    or task.status != "Waiting"
                    or task.name != "odoo_export"
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
            else:
                task = Task(
                    name="odoo_export",
                    submitted=now,
                    started=now,
                    status="0%",
                    user=user,
                )
            task.message = "Exporting plan data to odoo"
            task.save(using=self.database)

            # Get parameters
            missing = []
            self.odoo_user = Parameter.getValue("odoo.user", self.database)
            if not self.odoo_user:
                missing.append("odoo_user")
            self.odoo_password = settings.ODOO_PASSWORDS.get(self.database, None)
            if not self.odoo_password:
                self.odoo_password = Parameter.getValue("odoo.password", self.database)
            if not self.odoo_password:
                missing.append("odoo_password")
            self.odoo_db = Parameter.getValue("odoo.db", self.database)
            if not self.odoo_db:
                missing.append("odoo_db")
            self.odoo_url = Parameter.getValue("odoo.url", self.database)
            if not self.odoo_url:
                missing.append("odoo_url")
            if not self.odoo_url.endswith("/"):
                self.odoo_url += "/"
            self.odoo_company = Parameter.getValue("odoo.company", self.database)
            if not self.odoo_company:
                missing.append("odoo_company")
            self.odoo_language = Parameter.getValue(
                "odoo.language", self.database, "en_US"
            )
            if not self.odoo_language:
                missing.append("odoo_language")
            if missing:
                raise CommandError("Missing parameter %s" % ", ".join(missing))

            # Collect data to send
            task.status = "0%"
            task.message = "Collecting plan data to send"
            task.save(using=self.database, update_fields=("status", "message"))
            self.exported = []
            self.boundary = email.generator._make_boundary()
            body = "\n".join(self.generateDataToPublish()).encode("utf-8")

            # Connect to the odoo URL to POST data
            task.status = "33%"
            task.message = "Sending plan data to odoo"
            task.save(using=self.database, update_fields=("status", "message"))
            encoded = base64.encodebytes(
                ("%s:%s" % (self.odoo_user, self.odoo_password)).encode("utf-8")
            )
            size = len(body)
            req = Request(
                "%sfrepple/xml/" % self.odoo_url,
                data=body,
                headers={
                    "Authorization": "Basic %s" % encoded.decode("ascii")[:-1],
                    "Content-Type": "multipart/form-data; boundary=%s" % self.boundary,
                    "Content-length": size,
                },
            )
            with urlopen(req) as f:
                # Read the odoo response
                f.read()
            task.status = "33%"
            task.message = "Exporting plan data to odoo"
            task.save(using=self.database, update_fields=("status", "message"))

            # Mark the exported operations as approved
            task.status = "66%"
            task.message = "Marking exported data to odoo"
            task.save(using=self.database, update_fields=("status", "message"))
            for i in self.exported:
                i.status = "approved"
                i.save(using=self.database, update_fields=("status",))
            del self.exported

            # Task update
            task.status = "Done"
            task.message = None
            task.finished = datetime.now()
            task.processid = None

        except Exception as e:
            if task:
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
                task.processid = None
            raise e

        finally:
            if task:
                task.save(using=self.database)
            setattr(_thread_locals, "database", old_thread_locals)

    def generateDataToPublish(self):
        yield "--%s\r" % self.boundary
        yield 'Content-Disposition: form-data; name="webtoken"\r'
        yield "\r"
        yield "%s\r" % jwt.encode(
            {"exp": round(time.time()) + 600, "user": self.odoo_user},
            settings.DATABASES[self.database].get(
                "SECRET_WEBTOKEN_KEY", settings.SECRET_KEY
            ),
            algorithm="HS256",
        ).decode("ascii")
        yield "--%s\r" % self.boundary
        yield 'Content-Disposition: form-data; name="database"\r'
        yield "\r"
        yield "%s\r" % self.odoo_db
        yield "--%s\r" % self.boundary
        yield 'Content-Disposition: form-data; name="language"\r'
        yield "\r"
        yield "%s\r" % self.odoo_language
        yield "--%s\r" % self.boundary
        yield 'Content-Disposition: form-data; name="company"\r'
        yield "\r"
        yield "%s\r" % self.odoo_company
        yield "--%s\r" % self.boundary
        yield 'Content-Disposition: file; name="frePPLe plan"; filename="frepple_plan.xml"\r'
        yield "Content-Type: application/xml\r"
        yield "\r"
        yield '<?xml version="1.0" encoding="UTF-8" ?>'
        yield '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        yield "<operationplans>"
        today = datetime.today()

        # Purchase orders to export
        for i in (
            PurchaseOrder.objects.using(self.database)
            .filter(
                status="proposed",
                item__source__startswith="odoo",
                startdate__lte=today + timedelta(days=7),
            )
            .order_by("startdate")
            .select_related("location", "item", "supplier")
        ):
            if (
                i.status not in ("proposed", "approved")
                or not i.item
                or not i.item.source
                or not i.item.subcategory
                or not i.location.subcategory
                or not i.item.source.startswith("odoo")
                or i.supplier.name == "Unknown supplier"
            ):
                continue
            self.exported.append(i)
            yield '<operationplan reference=%s ordertype="PO" item=%s location=%s supplier=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" batch=%s/>' % (
                quoteattr(i.reference),
                quoteattr(i.item.name),
                quoteattr(i.location.name),
                quoteattr(i.supplier.name),
                i.startdate,
                i.enddate,
                i.quantity,
                quoteattr(i.location.subcategory),
                quoteattr(i.item.subcategory),
                int(i.criticality),
                quoteattr(i.batch or ""),
            )

        # Distribution orders to export
        for i in (
            DistributionOrder.objects.using(self.database)
            .filter(
                status="proposed",
                item__source__startswith="odoo",
                startdate__lte=today + timedelta(days=7),
            )
            .order_by("startdate")
            .select_related("item", "origin", "destination")
        ):
            if (
                i.status not in ("proposed", "approved")
                or not i.item
                or not i.item.source
                or not i.item.subcategory
                or not i.origin.subcategory
                or not i.destination.subcategory
                or not i.item.source.startswith("odoo")
            ):
                continue
            self.exported.append(i)
            yield '<operationplan status="%s" reference=%s ordertype="DO" item=%s origin=%s destination=%s start="%s" end="%s" quantity="%s" origin_id=%s destination_id=%s item_id=%s criticality="%d" batch=%s/>' % (
                i.status,
                quoteattr(i.reference),
                quoteattr(i.item.name),
                quoteattr(i.origin.name),
                quoteattr(i.destination.name),
                i.startdate,
                i.enddate,
                i.quantity,
                quoteattr(i.origin.subcategory),
                quoteattr(i.destination.subcategory),
                quoteattr(i.item.subcategory),
                int(i.criticality),
                quoteattr(i.batch or ""),
            )

        # Manufacturing orders to export
        for i in (
            ManufacturingOrder.objects.using(self.database)
            .filter(
                item__source__startswith="odoo",
                operation__source__startswith="odoo",
                operation__owner__isnull=True,
                status="proposed",
                startdate__lte=today + timedelta(days=7),
            )
            .order_by("startdate")
            .select_related("operation", "location", "item", "owner")
        ):
            if (
                i.status not in ("proposed", "approved")
                or not i.operation
                or not i.operation.source
                or not i.operation.item
                or not i.operation.source.startswith("odoo")
                or not i.item.subcategory
                or not i.location.subcategory
            ):
                continue
            self.exported.append(i)
            res = set()
            try:
                for j in i.operationplanresources:
                    res.add(j.resource.name)
            except Exception:
                pass
            demand_str = json.dumps(i.plan["pegging"]) if i.plan["pegging"] else ""
            if i.operation.category == "subcontractor":
                yield '<operationplan ordertype="PO" id=%s item=%s location=%s supplier=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" batch=%s/>' % (
                    quoteattr(i.reference),
                    quoteattr(i.item.name),
                    quoteattr(i.location.name),
                    quoteattr(i.operation.subcategory or ""),
                    i.startdate,
                    i.enddate,
                    i.quantity,
                    quoteattr(i.location.subcategory or ""),
                    quoteattr(i.item.subcategory or ""),
                    int(i.criticality),
                    quoteattr(i.batch or ""),
                )
            else:
                yield '<operationplan reference=%s ordertype="MO" item=%s location=%s operation=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" resource=%s demand=%s batch=%s/>' % (
                    quoteattr(i.reference),
                    quoteattr(i.operation.item.name),
                    quoteattr(i.operation.location.name),
                    quoteattr(i.operation.name),
                    i.startdate,
                    i.enddate,
                    i.quantity,
                    quoteattr(i.operation.location.subcategory),
                    quoteattr(i.operation.item.subcategory),
                    int(i.criticality),
                    quoteattr(",".join(res)),
                    quoteattr(demand_str),
                    quoteattr(i.batch or ""),
                )

        # Work orders to export
        # Normally we don't create work orders, but only updates existing work orders.
        # We leave it to odoo to create the workorders for a manufacturing order.
        for i in (
            ManufacturingOrder.objects.using(self.database)
            .filter(
                owner__operation__type="routing",
                operation__source__startswith="odoo",
                owner__item__source__startswith="odoo",
                status__in=("proposed", "approved"),
                startdate__lte=today + timedelta(days=7),
            )
            .order_by("startdate")
            .select_related("operation", "location", "item", "owner")
        ):
            if (
                i.status not in ("proposed", "approved")
                or not i.operation
                or not i.operation.source
                or not i.owner.operation.item
                or not i.operation.source.startswith("odoo")
                or not i.owner.item.subcategory
                or not i.location.subcategory
            ):
                continue
            self.exported.append(i)
            res = set()
            try:
                for j in i.operationplanresources:
                    res.add(j.resource.name)
            except Exception:
                pass
            yield '<operationplan reference=%s owner=%s ordertype="WO" item=%s location=%s operation=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s resource=%s batch=%s/>' % (
                quoteattr(i.reference),
                quoteattr(i.owner.reference),
                quoteattr(i.owner.operation.item.name),
                quoteattr(i.operation.location.name),
                quoteattr(i.operation.name),
                i.startdate,
                i.enddate,
                i.quantity,
                quoteattr(i.operation.location.subcategory),
                quoteattr(i.owner.operation.item.subcategory),
                quoteattr(",".join(res)),
                quoteattr(i.batch or ""),
            )

        # Write the footer
        yield "</operationplans>"
        yield "</plan>"
        yield "--%s--\r" % self.boundary
        yield "\r"

    # accordion template
    title = _("Export data to %(erp)s") % {"erp": "odoo"}
    index = 1450
    help_url = "integration-guide/odoo-connector.html"

    @staticmethod
    def getHTML(request):
        return Template(
            """
            {% load i18n %}
            <form role="form" method="post" action="{{request.prefix}}/execute/launch/odoo_export/">{% csrf_token %}
            <table>
              <tr>
                <td style="vertical-align:top; padding: 15px">
                   <button  class="btn btn-primary"  type="submit" value="{% trans "launch"|capfirst %}">{% trans "launch"|capfirst %}</button>
                </td>
                <td  style="padding: 0px 15px;">{% trans "Export frePPLe data to odoo." %}
                </td>
              </tr>
            </table>
            </form>
          """
        ).render(RequestContext(request))
