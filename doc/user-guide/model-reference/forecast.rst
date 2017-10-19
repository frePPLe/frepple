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
item             non-empty string  The item for which the forecast should be computed.
location         non-empty string  The location for which the forecast should be computed.
customer         non-empty string  The customer for which the forecast should be computed.
description      string            A description for this forecast record.
category         string            A category for this forecast record.
subcategory      string            A subcategory for this forecast record.
method           string            The forecast method to be used among following possibilities 
                                   
                                   * Automatic
                                   
                                   * Constant
                                   
                                   * Trend
                                   
                                   * Seasonal
                                   
                                   * Intermittent
                                   
                                   * Moving Average
                                   
                                   * Manual

                                   * Aggregate
priority         integer           The priority for this forecast record. Relevant if this forecast
                                   record is planned.
minshipment      number            The minimum shipment for this forecast record. Relevant if this 
                                   forecast
                                   record is planned.
maxlateness      number            The maximum lateness for this forecast record. Relevant if this                                    
                                   forecast record is planned.
discrete         boolean           Indicates whether the forecast quantity should be discrete (integer 
                                   values only),
                                   Possible values are : "TRUE" (default) or "FALSE".
planned          boolean           Indicates whether the forecasted quantity should be planned,
                                   Possible values are : "TRUE" (default) or "FALSE".                                   
================ ================= =====================================================================
