============
Key features
============

Browse the documentation by functional areas, and dig into the topics you are interested in.

  * :ref:`demand_forecasting`
  * :ref:`production_planning`
  * :ref:`capacity_modeling`
  * :ref:`routing_and_bom`
  * :ref:`user_interface`
  * :ref:`integration`
  * :ref:`odoo_integration`
  * :ref:`deployment`
  * :ref:`technology`
  * :ref:`pricing`

|

.. _demand_forecasting:

Demand forecasting
~~~~~~~~~~~~~~~~~~

+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| Feature                                 | Description                                                                | Read more                                                                     |
+=========================================+============================================================================+===============================================================================+
| **Statistical                           | The forecasting algorithm implements forecast methods for:                 | - Doc :doc:`user-interface/plan-analysis/forecast-report`                     |
| forecast**                              |                                                                            | - Example :doc:`examples/forecasting/forecast-method`                         |
|                                         | - Constant demand (single exponential smoothing)                           | - Example :doc:`examples/forecasting/middle-out-forecast`                     |
|                                         | - Trending demand (double exponential smoothing)                           |                                                                               |
|                                         | - Seasonal demand (Holt-Winters additive method)                           |                                                                               |
|                                         | - Intermittent demand (Croston method)                                     |                                                                               |
|                                         | - Moving average.                                                          |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | The system automatically selects and tunes the best method that gives      |                                                                               |
|                                         | the lowest forecast error.                                                 |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Outlier detection                     | Automatic detect and to exceptionally low or high demands:                 | - Video :doc:`a-day-in-the-life/demand-forecasting/filter-outliers`           |
| and correction**                        |                                                                            |                                                                               |
|                                         | The algorithm also implements a filter to reduce the impact of outliers    |                                                                               |
|                                         | on the generated statistical forecast (net forecast).                      |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Multi-dimensional and                 | Review forecast and demand history at any level of item, location,         | - Doc :doc:`user-interface/plan-analysis/forecast-editor`                     |
| hierarchical review**                   | customer, and time hierarchies.                                            | - `Live demo <https://demo.frepple.com/Distribution/forecast/editor/>`__      |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Automatic disaggregation of edits**   | Enter values at higher levels of the item, location, customer,             | - Doc :doc:`user-interface/plan-analysis/forecast-editor`                     |
|                                         | and time hierarchies. The values are automatically distributed to lower    | - `Live demo <https://demo.frepple.com/Distribution/forecast/editor/>`__      |
|                                         | levels.                                                                    | - Video :doc:`a-day-in-the-life/demand-forecasting/share-forecast`            |
|                                         |                                                                            | - Video :doc:`a-day-in-the-life/demand-forecasting/upload-forecast-values`    |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Forecast consumption**                | Sales orders consume from the gross forecast.                              | - Example :doc:`examples/forecasting/forecast-netting`                        |
|                                         |                                                                            |                                                                               |
|                                         | The sales orders and the remaining net forecast make up a complete and     |                                                                               |
|                                         | consistent demand for the complete planning horizon.                       |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+

|

.. _production_planning:

