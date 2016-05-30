
This directory contains an addon for Odoo v8 that provides a 2-way integration
between frePPLe and Odoo.

The module adds the following functionality in Odoo:

 - Web interface called by the frePPLe planning engine.
   It is accessible at the URL:
     http://<host>:<port>/frepple/xml?database=<db>&language=<language>&company=<yourcompany>
   The planning engine reads the XML-data at this address as input data.
   The planning engine will post results back to this same address, where they are translated
   to purchase quotations and manufacturing orders.

 - Configuration fields for the connector are defined in the company form:
     - Calendar:
       References a resource.calendar model that is used to define the working
       hours.
     - Manufacturing location:
       FrePPLe assumes each company has only a single manufacturing location.
       All bills of materials are modelled in this frePPLe location.
     - Cmdline:
       Command line launched when the plan generation for a company is launched
       interatively from the user interface.
       Note that when launched from a scheduler cron job, the command line is
       configured on the job directly.

 - New scheduler in the "warehouse/schedulers" menu to generate a frePPLe plan.

 - Scheduler cron job to generate a plan.

Full documentation on the installation, configuration and data mapping is 
available at:
  https://frepple.com/documentation/3.2/extension-modules/odoo-connector-module/

Here's the list of open issues for the connector (the list is not 
necessarily complete...):
  - use the stock.routes introduced by the new warehouse module
  - mrp.bom is now split over the 2 tables mrp.bom and mrp.bom_lines
  - mrp.bom now refers to a product.template
  - authentication issue when there are multiple databases in odoo 
  - v7 web controller allowed a streaming response, which is apparantly not possible
    any longer with v8. As a result the connector will be slower and consume more
    memory.

