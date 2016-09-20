========
Forecast
========

Any item/location/customer combination you wish frepple to compute the forecast for should be declared in this table.

.. rubric:: Key Fields

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             non-empty string  A unique name for this forecast record. We recommend 
                                   "Item - Location - Customer" E.g : "keyboard - factory1 - Google"
item             non-empty string  The item for which the forecast should be computed.
location         non-empty string  The location for which the forecast should be computed.
customer         non-empty string  The customer for which the forecast should be computed.
method           non-empty string  The method used to compute the forecast among following 
                                   possibilities: 
                                   
                                   * Automatic
                                   
                                   * Constant
                                   
                                   * Trend
                                   
                                   * Seasonal
                                   
                                   * Intermittent
                                   
                                   * Moving Average
                                   
                                   * Manual

                                   * Aggregate
                                   
planned          boolean           Indicates whether the forecasted quantity should be planned,
                                   possible values are : "TRUE" or "FALSE".
================ ================= ===========================================================                              
                                  
.. rubric::  Advanced topics

* Complete table description: :doc:`../../model-reference/forecast`