Production planning & scheduling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| Feature                                 | Description                                                                | Read more                                                                     |
+=========================================+============================================================================+===============================================================================+
| **Production planning**                 | The supply chain model spans end-to-end from raw material suppliers        |                                                                               |
|                                         | till the finished goods across multiple production locations, warehouses,  |                                                                               |
|                                         | distribution centers, subcontractors, and suppliers.                       |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Capacity planning**                   | FrePPLe's capacity plan provides a timely visibility of upcoming capacity  | - Doc :doc:`user-interface/plan-analysis/resource-report` screen              |
|                                         | bottlenecks, giving you the opportunity to evaluate different scenarios.   | - Video                                                                       |
|                                         | As such, it can be used in mid-term capacity planning processes.           |   :doc:`a-day-in-the-life/production-planning/identify-bottleneck-resources`  |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Production scheduling**               | Use frePPLe to generate detailed short-term production schedules. You can  | - Doc :doc:`user-interface/plan-analysis/plan-editor`                         |
|                                         | then visualize your plan in an interactive Gantt chart and make final      | - `Live demo <https://demo.frepple.com/planningboard/>`__                     |
|                                         | adjustments.                                                               | - Video                                                                       |
|                                         |                                                                            |   :doc:`a-day-in-the-life/production-planning/optimize-plan-in-gantt-chart`   |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Make-to-order,                        | Make-to-order, make-to-stock and assemble-to-order products are all        | - Example :doc:`examples/buffer/make-to-order`                                |
| make-to-stock and                       | supported.                                                                 |                                                                               |
| assemble-to-order**                     |                                                                            |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Exception based workflows**           | Improve the planner's productivity by focussing the work on problem        | - Video :doc:`a-day-in-the-life/production-planning/identify-expedite`        |
|                                         | areas in the plan.                                                         | - Video                                                                       |
|                                         |                                                                            |   :doc:`a-day-in-the-life/production-planning/check-impact-of-rush-orders`    |
|                                         |                                                                            |   :doc:`a-day-in-the-life/production-planning/review-late-orders`             |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Theory of constraints**               | A supply chain can only be as fast as the most constraining link.          |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | FrePPLe generates plans that will follow the pace of the bottleneck:       |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | - Capacity is not allocated until all materials are available. There is no |                                                                               |
|                                         |   point in reserving capacity for operations that can't start.             |                                                                               |
|                                         | - Material schedules are aligned with the available capacity.              |                                                                               |
|                                         |   Don't feed components to an assembly line faster than the                |                                                                               |
|                                         |   production rate.                                                         |                                                                               |
|                                         | - Coordinate subassemblies i.e. if one of the components or subassemblies  |                                                                               |
|                                         |   is constrained and late, the schedule of the other components are        |                                                                               |
|                                         |   aligned to match its availability.                                       |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **DDMRP (Demand Driven MRP)**           | FrePPLe aligns well with the principles of DDMRP and implements the base   |                                                                               |
|                                         | concepts.                                                                  |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Backward and forward                  | In backward scheduling mode, the planning algorithm counts backward from   |                                                                               |
| scheduling modes**                      | the due date of the demand for a just-in-time completion of the order.     |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | In forward scheduling mode, the planning algorithm tries to deliver each   |                                                                               |
|                                         | order ASAP.                                                                |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Constrained and                       | FrePPLe can generate different plan types:                                 |  - `Plan generation <command-reference.html#runplan>`_                        |
| unconstrained modes**                   |                                                                            |  - Video                                                                      |
|                                         | - Simple unconstrained plan: similar to a simple MRP run in an ERP. It     |    :doc:`a-day-in-the-life/production-planning/unconstrained-requirements`    |
|                                         |   plans all demands on time but overloads resources and plans operations   |                                                                               |
|                                         |   in the past.                                                             |                                                                               |
|                                         | - Fully constrained plans: all constraints are met and demand is planned   |                                                                               |
|                                         |   late or short in shortage situations.                                    |                                                                               |
|                                         | - Smart unconstrained plan:  intelligently searches all alternates to meet |                                                                               |
|                                         |   demand on time respecting all constraints, and only plans the portion of |                                                                               |
|                                         |   the demand that can absolutely not be met on time in an unconstrained    |                                                                               |
|                                         |   way. This results is an unconstrained plan that shows only the "real"    |                                                                               |
|                                         |   shortages.                                                               |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Fast heuristic solver                 | FrePPLe uses a heuristic planning algorithm, that can provide constrained  | - Doc :doc:`developer-guide/planning-algorithm`                               |
| algorithm**                             | and unconstrained plans.                                                   | - Example :doc:`examples/demand/demand-priorities`                            |
|                                         |                                                                            |                                                                               |
|                                         | The algorithm goes through the following loop:                             |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | 1) first order all the demands by priority, then by due date               |                                                                               |
|                                         | 2) loop over each demand in the list:                                      |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         |    a) search backward from the due date for all capacity and material      |                                                                               |
|                                         |       that the demand requires. This search will net any existing          |                                                                               |
|                                         |       inventory, then evaluate alternative operations and capacity.        |                                                                               |
|                                         |    b) if the above search didn't find a feasible solution to deliver the   |                                                                               |
|                                         |       demand on time, the search is repeated in forward scheduling mode    |                                                                               |
|                                         |       to deliver ASAP with minimal delay.                                  |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | This approach results in a fast plan generation that intelligently         |                                                                               |
|                                         | allocates constrained supply to the most important and urgent demands.     |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+

|

.. _odoo_integration:

Odoo integration
~~~~~~~~~~~~~~~~

