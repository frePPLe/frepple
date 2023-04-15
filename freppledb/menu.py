#
# Copyright (C) 2013 by frePPLe bv
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

from importlib import import_module

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from freppledb.common.menus import Menu

# Create the navigation menu.
# This is the one and only menu object in the application.
menu = Menu()

# Add our default topics.
menu.addGroup("sales", label=_("sales"), index=100)
menu.addGroup("inventory", label=_("inventory"), index=200)
menu.addGroup("capacity", label=_("capacity"), index=300)
menu.addGroup("purchasing", label=_("purchasing"), index=400)
menu.addGroup("distribution", label=_("distribution"), index=500)
menu.addGroup("manufacturing", label=_("manufacturing"), index=600)
menu.addGroup("admin", label=_("admin"), index=700)
menu.addGroup("help", label=_("help"), index=800)
menu.addItem("sales", "data", separator=True, index=1000)
menu.addItem("inventory", "data", separator=True, index=1000)
menu.addItem("capacity", "data", separator=True, index=1000)
menu.addItem("purchasing", "data", separator=True, index=1000)
menu.addItem("distribution", "data", separator=True, index=1000)
menu.addItem("manufacturing", "data", separator=True, index=1000)
menu.addItem("admin", "data", separator=True, index=1000)

# Adding the menu modules of each installed application.
# Note that the menus of the apps are processed in reverse order.
# This is required to allow the first apps to override the entries
# of the later ones.
for app in reversed(settings.INSTALLED_APPS):
    try:
        mod = import_module("%s.menu" % app)
    except ImportError as e:
        # Silently ignore if it's the menu module which isn't found
        if str(e) not in (
            "No module named %s.menu" % app,
            "No module named '%s.menu'" % app,
        ):
            raise e
