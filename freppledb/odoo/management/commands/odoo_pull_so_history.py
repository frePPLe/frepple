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
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from freppledb import __version__
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User, Parameter
from freppledb.common.utils import get_databases
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

    def getCustomers(self, models, uid):
        customers = {}
        res = models.execute_kw(
            self.odoo_db,
            uid,
            self.odoo_password,
            "res.partner",
            "search_read",
            [["|", ("parent_id", "=", False), ("parent_id.active", "=", True)]],
            {
                "fields": ["name", "parent_id", "is_company"],
                "order": "parent_id desc",
            },
        )
        for i in res:
            if i["is_company"]:
                name = "%s %s" % (i["name"], i["id"])
            elif i["parent_id"] == False or i["id"] == i["parent_id"][0]:
                name = "Individuals"
            else:
                if i["parent_id"][0] in customers:
                    name = customers[i["parent_id"][0]]
                else:
                    continue

            customers[i["id"]] = name

        # Sync the customer list with the frepple database
        missing_customers = list(
            set([customers[i] for i in customers])
            - set(
                [
                    i["name"]
                    for i in Customer.objects.using(self.database)
                    .filter(source="odoo_1")
                    .values("name")
                ]
            )
        )
        if missing_customers:
            with connections[self.database].cursor() as cursor:
                psycopg2.extras.execute_batch(
                    cursor,
                    """
                        insert into customer
                        (name, source)
                        values (%s,'odoo_1')
                        """,
                    [(i,) for i in missing_customers],
                )

        return customers

    def handle(self, **options):
        self.verbosity = int(options["verbosity"])
        self.database = options["database"]
        if self.database not in get_databases().keys():
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
            self.odoo_user = getattr(settings, "ODOO_USER", {}).get(
                self.database, None
            ) or Parameter.getValue("odoo.user", self.database)
            self.odoo_password = getattr(settings, "ODOO_PASSWORDS", {}).get(
                self.database, None
            ) or Parameter.getValue("odoo.password", self.database)
            self.odoo_db = getattr(settings, "ODOO_DB", {}).get(
                self.database, None
            ) or Parameter.getValue("odoo.db", self.database, None)
            self.odoo_url = (
                getattr(settings, "ODOO_URL", {}).get(self.database, None)
                or Parameter.getValue("odoo.url", self.database, "")
            ).strip()
            if not self.odoo_url.endswith("/"):
                self.odoo_url = self.odoo_url + "/"
            self.odoo_company = getattr(settings, "ODOO_COMPANY", {}).get(
                self.database, None
            ) or Parameter.getValue("odoo.company", self.database, None)
            self.singlecompany = getattr(settings, "ODOO_SINGLECOMPANY", {}).get(
                self.database, None
            ) or Parameter.getValue("odoo.singlecompany", self.database, "false")
            self.odoo_language = getattr(settings, "ODOO_SINGLECOMPANY", {}).get(
                self.database, None
            ) or Parameter.getValue("odoo.language", self.database, "en_US")
            self.odoo_delta = Parameter.getValue("odoo.delta", self.database, "999")

            # Check parameters
            missing = []
            if not self.odoo_user:
                missing.append("odoo_user")
            if not self.odoo_password:
                missing.append("odoo_password")
            if not self.odoo_db:
                missing.append("odoo_db")
            if not self.odoo_url:
                missing.append("odoo_url")
            if not self.odoo_company:
                missing.append("odoo_company")
            if not self.odoo_language:
                missing.append("odoo_language")
            if missing:
                raise CommandError("Missing parameter %s" % ", ".join(missing))

            common = xmlrpc.client.ServerProxy(
                "{}xmlrpc/2/common".format(self.odoo_url)
            )

            uid = common.authenticate(
                self.odoo_db, self.odoo_user, self.odoo_password, {}
            )

            models = xmlrpc.client.ServerProxy(
                "{}xmlrpc/2/object".format(self.odoo_url)
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
                task.message = "Pulling the customers from Odoo"
                task.save(using=self.database)
                customers = self.getCustomers(models, uid)
                startdate = min_date
                # number of days in the moving window we are pulling the data from
                step = 1
                step_percent = 100 / ((datetime.now() - min_date).days / step)
                percent = 0
                while startdate < datetime.now():
                    task.status = "%s%%" % (round(percent),)
                    percent += step_percent
                    task.message = "Working on period [%s,%s]" % (
                        startdate.strftime("%Y-%m-%d"),
                        (startdate + timedelta(days=step)).strftime("%Y-%m-%d"),
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
    index = 2500
    help_url = "command-reference.html#odoo_pull_so_history"

    @staticmethod
    def getHTML(request):
        if (
            request.user.has_perm("auth.run_db")
            and "freppledb.odoo" in settings.INSTALLED_APPS
        ):
            return render_to_string(
                "commands/odoo_pull_so_history.html",
                request=request,
            )
        else:
            return None
