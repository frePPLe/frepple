#
# Copyright (C) 2015 by frePPLe bvba
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

# This setup script is used to build a Python extension for the frePPLe library.
# The script is intended to be called ONLY from the makefile, and not as standalone command.

from distutils.core import setup, Extension
import os

mod = Extension(
  'frepple',
  sources=['pythonextension.cpp'],
  include_dirs=["../include"],
  define_macros=[("HAVE_LOCALTIME_R","1")],
  libraries=['frepple', 'xerces-c'],
  extra_compile_args=['-std=c++0x'],
  library_dirs=[os.environ['LIB_DIR']]
  )

setup (
  name = 'frepple',
  version = os.environ['VERSION'],
  author = "frepple.com",
  author_email = "info@frepple.com",
  url = "http://frepple.com",
  ext_modules = [mod],
  license="GNU Affero General Public License (AGPL)",
  classifiers = [
    'License :: OSI Approved :: GNU Affero General Public License (AGPL)',
    'Intended Audience :: Manufacturing',
    ],
  description = 'Bindings for the frePPLe production planning application',
  long_description = '''FrePPLe stands for "Free Production Planning Library".
It is a framework for modeling and solving production planning problems,
targeted primarily at discrete manufacturing industries.
'''
  )