+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| Feature                                 | Description                                                                | Read more                                                                     |
+=========================================+============================================================================+===============================================================================+
| **Maintain all data in odoo**           | All master data and transactions are managed by Odoo.                      | - Doc :doc:`erp-integration/odoo-connector/overview`                          |
|                                         | The frepple connector is an odoo addon that synchronizes all planning      |                                                                               |
|                                         | to frePPLe.                                                                |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Publish manufacturing orders          | Publish planning results back to odoo.                                     | - Doc :doc:`erp-integration/odoo-connector/overview`                          |
| and purchase orders**                   | With a simple click the planners can create manufacturing orders and       |                                                                               |
|                                         | purchase orders in odoo.                                                   |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Integrated user interface**           | The frepple user interface is integrated in odoo. Users log in odoo and    | - `Live demo odoo 14 <https://odoo14.frepple.com/>`__                         |
|                                         | can navigate from odoo to all frepple screens.                             | - `Live demo odoo 15 <https://odoo15.frepple.com/>`__                         |
|                                         |                                                                            | - `Live demo odoo 16 <https://odoo16.frepple.com/>`__                         |
|                                         |                                                                            | - `Live demo odoo 17 <https://odoo17.frepple.com/>`__                         |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+

|

.. _capacity_modeling:

Capacity modeling
~~~~~~~~~~~~~~~~~

+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| Feature                                 | Description                                                                | Read more                                                                     |
+=========================================+============================================================================+===============================================================================+
| **Resource types**                      | Different types of capacity constraints can be modeled:                    | - Doc :doc:`model-reference/resources`                                        |
|                                         |                                                                            | - Example :doc:`examples/resource/resource-type`                              |
|                                         | - capacity limit expressed as the number of simultaneous tasks             |                                                                               |
|                                         | - available capacity expressed as quantity per time bucket                 |                                                                               |
|                                         | - available capacity expressed as hours per time bucket                    |                                                                               |
|                                         | - unconstrained infinite-capacity resources or unconstrained)              |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Working hours and vacations**         | Define calendars based on working hours, shifts, factory shutdowns,        | - Example :doc:`examples/calendar/calendar-working-hours`                     |
|                                         | holiday periods, etc.                                                      | - Video :doc:`a-day-in-the-life/production-planning/define-operator-shifts`   |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Resource pools**                      | Group identical/similar resources (machines or operators) in an aggegrated | - Example :doc:`examples/resource/resource-alternate`                         |
|                                         | pool of resources.                                                         |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Resource skills**                     | Assign skills to machines and operators and set them as necessary to       | - Example :doc:`examples/resource/resource-skills`                            |
|                                         | perform specific operations. As a result, only a subset of the available   | - Doc :doc:`model-reference/skills`                                           |
|                                         | resources will be qualified to do the operation.                           | - Doc :doc:`model-reference/resource-skills`                                  |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Alternate resources**                 | The planning and scheduling algorithm can choose among alternative         | - Example :doc:`examples/resource/resource-alternate`                         |
|                                         | resources from a pool. The selection can be priority-based or cost-based.  |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Setup matrix**                        | Include changovers in your planning process. Sequence-dependent changeover | - Doc :doc:`model-reference/setup-matrices`                                   |
|                                         | time corresponds to cleaning, configuration, or tool changing time that is |                                                                               |
|                                         | required when switching between different resources (machines or           |                                                                               |
|                                         | operators) during the production process.                                  |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+

|

.. _routing_and_bom:

