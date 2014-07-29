
This directory contains an addon for odoo v7 that provides an interface for frePPLe.

The module provides the following functionality:

 - Web interface called by the frePPLe planning engine.
   It is accessible at the URL:
     http://<host>:<port>/frepple/xml?database=<db>&user=<user>&password=<password>&language=<language>&company=<yourcompany>
   The planning engine reads the XML-data at this address as input data.
   The planning engine will post results back to this same address, where they are translated
   to purchase quotations and manufacturing orders.

 - New scheduler in the "warehouse/schedulers" menu to generate a frePPLe plan.

 - Cron job to generate a plan.

Full documentation on the installation, configuration and data mapping is available at:
  http://frepple.com/documentation/extension-modules/openerp-connector-module/
