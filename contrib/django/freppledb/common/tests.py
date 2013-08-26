#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

from django.test import TestCase

from freppledb.common.models import User, UserPreference


class DataLoadTest(TestCase):

  def setUp(self):
    # Login
    self.client.login(username='admin', password='admin')

  def test_common_parameter(self):
    response = self.client.get('/admin/common/parameter/?format=json')
    self.assertContains(response, '"records":2,')


class UserPreferenceTest(TestCase):

  def test_get_set_preferences(self):
    user = User.objects.all().get(username='admin')
    before = user.getPreference('test')
    self.assertIsNone(before)
    user.setPreference('test',{'a':1,'b':'c'})
    after = user.getPreference('test')
    self.assertEqual(after, {'a':1,'b':'c'})