Routing and bill of materials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| Feature                                 | Description                                                                | Read more                                                                     |
+=========================================+============================================================================+===============================================================================+
| **Operation types**                     | Operations of different types can be modeled:                              | - Doc :doc:`model-reference/operations`                                       |
|                                         |                                                                            | - Example :doc:`examples/operation/operation-type`                            |
|                                         | - operations with a fixed duration, regardless of the quantity.            |                                                                               |
|                                         | - operations with a variable duration, proportional to the quantity.       |                                                                               |
|                                         | - routing operations that represent a sequence of operations.              |                                                                               |
|                                         | - alternate operations that represent a choice among alternatives.         |                                                                               |
|                                         | - split operations that proportionally distribute across alternatives.     |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Alternate operations**                | Products can be manufactured in different ways:                            | - Example :doc:`examples/operation/operation-alternate`                       |
|                                         |                                                                            |                                                                               |
|                                         | - multiple routings to produce the same item                               |                                                                               |
|                                         | - different versions of the bill of material                               |                                                                               |
|                                         | - make-or-buy: choose whether to produce in-house or buy from a supplier   |                                                                               |
|                                         | - make-or-outsource: choose whether to produce in-house or to outsource    |                                                                               |
|                                         |   an operation to a subcontractor.                                         |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | FrePPLe can plan these and automatically make a smart selection between    |                                                                               |
|                                         | the alternatives. The selection can be priority-based or cost-based.       |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | Alternates can be date-effective and quantity restrictions.                |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Alternate materials**                 | You can plan different versions of a bill of materials and include         | - Example :doc:`examples/buffer/alternate-materials`                          |
|                                         | alternate materials in a same bill of material.                            | - Doc :doc:`model-reference/operation-materials`                              |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Date effective bill of materials and  | FrePPLe can suggest different versions of the bill of material with        | - Doc :doc:`model-reference/operation-materials`                              |
| operations**                            | valid start and end dates.                                                 |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Co-products**                         | Operations can produce multiple items.                                     |                                                                               |
|                                         | Examples:                                                                  |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | - a sorting operation that produces items of different quantities or sizes |                                                                               |
|                                         | - an operation that produces a by-product in addition to the intended      |                                                                               |
|                                         |   item.                                                                    |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Minimum, maximum,                     | Some operations can only be scheduled within certain quantity constraints. | - Doc :doc:`model-reference/operations`                                       |
| and multiple operation                  | This applies to purchase orders, distribution orders and manufacturing     |                                                                               |
| size**                                  | orders.                                                                    |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Post-operation delay**                | The plan can include delays between operations. These add buffer time and  | - Example :doc:`examples/operation/operation-posttime`                        |
|                                         | robustness in the schedule to account for unexpected events.               |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | The post-operation delay is a soft constraint, which means we can generate |                                                                               |
|                                         | plans with a shorter delay if that is required to deliver a customer order |                                                                               |
|                                         | on time.                                                                   |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Operation dependencies**              | Operations are chained together through bill of materials (typical for     | - Example :doc:`examples/operation/operation-dependency`                      |
|                                         | most manufacturing environments) or through operation dependencies         |                                                                               |
|                                         | (typical for project-oriented manufacturing environments).                 |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+

|

.. _user_interface:

User interface
~~~~~~~~~~~~~~

+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| Feature                                 | Description                                                                | Read more                                                                     |
+=========================================+============================================================================+===============================================================================+
| **Web-based user interface**            | No installation is required on user's computers.                           |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | FrePPLe supports Chrome, Firefox, Edge, Safari and other modern            |                                                                               |
|                                         | web browsers.                                                              |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Multi-lingual**                       | Available in English, French, German, Hebrew, Italian, Japanese, Dutch,    | - `Live demo <https://demo.frepple.com/preferences/>`__                       |
|                                         | Portuguese, Brazilian Portuguese, Russian, Spanish, simplified and         | - Doc :doc:`developer-guide/translating-the-user-interface`                   |
|                                         | traditional Chinese.                                                       |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | The language is detected automatically from the user's browser, and can be |                                                                               |
|                                         | overriden as a user preference.                                            |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | Our user community often contribute translations for other languages.      |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Collaborative workflows**             | Integrates efficient and intuitive collaboration capabilities.             | - Doc :doc:`user-interface/getting-around/inbox`                              |
|                                         |                                                                            | - Doc :doc:`user-interface/getting-around/messages`                           |
|                                         | The user interface allows users to get notifications on changes in the     |                                                                               |
|                                         | plan. Notifications can be inline in the application, or through emails.   |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | Users can comment on the plan and attach documents.                        |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Excel import and  export**            | You can easily export the contents of all reports in Excel or CSV.         | - Doc :doc:`user-interface/getting-around/exporting-data`                     |
|                                         |                                                                            | - Doc :doc:`user-interface/getting-around/importing-data`                     |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Customizable screens**                | Each user can customize the reports to his/her needs and taste: visibility | - Doc :doc:`user-interface/getting-around/customizing-a-report`               |
|                                         | and order of the columns, column width, sorting and filtering.             |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Role-based permissions**              | Specify read, write, and view permissions per user or per user role.       | - Doc                                                                         |
|                                         |                                                                            |   :doc:`user-interface/getting-around/user-permissions-and-roles`             |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **What-if scenarios**                   | A scenario is a complete sandbox copy of the database. You can change any  | - Doc                                                                         |
|                                         | data element in a scenario without impacting the other scenarios.          |   :doc:`user-interface/what-if-scenarios`                                     |
|                                         |                                                                            |                                                                               |
|                                         | Typical use cases:                                                         |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | - Simulating different business scenarios                                  |                                                                               |
|                                         | - Separate long-term planning process (S&OP) and short-term scheduling     |                                                                               |
|                                         |   processes                                                                |                                                                               |
|                                         | - Use scenarios for business units that are completely unrelated           |                                                                               |
|                                         |   (i.e. no shared materials or resources).                                 |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Dashboard for KPIs**                  | The main screen is a dashboard that displays key metrics of the plan.      | - Doc :doc:`user-interface/cockpit`                                           |
|                                         |                                                                            |                                                                               |
|                                         | Customize your own dashboard easily to fit your decision process and       |                                                                               |
|                                         | business KPIs. You can organize the layout to visualize the KPIs that are  |                                                                               |
|                                         | relevant for your role and responsibility.                                 |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | The dashboard can be customized with addon.                                |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+

