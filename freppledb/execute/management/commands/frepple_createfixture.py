#
# Copyright (C) 2007-2013 by frePPLe bvba
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

import warnings

from .createfixture import Command as NewCommand


class Command(NewCommand):

  help = '''
  The frepple_createfixture command is deprecated. It is renamed to createfixture.
  '''

  def handle(self, **options):
    warnings.warn("The frepple_createfixture command is renamed to createfixture", DeprecationWarning)
    super().handle(**options)

  getHTML = None
