#
# Copyright (C) 2015 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from django.db import migrations


class AttributeMigration(migrations.Migration):
    """
    This migration subclass allows a migration in application X to change
    a model defined in application Y.
    This is useful to extend models in application Y with custom fields.

    By default we are extending the 'input' app. You can set extends_app_label
    in your migration subclass.
    """

    # Application in which we are extending the models.
    extends_app_label = "input"

    def __init__(self, name, app_label):
        super().__init__(name, app_label)
        self.real_app_label = app_label

    def __eq__(self, other):
        return (
            isinstance(other, AttributeMigration)
            and migrations.Migration.__eq__(self, other)
            and self.extends_app_label == other.extends_app_label
        )

    def __hash__(self):
        return hash("%s.%s.%s" % (self.app_label, self.name, self.extends_app_label))

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
