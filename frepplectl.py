#!/usr/bin/env python3

#
# Copyright (C) 2007-2013 by frePPLe bv
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

r"""
This command is the wrapper for all administrative actions on frePPLe.
"""

import os
import sys
import site

if __name__ == "__main__":
    try:
        # Autodetect Python virtual enviroment
        venv = os.environ.get("VIRTUAL_ENV", None)
        if not venv:
            curdir = os.path.dirname(os.path.realpath(__file__))
            for candidate in (
                # Development layout
                os.path.join(curdir, "venv"),
                # Linux install layout
                os.path.join(curdir, "..", "share", "frepple", "venv"),
            ):
                if os.path.isfile(
                    os.path.join(candidate, "bin", "python3")
                ) and os.path.isfile(os.path.join(candidate, "bin", "activate")):
                    os.environ["VIRTUAL_ENV"] = candidate
                    venv = candidate
                    break

        # Activate Python virtual environment
        if venv:
            prev_length = len(sys.path)
            os.environ["PATH"] = os.pathsep.join(
                [os.path.join(venv, "bin")]
                + os.environ.get("PATH", "").split(os.pathsep)
            )
            path = os.path.realpath(
                os.path.join(
                    venv,
                    "lib",
                    "python%d.%d" % sys.version_info[:2],
                    "site-packages",
                )
            )
            site.addsitedir(path)
            sys.path[:] = sys.path[prev_length:] + sys.path[0:prev_length]
            sys.real_prefix = sys.prefix
            sys.prefix = venv

        # Initialize django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freppledb.settings")
        import django

        django.setup()

        # Synchronize the scenario table with the settings
        from freppledb.common.models import Scenario

        Scenario.syncWithSettings()

        if "version" in sys.argv or "--version" in sys.argv:
            # Display the version and stop
            import freppledb

            sys.stdout.write(freppledb.__version__ + "\n")
        else:
            # Run the command
            from django.core.management import execute_from_command_line

            execute_from_command_line(sys.argv)

    except KeyboardInterrupt:
        print("\nInterrupted with Ctrl-C")
        sys.exit(1)
