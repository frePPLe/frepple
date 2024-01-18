#
# Copyright (C) 2007-2022 by frePPLe bv
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
    TRACEBACK_RE1 = r"""
    Traceback               # Traceback first line.
    [\s\S]+?                # Content.
    ([a-zA-Z]\w*):\ (.*)    # Exception and message.
    """
    TRACEBACK_RE2 = r"""
    Traceback               # Traceback first line.
    [\s\S]+?                # Content.
    ([a-zA-Z]\w*):\ (.*)    # Exception and message.
    [\s\S]+?
    ([a-zA-Z]\w*):\ (.*)    # Error or detail
    """
    TRACEBACK_ABOVE = r"""
    The\sabove\sexception\swas\sthe\sdirect\scause\sof\sthe\sfollowing\sexception:  # Only that sentence
    """
    TRACEBACK_PATTERN = re.compile(
        "%s|%s|%s" % (TRACEBACK_RE2, TRACEBACK_RE1, TRACEBACK_ABOVE), re.M | re.X
    )
    logdata = ""
    try:
        # assuming the log file is in /var/log/apache2/error.log
        filename = "error.log"
        folder = "/var/log/apache2"
        f = open(os.path.join(folder, filename), "r")
    except Exception:
        logdata = "File /var/log/apache2/error.log cannot be accessed."
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
            "title": "Exceptions found in the apache log file",
            "logdata": logdata
            if len(logdata) > 0
            else "No exception found in the log file",
        },
    )
