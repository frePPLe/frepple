#
# Copyright (C) 2015 by frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
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
