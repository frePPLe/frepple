"""
This file demonstrates writing tests using the unittest module.

You can execute the tests with the command:
  frepplectl test freppledb.my_app
"""

from django.test import TestCase


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Complex mathematical proof.
        """
        self.assertEqual(1 + 1, 2)
