#
# Copyright (C) 2007-2022 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import re

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache


@staff_member_required
@never_cache
def logapache(request):
    """
    This view shows the apache log file.
    """
    TRACEBACK_RE = r"""
    Traceback               # Traceback first line.
    [\s\S]+?                # Content.
    ([a-zA-Z]\w*):\ (.*)    # Exception and message.
    """
    TRACEBACK_ABOVE = r"""
    The\sabove\sexception\swas\sthe\sdirect\scause\sof\sthe\sfollowing\sexception:  # Only that sentence
    """
    TRACEBACK_PATTERN = re.compile(
        "%s|%s" % (TRACEBACK_RE, TRACEBACK_ABOVE), re.M | re.X
    )
    logdata = ""
    try:

        # assuming the log file is in /var/log/apache2/error.log
        filename = "error.log"
        folder = "/var/log/apache2"
        f = open(os.path.join(folder, filename), "r")
    except Exception:
        logdata = "File not found"
    else:
        try:
            file_content = f.read()
            if "Traceback" in file_content:
                # Do regex search and keep the last one only
                for match in TRACEBACK_PATTERN.finditer(file_content):
                    for line in match.group(0).splitlines(True):
                        # filter for the time and pid information
                        while line.strip().startswith("[") and "]" in line:
                            line = line[line.rindex("]") + 1 :]
                        logdata += line

                    logdata += "\n\n"

        finally:
            f.close()

    return render(
        request,
        "logapache.html",
        {
            "title": "Below are the exceptions found in the apache log file",
            "logdata": logdata
            if len(logdata) > 0
            else "No exception found in the log file",
        },
    )
