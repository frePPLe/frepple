#
# Copyright (C) 2018 by frePPLe bvba
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
    ('input', '0034_sizemaximum'),
  ]

  operations = [

    migrations.RunSQL(
      '''
      insert into common_parameter (name, value, lastmodified, description)
      values (
        'WIP.consume_material', 'true', now(),
        'Determines whether confirmed manufacturing orders and distribution orders consume material or not. Default is true.'
        )
      on conflict (name) do nothing
      ''',
	  '''
	  delete from parameter where name = 'WIP.consume_material'
	  '''
      ),
    migrations.RunSQL(
      '''
      insert into common_parameter (name, value, lastmodified, description)
      values (
        'WIP.consume_capacity', 'true', now(),
        'Determines whether confirmed manufacturing orders, purchase orders and distribution orders consume capacity or not. Default is true.'
        )
      on conflict (name) do nothing
      ''',
	  '''
	  delete from parameter where name = 'WIP.consume_capacity'
	  '''
      ),	  
  ]
