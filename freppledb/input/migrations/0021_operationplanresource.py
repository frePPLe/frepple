# Copyright (C) 2017 by frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.db import migrations


class Migration(migrations.Migration):

  dependencies = [
    ('input', '0020_buffer_owner'),
  ]

  operations = [
    migrations.RunSQL(
      'alter table operationplanresource rename column resource to resource_id'
    ),
  ]