|

.. _integration:

Integration
~~~~~~~~~~~

+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| Feature                                 | Description                                                                | Read more                                                                     |
+=========================================+============================================================================+===============================================================================+
| **Integrated data maintenance**         | Data that is not maintained in external systems can be managed in frePPLe. | - Doc :doc:`user-interface/data-maintenance`                                  |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Excel import and export**             | Import and export Excel data files for all reports.                        | - Doc :doc:`user-interface/getting-around/importing-data`                     |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **CSV import and export**               | Import and export CSV data files for all reports.                          | - Doc :doc:`user-interface/getting-around/importing-data`                     |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **REST API**                            | A web-based JSON-REST API allows frePPLe to be integrated online with      | - `Live demo <https://demo.frepple.com/api/>`__                               |
|                                         | other applications.                                                        |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Packaged connectors                   | Generic standard connectors for Odoo, Openbravo and Etendo are available.  |                                                                               |
| with ERP systems**                      |                                                                            |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Remote automation**                   | All administrative tasks can be remotely managed through a web-based API.  |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+

|

.. _deployment:

Deployment
~~~~~~~~~~

+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| Feature                                 | Description                                                                | Read more                                                                     |
+=========================================+============================================================================+===============================================================================+
| **Cloud deployment**                    | Our secure cloud infrastructure allows to get up and running in a fast     |                                                                               |
|                                         | and scalable way. The majority of our customers use the Cloud Edition.     |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **On-site deployment**                  | For security or policy reasons, you can install frePPLe on your own        |                                                                               |
|                                         | servers.                                                                   |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Monthly release                       | The frequency of major releases is about one per year.                     | - :doc:`release-notes`                                                        |
| cycle**                                 | A minor or patch release is available about once a month.                  |                                                                               |
|                                         |                                                                            |                                                                               |
|                                         | Migration scripts are available to move the database to a new release      |                                                                               |
|                                         | without reloading or losing data.                                          |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+

|

.. _technology:

Technology
~~~~~~~~~~

+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| Feature                                 | Description                                                                | Read more                                                                     |
+=========================================+============================================================================+===============================================================================+
| **Built on open-source stack**          | The front-end web application is based on HTML, jquery and AngularJS.      |                                                                               |
|                                         | The back-end infrastructure is written in Python, Django, and PostgreSQL.  |                                                                               |
|                                         | The planning algorithms are implemented in C++ and can be scripted with    |                                                                               |
|                                         | Python.                                                                    |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Extendable platform                   | You can code addons to extend the application with custom reports, data    |  - Doc :doc:`developer-guide/creating-an-extension-app`                       |
| with apps**                             | fields, and custom planning logic.                                         |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Designed for Linux and the cloud**    | Deploy on-premise on Ubuntu or as a Docker container.                      | - Doc :doc:`installation-guide/docker-container`                              |
|                                         | Or use the Cloud Edition hosted by us.                                     | - Doc :doc:`installation-guide/linux-binaries`                                |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+

|

.. _pricing:

Pricing
~~~~~~~

+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| Feature                                 | Description                                                                | Read more                                                                     |
+=========================================+============================================================================+===============================================================================+
| **Free open-source                      | The core product is available in an open-source Community Edition.         |                                                                               |
| Community Edition**                     |                                                                            |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Cloud and Enterprise                  | These editions provide extra features, plus enterprise-grade support.      |                                                                               |
| Editions**                              |                                                                            |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Free trial period**                   | You can try out the cloud edition for 30 days for free.                    |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Free for academic                     | The Cloud Edition with all features is available for free for academic     |                                                                               |
| use**                                   | use. Contact us to apply.                                                  |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Pricing is based on                   | Check out the `price calculator <https://frepple.com/pricing>`_            |                                                                               |
| the model size and the                  | on our website.                                                            |                                                                               |
| modules chosen**                        |                                                                            |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
| **Unlimited number of                   | The price is independent of the number of users.                           |                                                                               |
| users**                                 |                                                                            |                                                                               |
+-----------------------------------------+----------------------------------------------------------------------------+-------------------------------------------------------------------------------+
