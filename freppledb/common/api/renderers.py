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

from rest_framework.renderers import BrowsableAPIRenderer

class freppleBrowsableAPI(BrowsableAPIRenderer):
  '''
  Customized rendered for the browsable API:
    - added the 'title' variable to the context to make the breadcrumbs work
  '''
  def get_context(self, data, accepted_media_type, renderer_context):
    ctx = super(freppleBrowsableAPI, self).get_context(data, accepted_media_type, renderer_context)
    ctx['name'] = ctx['view'].serializer_class.Meta.model._meta.model_name
    if hasattr(ctx['view'], 'list'):
      ctx['title'] = "List API for %s" % ctx['name']
    else:
      ctx['title'] = "Detail API for %s" % ctx['name']
    return ctx
