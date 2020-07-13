=========================
Inventory planning screen
=========================

.. Important::

   This module is only available in the Enterprise Edition.

The inventory planning screen allows the management of the inventory policies
at the decoupling points in the supply chain.

It provides a one-stop screen from which the user can conveniently perform
the following actions:

- | The top section of the screen allows to filter and sort item-locations
    according to planning metrics and various attributes.
  | Item-locations requiring attention are easily found.
  | The results can be shown in units or in monetary value, and in different
    time buckets (ie weeks, months, quarters or years).

- | The bottom part has different tabs for different planning aspects.
  | Whenever a parameter is changed, you can hit the recalculate button
    to see the impact on the plan.

- A first tab show various **attributes and properties** of the selected 
  item-location combination:
  
  - Item attributes, including its cost, category, demand pattern and
    the sales metrics over the last 6 and 12 months.
    
  - Top 5 customers of the item at this location.
  
  - Location attributes.
  
  - | Details on the inventory status.
    | A bar chart shows the safety stock plus the replenishment quantity, 
      with two indicators to compare the inventory with this expected range.
    | The arrow on the right shows today's current stock level.
    | The arrow on the left shows the expected stock level one lead time from
      today.
    | The lowest of both inventory positions is used to compute the inventory
      status of the item-location.
 
  - Overview of the inventory and activity within the lead time of this
    at other locations in the network. This also includes the status of
    successor and predecessor parts.
    
  - | Summary of the replenishment methods, their lead time and size 
      constraints and effectivity.
    | The replenishment method can refer to production operations,
      distribution warehouses to transport from or suppliers to buy from.
   
  .. image:: ../_images/inventory-planning-attributes.png

  |
  
- | A second tab shows the **historical demand and the expected future forecast**.
  | The demand history in the past periods can be adjusted to remove
    exceptional demand outliers. Note that the adjustment is *added* to
    the actual history.

  | The predicted forecast for the future periods can be adjusted if the
    planner has more information on the expected sales. Note the the
    manually entered forecast *overrides* the computed value completely.

  | Below the forecast table, the planner can choose the forecast method for the
    item-location, and review the expected forecast error (evaluated using
    symmetric mean percentage error, aka SMAPE). After hitting the recompute
    button you can immediately see the updated forecast, inventory plan and
    replenishment transactions.
  | See the documentation of the inventory planning module to understand each
    parameter.

  .. image:: ../_images/inventory-planning-forecast.png

  |

- | A third tab shows the **planned inventory profile**.
  | Per period you can review the demand and supply. The reorder quantity
    and the safety stock are also displayed, and can be overridden in
    specific periods by the planner.

  | Below the plan table, the parameters affecting the inventory plan are
    displayed. You can change the parameter values, and hit the recompute
    button to immediately see the updated inventory plan and replenishment
    transactions.

  | When inventory planning parameters are highlighted with an exclamation
    triangle, it means that the value was set by a business rule.
 
  .. image:: ../_images/inventory-planning-plan.png

  |

- | The fourth tab shows the **planned and ongoing transactions** that are
    currently ongoing or proposed by frePPLe. The list shows purchase orders,
    incoming distribution orders, outgoing distribution orders and open 
    sales orders.

  | Date, quantity, item and supplier can be edited for proposed transactions.
  | When one or more rows are selected, the action list becomes active which is
    used to change the status of the transaction.
  | If the Openbravo or Odoo connector app is activated, the dropdown allows 
    the planner to immediately export the transaction immediately towards 
    the ERP system.

  .. image:: ../_images/inventory-planning-transactions.png

  |

- | A next tab shows **free-text comments** on the item, location and
    item-location. New comments can be added.

  .. image:: ../_images/inventory-planning-comments.png

  |


- | The last tab shows the **editing history** of the item, location and
    item-location.

  .. image:: ../_images/inventory-planning-history.png
