========
Forecast
========

This table allows to specify the item/location/customer combinations for which forecast should be computed.

**Fields**

================ ================= =====================================================================
Field            Type              Description
================ ================= =====================================================================
name             non-empty string  A unique name for this forecast record. We recommend 
                                   "Item - Location - Customer" E.g : "keyboard - factory1 - Google"
item             non-empty string  The item to which the forecast applies.
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
================ ================= =====================================================================
