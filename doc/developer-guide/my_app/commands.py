"""
This file implements custom plan calculation steps.
"""
import os
import time

from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext as _

from freppledb.common.commands import PlanTaskRegistry, PlanTask


@PlanTaskRegistry.register
class MyCalculation(PlanTask):
    description = "My customized planning step"

    # Defines when the task should be executed
    sequence = 51

    label = ("myapp", _("My own calculations"))

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if "myapp" in os.environ:
            # Defines the relative duration of this task.
            return 1
        else:
            # Skip this step
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        print("Starting incredibly complex calculation")
        time.sleep(20)
        print("Finished incredibly complex calculation")
