
This directory contains an addon for odoo v7 that provides an interface for frePPLe.

The module provides the following functionality:

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

Full documentation on the installation, configuration and data mapping is available at:
  http://frepple.com/documentation/extension-modules/openerp-connector-module/
