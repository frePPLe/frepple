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

from django.db import migrations


class AttributeMigration(migrations.Migration):
  '''
  This migration subclass allows a migration in application X to change
  a model defined in application Y.
  This is useful to extend models in application Y with custom fields.

  By default we are extending the 'input' app. You can set extends_app_label
  in your migration subclass.
  '''

  # Application in which we are extending the models.
  extends_app_label = 'input'

  def __init__(self, name, app_label):
    super().__init__(name, app_label)
    self.real_app_label = app_label

  def mutate_state(self, project_state, preserve=True):
    self.app_label = self.extends_app_label
    state = super().mutate_state(project_state, preserve)
    self.app_label = self.real_app_label
    return state

  def apply(self, project_state, schema_editor, collect_sql=False):
    self.app_label = self.extends_app_label
    state = super().apply(project_state, schema_editor, collect_sql)
    self.app_label = self.real_app_label
    return state

  def unapply(self, project_state, schema_editor, collect_sql=False):
    self.app_label = self.extends_app_label
    state = super().unapply(project_state, schema_editor, collect_sql)
    self.app_label = self.real_app_label
    return state
