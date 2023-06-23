=================
Forecast measures
=================

Forecast measures define numeric value that are stored for specified item + location + customer +
time bucket combinations.

FrePPLe provides a number of standard measures. With this table you can add project-specific
values to manage more complex demand forecasting processes and workflows.

The measures are visible and editable in the :doc:`../user-interface/plan-analysis/forecast-editor`,
:doc:`../user-interface/plan-analysis/forecast-report` and
:doc:`../user-interface/plan-analysis/inventory-planning`.

  .. Important::

     After any change to this table, you should regenerate the plan to assure the planning engine
     works with the latest definitions of the measures.

In addition to the measures you define in this table, the forecasting engine uses a number
of standard measures.

* | Calculation of the statistical forecast:
  | This process uses as input historical demand, which is read from the sum of "orderstotal" and
    "ordersadjustment" measures.
  | The statistical forecast populated in the measure "forecastbaseline".

* | Calculation of the forecast consumption:
  | This process reads as input the measure "forecasttotal", and all open sales orders will consume
    from this gross forecast. By default "forecasttotal" is computed as
    "if(forecastoverride == -1, forecastbaseline, forecastoverride)", but you can easily use a
    different formula.
  | The output is populated in the "forecastnet" and "forecastconsumed" measures.

* | Calculation of the supply planning:
  | This process considers the measure "forecastnet" as the remaining sales forecast to plan.
  | The outputs of the process goes in many tables, and also populates the measures "forecastplanned"
    and "ordersplanned".

=================== ================= =====================================================================
Field               Type              Description
=================== ================= =====================================================================
name                non-empty string  | A unique name.
                                      | The measure data are stored using this key in the database. Only
                                        alfanumeric characters are allowed.
label               string            The string used in the user interface. This will be translated
                                      automatically to the language configured in your browser.
description         string            Free text description.
type                string            Define the storage and calculation behavior this measure.

                                      * | **Aggregate**
                                        | At higher levels of the item, location, customer and time
                                          hierarchies the value of this measure is computed as the sum of all
                                          children.
                                        | Edits at higher levels are disaggregated to all children,
                                          proportional to the existing value of each child.
                                        | Examples: total sales, total sales value...

                                      * | **Local**
                                        | The value of such measures is only valid at the item, location,
                                          customer and time period where it is defined.
                                        | Examples: cost, price, margin...

                                      * | **Computed (beta-state)**
                                        | The value of these measures is computed with the expression
                                          specified in the compute-expression field.
                                        | Examples: forecasttotalvalue = forecasttotal * cost

mode_past           string            Visibility and editability policy for the current and past time
                                      periods.

                                      * Edit: Read and write access

                                      * View: Read-only access.

                                      * Hide: Don't allow user to display the value.

mode_future         string            Visibility and editability policy for the current and
                                      future time periods.

                                      * Edit: Read and write access

                                      * View: Read-only access.

                                      * Hide: Don't allow user to display the value.

formatter           string            Controls how the values should be displayed.

                                      Accepted values are "number" (default) and "currency".

discrete            bool              Specifies whether fractional numbers are acceptable for this measure
                                      or not.

defaultvalue        number            Specifies the value for the measure when it is left unspecified
                                      for a certain item + location + customer + time bucket combinations.

                                      0 is the default value.

                                      If the default value is -1, unspecified cells will display as an
                                      empty cell.

compute expression       string       For computed measures, this expression defines how the value is
                                      computed.

                                      The expression can use the following:

                                      * All standard and custom measures

                                      * All item attribute with a function call:
                                        item("myattribute")

                                      * All location attributes with a function call:
                                        location("myattribute")

                                      * All customer attributes with a function call:
                                        customer("myattribute")

                                      * Mathematical operators: +, -, \*, /, %, ^

                                      * Equality & Inequality operators: =, ==, <>, !=, <, <=, >, >=

                                      * Logic operators: and, mand, mor, nand, nor, not, or, shl, shr,
                                        xnor, xor, true, false

                                      * Mathematical functions: abs, avg, ceil, clamp, equal, exp, floor,
                                        frac,  log, log10, log2, logn,  max,  min,  mul,  ncdf,  nequal,
                                        root, round, roundn, sgn, sqrt, sum, swap, trunc

                                      * Control structures: if-then-else, ternary conditional, switch-case

                                      Here are some concrete examples:

                                      * round(forecastoveride * item("cost"))

                                      * if(forecastoveride != -1, forecastoverride, forecastbaseline)

                                      * if (x, y, z)

                                      * if (x > y) z; else w;

                                      * if (x > y) z; else if (w != u) v; else a;

                                      * x ? y : z

                                      * switch {
                                        case x: y;
                                        case a: b;
                                        default: i
                                        }

update expression   string            This expression is evaluated when the computed measure is updated
                                      by the user.

                                      It will use assignments to update the the measures used in the
                                      compute-expression. The variable newvalue is populated with the new
                                      value provided by the user.

                                      An example shows how the update expression basically inverses the
                                      compute expression:

                                      - compute expression:  forecastoverride * cost

                                      - update expression:   forecastoveride := newvalue / cost

=================== ================= =====================================================================
