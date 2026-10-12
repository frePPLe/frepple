#
# Copyright (C) 2026 by frePPLe bv
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
import sys

# Assure frePPLe is found in the Python path.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freppledb.settings")

from django.core.asgi import get_asgi_application

application = get_asgi_application()

# If running via Django's development server, also spin up the background scheduler
if "runserver" in sys.argv:
    import freppledb
    import subprocess
    from pathlib import Path

    bg_script = Path(freppledb.__file__).parent / "scheduler.py"
    venv = os.environ.get("VIRTUAL_ENV")
    python = os.path.join(venv, "bin", "python3") if venv else sys.executable
    worker = subprocess.Popen([python, str(bg_script)])
