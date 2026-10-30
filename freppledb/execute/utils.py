#
# Copyright (C) 2025 by frePPLe bv
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
import psutil
import re
import shutil
import signal
import subprocess
import sys


from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS

from freppledb.common.models import Parameter, Scenario
from freppledb.common.utils import get_databases


# This function will update the number of scenarios in the djangosettings.py file.
# The DATABASES variable must be using the "for i in range(x)" syntax
# Returns an error code
# 0: no error
# 1: not valid as scenario count drops below the minimum
# 2: not valid as scenario count exceeds the maximum
# 3: scenario to delete is not free
# 4: invalid scenarios parameter
# 5: error creating/dropping the database
def updateScenarioCount(addition=True):
    scenario_count = Scenario.objects.using(DEFAULT_DB_ALIAS).count()
    min_scenarios = (
        settings.MIN_NUMBER_OF_SCENARIOS
        if hasattr(settings, "MIN_NUMBER_OF_SCENARIOS")
        else 2
    )
    max_scenarios = (
        settings.MAX_NUMBER_OF_SCENARIOS
        if hasattr(settings, "MAX_NUMBER_OF_SCENARIOS")
        else 30
    )
    if not addition and scenario_count - 1 < min_scenarios:
        return 1
    if addition and scenario_count + 1 > max_scenarios:
        return 2
    if not addition:
        last_scenario = Scenario.objects.using(DEFAULT_DB_ALIAS).get(
            name=f"scenario{scenario_count-1}"
        )
        if last_scenario.status != "Free":
            return 3

    try:
        scenario_parameter = (
            Parameter.objects.using(DEFAULT_DB_ALIAS)
            .only("value")
            .get_or_create(
                pk="scenarios",
                defaults={"value": str(len(get_databases()))},
            )[0]
        )
        scenario_count = int(scenario_parameter.value)
    except Exception:
        return 4

    try:
        with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
            if addition:
                scenario_count += 1
                cursor.execute(
                    f"drop database if exists {settings.POSTGRES_DB_PREFIX}{scenario_count} WITH (FORCE)"
                )
                cursor.execute(
                    f"create database {settings.POSTGRES_DB_PREFIX}{scenario_count}"
                )
                if settings.DATABASES[DEFAULT_DB_ALIAS]["SQL_ROLE"]:
                    cursor.execute(
                        f"grant connect on database {settings.POSTGRES_DB_PREFIX}{scenario_count} to {settings.DATABASES[DEFAULT_DB_ALIAS]["SQL_ROLE"]}"
                    )
            else:
                cursor.execute(
                    f"drop database if exists {settings.POSTGRES_DB_PREFIX}{scenario_count} WITH (FORCE)"
                )
                scenario_count -= 1
    except Exception:
        return 5

    # Only update the parameter when all the above is successfull
    scenario_parameter.value = str(scenario_count)
    scenario_parameter.save(update_fields=["value"])
    return 0


def ReloadScheduler():
    if os.environ.get("SUPERVISOR_ENABLED") and shutil.which("supervisorctl"):
        # In a container: Ask supervisord to restart it instead.
        subprocess.run(
            [
                "supervisorctl",
                "-c",
                os.path.join(settings.FREPPLE_CONFIGDIR, "supervisord.conf"),
                "restart",
                "scheduler",
            ],
            check=False,
        )
    else:
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = proc.info["name"]
                if name and "frepple-sched" in name:
                    proc.send_signal(signal.SIGUSR1)
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        print("Warning: No scheduler process found.")
