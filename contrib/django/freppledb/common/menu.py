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

from django.utils.translation import ugettext as _
from django.conf import settings

from freppledb.menu import menu
from freppledb.admin import admin_site

# Admin menu
menu.addItem("admin", "admin_site", admin=admin_site, index=200)

# User menu
menu.addItem("user", "logout", url="/admin/logout/", label=_('Log out'), prefix=False, index=100)
menu.addItem("user", "preferences", url="/preferences/", label=_('Preferences'), index=200)
menu.addItem("user", "change password", url="/admin/password_change/", label=_('Change password'), index=300)

# Help menu
menu.addItem("help", "tour", javascript="tour.start('0,0,0')", label=_('Application tour'), index=100)
menu.addItem("help", "documentation", url="%sdoc/index.html" % settings.STATIC_URL, label=_('Documentation'), window=True, prefix=False, index=100)
menu.addItem("help", "website", url="http://frepple.com", window=True, label=_('frePPLe website'), prefix=False, index=200)

