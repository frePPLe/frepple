#
# Copyright (C) 2015-2017 by frePPLe bvba
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

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from rest_framework import generics
from rest_framework_bulk import ListBulkCreateUpdateDestroyAPIView
from rest_framework import filters
from rest_framework import permissions
from freppledb.common.models import User


@staff_member_required
@csrf_protect
def APIIndexView(request):
  permission_classes = (permissions.DjangoModelPermissions,)
  return render(request, 'rest_framework/index.html',
                context={
                 'title': _('REST API Help'),
                  }
                )


class frepplePermissionClass(permissions.DjangoModelPermissions):
  def has_permission(self, request, view):
    self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']
    self.perms_map['OPTIONS'] = ['%(app_label)s.view_%(model_name)s']
    self.perms_map['HEAD'] = ['%(app_label)s.view_%(model_name)s']

    # match the permissions on the correct database
    request.user._state.db = request.database


    # Django is not checking if user is active or superuser on the scenario
    try:
      useract = User.objects.all().using(request.database).get(username=request.user).is_active
      request.user.is_active = useract
      usersuper = User.objects.all().using(request.database).get(username=request.user).is_superuser
      request.user.is_superuser = usersuper
    except:
      request.user.is_active = False
      request.user.is_superuser = False

    return super(frepplePermissionClass, self).has_permission(request, view)


class frePPleListCreateAPIView(ListBulkCreateUpdateDestroyAPIView):
  '''
  Customized API view for the REST framework.:
     - support for request-specific scenario database
     - add 'title' to the context of the html view
  '''

  filter_backends = (filters.DjangoFilterBackend,)
  permission_classes = (frepplePermissionClass,)


  def get_queryset(self):
    queryset = super().get_queryset().using(self.request.database)
    return queryset

  def get_serializer(self, *args, **kwargs):
    kwargs['partial'] = True
    return super().get_serializer(*args, **kwargs)

  def allow_bulk_destroy(self, qs, filtered):
    # Safety check to prevent deleting all records in the database table
    if qs.count() > filtered.count():
      return True
    # default checks if the qs was filtered
    # qs comes from self.get_queryset()
    # filtered comes from self.filter_queryset(qs)
    return False


class frePPleRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
  '''
  Customized API view for the REST framework.
     - support for request-specific scenario database
     - add 'title' to the context of the html view
  '''
  permission_classes = (frepplePermissionClass,)

  def get_queryset(self):
    if self.request.database == 'default':
      return super().get_queryset()
    else:
      return super().get_queryset().using(self.request.database)
