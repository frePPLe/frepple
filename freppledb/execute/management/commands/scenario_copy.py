#
# Copyright (C) 2010-2019 by frePPLe bv
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
import subprocess
from datetime import datetime

from django.db.models import Case, When, Value, IntegerField
from django.db.models.functions import Cast, Substr, Length
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string

from freppledb.execute.models import Task, ScheduledTask
from freppledb.execute.views import FileManager
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User, Scenario, Parameter
from freppledb.common.report import create_connection
from freppledb.common.utils import getStorageUsage
from freppledb.input.models import Item
from freppledb import __version__


class Command(BaseCommand):
    help = """
        This command copies the contents of a database into another.
        The original data in the destination database are lost.

        The pg_dump and psql commands need to be in the path, otherwise
        this command will fail.
        """

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument("--user", help="User running the command"),
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Overwrite scenarios already in use",
        )
        parser.add_argument(
            "--description", help="Description of the destination scenario"
        )
        parser.add_argument(
            "--task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Unused argument for this command",
        )
        parser.add_argument(
            "--promote",
            action="store_true",
            default=False,
            help="promotes a scenario to production",
        )
        parser.add_argument(
            "--dumpfile", default=None, help="specifies source dump file"
        )
        parser.add_argument("source", help="source database to copy")
        parser.add_argument("destination", help="destination database to copy")

    def handle(self, **options):
        # Make sure the debug flag is not set!
        # When it is set, the django database wrapper collects a list of all sql
        # statements executed and their timings. This consumes plenty of memory
        # and cpu time.
        tmp_debug = settings.DEBUG
        settings.DEBUG = False

        # Pick up options
        force = options["force"]
        promote = options["promote"]
        test = "FREPPLE_TEST" in os.environ
        source = options["source"]
        Scenario.syncWithSettings()
        try:
            sourcescenario = Scenario.objects.using(DEFAULT_DB_ALIAS).get(pk=source)
        except Exception:
            raise CommandError("No source database defined with name '%s'" % source)

        if options["user"]:
            try:
                user = User.objects.all().using(source).get(username=options["user"])
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None

        # Initialize the task
        now = datetime.now()
        task = None
        if "task" in options and options["task"]:
            try:
                task = Task.objects.all().using(source).get(pk=options["task"])
            except Exception:
                raise CommandError("Task identifier not found")
            if (
                task.started
                or task.finished
                or task.status != "Waiting"
                or task.name != "scenario_copy"
            ):
                raise CommandError("Invalid task identifier")
            task.status = "0%"
            task.started = now
        else:
            task = Task(
                name="scenario_copy", submitted=now, started=now, status="0%", user=user
            )
        task.processid = os.getpid()
        task.save(using=source)

        # Validate the arguments
        destination = options["destination"]
        destinationscenario = None
        try:
            task.arguments = "%s%s %s" % (
                ("--dumpfile=%s " % options["dumpfile"]) if options["dumpfile"] else "",
                source,
                destination,
            )
            if options["description"]:
                task.arguments += '--description="%s"' % options["description"].replace(
                    '"', '\\"'
                )
            if force:
                task.arguments += " --force"
            task.save(using=source)
            try:
                destinationscenario = Scenario.objects.using(DEFAULT_DB_ALIAS).get(
                    pk=destination
                )
            except Exception:
                raise CommandError(
                    "No destination database defined with name '%s'" % destination
                )
            if source == destination:
                raise CommandError("Can't copy a schema on itself")
            if sourcescenario.status != "In use":
                raise CommandError("Source scenario is not in use")
            if destinationscenario.status != "Free" and not force and not promote:
                # make sure destination scenario is properly built otherwise it is considered Free
                scenario_is_free = False
                try:
                    User.objects.using(
                        destination
                    ).all().count()  # fails if scenario not properly built
                except Exception:
                    scenario_is_free = True
                if not scenario_is_free:
                    raise CommandError("Destination scenario is not free")
            if promote and (
                destination != DEFAULT_DB_ALIAS or source == DEFAULT_DB_ALIAS
            ):
                raise CommandError(
                    "Incorrect source or destination database with promote flag"
                )

            # check that dump file exists
            if options["dumpfile"] and not os.path.isfile(
                os.path.join(settings.FREPPLE_LOGDIR, options["dumpfile"])
            ):
                raise CommandError("Cannot find dump file %s" % options["dumpfile"])

            # confirm there is enough storage to proceed
            maxstorage = getattr(settings, "MAXSTORAGE", 0) or 0
            if maxstorage:
                storageUsage = round(getStorageUsage() / 1024 / 1024)
                if storageUsage > maxstorage:
                    raise CommandError(
                        "Storage quota exceeded: %sMB used out of %sMB available. Please free some disk space and try again"
                        % (storageUsage, maxstorage)
                    )

            # Logging message - always logging in the default database
            destinationscenario.status = "Busy"
            destinationscenario.save(update_fields=["status"], using=DEFAULT_DB_ALIAS)

            # tables excluded from promotion task
            excludedTables = [
                "common_user",
                "common_scenario",
                "auth_group",
                "auth_group_permissions",
                "auth_permission",
                "django_content_type",
                "common_comment",
                "common_notification",
                "common_follower",
                "common_user_groups",
                "common_attribute",
                "common_user_user_permissions",
                "common_preference",
                "reportmanager_report",
                "reportmanager_column",
                "execute_schedule",
            ]
            # look for extra tables for which the user has no ownership
            noOwnershipTables = []
            with connections[source].cursor() as cursor:
                cursor.execute(
                    """
                select tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname='public' and tableowner != %s;
                """,
                    (settings.DATABASES[source]["USER"],),
                )

                for t in cursor:
                    noOwnershipTables.append(t[0])

                # pg_dump still creates the sequences from the excluded tables
                # we need to explicitly exclude them too
                if destination == DEFAULT_DB_ALIAS:
                    cursor.execute(
                        """
                    select s.relname as sequencename
                    from pg_class s
                    inner join pg_depend d on d.objid=s.oid and d.classid='pg_class'::regclass and d.refclassid='pg_class'::regclass
                    inner join pg_class t on t.oid=d.refobjid
                    inner join pg_namespace n on n.oid=t.relnamespace
                    inner join pg_attribute a on a.attrelid=t.oid and a.attnum=d.refobjsubid
                    inner join pg_sequences on pg_sequences.sequencename = s.relname
                    where s.relkind='S' and n.nspname = 'public' and t.relname = any(%s);
                    """,
                        (excludedTables,),
                    )
                    excludedSequences = [i[0] for i in cursor]
            # Cleaning of the destination scenario
            with connections[destination].cursor() as cursor:
                quick_drop_failed = False
                if destination != DEFAULT_DB_ALIAS:
                    try:
                        cursor.execute(
                            "drop owned by %s" % settings.DATABASES[destination]["USER"]
                        )
                    except Exception:
                        quick_drop_failed = True
                    sql_role = settings.DATABASES[destination].get("SQL_ROLE", None)
                    if sql_role:
                        with create_connection(destination).cursor() as cursor2:
                            try:
                                cursor2.execute("set role %s", (sql_role,))
                                cursor2.execute("drop owned by %s" % sql_role)
                            except Exception:
                                quick_drop_failed = True
                if destination == DEFAULT_DB_ALIAS or quick_drop_failed:
                    # drop tables
                    cursor.execute(
                        """
                        select tablename
                        FROM pg_catalog.pg_tables
                        WHERE schemaname='public'
                        """
                    )
                    tables = [
                        connections[destination].ops.quote_name(i[0])
                        for i in cursor
                        if quick_drop_failed or i[0] not in excludedTables
                    ]
                    if tables:
                        cursor.execute("drop table %s cascade" % (",".join(tables)))

                    # drop any remaining type
                    cursor.execute(
                        """
                        SELECT typname
                        from pg_type
                        inner join pg_namespace on pg_namespace.oid = typnamespace
                        where nspname = 'public';
                        """
                    )
                    types = [i[0] for i in cursor]
                    for i in types:
                        try:
                            cursor.execute(
                                "drop type %s"
                                % connections[destination].ops.quote_name(i)
                            )
                        except Exception:
                            # silently fail
                            pass

                    # drop materialzed views
                    cursor.execute(
                        """
                        select
                        matviewname
                        from pg_matviews
                        where schemaname = 'public'
                        """
                    )
                    matviews = [i[0] for i in cursor]
                    for i in matviews:
                        cursor.execute(
                            "drop materialized view %s"
                            % connections[destination].ops.quote_name(i)
                        )

                    # drop routines
                    cursor.execute(
                        """
                        SELECT routines.routine_name
                        FROM information_schema.routines
                        WHERE routines.specific_schema='public'
                        """
                    )
                    routines = [i[0] for i in cursor]
                    for i in routines:
                        cursor.execute(
                            "drop routine %s"
                            % connections[destination].ops.quote_name(i)
                        )

                    # drop triggers
                    cursor.execute(
                        """
                        SELECT trigger_name
                        FROM information_schema.triggers
                        """
                    )
                    triggers = [i[0] for i in cursor]
                    for i in triggers:
                        cursor.execute(
                            "drop trigger %s"
                            % connections[destination].ops.quote_name(i)
                        )

                    # drop views
                    cursor.execute(
                        """
                        select table_name from INFORMATION_SCHEMA.views WHERE table_schema = 'public'
                        """
                    )
                    views = [i[0] for i in cursor]
                    for i in views:
                        cursor.execute(
                            "drop view %s" % connections[destination].ops.quote_name(i)
                        )

            # Remove the old scenario access rights
            if destination != DEFAULT_DB_ALIAS:
                with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
                    cursor.execute(
                        """
                        update common_user
                        set databases = array_remove(databases, %s)
                        where %s = any(databases)
                        """,
                        (destination, destination),
                    )

            # Copying the data
            if settings.DATABASES[source]["PASSWORD"]:
                os.environ["PGPASSWORD"] = settings.DATABASES[source]["PASSWORD"]
            try:
                if not options["dumpfile"]:
                    cmd = "pg_dump -Fc %s%s%s%s%s%s | pg_restore -n public -Fc %s%s%s -d %s"
                    commandline = cmd % (
                        settings.DATABASES[source]["USER"]
                        and ("-U %s " % settings.DATABASES[source]["USER"])
                        or "",
                        settings.DATABASES[source]["HOST"]
                        and ("-h %s " % settings.DATABASES[source]["HOST"])
                        or "",
                        settings.DATABASES[source]["PORT"]
                        and ("-p %s " % settings.DATABASES[source]["PORT"])
                        or "",
                        (
                            (
                                "%s %s "
                                % (
                                    " --exclude-table ".join(
                                        ["", *(excludedTables + excludedSequences)]
                                    ),
                                    " --exclude-table-data ".join(
                                        ["", *(excludedTables)]
                                    ),
                                )
                            )
                            if destination == DEFAULT_DB_ALIAS
                            else ""
                        ),
                        (
                            (
                                "%s "
                                % (" --exclude-table ".join(["", *noOwnershipTables]))
                            )
                            if len(noOwnershipTables) > 0
                            else ""
                        ),
                        test
                        and settings.DATABASES[source]["TEST"]["NAME"]
                        or settings.DATABASES[source]["NAME"],
                        settings.DATABASES[destination]["USER"]
                        and ("-U %s " % settings.DATABASES[destination]["USER"])
                        or "",
                        settings.DATABASES[destination]["HOST"]
                        and ("-h %s " % settings.DATABASES[destination]["HOST"])
                        or "",
                        settings.DATABASES[destination]["PORT"]
                        and ("-p %s " % settings.DATABASES[destination]["PORT"])
                        or "",
                        test
                        and settings.DATABASES[destination]["TEST"]["NAME"]
                        or settings.DATABASES[destination]["NAME"],
                    )
                else:
                    cmd = "pg_restore -n public -Fc --no-password %s%s%s -d %s %s"
                    commandline = cmd % (
                        settings.DATABASES[destination]["USER"]
                        and ("-U %s " % settings.DATABASES[destination]["USER"])
                        or "",
                        settings.DATABASES[destination]["HOST"]
                        and ("-h %s " % settings.DATABASES[destination]["HOST"])
                        or "",
                        settings.DATABASES[destination]["PORT"]
                        and ("-p %s " % settings.DATABASES[destination]["PORT"])
                        or "",
                        test
                        and settings.DATABASES[destination]["TEST"]["NAME"]
                        or settings.DATABASES[destination]["NAME"],
                        os.path.join(settings.FREPPLE_LOGDIR, options["dumpfile"]),
                    )

                with subprocess.Popen(
                    commandline,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                ) as p:
                    error_message = None
                    try:
                        res = p.communicate()
                        task.processid = p.pid
                        task.save(using=source)
                        p.wait()
                        error_message = res[1].decode().partition("\n")[0]
                        if p.returncode != 0 or "error" in error_message.lower():
                            raise Exception(error_message)

                        if not options["dumpfile"]:
                            # Successful copy can still leave warnings and errors
                            # To confirm copy is ok, let's check that the scenario copy task exists
                            # in the destination database
                            t = (
                                Task.objects.using(destination)
                                .filter(id=task.id)
                                .first()
                            )
                            if (
                                not t
                                or t.name != task.name
                                or t.submitted != task.submitted
                            ):
                                destinationscenario.status = "Free"
                                destinationscenario.save(
                                    update_fields=["status"],
                                    using=DEFAULT_DB_ALIAS,
                                )
                                raise Exception("Database copy failed")
                            t.status = "Done"
                            t.finished = datetime.now()
                            t.message = "Scenario copied from %s" % source
                            t.save(
                                using=destination,
                                update_fields=["status", "finished", "message"],
                            )

                    except Exception as e:
                        p.kill()
                        p.wait()
                        # Consider the destination database free again
                        if destination != DEFAULT_DB_ALIAS:
                            destinationscenario.status = "Free"
                            destinationscenario.save(
                                update_fields=["status"],
                                using=DEFAULT_DB_ALIAS,
                            )
                        raise Exception(e or "Database copy failed")
            finally:
                if settings.DATABASES[source]["PASSWORD"]:
                    del os.environ["PGPASSWORD"]

            # Assure the identity sequences are bigger than the id values
            with connections[destination].cursor() as cursor:
                cursor.execute(
                    """
                    with cte as (
                        select 'common_user_id_seq' as seq,
                        (select last_value from common_user_id_seq) as last_val,
                        coalesce((select max(id) from common_user),1) as max_id
                        union all
                        select 'auth_group_id_seq' as seq,
                        (select last_value from auth_group_id_seq) as last_val,
                        coalesce((select max(id) from auth_group),1) as max_id
                        union all
                        select 'auth_group_permissions_id_seq' as seq,
                        (select last_value from auth_group_permissions_id_seq) as last_val,
                        coalesce((select max(id) from auth_group_permissions),1) as max_id
                        union all
                        select 'django_content_type_id_seq' as seq,
                        (select last_value from django_content_type_id_seq) as last_val,
                        coalesce((select max(id) from django_content_type),1) as max_id
                        union all
                        select 'common_comment_id_seq' as seq,
                        (select last_value from common_comment_id_seq) as last_val,
                        coalesce((select max(id) from common_comment),1) as max_id
                        union all
                        select 'common_notification_id_seq' as seq,
                        (select last_value from common_notification_id_seq) as last_val,
                        coalesce((select max(id) from common_notification),1) as max_id
                        union all
                        select 'common_follower_id_seq' as seq,
                        (select last_value from common_follower_id_seq) as last_val,
                        coalesce((select max(id) from common_follower),1) as max_id
                        union all
                        select 'common_user_groups_id_seq' as seq,
                        (select last_value from common_user_groups_id_seq) as last_val,
                        coalesce((select max(id) from common_user_groups),1) as max_id
                        union all
                        select 'common_user_user_permissions_id_seq' as seq,
                        (select last_value from common_user_user_permissions_id_seq) as last_val,
                        coalesce((select max(id) from common_user_user_permissions),1) as max_id
                        union all
                        select 'common_preference_id_seq' as seq,
                        (select last_value from common_preference_id_seq) as last_val,
                        coalesce((select max(id) from common_preference),1) as max_id
                        union all
                        select 'reportmanager_report_id_seq' as seq,
                        (select last_value from reportmanager_report_id_seq) as last_val,
                        coalesce((select max(id) from reportmanager_report),1) as max_id
                        union all
                        select 'reportmanager_column_id_seq' as seq,
                        (select last_value from reportmanager_column_id_seq) as last_val,
                        coalesce((select max(id) from reportmanager_column),1) as max_id
                        )
                    select setval(seq, max_id, true), seq
                    from cte
                    where last_val < max_id
                    """
                )

            # Check the permissions after restoring a backup.
            if (
                options["dumpfile"]
                and task.user
                and not User.objects.using(destination)
                .filter(username=task.user.username, is_active=True)
                .count()
            ):
                # Restoring a backup shouldn't give a user access to data he didn't have access to before...
                raise Exception(
                    "Permission denied - you did't have access rights to the scenario that was backed up"
                )

            # Shut down the web service in the destination
            if "freppledb.webservice" in settings.DATABASES:
                call_command("stopwebservice", database=destination, force=True)

            # Update the scenario table
            destinationscenario.status = "In use"
            if options["description"]:
                destinationscenario.description = options["description"]
                destinationscenario.save(
                    update_fields=["status", "description"],
                    using=DEFAULT_DB_ALIAS,
                )
            else:
                destinationscenario.save(
                    update_fields=["status"], using=DEFAULT_DB_ALIAS
                )

            # Delete parameter that marks a running worker
            if destination != DEFAULT_DB_ALIAS:
                try:
                    Parameter.objects.using(destination).filter(
                        name="Worker alive"
                    ).delete()
                except BaseException:
                    pass

            # Give access to the destination scenario to:
            #  a) the user doing the copy
            #  b) all active superusers from the source schema
            # unless it's a promotion
            if destination != DEFAULT_DB_ALIAS:
                # Read all superusers from the source database
                access_allowed = [
                    u["id"]
                    for u in User.objects.using(source)
                    .filter(is_superuser=True)
                    .only("id")
                    .values("id")
                ]
                if user and not user.is_superuser:
                    access_allowed.append(user.pk)
                with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
                    cursor.execute(
                        """
                        update common_user
                        set databases = array_append(databases, %s)
                        where (databases is null or not %s = any(databases))
                        and id = any(%s)
                        """,
                        (destination, destination, access_allowed),
                    )

            # Delete data files present in the scenario folders
            if destination != DEFAULT_DB_ALIAS and settings.DATABASES[destination][
                "FILEUPLOADFOLDER"
            ] not in (
                settings.DATABASES[DEFAULT_DB_ALIAS]["FILEUPLOADFOLDER"],
                settings.DATABASES[source]["FILEUPLOADFOLDER"],
            ):
                FileManager.cleanFolder(0, destination)
                FileManager.cleanFolder(1, destination)

            # Logging message
            task.processid = None
            task.status = "Done"
            task.finished = datetime.now()

            # Update the task in the destination database
            dest_task = Task(
                name=task.name,
                submitted=task.submitted,
                started=task.started,
                finished=task.finished,
                arguments=task.arguments,
                status="Done",
                message=task.message,
                user=user,
            )
            if options["dumpfile"]:
                dest_task.message = "Scenario restored from %s" % options["dumpfile"]
            elif promote:
                dest_task.message = "Scenario promoted from %s" % source
            else:
                dest_task.message = "Scenario copied from %s" % source
            dest_task.save(using=destination)
            if options["dumpfile"]:
                task.message = "Scenario %s restored from %s" % (
                    destination,
                    options["dumpfile"],
                )
            else:
                task.message = "Scenario copied to %s" % destination

            # Delete any waiting tasks in the new copy.
            # This is needed for situations where the same source is copied to
            # multiple destinations at the same moment.
            if not options["dumpfile"]:
                Task.objects.all().using(destination).filter(id__gt=task.id).delete()

            if not promote:
                # Don't automate any task in the new copy
                for i in ScheduledTask.objects.all().using(destination):
                    i.next_run = None
                    i.data.pop("starttime", None)
                    i.data.pop("monday", None)
                    i.data.pop("tuesday", None)
                    i.data.pop("wednesday", None)
                    i.data.pop("thursday", None)
                    i.data.pop("friday", None)
                    i.data.pop("saturday", None)
                    i.data.pop("sunday", None)
                    i.save(using=destination)

                # Remove links to log files from other scenario (except when restoring
                # in the same scenario as where the dump was made)
                if not (
                    options["dumpfile"] and f".{destination}." in options["dumpfile"]
                ):
                    Task.objects.using(destination).filter(
                        logfile__isnull=False
                    ).update(logfile=None)

            if options["dumpfile"]:
                setattr(_thread_locals, "database", destination)
                call_command("migrate", database=destination)
                delattr(_thread_locals, "database")
        except Exception as e:
            if task:
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
            if destinationscenario and destinationscenario.status == "Busy":
                if destination == DEFAULT_DB_ALIAS:
                    destinationscenario.status = "In use"
                else:
                    destinationscenario.status = "Free"
                destinationscenario.save(
                    update_fields=["status"], using=DEFAULT_DB_ALIAS
                )
            raise e
        finally:
            if task:
                task.processid = None
                task.save(using=source)
            settings.DEBUG = tmp_debug

    # accordion template
    title = _("scenario management")
    index = 1300
    help_url = "command-reference.html#scenario-copy"

    @staticmethod
    def getHTML(request):
        # Synchronize the scenario table with the settings
        Scenario.syncWithSettings()

        # Collect scenario status
        scenarios = []
        active_scenarios = []
        free_scenarios = 0
        for i in (
            Scenario.objects.using(DEFAULT_DB_ALIAS)
            .annotate(
                sort_key=Case(
                    When(name="default", then=Value(0)),
                    When(
                        name__startswith="scenario",
                        then=Cast(Substr("name", 9, Length("name")), IntegerField()),
                    ),
                    default=Value(9999),
                    output_field=IntegerField(),
                )
            )
            .order_by("sort_key", "name")
        ):
            scenarios.append(i)
            if i.name in (request.user.databases or []):
                active_scenarios.append(i.name)
            if i.status == "Free":
                free_scenarios += 1

        # Deactivate this task when either:
        # - There is only 1 scenario
        # - All scenarios are in use and this user is active in only a single one
        if len(scenarios) <= 1 or (not free_scenarios and len(active_scenarios) == 1):
            return None

        # Look for dump files in the log folder of production
        dumps = []
        for f in sorted(os.listdir(settings.FREPPLE_LOGDIR)):
            if os.path.isfile(
                os.path.join(settings.FREPPLE_LOGDIR, f)
            ) and f.lower().endswith(".dump"):
                dumps.append(f)

        return render_to_string(
            "commands/scenario_copy.html",
            {
                "scenarios": scenarios,
                "DEFAULT_DB_ALIAS": DEFAULT_DB_ALIAS,
                "current_database": request.database,
                "active_scenarios": active_scenarios,
                "dumps": dumps,
                "THEMES": settings.THEMES,
                "has_free_scenarios": any(
                    j.status == "Free" and j.name != DEFAULT_DB_ALIAS for j in scenarios
                ),
                "can_add_scenarios": (
                    hasattr(settings, "MIN_NUMBER_OF_SCENARIOS")
                    and hasattr(settings, "MAX_NUMBER_OF_SCENARIOS")
                ),
            },
            request=request,
        )
