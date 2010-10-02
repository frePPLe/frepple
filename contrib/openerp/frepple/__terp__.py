# -*- encoding: utf-8 -*-
#
# Copyright (C) 2010 by Johan De Taeye
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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

{
    "name" : "Advanced Planning and Scheduling Module",
    "version" : "1.0",
    "author" : "frePPLe",
    "website" : "http://www.frepple.com",
    "category" : "Generic Modules/Production",
    "depends" : ["mrp"],
    "license" : "Other OSI approved licence",
    "description": """
    This module performs constrained planning scheduling with frePPLe.
    """,
    "init_xml": [],
    "update_xml": [
      'frepple_data.xml',
      'frepple_view.xml',
      'ir.model.access.csv',
      ],
    "demo_xml": [],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
