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
   resources and by planning manufacturing orders adjacent to others
   requiring the same setup.
   
A setup matrix defines the time and cost of setup conversions on a resource.
A setup matrix contains a list of rules that define the changeover cost and duration.

To compute the time of a changeover the algorithm will evaluate all rules in
sequence (in order of priority). As soon as a matching rule is found, it is
applied and subsequent rules are not evaluated. If no matching rule is found,
that changeover is not allowed.

For a rule to match a changeover between we construct a regular expression
'<rule from> to <rule to>'. This rule is applicable a changeover 'A to B' if this
string matches the regular expression of that rule.
See https://www.debuggex.com/cheatsheet/regex/javascript for a quick cheat sheet
with all regular expression capabilities. FrePPLe uses the javascript / ecmascript
grammar for regular expressions.

Here is a example setup matrix to illustrate the matching:

========== =============== ============== ==========  =====
Priority   From            To             Duration    Cost
========== =============== ============== ==========  =====
1          light(.*)       \\1            0           10
2          .\*red          .\*red         0           10
3          .\*green        .\*red         1 day       50
4          .\*green                       2 day       50
5          [yellow|blue]   black          2 day       50
6          .*              .*             3 day       50
========== =============== ============== ==========  =====

Based on this matrix:

- | A change from 'lightgreen' to 'green' takes no time, but costs 10.
  | Rule 1 applies: \\1 in the to-setup references the (.*) capturing
    group.
 
- | A change from 'lightgreen' to 'red' takes 1 day and costs 50.
  | Rule 3 applies.
  | Rule 1 doesn't apply because the (.*) capturing group doesn't match
    the reference \\1.

- | A change from 'green' to 'black' takes 2 days and costs 50.
  | Rule 4 applies.

- | A change from 'blue' to 'black' takes 2 days and costs 50.
  | Rule 5 applies.

- | A change from 'red' to 'black' takes 3 days and costs 50.
  | Rule 5 applies.
  | Without rule 6 this changeover would not be allowed.
  
- | A change from 'red' to 'red' takes 0 time and costs nothing.
  | When the from and to setup are identical we simply don't evaluate any
    of the rules.

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
tosetup      string            | The new setup.
                               | If the field is empty the rules applies to any new
                                 setup value.
duration     timeperiod        Duration of the changeover.
resource     resource          | Resource required the changeover.
                               | Only unconstrained resources can be assigned
                                 during a changeover.
cost         double            Cost of the changeover.
============ ================= ===========================================================
