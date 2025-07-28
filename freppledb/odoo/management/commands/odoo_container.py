#
# Copyright (C) 2022 by frePPLe bv
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

import os.path
import psycopg2
import subprocess

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS

from freppledb import __version__
from freppledb.common.models import Parameter
from freppledb.common.utils import get_databases

from ...utils import getOdooVersion


class Command(BaseCommand):
    help = "Utility command for development to spin up an odoo docker container"

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            dest="full",
            default=False,
            help="Complete rebuild of image and database",
        )
        parser.add_argument(
            "--populate",
            action="store_true",
            dest="populate",
            default=False,
            help="Populate the database with a medium size random dataset",
        )
        parser.add_argument(
            "--destroy",
            action="store_true",
            dest="destroy",
            default=False,
            help="Use this option to clean up all docker objects",
        )
        parser.add_argument(
            "--multidb",
            action="store_true",
            dest="multidb",
            default=False,
            help="Use this option to run the odoo container in multi-database mode",
        )
        parser.add_argument(
            "--nolog",
            action="store_true",
            dest="nolog",
            default=False,
            help="Tail the odoo log at the end of this command",
        )
        parser.add_argument(
            "--container-port",
            type=int,
            default=8069,
            help="Port number for odoo. Defaults to 8069",
        )
        parser.add_argument(
            "--frepple-url",
            default="http://localhost:8000",
            help="URL where frepple is available. Defaults to 'http://localhost:8000'",
        )
        parser.add_argument(
            "--odoo-url",
            default="http://localhost:8069",
            help="URL where odoo is available. Defaults to 'http://localhost:8069'",
        )
        parser.add_argument(
            "--odoo-db-host",
            default=get_databases()[DEFAULT_DB_ALIAS]["HOST"],
            help="Database host to use for odoo. Defaults to the same as used by frepple.",
        )
        parser.add_argument(
            "--odoo-db-port",
            default=get_databases()[DEFAULT_DB_ALIAS]["PORT"],
            help="Database port to use for odoo. Defaults to the same as used by frepple.",
        )
        parser.add_argument(
            "--odoo-db-user",
            default=get_databases()[DEFAULT_DB_ALIAS]["USER"],
            help="Database user to use for odoo. Defaults to the same as used by frepple.",
        )
        parser.add_argument(
            "--odoo-db-password",
            default=get_databases()[DEFAULT_DB_ALIAS]["PASSWORD"],
            help="Database password to use for odoo. Defaults to the same as used by frepple.",
        )
        parser.add_argument(
            "--odoo-addon-path",
            default=os.path.join(os.path.dirname(__file__), "..", "..", "odoo_addon"),
            help="Location of the odoo connectors to install.",
        )
        parser.add_argument(
            "--docker-arg",
            action="append",
            help="Extra arguments to pass to the 'docker run' command. Can be used multiple times.",
        )

    def handle(self, **options):
        dockerfile = os.path.join(options["odoo_addon_path"], "dockerfile")
        try:
            odooversion = getOdooVersion(dockerfile)
        except Exception:
            raise CommandError("Can't determine odoo version")

        # Used as a) docker image name, b) docker container name,
        # c) docker volume name and d) odoo database name.
        name = "odoo_frepple_%s" % odooversion

        if options["destroy"]:
            if options["verbosity"]:
                print("DELETING DOCKER CONTAINER")
            subprocess.run(["docker", "rm", "--force", name])
            if options["verbosity"]:
                print("DELETING DOCKER VOLUME")
            subprocess.run(["docker", "volume", "rm", "--force", name])
            if options["verbosity"]:
                print("DELETING ODOO DATABASE")
            cmd = [
                "dropdb",
                "-U",
                options["odoo_db_user"],
                "--force",
                "--if-exists",
                name,
            ]
            if options["odoo_db_host"]:
                cmd.extend(
                    [
                        "-h",
                        options["odoo_db_host"],
                    ]
                )
            if options["odoo_db_port"]:
                cmd.extend(
                    [
                        "-p",
                        options["odoo_db_port"],
                    ]
                )
            subprocess.run(cmd)
            return

        if options["full"]:
            if options["verbosity"]:
                print("PULLING ODOO BASE IMAGE")
            subprocess.run(["docker", "pull", "odoo:%s" % odooversion])

        if options["verbosity"]:
            print("BUILDING DOCKER IMAGE")
        args = ["docker", "build", "-f", dockerfile, "-t", name, "."]
        if options["multidb"]:
            args += ["--build-arg", "MULTIDB=true"]
        subprocess.run(
            args,
            cwd=options["odoo_addon_path"],
        )

        if options["verbosity"]:
            print("DELETE OLD CONTAINER")
        subprocess.run(["docker", "rm", "--force", name])
        if options["full"]:
            subprocess.run(["docker", "volume", "rm", "--force", name])

        if options["full"]:
            if options["verbosity"]:
                print("CREATE NEW DATABASE")
            env = os.environ.copy()
            env["PGPASSWORD"] = options["odoo_db_password"]
            extraargs = []
            if options["odoo_db_host"]:
                extraargs = extraargs + [
                    "-h",
                    options["odoo_db_host"],
                ]
            if options["odoo_db_port"]:
                extraargs = extraargs + [
                    "-p",
                    options["odoo_db_port"],
                ]
            subprocess.run(
                [
                    "dropdb",
                    "-U",
                    options["odoo_db_user"],
                    "--force",
                    "--if-exists",
                ]
                + extraargs
                + [
                    name,
                ],
                env=env,
            )
            subprocess.run(
                [
                    "createdb",
                    "-U",
                    options["odoo_db_user"],
                    name,
                ]
                + extraargs,
                env=env,
            )

            if options["verbosity"]:
                print("INITIALIZE ODOO DATABASE")
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                ]
                + (
                    ["--add-host", "host.docker.internal:host-gateway"]
                    if os.name != "nt"
                    else []
                )
                + [
                    "-v",
                    "%s:/var/lib/odoo" % name,
                    "-e",
                    "HOST=%s"
                    % (
                        "host.docker.internal"
                        if not options["odoo_db_host"]
                        or options["odoo_db_host"] == "localhost"
                        else options["odoo_db_host"]
                    ),
                    "-e",
                    "USER=%s" % options["odoo_db_user"],
                    "-e",
                    "PASSWORD=%s" % options["odoo_db_password"],
                    "--name",
                    name,
                    name,
                    "odoo",
                    (
                        "--init=base,frepple,freppledata,sale_management"
                        if options["multidb"]
                        else "--init=base,frepple,freppledata,autologin,sale_management"
                    ),
                    (
                        "--load=web,frepple"
                        if options["multidb"]
                        else "--load=web,autologin"
                    ),
                    "--database=%s" % name,
                    "--stop-after-init",
                ]
            )

            if options["populate"]:
                if options["verbosity"]:
                    print("POPULATE ODOO DATABASE WITH A MEDIUM-SIZE DATASET")
                    print("THIS WILL TAKE A WHILE...")
                subprocess.run(
                    [
                        "docker",
                        "run",
                        "--rm",
                    ]
                    + (
                        ["--add-host", "host.docker.internal:host-gateway"]
                        if os.name != "nt"
                        else []
                    )
                    + [
                        "-v",
                        "%s:/var/lib/odoo" % name,
                        "-e",
                        "HOST=%s"
                        % (
                            "host.docker.internal"
                            if not options["odoo_db_host"]
                            or options["odoo_db_host"] == "localhost"
                            else options["odoo_db_host"]
                        ),
                        "-e",
                        "USER=%s" % options["odoo_db_user"],
                        "-e",
                        "PASSWORD=%s" % options["odoo_db_password"],
                        "--name",
                        name,
                        name,
                        "odoo",
                        "populate",
                        "-d",
                        name,
                        "--size=medium",
                        "--db_host=%s"
                        % (
                            "host.docker.internal"
                            if not options["odoo_db_host"]
                            or options["odoo_db_host"] == "localhost"
                            else options["odoo_db_host"]
                        ),
                        "--db_user=%s" % options["odoo_db_user"],
                        "--db_password=%s" % options["odoo_db_password"],
                    ]
                )
        else:
            if options["verbosity"]:
                print("UPGRADE FREPPLE ADDON")
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                ]
                + (
                    ["--add-host", "host.docker.internal:host-gateway"]
                    if os.name != "nt"
                    else []
                )
                + [
                    "-v",
                    "%s:/var/lib/odoo" % name,
                    "-e",
                    "HOST=%s"
                    % (
                        "host.docker.internal"
                        if not options["odoo_db_host"]
                        or options["odoo_db_host"] == "localhost"
                        else options["odoo_db_host"]
                    ),
                    "-e",
                    "USER=%s" % options["odoo_db_user"],
                    "-e",
                    "PASSWORD=%s" % options["odoo_db_password"],
                    "--name",
                    name,
                    name,
                    "odoo",
                    "--update",
                    "frepple",
                    "--database=%s" % name,
                    "--stop-after-init",
                ]
            )

        if options["verbosity"]:
            print("CONFIGURE ODOO DATABASE")
        conn_params = {
            "database": name,
            "user": options["odoo_db_user"],
            "password": options["odoo_db_password"],
        }
        if options["odoo_db_host"]:
            conn_params["host"] = options["odoo_db_host"]
        if options["odoo_db_port"]:
            conn_params["port"] = options["odoo_db_port"]
        with psycopg2.connect(**conn_params) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update res_company set
                        manufacturing_warehouse = (
                            select id
                            from stock_warehouse
                            where stock_warehouse.company_id = res_company.id
                            order by id
                            limit 1
                            ),
                        webtoken_key = '%s',
                        frepple_server = '%s',
                        disclose_stack_trace = true
                    """
                    % (
                        get_databases()[DEFAULT_DB_ALIAS].get(
                            "SECRET_WEBTOKEN_KEY", None
                        )
                        or settings.SECRET_KEY,
                        options["frepple_url"],
                    )
                )
                cursor.execute(
                    """
                    select res_company.name, stock_warehouse.name
                    from res_company
                    inner join res_users
                        on res_users.company_id = res_company.id
                        and login = 'admin'
                    inner join stock_warehouse
                        on stock_warehouse.company_id = res_company.id
                    order by stock_warehouse.id
                    """
                )
                company, mfglocation = cursor.fetchone()

        if options["verbosity"]:
            print("CONFIGURE FREPPLE PARAMETERS")
        p = Parameter.objects.get_or_create(name="odoo.company")[0]
        p.value = company
        p.save()
        p = Parameter.objects.get_or_create(name="odoo.db")[0]
        p.value = name
        p.save()
        p = Parameter.objects.get_or_create(name="odoo.user")[0]
        p.value = "admin"
        p.save()
        p = Parameter.objects.get_or_create(name="odoo.password")[0]
        p.value = "admin"
        p.save()
        p = Parameter.objects.get_or_create(name="odoo.production_location")[0]
        p.value = mfglocation
        p.save()
        p = Parameter.objects.get_or_create(name="odoo.url")[0]
        p.value = options["odoo_url"]
        p.save()

        with_ip = "freppledb.inventoryplanning" in settings.INSTALLED_APPS
        with_abc = "freppledb.abc_classification" in settings.INSTALLED_APPS
        if with_ip:
            if options["verbosity"]:
                print("INSTALLING INVENTORY PLANNING DATA")

            from freppledb.inventoryplanning.models import Segment, BusinessRule

            # deploy the default_segments fixture in case it's not there
            if with_abc:
                management.call_command(
                    "loaddata", "default_segments.json", verbosity=0
                )

            # segment Purchased items
            query = """
            (item.name,location.name) in (select item_id, coalesce(location_id,location.name)
            from itemsupplier where supplier_id != 'Unknown supplier')
            """
            s_p = Segment.objects.get_or_create(name="Purchased items", query=query)[0]
            s_p.description = "Purchased items"
            s_p.save()

            # business rules
            if with_abc:
                try:
                    br = BusinessRule.objects.get_or_create(
                        segment=Segment.objects.get(name="A parts"),
                        business_rule="service_level",
                    )[0]
                    br.priority = 10
                    br.description = "servce level of 95% for A Parts"
                    br.value = "95"
                    br.save()
                except Segment.DoesNotExist:
                    pass

                try:
                    br = BusinessRule.objects.get_or_create(
                        segment=Segment.objects.get(name="B parts"),
                        business_rule="service_level",
                    )[0]
                    br.priority = 10
                    br.description = "servce level of 75% for B Parts"
                    br.value = "75"
                    br.save()
                except Segment.DoesNotExist:
                    pass

                try:
                    br = BusinessRule.objects.get_or_create(
                        segment=Segment.objects.get(name="C parts"),
                        business_rule="service_level",
                    )[0]
                    br.priority = 10
                    br.description = "servce level of 50% for C Parts"
                    br.value = "50"
                    br.save()
                except Segment.DoesNotExist:
                    pass

            br = BusinessRule.objects.get_or_create(
                segment=s_p, business_rule="ss_min_poc"
            )[0]
            br.priority = 10
            br.description = "Two weeks of safety stock for purchased items"
            br.value = "14"
            br.save()

            br = BusinessRule.objects.get_or_create(
                segment=s_p, business_rule="roq_min_poc"
            )[0]
            br.priority = 10
            br.description = "Two weeks of ROQ for purchased items"
            br.value = "14"
            br.save()

        # Stop other odoo container already running on port 8069
        container = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "publish=%s" % options["container_port"],
                "--format",
                "{{.ID}}",
            ],
            capture_output=True,
            text=True,
        ).stdout
        if container:
            if options["verbosity"]:
                print("STOPPING ANOTHER ODOO CONTAINER")
            subprocess.run(["docker", "stop", container.strip()])

        if options["verbosity"]:
            print("CREATING DOCKER CONTAINER")
        container = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "-p",
                "%s:8069" % (options["container_port"],),
                "-p",
                "%s:8071" % (options["container_port"] + 2,),
                "-p",
                "%s:8072" % (options["container_port"] + 3,),
                "-v",
                "%s:/var/lib/odoo" % name,
                "--restart",
                "always",
            ]
            + ([i for i in options["docker_arg"]] if options["docker_arg"] else [])
            + (
                ["--add-host", "host.docker.internal:host-gateway"]
                if os.name != "nt"
                else []
            )
            + [
                "-e",
                "HOST=%s"
                % (
                    "host.docker.internal"
                    if not options["odoo_db_host"]
                    or options["odoo_db_host"] == "localhost"
                    else options["odoo_db_host"]
                ),
                "-e",
                "USER=%s" % options["odoo_db_user"],
                "-e",
                "PASSWORD=%s" % options["odoo_db_password"],
                "--name",
                name,
                "-t",
                name,
                "odoo",
                "--load=web,frepple" if options["multidb"] else "--database=%s" % name,
                # "--log-sql",    # Debugging option: log the odoo SQL queries
            ],
            capture_output=True,
            text=True,
        ).stdout.strip()

        if options["verbosity"]:
            print("CONTAINER READY: %s " % container)
            if not options["nolog"]:
                print("Hit CTRL-C to stop displaying the container log")
                subprocess.run(["docker", "attach", container])
