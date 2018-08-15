==============
Setup matrices
==============

.. important::

   This planning algorithm in the **Community Edition** respects
   the setup matrices, but does NOT do any effort to reduce the setup
   times and does NOT have all logic to handle the complexities of 
   propagating setup changes. Your mileage will vary.
   
   In the **Enterprise Edition** the more advanced solver will reduce the
   setup times by choosing smartly among different available alternate
   resources and by planning operationplans adjacent to others requiring
   the same setup.
   
A setup matrix defines the time and cost of setup conversions on a resource.
Within a setup matrix rules are used to define the changeover cost and
duration.

To compute the time of a changeover the algorithm will evaluate all rules in
sequence (in order of priority). For a rule to match the changeover between
theoriginal setup X to a new setup Y, two conditions need to be fulfilled:

* | The original setup X must match with the fromsetup of the rule.
  | If the fromsetup field is empty, it is considered a match.
* | The new setup Y must match with the tosetup of the rule.
  | If the tosetup field is empty, it is considered a match.

The wildcard characters \* and ? can be used in the fromsetup and tosetup
fields. As soon as a matching rule is found, it is applied and subsequent
rules are not evaluated. If no matching rule is found, the changeover is
not allowed.

For instance, consider a setup matrix with the following rules:

========== ======= ======= ==========  =====
Priority   From    To      Duration    Cost
========== ======= ======= ==========  =====
1          \*green \*green 0           10
2          \*red   \*red   0           10
3          \*green \*red   1 day       50
4          \*green         2 day       50
5                          3 day       50
========== ======= ======= ==========  =====

Based on this matrix:

- A change from 'lightgreen' to 'darkgreen' takes no time, but costs 10.
  Rule 1 applies.

- A change from 'green' to 'black' takes 2 days and costs 50. Rule 4 applies.

- | A change from 'red' to 'black' takes 3 days and costs 50. Rule 5 applies.
  | Without rule 5 this changeover would not be allowed.

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  | Unique name of the setup matrix.
                               | This is the key field and a required attribute.
rules        list of setup     A read-only list of rules in this matrix.
             matrix rules
============ ================= ===========================================================

Setup rule
----------

Within a setup matrix rules are used to define the changeover cost and duration.

The rules are evaluated in sequence, starting with the lowest priority number.

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
priority     integer           | The priority of the rule.
                               | This is the key field.
fromsetup    string            | The previous setup.
                               | If the field is empty the rules applies to any previous
                                 setup value.

                               Wildcard characters are allowed in this string: \* matches
                               a sequence of characters, and ? matches a single character.

tosetup      string            | The new setup.
                               | If the field is empty the rules applies to any new
                                 setup value.
                               | Wildcard characters are allowed in this string, similar
                                 as in the fromsetup field.
duration     timeperiod        Duration of the changeover.
cost         double            Cost of the changeover.
============ ================= ===========================================================
