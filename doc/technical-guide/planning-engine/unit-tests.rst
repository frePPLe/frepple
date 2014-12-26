==========
Unit tests
==========

The folder *tests* contains over 50 subfolders with unit tests, and each folder
verifies the behavior of the planning engine in a specific area.

The test suite is run by the runtest.py script:

::

   runtest.py
     Run all tests.

   runtest.py --exclude not_this_test
     Run all tests, except the ones you choose to skip.

   runtest.py A B
     Run the tests A and B.

   runtest.py --debug A
     Run the test A, verbosely showing its output.

   runtest.py --help
     Print information on the script and its options.

   runtest.py --regression
     Run all tests, except the ones not suitable in a regression test.
     See the code of the script to see which tests are excluded.

You are encouraged to submit additional test cases to the test suite, wich
is used to validate each new release.
