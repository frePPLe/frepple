#
# Copyright (C) 2024 by frePPLe bv
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


from datetime import datetime, timedelta
import psycopg2.extras
from urllib.request import HTTPError, URLError
import xmlrpc.client


from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections
from django.template import Template, RequestContext
from django.utils.translation import gettext_lazy as _

from freppledb import __version__
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User, Parameter
from freppledb.execute.models import Task
from freppledb.input.models import (
    Item,
    Location,
    Customer,
)


class Command(BaseCommand):
    help = "Imports all the Odoo demand history into frePPLe."

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument("--user", help="User running the command")
        parser.add_argument(
            "--step",
            type=float,
            default=1,
            help="Pull the demand history in batches of step days",
        )
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
                    or task.name != "odoo_pull_so_history"
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
            else:
                task = Task(
                    name="odoo_pull_so_history",
                    submitted=now,
                    started=now,
                    status="0%",
                    user=user,
                )
            task.message = "Pulling closed demand history from Odoo"
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
            if self.odoo_url.endswith("/"):
                self.odoo_url = self.odoo_url[0 : len(self.odoo_url) - 1]
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

            common = xmlrpc.client.ServerProxy(
                "{}/xmlrpc/2/common".format(self.odoo_url)
            )

            uid = common.authenticate(
                self.odoo_db, self.odoo_user, self.odoo_password, {}
            )

            models = xmlrpc.client.ServerProxy(
                "{}/xmlrpc/2/object".format(self.odoo_url)
            )

            # get the oldest write_date for the sales order lines

            res = models.execute_kw(
                self.odoo_db,
                uid,
                self.odoo_password,
                "sale.order.line",
                "search_read",
                [
                    [
                        ("product_id", "!=", False),
                    ]
                ],
                {
                    "fields": ["write_date"],
                    "limit": 1,
                    "order": "write_date",
                },
            )
            min_date = None
            for i in res:
                min_date = datetime.strptime(i["write_date"], "%Y-%m-%d %H:%M:%S")
            if min_date:

                # read the items
                items = {}
                for i in (
                    Item.objects.using(self.database)
                    .filter(source="odoo_1")
                    .filter(subcategory__isnull=False)
                    .values("name", "subcategory")
                ):
                    items[int(i["subcategory"].split(",")[1])] = i["name"]

                # read the locations
                locations = {}
                for i in (
                    Location.objects.using(self.database)
                    .filter(source="odoo_1")
                    .filter(subcategory__isnull=False)
                    .values("name", "subcategory")
                ):
                    locations[int(i["subcategory"])] = i["name"]

                # read the customers
                customers = {}
                for i in (
                    Customer.objects.using(self.database)
                    .filter(source="odoo_1")
                    .exclude(name="Individuals")
                    .exclude(name="All customers")
                    .values("name")
                ):
                    customers[int(i["name"].split()[-1])] = i["name"]
                startdate = min_date
                # number of days in the moving window we are pulling the data from
                step = 1
                step_percent = 100 / ((datetime.now() - min_date).days / step)
                percent = 0
                while startdate < datetime.now():
                    task.status = "%s%%" % (round(percent),)
                    percent += step_percent
                    task.message = "Working on period [%s,%s]" % (
                        startdate,
                        startdate + timedelta(days=step),
                    )
                    task.save(using=self.database)
                    res_sol = models.execute_kw(
                        self.odoo_db,
                        uid,
                        self.odoo_password,
                        "sale.order.line",
                        "search_read",
                        [
                            [
                                ("write_date", ">=", startdate),
                                (
                                    "write_date",
                                    "<",
                                    startdate + timedelta(days=step),
                                ),
                                ("product_id", "!=", False),
                            ],
                        ],
                        {
                            "fields": [
                                "qty_delivered",
                                "state",
                                "product_id",
                                "product_uom_qty",
                                "product_uom",
                                "order_id",
                            ],
                        },
                    )
                    so_ids = [r["order_id"][0] for r in res_sol]

                    res_so = models.execute_kw(
                        self.odoo_db,
                        uid,
                        self.odoo_password,
                        "sale.order",
                        "search_read",
                        [
                            [
                                ("id", "in", so_ids),
                            ],
                        ],
                        {
                            "fields": [
                                "state",
                                "partner_id",
                                "commitment_date",
                                "date_order",
                                "warehouse_id",
                            ],
                        },
                    )
                    so = {r["id"]: r for r in res_so}

                    insert_statements = []
                    for i in res_sol:
                        if i["order_id"][0] not in so or so[i["order_id"][0]][
                            "state"
                        ] not in ("done", "sale"):
                            continue
                        item = items.get(i["product_id"][0])
                        if not item:
                            continue
                        location = locations.get(
                            so[i["order_id"][0]]["warehouse_id"][0]
                        )
                        if not location:
                            continue
                        customer = customers.get(so[i["order_id"][0]]["partner_id"][0])
                        if not customer:
                            continue
                        name = "%s %s" % (i["order_id"][1], i["id"])
                        due = (
                            so[i["order_id"][0]].get("commitment_date", False)
                            or so[i["order_id"][0]]["date_order"]
                        )
                        quantity = i["product_uom_qty"]
                        insert_statements.append(
                            (name, item, location, customer, due, quantity)
                        )

                    with connections[self.database].cursor() as cursor:
                        psycopg2.extras.execute_batch(
                            cursor,
                            """
                        insert into demand
                        (name, item_id, location_id, customer_id, due, quantity, status, priority)
                        values (%s,%s,%s,%s,%s,%s,'closed',10) on conflict (name)
                        do update set item_id = excluded.item_id,
                        location_id = excluded.location_id,
                        customer_id = excluded.customer_id,
                        due = excluded.due,
                        quantity = excluded.quantity,
                        status = excluded.status,
                        priority= excluded.priority
                        """,
                            insert_statements,
                        )
                    startdate += timedelta(days=step)

            # Task update
            task.status = "Done"
            task.message = None
            task.finished = datetime.now()
            task.processid = None

        except HTTPError as e:
            if task:
                task.status = "Failed"
                task.message = "Internal server error %s on odoo side" % e.code
                task.finished = datetime.now()
                task.processid = None
            raise e

        except URLError as e:
            if task:
                task.status = "Failed"
                task.message = "Couldn't connect to odoo"
                task.finished = datetime.now()
                task.processid = None
            raise e

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

    # accordion template
    title = _("Pull all demand history from %(erp)s") % {"erp": "odoo"}
    index = 1425
    help_url = "command-reference.html#odoo_pull_so_history"

    @staticmethod
    def getHTML(request):
        if (
            request.user.has_perm("auth.run_db")
            and "freppledb.odoo" in settings.INSTALLED_APPS
        ):
            context = RequestContext(request)

            template = Template(
                """
        {% load i18n %}
        <form role="form" method="post" action="{{request.prefix}}/execute/launch/odoo_pull_so_history/">{% csrf_token %}
        <table>
          <tr>
            <td style="vertical-align:top; padding: 10px">
               <button  class="btn btn-primary" type="submit" value="{% trans "launch"|capfirst %}">{% trans "launch"|capfirst %}</button>
            </td>
          </tr>
        </table>
        </form>
        """
            )
            return template.render(context)
        else:
            return None
