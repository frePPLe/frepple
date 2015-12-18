============================
Distribution planning screen
============================

.. Important::

   This module is only available in the Enterprise Edition.

The distribution planning screen is designed for distribution-intensive 
planning problems. It provides a one-stop screen from which the user
can conveniently perform the following actions:

  - | The top section of the screen allows to filter and sort item-locations
      according to planning metrics and various attributes. 
    | Item-locations requiring attention are easily found.
    | The results can be shown in units or in monetary value, and in different
      time buckets (ie weeks, months, quarters or years).
  
  - | The bottom part has different tabs for different planning aspects.
    | Whenever a parameter is changed, you can hit the recalculate button
      to see the impact on the result.
  
  - | A first tab shows the **historical demand and the expected future forecast**.
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
       
    .. image:: ../_images/distribution-planning-forecast.png
    
    |
      
  - | A second tab shows the **planned inventory profile**.
    | Per period you can review the demand and supply. The reorder quantity
      and the safety stock are also displayed, and can be overridden in
      specific periods by the planner.
      
    | Below the plan table, the parameters affecting the inventory plan are 
      displayed. You can change the parameter values, and hit the recompute
      button to immediately see the updated inventory plan and replenishment 
      transactions.
            
    .. image:: ../_images/distribution-planning-plan.png
    
    |

  - | The third tab shows the **planned and ongoing transactions** that are
      currently ongoing or proposed by frePPLe. The list shows purchase orders, 
      incoming distribution orders and outgoing distribution orders.
      
    | Date, quantity, item and supplier can be edited for proposed transactions.
    | When one or more rows are selected, the action list becomes active which is
      used to change the status of the transaction. 
    | If the Openbravo connector app is activated, the dropdown allows the planner
      to immediately export the transaction immediately towards Openbravo. 
    
    .. image:: ../_images/distribution-planning-transactions.png
    
    |

  - | A next tab shows **free-text comments** on the item, location and 
      item-location. New comments can be added.
      
    .. image:: ../_images/distribution-planning-comments.png
    
    |


  - | The last tab shows the **editing history** of the item, location and 
      item-location.
      
    .. image:: ../_images/distribution-planning-history.png
         