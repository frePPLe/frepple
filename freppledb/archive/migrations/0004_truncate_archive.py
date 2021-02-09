#
# Copyright (C) 2021 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.db import migrations


class Migration(migrations.Migration):
    """
    The archived inventory table is incorrect in previous releases.
    We're resetting all arhived history till now and restart.
    """

    dependencies = [("archive", "0003_permissions")]
    operations = [migrations.RunSQL("truncate ax_manager cascade")]
