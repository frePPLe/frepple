#
# Copyright (C) 2007-2013 by frePPLe bvba
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

from importlib import import_module

from django.conf import settings
from django.contrib.admin.sites import AdminSite, AlreadyRegistered


class freppleAdminSite(AdminSite):
  def register(self, model_or_iterable, admin_class=None, force=False, **options):
    try:
      super(freppleAdminSite, self).register(model_or_iterable, admin_class, **options)
    except AlreadyRegistered:
      # Ignore exception if the model is already registered. It indicates that
      # another app has already registered it.
      if force:
        # Unregister the previous one and register ourselves
        self.unregister(model_or_iterable)
        super(freppleAdminSite, self).register(model_or_iterable, admin_class, **options)


# Create two admin sites where all our apps will register their models
data_site = freppleAdminSite(name='data')

# Adding the admin modules of each installed application.
for app in settings.INSTALLED_APPS:
  try:
    mod = import_module('%s.admin' % app)
  except ImportError as e:
    # Silently ignore if its the admin module which isn't found
    if str(e) not in ("No module named %s.admin" % app, "No module named '%s.admin'" % app):
      raise e
