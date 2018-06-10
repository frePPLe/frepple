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
from freppledb.common.auth import getWebserviceAuthorization


@staff_member_required
@csrf_protect
def APIIndexView(request):
  try:
    exp = int(request.GET.get("exp", '3'))
  except:
    exp = 3
  if exp > 7:
    exp = 7
  return render(
    request,
    'rest_framework/index.html',
    context={
      'exp': exp,
      'request': request,
      'title': _('REST API Help'),
      'token': getWebserviceAuthorization(user=request.user.username, exp=exp * 86400)
      }
    )


class frepplePermissionClass(permissions.DjangoModelPermissions):
  def has_permission(self, request, view):
    self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']
    self.perms_map['OPTIONS'] = ['%(app_label)s.view_%(model_name)s']
    self.perms_map['HEAD'] = ['%(app_label)s.view_%(model_name)s']

    # match the permissions on the correct database
    if not hasattr(request.user, '_state'):
      return False
    request.user._state.db = request.database

    # Django is not checking if user is active or superuser on the scenario
    try:
      thisuser = User.objects.all().using(request.database).get(username=request.user)
      request.user.is_active = thisuser.is_active
      request.user.is_superuser = thisuser.is_superuser
    except Exception:
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
