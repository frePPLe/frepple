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

import operator

from django.utils.encoding import force_str
from django.contrib.auth.models import Permission
from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.models import ContentType
from django.utils.text import capfirst

from freppledb.common.report import EXCLUDE_FROM_BULK_OPERATIONS

import logging

logger = logging.getLogger(__name__)


class MenuItem:
    def __init__(
        self,
        name,
        model=None,
        report=None,
        url=None,
        javascript=None,
        label=None,
        index=None,
        prefix=True,
        window=False,
        separator=False,
        identifier=None,
        permission=None,
        dependencies=None,
        admin=False,
        callback=None,
        excludeFromBulkOperations=None,
    ):
        self.name = name
        self.url = url
        self.javascript = javascript
        self.report = report
        self.model = model
        if label:
            self.label = label
        elif report:
            self.label = report.title
        elif model:
            self.label = model._meta.verbose_name_plural
        else:
            self.label = None
        self.index = index
        self.prefix = prefix
        self.window = window
        self.separator = separator
        self.identifier = identifier
        if excludeFromBulkOperations is not None:
            self.excludeFromBulkOperations = excludeFromBulkOperations
        else:
            self.excludeFromBulkOperations = model in EXCLUDE_FROM_BULK_OPERATIONS
        self.permission = permission
        self.dependencies = dependencies
        self.admin = admin
        self.callback = callback

    def __str__(self):
        return self.name

    def has_permission(self, user):
        if self.separator:
            return True
        if callable(self.permission):
            return self.permission(user)
        if self.permission:
            if not user.has_perm(self.permission):
                return False
        if self.report:
            # The menu item is a report class
            return self.report.has_permission(user)
        if self.model:
            # The menu item is a model
            return user.has_perm(
                "%s.view_%s" % (self.model._meta.app_label, self.model._meta.model_name)
            )
        # Other item is always available
        return True

    def can_add(self, user):
        return self.model and user.has_perm(
            "%s.%s"
            % (
                self.model._meta.app_label,
                get_permission_codename("add", self.model._meta),
            )
        )


class Menu:
    def __init__(self):
        # Structure of the _groups field:
        #   [
        #     (name, label, id, [ Menuitem1, Menuitem2, ]),
        #     (name, label, id, [ Menuitem3, Menuitem3, ]),
        #   ]
        self._groups = []
        # Structure of the _cached_menu field for a certain language:
        #   [
        #     (label as unicode, [ (index, unicode label, Menuitem1), (index, unicode label, Menuitem2), ]),
        #     (label as unicode, [ (index, unicode label, Menuitem3), (index, unicode label, Menuitem4), ]),
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
                if label:
                    gr[1] = label
                if index is not None:
                    gr[2] = index
                return
        # Create new group, if it wasn't found already
        self._groups.append([name, label or name, index, []])

    def removeGroup(self, name):
        # Scan across groups
        for i in range(len(self._groups)):
            if self._groups[i][0] == name:
                del self._groups[i]
                return
        # No action required when the group isn't found

    def addItem(
        self,
        group,
        name,
        separator=False,
        report=None,
        url=None,
        javascript=None,
        label=None,
        index=None,
        prefix=True,
        window=False,
        model=None,
        identifier=None,
        permission=None,
        dependencies=None,
        admin=False,
        callback=None,
        excludeFromBulkOperations=None,
    ):
        for i in range(len(self._groups)):
            if self._groups[i][0] == group:
                # Found the group
                for j in range(len(self._groups[i][3])):
                    if self._groups[i][3][j].name == name:
                        # Update existing item
                        it = self._groups[i][3][j]
                        if index:
                            it["index"] = index
                        if url:
                            it["url"] = url
                        if javascript:
                            it["javascript"] = javascript
                        if report:
                            it["report"] = report
                        if label:
                            it["label"] = label
                        it["prefix"] = prefix
                        it["window"] = window
                        it["separator"] = separator
                        it["model"] = model
                        it["admin"] = admin
                        it["callback"] = callback
                        if excludeFromBulkOperations is not None:
                            it["excludeFromBulkOperations"] = excludeFromBulkOperations
                        return
                # Create a new item
                self._groups[i][3].append(
                    MenuItem(
                        name,
                        report=report,
                        url=url,
                        javascript=javascript,
                        label=label,
                        index=index,
                        prefix=prefix,
                        window=window,
                        separator=separator,
                        model=model,
                        identifier=identifier,
                        permission=permission,
                        dependencies=dependencies,
                        admin=admin,
                        callback=callback,
                        excludeFromBulkOperations=excludeFromBulkOperations,
                    )
                )
                return
        # Couldn't locate the group
        raise Exception("Menu group %s not found" % group)

    def removeItem(self, group, name):
        for i in range(len(self._groups)):
            if self._groups[i][0] == group:
                # Found the group
                for j in range(len(self._groups[i][3])):
                    if self._groups[i][3][j].name == name:
                        # Update existing item
                        del self._groups[i][3][j]
                        return
        # Couldn't locate the group or the item
        raise Exception("Menu item %s not found in group %s " % (name, group))

    def getMenu(self, language):
        # Lookup in the cache
        m = self._cached_menu.get(language, None)
        if m:
            return m

        # Build new menu for this language
        # Sort the groups by 1) id and 2) order of append.
        self._groups.sort(key=operator.itemgetter(2))

        # Build the list of items in each group
        m = []
        for i in self._groups:
            items = []
            for j in i[3]:
                items.append((j.index, capfirst(force_str(j.label)), j))
            # Sort by 1) id and 2) label. Note that the order can be different for each language!
            items.sort(key=operator.itemgetter(0, 1))
            m.append((force_str(i[1]), items))

        # Put the new result in the cache and return
        self._cached_menu[language] = m
        return m

    def createReportPermissions(self, app):
        # Find all registered menu items of the app.
        content_type = None
        for i in self._groups:
            for j in i[3]:
                if (
                    j.report
                    and j.report.__module__.startswith(app)
                    and hasattr(j.report, "permissions")
                ):
                    # Loop over all permissions of the class
                    for k in j.report.permissions:
                        if content_type is None:
                            # Create a dummy contenttype in the app
                            content_type = ContentType.objects.get_or_create(
                                model="permission", app_label="auth"
                            )[0]
                        # Create the permission object
                        p = Permission.objects.get_or_create(
                            codename=k[0], content_type=content_type
                        )[0]
                        p.name = k[1]
                        p.save()
