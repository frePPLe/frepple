========
Forecast
========

This table specifies the lowest level item/location/customer combinations for which 
forecast data is maintained and/or a statistical forecast is to be computed.

Note that higher levels in the hierarchy don't need to be inserted in this table.

================ ================= =====================================================================
Field            Type              Description
================ ================= =====================================================================
name             non-empty string  A unique name for this forecast record. We recommend 
                                   "Item - Location - Customer" E.g : "keyboard - factory1 - Google"
item             non-empty string  The item to which the forecast applies.
batch            string            | Blank/unused for make-to-stock items.
                                   | For make-to-order items, it identifies the material
                                     batch that can be used to satisfy the demand. This field
                                     can be set to the forecast name (true make-to-order
                                     production), or it can be set an item attribute (eg color
                                     of the item).
location         non-empty string  The location to which the forecast applies.
customer         non-empty string  The customer to which the forecast applies.
description      string            A description for this forecast record.
category         string            A category for this forecast record.
subcategory      string            A subcategory for this forecast record.
method           string            The forecast method to be used among following possibilities 
                                   
                                   * Automatic (default value)
                                   
                                   * Constant
                                   
                                   * Trend
                                   
                                   * Seasonal
                                   
                                   * Intermittent
                                   
                                   * Moving Average
                                   
                                   * Manual

                                   * Aggregate
priority         integer           | The priority for this forecast record.
                                   | Used only if this forecast is planned.
minshipment      number            | The minimum shipment for this forecast record.
                                   | Used only if this forecast is planned.
maxlateness      number            | The maximum allowed delivery delay for this forecast record.
                                   | Used only if this forecast is planned.
                                   | The default value allows a delay of 5 years.
discrete         boolean           | Indicates whether the forecast quantity should be discrete 
                                     (integer values only).
                                   | Possible values are : "TRUE" (default) or "FALSE".
planned          boolean           | Indicates whether the forecasted quantity should be planned.
                                   | Possible values are : "TRUE" (default) or "FALSE".                
operation        string            | Operation to be used to satisfy the forecast.
                                   | When left unspecified, frePPLe will automatically create
                                     a delivery operation for the item and location combination.                                     
================ ================= =====================================================================
