#
# Copyright (C) 2013 by Johan De Taeye, frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.template import Library, Node, TemplateSyntaxError


register = Library()

#
# Tags related to jqgrid.
#
# These tags depend on the following context variables:
#  - reportclass
#  - is_popup
#  - preferences
#

class ColModelNode(Node):
  r'''
  A tag to return colmod.
  '''
  def __init__(self, frozen = False):
    self.frozen = frozen

  def render(self, context):
    try:
      reportclass = context['reportclass']
      is_popup = context['is_popup']
      prefs = context['preferences']
      if not prefs:
        frozencolumns = (self.frozen and 10000) or reportclass.frozenColumns
        prefs = [ (i,False,reportclass.rows[i].width) for i in range(len(reportclass.rows)) ]
      else:
        frozencolumns = (self.frozen and 10000) or prefs.get('frozen', reportclass.frozenColumns)
        prefs = prefs['rows']
      result = []
      if is_popup:
        result.append("{name:'select',label:gettext('Select'),width:75,align:'center',sortable:false,search:false}")
      count = -1
      for (index, hidden, width) in prefs:
        count += 1
        result.append(u"{%s,width:%s,counter:%d%s%s%s,searchoptions:{searchhidden: true}}" % (
           reportclass.rows[index], width, index,
           count < frozencolumns and ',frozen:true' or '',
           is_popup and ',popup:true' or '',
           hidden and ',hidden:true' or ''
           ))
      return ',\n'.join(result)
    except:
      return ''  # Silently fail

  def __repr__(self):
    return "<colmodel Node>"

def colModel(parser, token):
  tokens = token.contents.split()
  l = len(tokens)
  if l == 1:
    return ColModelNode()
  elif l == 2 and tokens[1] == 'False':
    return ColModelNode(False)
  elif l == 2 and tokens[1] == 'True':
    return ColModelNode(True)
  else:
    raise TemplateSyntaxError, "'%s' accepts only 'True' or 'False' as optional argument" % tokens[0]
  return ColModelNode()

colModel.is_safe = True
register.tag('colmodel', colModel)