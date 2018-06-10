==============
Business rules
==============

Business rules are used to apply an inventory policy to a segment or to be more accurate to all item-locations belonging to a given segment.
Multiple business rules can be applied to a segment.
Note that it is not mandatory to apply a business rule to a segment if that segment has been created for filtering purpose.
The available possible business rules are divided into two categories, 
the business rules having an impact on the safety stock and the business rules having an impact on the ROQ.

*  |  Business rules having an impact on the **safety stock**:

   |  **Service Level** : The minimum service level to apply to the collection of item-locations belonging to the segment. 
      The value for that business rule should be a number between 0 and 100 (95 means 95% of service level).

   |  **Safety Stock Minimum Quantity** : The minimum safety stock quantity.

   |  **Safety Stock Maximum Quantity** : The maximum safety stock quantity.

   |  **Safety Stock Minimum Period of Cover (days)** : The minimum period of cover expressed in days.
      If the value of this business rule is 90 then the safety stock cannot be less than 90 days of forecast.

   |  **Safety Stock Maximum Period of Cover** : The maximum period of cover expressed in days.
      If the value of this business rule is 90 then the safety stock cannot be more than 90 days of forecast.

*  |  Business rules having an impact on the **ROQ**:

   |  **ROQ Minimum Quantity** : The minimum ROQ quantity.

   |  **ROQ Maximum Quantity** : The maximum ROQ quantity.

   |  **ROQ Minimum Period of Cover** : The minimum period of cover expressed in days.
      If the value of this business rule is 90 then the ROQ cannot be less than 90 days of forecast.

   |  **ROQ Maximum Period of Cover** : The maximum period of cover expressed in days.
      If the value of this business rule is 90 then the ROQ cannot be more than 90 days of forecast.
      
In this example, we created three business rules :

*  |  Safety Stock Maximum Period of Cover: This business rule applies to segment *Expensive parts in Brussels* and makes sure that no more than 90 days of forecast will be used as safety stock for these item-locations.

*  |  Service Level : This business rule applies to segment *Cheap parts in Paris* and forces an fill rate of at least 98% for these parts.

*  |  ROQ Minimum Period of Cover : This business rule applies to segment *All parts in RDC* and makes sure that a minimum of 90 days of forecast is ordered when replenishing from the supplier.
      
        
