#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

import operator

from django.utils.encoding import force_unicode
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

import logging
logger = logging.getLogger(__name__)


class Menu:

  def __init__(self):
    # Structure of the _groups field:
    #   [
    #     (name, label, id, [ (name, id, reportclass), (name, id, reportclass), ]),
    #     (name, label, id, [ (name, id, reportclass), (name, id, reportclass), ]),
    #   ]
    self._groups = []
    # Structure of the _cached_menu field:
    #   [
    #     (label as unicode, [ (id, label, url, [permissions,]), (id, label, url, [permissions,]), ]),
    #     (label as unicode, [ (id, label, url, [permissions,]), (id, label, url, [permissions,]), ]),
    #   ]
    self._cached_menu = {}


  def __str__(self):
    return str(self._groups)


  def addGroup(self, name, index=None, label=None):
    # Search across existing groups
    gr = None
    for i in range(len(self._groups)):
      if self._groups[i][0] == name:
        # Update existing group
        gr = self._groups[i]
        if label: gr[1] = label
        if index: gr[2] = index
        return
    # Create new group, if it wasn't found already
    self._groups.append( (name, label or name, index, []) )


  def removeGroup(self, name):
    # Scan across groups
    for i in range(len(self._groups)):
      if self._groups[i][0] == name:
        del self._groups[i]
        return
    # No action required when the group isn't found


  def addItem(self, group, name, reportclass, index=None):
    for i in range(len(self._groups)):
      if self._groups[i][0] == group:
        # Found the group
        for j in range(len(self._groups[i][3])):
          if self._groups[i][3][j][0] == name:
            # Update existing item
            if index: self._groups[i][3][j][1] = index
            self._groups[i][3][j][2] = reportclass
            return
        # Create a new item
        self._groups[i][3].append( (name, index, reportclass) )
        return
    # Couldn't locate the group
    raise Exception("Menu group %s not found" % group)


  def removeItem(self, group, name):
    for i in range(len(self._groups)):
      if self._groups[i][0] == group:
        # Found the group
        for j in range(len(self._groups[i][3])):
          if self._groups[i][3][j][0] == name:
            # Update existing item
            del self._groups[i][3][j]
            return
    # Couldn't locate the group or the item
    raise Exception("Menu item %s not found in group %s " % (name, group))


  def getMenu(self, language):
    # Lookup in the cache
    m = self._cached_menu.get(language, None)
    if m: return m
    # Build new menu for this language
    # Sort the groups by 1) id and 2) order of append.
    self._groups.sort(key=operator.itemgetter(2))
    # Build the list of items in each group
    m = []
    for i in self._groups:
      items = []
      for j in i[3]:
        items.append( (j[1], force_unicode(j[2].title), reverse(j[2].as_view()), j[2].permissions) )
      # Sort by 1) id and 2) label. Note that the order can be different for each language!
      items.sort(key=operator.itemgetter(0,1))
      m.append( ( force_unicode(i[1]), items ) )
    # Put the new result in the cache and return
    self._cached_menu[language] = m
    return m


  def createReportPermissions(self, app):
    # Find all registered menu items of the app.
    content_type = None
    for i in self._groups:
      for j in i[3]:
        if j[2].__module__.startswith(app):
          # Loop over all permissions of the class
          for k in j[2].permissions:
            if content_type == None:
              # Create a dummy contenttype in the app
              content_type = ContentType.objects.get_or_create(name="reports", model="", app_label=app.split('.')[-1])[0]
            # Create the permission object
            # TODO: cover the case where the permission refers to a permission of a model in the same app.
            # TODO: cover the case where app X wants to refer to a permission defined in app Y.
            p = Permission.objects.get_or_create(codename=k[0], content_type=content_type)[0]
            p.name = k[1]
            p.save()

