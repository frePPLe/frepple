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
import re
import shutil
import subprocess
import sys


from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS

from freppledb.common.models import Scenario


# This function will update the number of scenarios in the djangosettings.py file.
# The DATABASES variable must be using the "for i in range(x)" syntax
# Returns an error code
# 0: no error
# 1: not valid as scenario count drops below the minimum
# 2: not valid as scenario count exceeds the maximum
# 3: scenario to delete is not free
# 4: invalid djangosettings.py format
# 5: unknown error
def updateScenarioCount(addition=True):
    using_apache = "freppleserver" not in sys.argv
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

    # Udate djangosettings.py file
    file_path = os.path.join(settings.FREPPLE_CONFIGDIR, "djangosettings.py")

    inside_databases = False
    brace_depth = 0
    # Regex to match "for i in range(n)"
    range_pattern = re.compile(r"for\s+i\s+in\s+range\((\d+)\)")
    with open(file_path, "r") as file:
        lines = file.readlines()
    new_val = None
    found = False
    error_code = 0
    with open(file_path, "w") as file:
        for line in lines:
            # Detect the start of DATABASES dict
            if "DATABASES" in line and "=" in line and "{" in line:
                inside_databases = True
                brace_depth = line.count("{") - line.count("}")

            elif inside_databases:
                brace_depth += line.count("{") - line.count("}")
                if brace_depth <= 0:
                    inside_databases = False

            # Only modify range inside DATABASES block
            if inside_databases:
                match = range_pattern.search(line)
                if match:
                    found = True
                    current_val = int(match.group(1))
                    if current_val != scenario_count:
                        return 5
                    new_val = (
                        current_val
                        if error_code
                        else (current_val + 1 if addition else current_val - 1)
                    )
                    line = range_pattern.sub(f"for i in range({new_val})", line)

            file.write(line)

    if not found:
        return 4

    # Update the apache configuration file
    file_path = "/etc/apache2/sites-enabled/z_frepple.conf"
    if using_apache and os.access(file_path, os.W_OK):
        # Regex to match 'Proxypass "/ws/' and 'Proxypass "/svc/'
        range_pattern = re.compile(r'Proxypass\s+"\/(svc|ws)\/')
        with open(file_path, "r") as file:
            lines = file.readlines()
        updated = False
        service_port = int(
            settings.DATABASES[DEFAULT_DB_ALIAS]["FREPPLE_PORT"].split(":")[-1]
        )
        with open(file_path, "w") as file:
            for line in lines:
                if range_pattern.search(line):
                    if updated:
                        continue
                    updated = True
                    for i in range(new_val):
                        if i == 0:
                            file.write(
                                f'Proxypass "/ws/default/" "ws://localhost:{service_port+i}/ws/default/" retry=0\n'
                            )
                            file.write(
                                f'Proxypass "/svc/default/" "http://localhost:{service_port+i}/" retry=0\n'
                            )
                        else:
                            file.write(
                                f'Proxypass "/ws/scenario{i}/" "ws://localhost:{service_port+i}/ws/scenario{i}/" retry=0\n'
                            )
                            file.write(
                                f'Proxypass "/svc/scenario{i}/" "http://localhost:{service_port+i}/" retry=0\n'
                            )
                else:
                    file.write(line)

    if new_val:

        # We need to create/drop now the database
        # get the db name
        match = re.match(r"^(.*?)(\d+)$", settings.DATABASES[DEFAULT_DB_ALIAS]["NAME"])
        if match:
            before_digits = match.group(1)
        else:
            return 4

        with connections[DEFAULT_DB_ALIAS].cursor() as cursor:

            cursor.execute(
                f"drop database if exists {before_digits}{new_val if not addition else new_val-1}"
            )
            if addition:
                cursor.execute(f"create database {before_digits}{new_val-1}")

            Scenario.syncWithSettings()
            if using_apache and shutil.which("apachectl"):
                # Development server automatically reloads the settings.
                # An apache server reload needs to be triggered manually.
                print("reloading apache server")
                subprocess.run(["apachectl", "-k", "graceful"], check=True)

    return 0
