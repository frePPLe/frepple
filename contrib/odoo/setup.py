#!/usr/bin/python3
#
# Copyright (C) 2014 by frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


from distutils.core import setup

setup(
  name = 'frePPLe',
  description = 'odoo extension module for frePPLe',
  url = 'http://frepple.com',
  author = 'frePPLe bvba',
  author_email = 'jdetaeye@frepple.com',
  version = '4.0',
  packages = ['addons.frepple','addons.frepple.controllers'],
  data_files = [
     ('addons/frepple', ['addons/frepple/frepple_data.xml']),
     ('addons/frepple/static/src/img', ['addons/frepple/static/src/img/icon.png'])
     ]
  )
