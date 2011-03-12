#
# Copyright (C) 2009 by Johan De Taeye, frePPLe bvba
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

from distutils.core import setup
from django.conf import settings

setup(name = 'freppledb',
      version = settings.FREPPLE_VERSION,
      author = "www.frepple.com",
      author_email = "info@www.frepple.com",
      url = "http://www.frepple.com",
      packages = [ 
        'freppledb', 'freppledb.common', 'freppledb.common.templatetags', 
        'freppledb.execute', 'freppledb.execute.management', 
        'freppledb.input', 'freppledb.output', 'freppledb.output.views', 
        ],
      package_dir = {'freppledb': 'freppledb'},
      package_data = {'freppledb': [
         'common/fixtures/*', 'input/fixtures/*', 
         'locale/*/*/*', 'static/*', 'execute/*.xml', 
         'templates/*.*', 'templates/*/*'
         ]},
      options = { "install" : {'optimize': 2}},
      classifiers = [
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Intended Audience :: Manufacturing',
        'Framework :: Django',        
        ],
      description = "Free Production Planning Library",
      long_description = '''FrePPLe stands for "Free Production Planning Library".
It is a framework for modeling and solving production planning problems,
targeted primarily at discrete manufacturing industries.
'''
      )
