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


from xml.sax.saxutils import escape

IntegerOperator = {
  'lte': '&lt;=',
  'gte': '&gt;=',
  'lt': '&lt;&nbsp;',
  'gt': '&gt;&nbsp;',
  'exact': 'exact',
  }
TextOperator = {
  'icontains': 'icontains',
  'contains': 'contains',
  'startswith': 'startswith',
  'endswith': 'endswith',
  'exact': 'exact',
  }

def _create_rowheader(req, sort, cls):
  '''
  Generate html header row for the columns of a table or list report.
  '''
  result = ['<form>']
  number = 0
  args = req.GET.copy()
  args2 = req.GET.copy()

  # A header cell for each row
  for row in cls.rows:
    number = number + 1
    title = unicode((row[1].has_key('title') and row[1]['title']) or row[0])
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
      widget = ('filter_widget' in row[1] and row[1]['filter_widget']) or FilterText
      if 'filter' in row[1] or 'filter_widget' in row[1]:
        result.append( '<th %s><a href="%s?%s">%s%s</a><br/>%s</th>' \
          % (y, req.path, escape(args.urlencode()),
             title[0].upper(), title[1:],
             widget.output(row, number, args)
             ) )
        #for i in args:
        #  field, sep, operator = i.rpartition('__')
        #  if field == row[1]['filter'] and i in args2: del args2[i]
        if cls.rows[number-1][1]['filter'] in args2: del args2[cls.rows[number-1][1]['filter']]
      else:
        result.append( '<th %s style="vertical-align:top"><a href="%s?%s">%s%s</a></th>' \
          % (y, req.path, escape(args.urlencode()),
             title[0].upper(), title[1:],
            ) )
        #for i in args:
        #  field, sep, operator = i.rpartition('__')
        #  if field == row[0] and i in args2: del args2[i]
        if row[0] in args2: del args2[row[0]]
    else:
      # No sorting is allowed on this field
      result.append( '<th style="vertical-align:top">%s%s</th>' \
          % (title[0].upper(), title[1:]) )

  # Extra hidden fields for query parameters that aren't rows
  for key in args2:
    result.append( '<th><input type="hidden" name="%s" value="%s"/>' % (key, args[key]))

  # 'Go' button
  result.append( '<th><input type="submit" value="Go" tabindex="1100"/></th></form>' )
  return '\n'.join(result)


class FilterText:
  @classmethod
  def output(cls, row, number, args):
    global TextOperator
    return '<input type="text" size="%d" value="%s" name="%s" tabindex="%d"/>' \
          % ((row[1].has_key('filter_size') and row[1]['filter_size']) or 10,
             args.get(row[1]['filter'],''),
             row[1]['filter'], number+1000,
             )


#class FilterInteger:
#  @classmethod
#  def output(cls, row, number, args):
#    global IntegerOperator
#    res = []
#    rowfield = (row[1].has_key('filter') and row[1]['filter']) or row[0]
#    for i  in args:
#      field, sep, operator = i.rpartition('__')
#      if field == rowfield:
#        res.append('<span id="b" oncontextmenu="ole(event)">&gt;</span><input id="olie" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
#          % (IntegerOperator[operator],
#             (row[1].has_key('filter_size') and row[1]['filter_size']) or 9,
#             args.get(i), #row[1]['filter'],''),
#             rowfield, operator, number+1000,
#             ))
#    if len(res) > 0:
#      return '<br/>'.join(res)
#    else:
#      return '<span id="a" oncontextmenu="ole(event)">&gt;</span><input id="olie" type="text" size="%d" value="%s" name="%s" tabindex="%d"/>' \
#          % ((row[1].has_key('filter_size') and row[1]['filter_size']) or 9,
#             args.get(row[1]['filter'],''),
#             row[1]['filter'], number+1000,
#             )
