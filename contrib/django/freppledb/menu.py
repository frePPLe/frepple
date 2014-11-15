#
# Copyright (C) 2013 by Johan De Taeye, frePPLe bvba
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

from django.conf import settings
from django.utils.importlib import import_module
from django.utils.translation import ugettext_lazy as _

from freppledb.common.menus import Menu

# Create the navigation menu.
# This is the one and only menu object in the application.
menu = Menu()

# Add our default topics.
menu.addGroup("input", label=_("Input"), index=100)
menu.addGroup("reports", label=_("Reports"), index=200)
menu.addGroup("admin", label=_("Admin"), index=300)
menu.addGroup("user", label=_("User"), index=400)
menu.addGroup("help", label="?", index=500)

# Adding the menu modules of each installed application.
# Note that the menus of the apps are processed in reverse order.
# This is required to allow the first apps to override the entries
# of the later ones.
for app in reversed(settings.INSTALLED_APPS):
  try:
    mod = import_module('%s.menu' % app)
  except ImportError as e:
    # Silently ignore if it's the menu module which isn't found
    if str(e) not in ("No module named %s.menu" % app, "No module named '%s.menu'" % app):
      raise e
