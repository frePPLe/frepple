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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

r'''
An reusable application that contains common functionality of different
frePPLe data models.

The common functionality handles:
  - breadcrumbs
  - user preferences: reporting buckets, report start and end dates, report output type
  - login using the e-mail address
  - date and time bucket definition
'''

from django import template

# Make our tags built-in, so we don't have to load them any more in our
# templates with a 'load' tag.
template.add_to_builtins('common.templatetags.breadcrumbs')
