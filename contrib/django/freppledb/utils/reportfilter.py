#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$
# email : jdetaeye@users.sourceforge.net


from django.utils.translation import ugettext as _
from django.utils.html import escape
from django.utils.text import capfirst


IntegerOperator = {
  'lte': '&lt;=',
  'gte': '&gt;=',
  'lt': '&lt;&nbsp;',
  'gt': '&gt;&nbsp;',
  'exact': '==',
  }
TextOperator = {
  'icontains': 'i in',
  'contains': 'in',
  'istartswith': 'i starts',
  'startswith': 'starts',
  'iendswith': 'i ends',
  'endswith': 'ends',
  'iexact': 'i is',
  'exact': 'is',
  }


def _create_rowheader(req, sort, cls):
  '''
  Generate html header row for the columns of a table or list report.
  '''
  result = ['<form>']
  number = 0
  args = req.GET.copy()
  args2 = req.GET.copy()

  # When we update the filter, we always want to see page 1 again
  if 'p'in args2: del args2['p']

  # A header cell for each row
  for row in cls.rows:
    number = number + 1
    title = capfirst(escape((row[1].has_key('title') and row[1]['title']) or row[0]))
    if not row[1].has_key('sort') or row[1]['sort']:
      # Sorting is allowed
      if int(sort[0]) == number:
        if sort[1] == 'a':
          # Currently sorting in ascending order on this column
          args['o'] = '%dd' % number
          y = 'class="sorted ascending"'
        else:
          # Currently sorting in descending order on this column
          args['o'] = '%da' % number
          y = 'class="sorted descending"'
      else:
        # Sorted on another column
        args['o'] = '%da' % number
        y = ''
      # Which widget to use
      if 'filter' in row[1]:
        # Filtering allowed
        result.append( '<th %s><a href="%s?%s">%s</a><br/>%s</th>' \
          % (y, escape(req.path), escape(args.urlencode()),
             title, row[1]['filter'].output(row, number, args)
             ) )
        rowfield = row[1]['filter'].field or row[0]
      else:
        # No filtering allowed
        result.append( '<th %s><a href="%s?%s">%s</a></th>' \
          % (y, escape(req.path), escape(args.urlencode()), title) )
        rowfield = row[0]
      for i in args:
        field, sep, operator = i.rpartition('__')
        if (field or operator) == rowfield and i in args2: del args2[i]
    else:
      # No sorting is allowed on this field
      # If there is no sorting allowed, then there is also no filtering
      result.append( '<th>%s</th>' % title )

  # Extra hidden fields for query parameters that aren't rows
  for key in args2:
    result.append( '<th><input type="hidden" name="%s" value="%s"/>' % (key, args2[key]))

  # 'Go' button
  result.append( '<th><input type="submit" value="Go" tabindex="1100"/></th></form>' )
  return '\n'.join(result)


class FilterText(object):
  def __init__(self, operator="icontains", field=None, size=10):
    self.operator = operator
    self.field = field
    self.size = size

  def output(self, row, number, args):
    global TextOperator
    rowfield = self.field or row[0]
    res = []
    for i in args:
      try:
        field, sep, operator = i.rpartition('__')
        if field == '':
          field = operator
          operator = 'exact'
        if field == rowfield:
          res.append('<span id="%d">%s</span><input type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
            % (number+1000, TextOperator[operator], self.size,
               escape(args.get(i)),
               rowfield, operator, number+1000,
               ))
      except:
        # Silently ignore invalid filters
        pass
    if len(res) > 0:
      return '<br/>'.join(res)
    else:
      return '<span id="%d">%s</span><input type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
          % (number+1000, TextOperator[self.operator], self.size,
             escape(args.get("%s__%s" % (rowfield,self.operator),'')),
             rowfield, self.operator, number+1000,
             )


class FilterNumber(object):
  def __init__(self, operator="lt", field=None, size=9):
    self.operator = operator
    self.field = field
    self.size = size

  def output(self, row, number, args):
    global IntegerOperator
    res = []
    rowfield = self.field or row[0]
    for i in args:
      try:
        # Skip empty filters
        if args.get(i) == '': continue
        # Determine field and operator
        field, sep, operator = i.rpartition('__')
        if field == '':
          field = operator
          operator = 'exact'
        if field == rowfield:
          res.append('<span id="b" oncontextmenu="ole(event)">%s</span><input id="olie" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
            % (IntegerOperator[operator],
               self.size,
               escape(args.get(i)),
               rowfield, operator, number+1000,
               ))
      except:
        # Silently ignore invalid filters
        pass
    if len(res) > 0:
      return '<br/>'.join(res)
    else:
      return '<span id="a" oncontextmenu="ole(event)">%s</span><input id="olie" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
          % (IntegerOperator[self.operator], self.size,
             escape(args.get("%s__%s" % (rowfield,self.operator),'')),
             rowfield, self.operator, number+1000,
             )


class FilterDate(object):
  def __init__(self, operator="lt", field=None, size=9):
    self.operator = operator
    self.field = field
    self.size = size

  def output(self, row, number, args):
    global IntegerOperator
    res = []
    rowfield = self.field or row[0]
    for i in args:
      try:
        # Skip empty filters
        if args.get(i) == '': continue
        # Determine field and operator
        field, sep, operator = i.rpartition('__')
        if field == '':
          field = operator
          operator = 'exact'
        if field == rowfield:
          res.append('<span id="b" oncontextmenu="ole(event)">%s</span><input class="vDateField" id="olie" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
            % (IntegerOperator[operator],
               self.size,
               escape(args.get(i)),
               rowfield, operator, number+1000,
               ))
      except:
        # Silently ignore invalid filters
        pass
    if len(res) > 0:
      return '<br/>'.join(res)
    else:
      return '<span id="a" oncontextmenu="ole(event)">%s</span><input class="vDateField" id="olie" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
          % (IntegerOperator[self.operator], self.size,
             escape(args.get("%s__%s" % (rowfield,self.operator),'')),
             rowfield, self.operator, number+1000,
             )


class FilterChoice(object):
  def __init__(self, field=None, choices=None):
    self.field = field
    self.choices = choices

  def output(self, row, number, args):
    rowfield = self.field or row[0]
    value = args.get(rowfield, None)
    result = ['<select name="%s"> <option value="">%s</option>' \
      % (rowfield, _('All')) ]
    for code, label in self.choices:
      if code != '':
        if (code == value):
          result.append('<option value="%s" selected="yes">%s</option>' % (code, unicode(label)))
        else:
          result.append('<option value="%s">%s</option>' % (code, unicode(label)))
    result.append('</select>')
    return ' '.join(result)


class FilterBool(FilterChoice):
  def __init__(self, field=None):
    super(FilterBool, self).__init__(
      field=field,
      choices=( ('0',_('False')), ('1',_('True')), ),
      )
