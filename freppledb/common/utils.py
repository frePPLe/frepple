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

from importlib.util import find_spec
from io import StringIO
import math
import os
from pathlib import Path
import tokenize


from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS


def getPostgresVersion():
    """
    Find a PostgreSQL client that matches your database instance version.
    If an exact match isn't found, try higher numbers.
    """
    v = math.floor(connections[DEFAULT_DB_ALIAS].pg_version / 10000)
    while True:
        if os.path.isdir(f"/usr/lib/postgresql/{v}/bin"):
            return v
        v += 1
        if v > 20:
            raise Exception("No client found for your PostgreSQL version")


def forceWsgiReload():
    wsgi = os.path.join(settings.FREPPLE_CONFIGDIR, "wsgi.py")
    if os.access(wsgi, os.W_OK):
        Path(wsgi).touch()
    else:
        wsgi = os.path.join(os.path.split(find_spec("freppledb").origin)[0], "wsgi.py")
        if os.access(wsgi, os.W_OK):
            Path(wsgi).touch()


def getStorageUsage():
    """
    The storage counts:
    - All files in the LOGDIR folder.
      This includes input data files, engine log files, database dump files, plan export files.
    - Postgres database storage.
    """
    from freppledb.common.models import Scenario

    total_size = 0

    # Add the size of all log files and data files
    for dirpath, dirnames, filenames in os.walk(settings.FREPPLE_LOGDIR):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    # Add the size of all scenarios in use
    dblist = [
        get_databases()[sc.name]["NAME"]
        for sc in Scenario.objects.using(DEFAULT_DB_ALIAS)
        .filter(status="In use")
        .only("name")
    ]
    with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
        cursor.execute(
            "select %s" % " + ".join(["pg_database_size(%s)"] * len(dblist)), dblist
        )
        dbsizevalue = cursor.fetchone()
        if len(dbsizevalue) > 0:
            total_size += dbsizevalue[0]
    return total_size


def update_variable_in_file(file_path, var_name, new_value_code):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    code = "".join(lines)
    tokens = list(tokenize.generate_tokens(StringIO(code).readline))

    new_lines = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == tokenize.NAME and token.string == var_name:
            # Peek ahead to find '='
            j = i + 1
            while j < len(tokens) and tokens[j].string != "=":
                j += 1
            if j >= len(tokens):
                break

            # Find the start of the assignment
            start_line = tokens[i].start[0] - 1

            # Now find the end of the assignment
            bracket_stack = []
            end_line = start_line
            k = j + 1
            while k < len(tokens):
                tok = tokens[k]
                if tok.string in "([{":
                    bracket_stack.append(tok.string)
                elif tok.string in ")]}":
                    if bracket_stack:
                        bracket_stack.pop()
                if not bracket_stack and tok.type in {tokenize.NEWLINE, tokenize.NL}:
                    end_line = tok.end[0] - 1
                    break
                end_line = tok.end[0] - 1
                k += 1

            # Replace lines from start_line to end_line with new assignment
            indent = lines[start_line][
                : len(lines[start_line]) - len(lines[start_line].lstrip())
            ]
            new_assignment = f"{indent}{var_name} = {new_value_code}\n"

            new_lines.extend(lines[:start_line])
            new_lines.append(new_assignment)
            new_lines.extend(lines[end_line + 1 :])
            break
        i += 1
    else:
        # Variable not found, append it at the end
        new_assignment = f"{var_name} = {new_value_code}\n"
        new_lines = lines + [new_assignment]

    # Write the updated lines back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def get_databases(includeReporting=False):
    if not includeReporting:
        return {
            k: v
            for k, v in settings.DATABASES.items()
            if not v.get("IS_REPORTING_DATABASE", False)
        }
    else:
        return settings.DATABASES
