Release notes
-------------

9.7.0 (Upcoming release)
========================

This release is scheduled for end of January.
You can already check out a `preview <https://demo-preview.frepple.com>`_.

9.6.0 (2025-02-07)
==================

.. rubric:: User interface

- | Row selection logic updated. If the user clicks on the checkbox of a row,
    that row is selected on top of the existing selection.
  | The hotkey CRTL+A selects all the rows of the current page.

- | The detail widgets with the details of a purchase order, manufacturing order,
    or distribution order can now be rearranged.
  | Different people just want to see different information first.

- | The tasks in the execution screen can now be rearranged.
  | It's convenient to put commmonly used tasks at the top.

- | Bug fix: Users could not be set active or inactive in a scenario.

- | Addition of parameter archive.duration to delete the old archived data.
  | So far, the archived data wasn't deleted.

.. rubric:: Demand forecasting

- | The database structure for storing forecast data has been refactored.
  | The new structure uses considerable less database storage and is a bit faster.

  | !!! IMPORTANT !!!
  | If you use the field forecastplan.value in your custom reqorts,
    you will need to rewrite your queries to the new structure.

.. rubric:: Production planning

- | Operations can now consume and produce material in different
    locations.
  | Until now, an operation always consumed and produced material
    in the same location. This new feature makes modeling complex
    multi-location production environments easier.

- | Purchase orders, manufacturing orders and distribution orders
    get an extra field "remark", which allows users to leaves free text
    comments on them.
  | In earlier releases some implementations already used a custom attribute
    field for this purpose.

- | Bug fix: Sales orders in the status "inquiry" incorrectly were being planned
    when a) the owner field is set and b) the delivery policy is set to alltogether.

.. rubric:: Odoo integration

- | 17, 18: Extra robostness to avoid creating manufacturing orders on
    phantom kit bill of materials.

- | 17, 18: Support for routes that produce or consume items
    from different warehouses.

- | 17, 18: The customer names are replaced with their Odoo IDs in frePPLe.
    The name of the customer can be found in the description field.

9.5.0 (2024-12-27)
==================

This release is scheduled for end of December.
You can already check out a `preview <https://demo-preview.frepple.com>`_.

.. rubric:: User interface

- | The inventory report got a segment dropdown to allow easier filtering.
  | This applies to Enterprise and Cloud Editions only.

- | Row selection logic updated. Clicking on a row unselects any existing selection
    unless the shift key (to select a range of rows) or the ctrl key (to add a row
    to the existing selection) is pressed.

- | Performance optimization for configurations with a high number of scenarios.
  | When many scenarios are active we noticed the user interface performance
    is impacted, and frepple also needed an increasing number of database connections.
  | These bottlenecks have now been resolved, and extra scenarios no longer
    impact scalability and performance.

.. rubric:: Production planning

- | The planning algorithm has been refined to avoid corner cases where a
    large amount of small manufacturing orders are being generated.

- | Fix for the approved manufacturing orders. If its operation has an offset, the
    manufacturing order could be moved in time when running a plan.

.. rubric:: Demand forecasting

- | Missing sales order data in the recent past was considered by the forecast engine as buckets
    with no demand history. That was leading to a lower forecast than expected. A new enhancement
    detects this situation and ignores the last buckets with no demand history when generating a
    statistical forecast.

.. rubric:: Inventory planning

- | A corner case has been resolved in the ABC classification.
  | Items with a cost equal to 0 were not getting a classification. They will now
    be classified in the last group (C if the ABC parameters were not updated).
  | This applies to Enterprise and Cloud Editions only.

.. rubric:: Odoo integration

- | 18: Keep the language selection of a user identical in odoo and frepple.
  | Displaying both user interfaces in a different language isn't very nice, isn't it?

- | 18: Synchronize products tags from odoo into the item category in frepple.

.. rubric:: Integration

- | The API for uploading data files to the "import data files" task has extra URLs for
    retrieving the list of all data files, with their timestamp and file size.

- | Fixed a minor inconsistency between full and incremental export of work orders.
  | The full export only sent approved and proposed workorders, whereas the incremental
    export didn't include such a filter. The filter is now removed.

.. rubric:: System administration

- | The docker container logs now display the apache output.
  | The container logs now provide a better insight in the container status. Muuuuch
    easier than navigating to the volume with the apache log files.

9.4.0 (2024-11-08)
==================

.. rubric:: Odoo integration

- | 18: Initial support for odoo 18. This is still experimental and for testing purposes only.

- | 17, 18: Improvements for multi-warehouse odoo configurations.

- | 17, 18: Ability to export a remark from frepple into odoo on
    manufacturing orders, distribution orders or purchase orders.
  | The remark shows up in the "source" field in odoo.

- | 17, 18: Blanket order is now populated in odoo when exporting purchase orders from frePPLe.

- | 17, 18: Various bug fixes to support configurations where odoo schedules work orders,
    while frepple only plans at the manufacturing order level.

- | The odoo database, company, user can now be configured in the djangosettings configuration
    file.
  | This improves security and also eases configuration and deployments.

- | Extra robustness to deal with control characters in the odoo data.
  | Amazing what strange data one finds in an ERP system...

.. rubric:: Production planning

- | A lot of bad data condititions that used to abort the planning run are now replaced
    with warnings instead. Ignoring such data errors will make the planning more robust
    and resilient.

.. rubric:: User interface

- | Ability to delete users.
  | Until now you could not delete users. You could already mark them inactive
    to prevent them from logging in, but that's not good enough.

- | Updated rules for default permissions of new users.
  | If no default permissions are defined (using the "DEFAULT_USER_GROUP" setting in
    your djangosettings.py file), new users are automatically marked as superusers.
  | The new behavior makes the first steps in frepple after an initial intallation
    easier and smoother. For broader deployments, the configuration of the correct
    default permissions remains important.

- | Bug fix in scenario promotion. When promoting a scenario as the production
    scenario the user preferences and group permissions where copied into
    the production scenario, which isn't right.
  | There was also an issue with custom reports after a scenario promotion.

.. rubric:: System administration

- | The support for external authentication (introduced in the previous release)
    has now been validated with Microsoft Entra ID (formerly known as Azure AD).

9.3.0 (2024-09-27)
==================

.. rubric:: Demand forecasting

- | Bug fix: Form for increasing forecast by a fixed value or percentages is now working
    more intuitively at aggregate levels.

.. rubric:: User interface

- | Optimization of the response time when doing interactive planning with the PO/MO/DO screens.
  | With large datasets, it could take time to complete a save after updating the dates
  | or the quantity of a PO/MO/DO. The response time has been significantly improved.

.. rubric:: Documentation

- | Added support to use external authentication methods using OAuth, SAML, OpenID, ...
    More and more companies are moving towards these protocols with multi-factor authentication
    to securely manage users, passwords and their access rights.
  | The procedure to enable OAuth2 is included in the documentation. Other methods
    can be enabled with minimal coding and configuration.

.. rubric:: Development

- | The development container have been improved and this is now the easy, simple
    and recommended method to do any development on frepple or frepple addons.
  | Within 5 minutes any developer can now have a complete development
    environment ready.

.. rubric:: Odoo integration

- | 17: To keep the names shorter in frepple we now a) use the warehouse short code
    (instead of its full name) and b) use only the item code in the operation names
    (instead of including also the much longer item name).

- | Bug fix: Manufacturing orders for make-to-order products couldn't be updated
    with new dates from frepple.

.. rubric:: System performance

- | Various performance improvements for frePPLe server under heavy load.

9.2.0 (2024-08-30)
==================

.. rubric:: System administration

- | Administrators can now set a quota to limit the `disk space usage <installation-guide/setting-disk-space-quotas.html>`_
    of frePPLe.

.. rubric:: User interface

- | Users can now choose a separate theme for each scenario.
  | This avoids mistakes where changes are applied to the wrong scenario.

- | A small annoyance was resolved: Until now graphs were not updated when
    resizing your browser window  Now the graphs are redrawn to fit the new
    window size.

.. rubric:: Production planning

- | Subcontractor operations (ie operations with category "subcontractor") are
    now respecting the purchasing lead time constraint rather than the
    manufacturing lead time constraint.
  | The new behavior fits the user expectations better.

- | Bug fix: Buffer max inventory was not always correctly respected if a buffer
    is replenished through multiple or date-effective suppliers.

- | Fix multithreading crash when using make-to-order items.

- | Bug fix: When manufacturing orders were assigned to completely unexpected
    resources, these assignments were ignored.
  | Now we respect and preserve that assigned resource.

.. rubric:: Odoo integration

- | 17: Added support for multi-database odoo configurations.

- | 15, 16, 17: Subcontracting should respect the purchasing minimum quantity
    rather than the bill of material minimum quantity.

- | 17: Performance improvements of about 20% to 30% when importing odoo data into frepple.

- | 17: Partial support for multi-warehouse odoo configurations.
  | In previous connector version we handled it through customization.
  | Now we map the stock routes into item distributions and place the BOMs in
    the correct manufacturing locations.
  | The current mapping does NOT handle all possible odoo configurations yet. It may work
    for your setup or may not.

9.1.0 (2024-07-05)
==================

The big news is that this release adds an AI based forecasting method. AI is a trendy and hot topic these days
and we couldn't stay behind :-)

.. rubric:: Production planning

- | Bug fix: Planning operation dependencies could leave partially planned demands in 9.0.0.

.. rubric:: Demand forecasting

- | Introduction of machine learning forecasting capabilities to frePPLe with the addition of a
    new app based on the `orbit library <https://orbit-ml.readthedocs.io/en/latest/>`_.
  | The machine learning forecast app is still in beta-testing and would require the frePPLe team to
    help to make it production ready.

- | The comment window of the forecast editor screen is removed. You can still enter comments
    in the comment tab as in earlier releases.
  | A comment for a parent will be displayed when selecting a child. Similarly comments
    for a child when be displayed at the parent level.

- | Outlier count:  Extra attributes have been added to the item object to count how many
    outliers were found in the last bucket, last 6 buckets and last 12 buckets.

- | Bug fix: Fixes a nasty engine crash in complex multithreading situations.

.. rubric:: User interface

- | When releasing a scenario, the data of that scenario is now deleted to optimize the database
    disk space.

.. rubric:: Supported operating systems

- | The docker image of 9.0.0 missed the root certificates required for any remote https connection.

.. rubric:: Odoo integration

- | 16, 17: The connector no longer depends on the external jwt python package.
  | Installing the dependency frequently created trouble or confusion.

- | 15, 16, 17: Addition of the expiry dates management. Lot expiry dates and product expiration time
    are retrieved by the connectors in frePPLe. This functionality requires the
    `shelf life <apps/shelflife.html>`_ app to be installed on the frePPLe side.
    Note that the shelf life app is only available in the enterprise version of frePPLe.

- | 15, 16, 17: The product category in Odoo is now used to build the item hierarchy in frePPLe.
    This is very useful in forecast editor to navigate the forecast by category.

- | 17: Fix for the lunch periods in calendars that were incorrectly considered as working time.

- | 15, 16, 17: Addition of a new command *Pull demand history from Odoo*. This command uses the
    XML RPC interface of Odoo and pulls all the sales history in the frepple database.

.. rubric:: System administration

- | A lot of settings in the /etc/frepple/djangosettings.py configuration file can now
    be set through environment variables.
  | This makes it easier to manage the runtime configuration in container-based deployments.
    Advanced configurations will continue to require a custom dockerfile to tailor the image.

9.0.0 (2024-06-01)
==================

.. rubric:: Production planning

- | The handling of safety stocks by planning algorithm has been enhanced to
    generate more intuitive and better plans.
  | This may result in small differences in the plans when migrating to the new
    release.

- | Buffers have new fields "maximum" and "maximum calendar" that specifies a
    replenish-up-to stock level.

- | Removed the parameters plan.calendar, allowsplits and plan.planSafetyStockFirst.

- | Bug fix: Unnecessary late deliveries when confirmed replenishment exist far beyond
    the lead time.

- | Flows of type "transfer" are deprecated.
  | :doc:`Operation dependencies </model-reference/operation-dependencies>` or
    :doc:`operation material offsets </model-reference/operation-materials>` are a much cleaner
    and more performant alternative.

.. rubric:: Demand forecasting

- | Bug fix: "Orders planned" row in forecast editor and forecast report wasn't
    calculated correctly when orders aren't at the level where the forecast is planned.

- | The parameters for the statistical forecast methods (alfa, beta, gamma...) will have
    a value set to "default". The planner still has the possibility to update the value with
    a custom value.
  | The datasets *parameters_day_forecast, parameters_week_forecast, parameters_month_forecast* are
    removed.

.. rubric:: Supported operating systems

- | Ubuntu 24 LTS is now the supported operating system.
  | For all other operating systems a docker container is the way to run frepple.

.. rubric:: User interface

- | The `demand gantt report <user-interface/plan-analysis/demand-gantt-report.html>`_ was updated
    to display a routing operation before its suboperations.

- | You can now configure frepple to hide the hours, minutes and seconds from
    all date fields. This is handy when you are not interested in the precise
    timing within each day of your plan.
  | A new flag DATE_STYLE_WITH_HOURS has been added to the djangosettings file.
    It's true by default.

- | Bug fix: Adding custom attributes was broken.

- | Bug fix: The field "end items" in the purchase order and distribution order screen
    wasn't searchable.

.. rubric:: Odoo integration

- | 15, 16, 17: The shipping policy on odoo sales orders is now mapped.
  | The connector already had it for a while as an inactive option that was commented out.
    The default behavior is changing now.

- | 16, 17: Support for Odoo make-to-order products.
  | Odoo automatically creates the manufacturing orders and purchase orders for
    such products. The frepple connector respects their links to the source sales order
    or manufacturing order.

- | 17: Addition of `quoting <erp-integration/odoo-connector/using-the-connector-in-odoo.html#quoting-capabilities>`_ capabilities
  | An extra button is added to get a promised date for a quote in Odoo.
  | A new *Frepple Quotes* screen is added to get a promised date for a product.
  | Many thanks to https://e-powerinternational.com/ for this contribution!

- | 16, 17: Correct handling of locked purchase orders.

- | 16, 17: New mapping for odoo reorder points, which uses the new buffer.maximum field.

- | The "odoo export" command now sends back information on the planned delivery date of every
    open sales order.
  | This can be valuable feedback in odoo to the sales team.

.. rubric:: System administration

- | Ability to customize the "export plan results" task.
  | Until now you had to rely on the standard export logic or write a frepple app to tailor the
    export to your needs.
  | Now you can customize the exports from the user interface.

.. rubric:: Documentation

- | A `page <installation-guide/advanced-configuration.html>`_ was added to the
    installation guide with advanced configuration options.
  | These topics frequently come up, so let's capture that knowledge.

8.6.0 (2024-04-05)
==================

.. rubric:: Production planning

- | Enhancements to improve the plan quality in the presence of temporary
    unresolvable material shortages.

- | The planning algorithm now plans sales orders in status "quote" after
    "open" sales orders and net forecast. The quotes thus can't steal capacity or
    material away from regular demand.
  | In earlier releases quotes were just ordered among the open sales orders and
    net forecast. Depending on their priority and due date quote can take precedence
    over regular demand.

- | Bug fix: When the solver runs into a data exception when planning a routing
    operation, the planning algorithm didn't correctly roll back and clean the plan.
  | The symptom is an error during the export of the plan.

- | Bug fix: The manufacturing order summary report didn't correctly handle operations
    with 0 duration.

.. rubric:: Demand forecasting

- | Performance improvements when disaggregating edits in sparse hierarchies.

.. rubric:: User interface

- | Bug fix: The report manager didn't work on scenario databases.
  | This was correctly a long time already in Enterprise and Cloud Editions, but
    we missed fixing it on the Community Edition.

8.5.0 (2024-03-02)
==================

.. rubric:: Production planning

- | Reduced memory consumption and improved performance.

.. rubric:: Demand forecasting

- | When changing the forecast method in the forecast editor or inventory planning screen,
    the forecast is now immediately recomputed.
  | In previous releases you had to regenerate the plan before seeing the new forecast values.

- | Addition of the batch field to the `forecast <model-reference/forecast.html>`_ table.
    The batch field was only available in the sales order table. See the
    `make to order <examples/buffer/make-to-order.html>`_ example for more details.

.. rubric:: User interface

- | In the `preferences screen <user-interface/getting-around/user-preferences.html>`_
    you can now reset your screen personalization.
  | You can restart from a clean slate. Or you can inherit them from another user.
    Or you can copy them from another scenario.

- | Addition of the item *unit of measure* column in the
    `supply path screen <user-interface/plan-analysis/supply-path-where-used.html>`_.

- | Addition of hyperlinks in the network status widget to get detailed information
    on the displayed numbers.

- | The routing suboperations now have the same level in the *upstream/downstream
    Operations* widgets and in the demand delivery plan. This way, they will all expand/hide
    in one click.

- | The *forecast widget* was updated not to display too many values on the x-axis. The planner
    can choose to display the data in different time buckets (month, week, day...).

- | The *manufacturing/distribution/purchase orders widgets* were modified to display clickable
    bars instead of lines. These widgets display data based on the selected time bucket.

.. rubric:: Odoo integration

- | Switching work orders to alternate work centers in a pool is now fully supported.
  | Existing assigment were already sent from odoo to frePPLe. When reassiging
    in frePPLe the new assignment is communicated back to odoo.

- | 15, 16, 17: The mapping of calendars now includes the odoo identifier.
  | This is needed to guarantuee uniquess of the calendars.

- | 15, 16, 17: The frePPLe item name is now mapped to the Odoo product internal reference,
    unless the internal reference is not unique in Odoo.

- | 15, 16, 17: Allow export of approved and confirmed purchase orders from frePPLe to Odoo to
    update various fields of the Odoo purchase order lines (quantity, receipt date, item...).

- | 15, 16, 17: Creation of purchase orders in Odoo (upon export from frePPLe) uses generic
    Odoo code so that fields such as tax, unit_price, description... are standard.

- | The XMLRPC version of the connector is deprecated.
  | It has always been only an experimental feature, which we see now as a dead end.

.. rubric:: System administration

- | Scheduled tasks are now also possible in docker containers.
  | The automated scheduling of tasks on a time schedul no longer uses the at-command.

- | Bug fix: sending an email when executing a task group fails didn't work.

- | Bug fix: Basic authentication on web requests failed when the password contains colons.

8.4.0 (2024-01-19)
==================

.. rubric:: Production planning

- | The solver now considers purchasing lead time and manufacturing lead time
    as separate constraints.
  | This is useful in situations where manufacturing orders and capacity are
    being scheduled by the production planner(s) while the material planner(s)
    still work on procuring the materials.

- | The release fence is no longer selectable as a separate constraints.
    Respecting the release fence is now implicitly included in the lead time
    constraint.
  | In practice we have never come across the need to control the fence constraint
    separately. So, let's simplify things here.

- | Bug fix: Corner case with unplanned demand when an item is consumed multiple times
    in the same supply path.

- | Bug fix: Manufacturing orders were being proposed on resources with a
    0-priority skill.
  | Consistent with other alternates, the planning algorithm should never
    propose replenishments on 0-priority alternates. Such alternates are
    only selected manually.

.. rubric:: Demand forecasting

- | Reduced memory consumption.

.. rubric:: User interface

- | A bulk update of a field on many records in a table is now much
    easier: first select the records to be updated, click the "update"
    icon and fill in the popup form with the fields you want to update.

- | Easier management of the membership of user groups.
  | The group edit form now has a widget that allows you to select the users
    belonging to that group.

.. rubric:: Odoo integration

- | 16, 17: Mapping of Odoo "replenish on order" products into frepple
    make-to-order items.
  | For such items both Odoo and frepple maintain a hard link between
    consumers and producers of material.

- | 15, 16, 17: Added mapping for Odoo's "Resource Time Off" model.

.. rubric:: Cloud infrastructure

- | Part of our cloud servers are now running in the Amazon data center in
    Ohio (USA). Until now our cloud servers were all running in the Amazon
    data center in Ireland.
  | Cloud customers whose frepple infrastructure was moved will be notified.

.. rubric:: Legal

- | Refreshed the `privacy policy <https://frepple.com/privacy-policy-2/>`_.
  | No real changes here, just bringing up to date the list of third party
    applications we work with.

8.3.0 (2023-12-08)
==================

.. rubric:: Production planning

- | Bug fix: Custom operationplan attributes couldn't be edited in the user
    interface.

- | Capacity report: Clicking to get the detail of the MOs consuming from a bucketized
    resource will now display all the MOs of the time buckets overlapping the filtering dates.

- | Resource detail report: A new display mode is added to display the resource schedule as
    a Gantt chart.
  | This is experimental feature that will evolve in following releases.

 - | Bug fix: Safety stock solving in buffers replenished with a routing operation
     that has a size multiple could generate excess material.

.. rubric:: User interface

- | Frepple is now installable as an app on your tablet and smartphone.
  | Your browser will provide a prompt to guide you through the installation.

- | The home screen of the application has be redesigned.
  | We've noticed that the home screen isn't commonly used as a central screen in the
    planner's daily workflow. We're trying to improve that.
  | Generating a plan or executing a task group is now possible from the home screen.
  | Any thoughts and ideas to further improve this screen are welcome!

- | A new `apps screen <user-interface/getting-around/apps.html>`_ allows superusers
    to interactively install optional extension module apps.
  | Until now, administrators had to edit the INSTALLED_APPS setting in the
    /etc/frepple/djangosettings.py configuration file.

- | In the manufacturing order, purchase order and distribution order screens you can
    now use the familiar clock icon to set the time horizon.
  | Just easier and simpler, isn't it?

- | The 'about frepple' option in the help menu is now gone.
  | The new apps screen in the admin menu provides the same (and more) information.

- | More updates to the Italian translations, contributed by Sbadux. Grazie mille!

- | Records in the upstream/downstream operations widgets (appearing when selecting a single PO/MO/DO)
    are now sorted by date (they were previously sorted by item).

- | Better management of the errors when copying a scenario. Sometimes, a scenario copy could
    appear as successful in the UI but the copy didn't work properly. These silent errors are
    now captured in the execute logs and the task will be reported as failed.

- | Browser sessions time out after 1 day rather than 1 hour.
  | The setting SESSION_LOGOUT_IDLE_TIME controls this timeout. We increased the
    default limit to improve the user experience.

- | Date strings in CSV or Excel uploads are now parsed according to the configured
    date style.
  | The default remains 'YYYY-MM-DD hh:mm\:ss' (international style). Using the
    DATE_STYLE setting in the djangosettings.py file this can be changed
    to 'DD-MM-YYYY hh:mm:ss' (European style) or 'MM-DD-YYYY hh:mm:ss' (US style).

.. rubric:: Odoo integration

- | 17: Support is added for the new Odoo version 17.
  | At this stage this requires additional testing and validation. And yes, you can help
    us with this!
  | Correction in product reservations when MOs are defined with a multi-step route.

- | 14 & 15 & 16: Bug fix. Connector had a problem authenticating in a multi-database
    Odoo configuration.

.. rubric:: System administration

- | The command "empty" now requires either the argument "--all" or the
    argument "--models=list-of-models-to-be erased".
  | This change avoids erasing by accident all data from the database.

8.2.0 (2023-10-20)
==================

.. rubric:: Production planning

- | The "why short or late" reasons for lead time constraints are improved to
    provide more meaningful and intuitive results.
  | A first change is that dates on the before-current and before-fence constraints
    are now based on the start date rather than the end date. Using the start date
    is a more intuitive way to interpret and evaluate the constraint.
  | An optional change is that the algorithm can now limit the before-current
    and before-fence constraints to only the most constraining operation. By
    setting the parameter "plan.minimalBeforeCurrentConstraints" you'll get a
    shorter list of constraints.

.. rubric:: User interface

- | Bug fix: filter on null values wasn't working in "report manager" custom reports.

- | Updated Italian translations have been contributed by Sbadux. Grazie mille!

.. rubric:: Odoo integration

- | 15 & 16: Onhand inventory is now filtered.
  | We only transfer inventory in locations on type "internal", and exclude scrap and
    return locations.

- | 15 & 16: The mapping for subcontracting bill of materials has been improved.
  | The subcontractor resupply transactions are now synced correctly.

- | 15 & 16: The reference of bill of materials is now mapped into the operation description field.

- | 12: Backport of some recent developments to this older odoo version: working hour calendars,
    resource calendars, manufacturing orders material reservations.

.. rubric:: Documentation

- | The use case videos section has been reworked and is expanded into a collection
    of "a day in the life" daily workflows.
  | These workflows are categorized for different planning roles: demand planner, inventory
    planner, production planner and material planners.

.. rubric:: Data integration

- | The export to folder command didn't respect the date format configured in your djangosettings.py.

.. rubric:: Legal

- | The word frepple is now
    `officially registered as a trade mark <https://euipo.europa.eu/eSearch/#details/trademarks/018891700>`_
  | This provides us a more robust defense against any incorrect use of our work.

8.1.3 (2023-09-18)
==================

- | Bug fix: interactive edits not working in docker container.

8.1.2 (2023-09-15)
==================

- | Bug fix: the sales order delay field wasn't updated correctly any longer in 8.1.0.

8.1.1 (2023-09-14)
==================

- | An ugly bug slipped through the cracks and the 8.1.0 release is no good.
  | Sorry about this.

8.1.0 (2023-09-13)
==================

.. rubric:: Production planning

- | Bug fix: A corner case was corrected during safety stock planning
    when the producing flow has a offset.

- | The `demand gantt report <user-interface/plan-analysis/demand-gantt-report.html>`_
    has extra columns "quantity required confirmed" and "quantity required proposed".
  | This split of the "quantity required" allows a planner to easily see what part
    of a sales order is already covered with existing supply.
  | This report can also now be downloaded using the download button.

- | Automatic web service starts no longer modify the plan.
  | Until now, the web service start tried to keep the plan feasible. The resulting
    plan changes are found to confuse users.

- | Approved and confirmed manufacturing orders now detect missing upstream
    supply on operation dependencies. Any missing supply is now replenished.

- | Bug fix: A corner case was corrected during safety stock planning
    when the producing flow has an offset.

- | Bug fix: A corner case was corrected when approved steps in a routing
    manufacturing order were infeasible. They approved steps were reduced correctly
    in size, but the material and capacity consumption on sibling manufacturing
    orders in the routing were not updated.

.. rubric:: Demand forecasting

- | Significant memory usage and performance optimizations.

- | Records in a forecast report file (with typically forecast overrides) were only
    considered if the forecast combination exists in the
    `forecast <model-reference/forecast.html>`_ table. From now on, records will be processed
    even without forecast record, provided they are at leaf level (lowest level of hierarchy for the
    item, location and customer specified).
    Corresponding records will be automatically created in the forecast table with the planned flag equal
    to true and the forecast method set to automatic.

.. rubric:: User interface

- | Fixed some small bugs where the user interface, data import and data
    export didn't work correct with European style date and number formats.

- | Bug fix: Exporting custom reports that contain any of the characters [ ] : ? / \
    resulted in an error. These characters aren't accepted by Excel.

.. rubric:: Odoo integration

- | The approval button to export a proposed purchase order, distribution order
    or manufacturing order from frePPLe to odoo is now a button rather than a
    dropdown. Saves you a click.

- | 15 & 16: Handle the corner case where a purchase order has an ordering
    date later than its delivery date.

- | 15 & 16: Bug fix where confirmed manufacturing orders are consuming materials
    in the wrong work order.

- | 15 & 16: Addition of parameter odoo.delta that prevents the connectors from reading
    the entire sales order history. The usage of this parameter should reduce
    the duration of the odoo import task for companies with a signifiant number of sales
    order records.

- | Bug fix: Reordering rules on zero-stock buffers were incorrectly ignored.

.. rubric:: System administration

- | The command to `back up the database <command-reference.html#backup>`_ is renamed
    to `contact frePPLe support <command-reference.html#backup>`_ as this is the official way
    for sharing a database dump with the frePPLe support.
  | This command used to be available for users defined in the SUPPORT_USERS variable.
    The SUPPORT_USERS variable disappears as the command is now available to all super users.

.. rubric:: System architecture

- | The code has been refactored to make all interactive planning more flexible and more
    scalable.

8.0.0 (2023/06/03)
==================

This release brings two exciting changes:

- | The license of the Community Edition changes from `AGPL <https://wikipedia.org/wiki/Affero_General_Public_License>`_ to
    `MIT <https://wikipedia.org/wiki/MIT_License>`_.
  | Read `this post <https://frepple.com/blog/why-we-are-changing-our-license-from-agpl-to-mit/>`__ to learn more.

- | The forecasting module is moving into the Community Edition.
  | So far, it was available only in the Enterprise and Cloud Editions.
  | Read `this post <https://frepple.com/blog/the-forecast-module-goes-open-source/>`__ to learn more.

Join the `webinar on Thursday June 8 at 4 PM Central European Time <https://frepple.com/webinar_frepple_8.ics>`_ to hear the full story
and ask us any questions you may have.

.. rubric:: Production planning

- | Closed operationplans are no longer automatically deleted.
  | Some customers like to keep them around. In very old releases we did keep
    them, but then stopped doing that.

- | Bug fix: Fix corner case with the tools-per-piece feature when the tool
    availability conflicts with the operation size minimum.

- | Bug fix: When operation maximum size is specified on buffers with alternate
    replenishment operations, some demands could remain partially unplanned.

- | Bug fix: The autofence that makes the solver wait for existing confirmed
    and approved supply had a corner case where extra replenishments were
    incorrectly triggered.

- | Bug fix: Calendar buckets with an effective start time before 2am were
    not correctly handled on dates where the daylight saving time changes.

.. rubric:: User interface

- | Updated German translations have been contributed by Thomas Stöckel. Vielen Dank!

- | Bug fix: 7.2 introduced some situations where some reports in scenarios
    mix data from the default scenario.

.. rubric:: Report manager

- | A new parameter report_download_limit is introduced to protect the application
    performance against inefficient and excessive SQL queries.
  | Downloading a custom report is by default limited to 20000 rows.

.. rubric:: Odoo integration

- | 15 & 16: Usability improvements to skill maintenance.

- | Bug fix: Item supplier records were not synced from odoo if the source field
    of the supplier is edited.

7.3.0 (2023/04/14)
==================

.. rubric:: User interface

- | Some smaller layout and styling updates were added, continuing on the big user interface
    refresh of 7.2.

- | The command *Publish reports by email* will not send empty reports anymore. If all reports
    to be sent are empty then no mail is sent.

- | Fix style problem of date widgets in Chrome 112.

.. rubric:: Production planning

- | A new type of resource is added to model tools that are attached to each
    individual pieces of a manufacturing order.
  | It's used to model holders or frames that are attached to each piece while
    it is on the shop floor. A big manufacturing order needs more holders than a smaller one,
    which is different from the other resource types.
  | Check out `example resource tools <examples/resource/resource-tool.html>`_ for more details.

- | Completed and closed manufacturing orders no longer create problems.
  | This reduces the alert list a bit compared to previous releases.

- | Bug fix: A corner case was corrected when a manufacturing orders require a certain resource skill
    while not a single resource has the required skill.

- | Bug fix: When a routing manufacturing order included some step manufacturing orders in the
    "proposed" status, then other manufacturing order steps in the "approved", "confirmed" or
    "completed" status were getting ignored and deleted.

- | The default search mode in the operation resource table is changed from "priority"
    to "minpenalty".
  | Since this field is used in modeling resource pools, dividing the work over the pool
    is a more intuitive default (compared to loading the primary member of the pool).

.. rubric:: Odoo integration

- | 15 & 16: The progress of work orders is now synchronised between odoo and frepple.
  | Earlier releases only interfaced at the level of the manufacturing orders, and completely
    left the detail of the progress to odoo. However, when the duration and complexity of
    manufacturing orders is increasing, the more detailed level of the work orders
    is needed to generate a good and accurate plan.
  | The connector now creates frepple operations specific to each manufacturing order to
    correctly capture the details of its progress. Odoo allows manual editing (of
    materials, work centers, durations, dependencies, ...) at the manufacturing order level.
    Only with a dedicated operation can we assure that frepple correctly represents the
    odoo data.

- | 15 & 16: On manufacturing orders the connector now picks up the quantity actually
    produced instead of only the quantity.
  | When pieces are scrapped or lost in any other way in the factory, the manufacturing
    orders in frepple will now adjust accordingly.

.. rubric:: Internal APIs

- | The database structure for pegging information has been optimized for size and
    performance.
  | If your customizations rely on the pegging data (either in a custom report or through
    the REST API), it may need updating.

7.2.0 (2023/03/03)
==================

.. rubric:: User interface

- | The styling and layout has been refreshed.

- | Updated Spanish translations have been contributed by Zipus. Gracias!

- Bug fix: The empty-database task didn't work if only the resource-detail or
  inventory-detail tables were selected by the user.

- | Excel exports for fields of type duration is improved and more intuitive with
    the default behavior of Excel.
  | Durations less than a day are exported in the format hh:mm:ss. Longer
    durations are exported by default as a number of days.
  | A new parameter excel_duration_in_days is added to maintain backward compatibility for
    customers that rely on the old format. The new format is the default,
    but if set to false we stick with the old format.

- Bug fix: Occassionally the user screen didn't open and showed an error.

.. rubric:: Production planning

- | Support for tool resources.
  | In some industries a mould, fixture or holder is attached to a manufacturing order,
    and the same tool accompanies it during multiple steps of routing.
  | The tools are modelled as resources in frepple, with the subcategory field set to true.
    The planning algorithm will assure that the same tool resource is selected for all steps
    in a routing.

- | The logic for automatically fixing broken supply path is enhanced to cover situations
    where the effective data of item-suppliers, item-distributions or operations has expired.
  | See the doc on the `parameter fixBrokenSupplyPath <model-reference/parameters.html>`_.

- | Improved level-loading logic for assigning resources to approved and
    confirmed manufacturing orders.
  | When approved and confirmed manufacturing orders are loaded from your
    ERP without any assigned resources, frePPLe automatically assign resources.
    In previous releases we always assigned the most efficient resource from a pool of
    possible resources. With this enhancement we consider also the loading of each
    resource to come up with a level-loaded utlization of the resources
    in the pool.

- Bug fix: Various corrections and enhancements to the operation dependency functionality.

.. rubric:: Odoo integration

- | The frepple connector is now available from the odoo app store.
  | You can downloaded and install from https://apps.odoo.com/apps/modules/16.0/frepple/
  | Hint: Feel free to give us some stars and leave some feedback there :-)

- | 15 & 16: Support for operations requiring multiple workcenters at the same time.
    An extra field name *secondary workcenters* has been added to the operation model.

- | 14 & 15 & 16: Bug fix to handle bill of materials that produce more than 1 unit
    of the product.

- | 15 & 16: Added a flag on workcenters to indicate tools (see above).

- | 14 & 15 & 16: Update of replenishment logic when products can be both purchased and manufactured.
    The solver will try first to buy then to manufacture.

- | 14 & 15 & 16: Improved logic to handle situations where there are multiple vendor definitions
    for the same supplier and item.
  | Earlier releases used the first record. Now we take the minimum quantity and minimum lead time
    of all date-effective records we find.

- | 14 & 15 & 16: When exporting RFQ purchase orders we now populate the order deadline date
    and receipt date.
  | We put the earliest order start and end date of the exported frepple records in these
    fields. This makes it easier to quickly evaluate the urgency of the RFQs in the list.

- | 14 & 15 & 16: Bug fix. When a material was manually deleted from an odoo manufacturing order,
    frepple was still using it.

- | 14 & 15 & 16: Bug fix. Workcenter skills were not synchronised.

.. rubric:: Documentation

- The chapters are restructured and some new pages are added. We hope this
  makes it easier to find the info you're looking for.

7.1.0 (2023/01/13)
==================

.. rubric:: Production planning

- | A new `operation dependencies <model-reference/operation-dependencies.html>`_
    table allows to define relations between operations.
  | This is useful to model the following situations:
  | - Define which steps in a routing operation can be executed in parallel
      rather than sequential.
  | - Define relations between different subprojects and tasks in a
      project-oriented business.

- | When uploading or editing purchase orders, manufacturing orders or
    distribution orders the inventory plans and resource plans are
    immediately updated.
  | In previous releases this update was only done after rerunning the plan.
    The new functionality thus greatly improves the capabilities to make
    interactive changes to the plan.
  | Users of the Enterprise Edition already had this functionality through the
    planning engine web service.

- Bug fix: Resolved infinite loop corner case when planning a sales order owner
  with delivery policy "all together" and one of the lines has a broken supply
  path.

.. rubric:: System administration

- | The database name is now configurable in the docker container.
  | The default database names are "frepple", "scenario1", "scenario2", "scenario3".
  | If the POSTGRES_DBNAME argument is passed as "X", the database names will be
    "X0", "X1", "X2" and "X3".

- | Bug fix: restoring a database backup in a scenario was broken.

.. rubric:: User interface

- | Addition of a *debug report* link in the *Help/About FrePPLe* window.
    This report will display the exceptions found in the apache log files
    and can help understand the root cause of an error. Any sensitive information
    is hidden, only the traceback exception is displayed.

.. rubric:: Odoo integration

- | 14 & 15 & 16: Support for odoo's 2-week working hour calendars, which has
    different working hours in alternative weeks.

7.0.0 (2022/11/18)
==================

.. rubric:: Software stack

- | Support for Ubuntu 18 is dropped.
  | The frepple team will only support Ubuntu 20. Use a Docker container
    to run on other platforms.

- | The minimum PostgreSQL version is now 12.

.. rubric:: User interface

- | The date format is now configurable.
  | The setting DATE_STYLE in the djangosettings.py configuration file now controls
    how dates are formatted in the user interface.

- | Minor improvement when loading data Excel files with autofilter tables.
  | Since quite often excel spreadsheet contain real data outside of the table,
    we somehwat relaxed our logic to strictly read only the data from the
    autofilter table.

.. rubric:: Production planning

- | The default value of parameter allowsplits is changed from true to false.

- | Bug fix: The planning algorithm has been improved to handle corner
    cases with the autofence parameter.
  | When awaiting confirmed supply conditions did occur where a demand
    with a later due date was planned before a demand with an earlier
    due date.

.. rubric:: Odoo integration

- | The new Odoo 16 is now also supported by the connector.

- | v12 & 13 & 14 & 15 & 16: Correction of a bug in the uom conversion. Quantities were
    divided instead of multiplied by uom conversion factor and vice versa.

- | 14 & 15 & 16: When planners manually approve purchase and manufacturing orders, the
    odoo transaction is mark with that planner as responsible.
  | In previous releases, the generic account running the frepple connector was used
    instead. Which isn't very useful or handy...

- | 14 & 15 & 16: Confirmed sales orders are now synchronized through information
    from the deliveries instead of the sales order lines.
  | This provides more detailed information on partial deliveries, reservations
    and scheduled shipment dates.

- | 14 & 15 & 16: Confirmed purchase orders are now synchronized through information
    from the receipts instead of the purchase order lines.
  | This provides more detailed information on partial deliveries, reservations
    and scheduled receipt dates.

- | 14 & 15 & 16: A new configuration flag "respect_reservations" is added for the connector.
  | When this flag is checked, frepple fully respects the material reservations
    of odoo. Frepple only plans with the unreserved materials.
  | When this flag is false, frepple plans with the full material availability
    regardless of any reserved quantities in odoo. The implicit assumption is that
    any reservations will be unreserved in odoo when needed.

- | v14 & 15 & 16: Access rights to frepple are now configurable per user in odoo.
    The connector will also automatically synchronize the list of authorised users
    between odoo and frepple.

- | v14 & 15 & 16: Performance optimization by allowing gzip compression of the web
    traffic between the odoo and frepple servers.
  | This will only give an improvement when you have a proxy server in front of
    odoo that does this compression.

.. rubric:: System administration

- | The installation process has been simplified. Except for the postgresql configuration,
    everything else is now handled in the installer.

    - The installer now automatically can migrate your databases during
      a frepple upgrade. A prompt is shown to confirm whether or not you want to do this.

    - All python dependencies are now included as a virtual environment. You no longer
      have to deal with the requirements.txt file yourself.

    - A number of apache configurations are now done by the installer.

6.25.0 (2022/09/16)
===================

.. rubric:: Production planning

- | Graphical calendar editor.
  | A new screen visualizes how the calendar value changes over time. The
    new screen also allows easy creation of extra calendar buckets.
  | Until now, calendar buckets have been quite abstract to grasp and understand.
    The new screen should make this a lot easier and intuitive.

- | Synchronised delivery of sales order.
  | So far each sales order was planned independent. In practice it is pretty
    common that sales orders are grouped together under a header and the delivery
    within the group needs to be synchronised.
  | A new field "policy" is added, with 3 possible values: "independent",
    "all together" and "in ratio".
  | The "independent" policy is the default and treats each sales order
    separately, just as in previous releases.
  | The "all together" policy assures all sales orders with the same owner
    are shipped together to the customer.
  | The "in ratio" policy assures that partial deliveries maintain the same
    ratio as the initial order. For instance, imagine a customer requires 5
    tables and 20 chairs. You can ship 1 table and 4 chairs, but not 1 table
    and all 20 chairs.

- | Bug fix: Updating purchase orders, manufacturing orders or distribution orders
    could create incorrect duplicate records in the inventory detail table.

- | Bug fix: Operation batching didn't consider infinite buffers correctly.

- | Bug fix: Safety stock planning could leave material shortages in the plan in some
    conditions.
  | The corner cases where this potentially happens have confirmed purchase orders
    within the autofence window of safety stock shortfalls.

- | Bug fix: Bucketized resources didn't handle the parameter allowsplits=false
    correctly.
  | Thanks to kobsam from a nice open source contribution!

.. rubric:: Odoo integration

- | v14 & 15: Products of type "consumable" are no longer interfaced to frepple.
    These are assumed not be of interest for planning.
  | Variant management. The connectors are now managing the variants.
    The BOMs are correctly reflecting the "Apply on variants" field.

- | v12, v14 & v15: Variant management. The connectors are now managing the variants.
    The BOMs are correctly reflecting the "Apply on variants" field.

- | v14 & v15: Material consumption of a manufacturing order level are now
    included in the interface.
  | These can deviate from the material consumption defined in the bill of material:
    e.g. when the bill of material is changed, or when the user manually edited the
    materials on the manufacturing order.

- | v14: Bug fix for mapping odoo reorderpoints to frepple.

6.24.0 (2022/07/29)
===================

.. rubric:: Production planning

- | When selecting a resource from a pool, the planning algorithm now uses
    the resource efficiency as tie breaker in case the priority, cost or
    penalty criterion is identical for multiple alternative resources.
  | Earlier releases used the resource name as tie breaker, which is quite
    arbitrary.

.. rubric:: User interface

- | The 'export workbook' task no longer exports automatically generated
    identifier fields.
  | The presence of such fields could interfere when importing the excel workbook again.

.. rubric:: Third party components - Performance

- | A django patch has been backported to the frepple django fork.
  | It reduces the number of required database connections and will
    improve performance for deployments with many scenario databases.

.. rubric:: Odoo integration

- | Odoo 15 is now also supported by the connector

- | Ability to write back the scheduled start and finish dates of work orders
    from frepple to odoo.

- | v14: Bug fix, subcontractor lead time was interpreted by frepple in
    working hours rather than calendar days.

- | v14: Bug fix for mapping odoo reorderpoints to frepple.

- | v14: Bug fixes for multi-company odoo configurations.

- | v14: Bug fix, manufacturing orders in the status "to close" were
    incorrectly being ignored.

- | v14: Bug fix, improved logic to handle cases with multiple purchase records
    for the same item+supplier combination are present.

- | v14: Assure compatibility with the latest releases of the Python
    package pyjwt.

- | v14: Reduced memory footprint.

6.23.0 (2022/6/8)
=================

.. rubric:: User interface

- | Your user preferences now include an option to set a default scenario.
  | Some users do the majority of their day-to-day actions in a scenario different
    from the default production scenario. This option will make the life of such
    users easier.

- | A new filter "is null" is now available on fields of reports.
  | This makes it easier to filer empty fields or non-empty fields.

.. rubric:: Odoo integration

- | V14: The connector code has been refactored to clean up and simplify the code.

- | V14: The connector now maps the status of individual work orders.
  | In previous releases the connector only mapped the manufacturing orders. For
    very long manufacturing orders and with many work orders this extra detail is
    important.

- | A new parameter odoo.allowSharedOwnership allows users to edit records
    read from odoo.
  | By default records read from odoo aren't editable in frepple. You loose your
    edits with every run of the connector.
  | If this flag is set to true you can override the odoo data if the source field
    of the overridden records is also edited.

- | V12: Performance improvement for reading large amounts of product templates.
  | We noticed that the runtime increases exponentially as the number of product
    templates goes up. Newer odoo releases don't show the same inefficiency.

.. rubric:: System administration

- | A set of Kubernetes configuration files is now available for quick deployment
    on a kubernetes cluster.

6.22.0 (2022/5/6)
=================

.. rubric:: User interface

- | When drilling into an item, the "Plan" tab has been removed as the same information
    can be found in the "Inventory" tab.

  | Inventory report: Backlog is calculated at the end of the bucket. It used to be
    calculated at the start of the bucket

.. rubric:: Production planning

- | The `itemsupplier <model-reference/item-suppliers.html>`_ table gets an extra
    field "hard_safety_leadtime" to model an extra delay to be considered when a
    purchase order is received.
  | We already had a field "extra_safety_leadtime". This models a *soft* constraint
    (we try to respect, but can compress it if needed). The new field models a *hard*
    constraint - regardless of the urgency, we need to plan for the extra delay when
    a purchase order is received.
  | Typical use cases are for modeling quality control, material handling or administrative
    delays.

- | Infinite buffers no longer peg consumer and producers.
  | The FIFO assocation between consumers and producers makes sense for regular buffers,
    but only gives confusing results in infinite buffers.

- | Bug fix: The planning algorithm created a plan with unnecessary lateness in
    situations where a buffer has both an unresolvable material shortage and
    confirmed supply exists further in the horizon.
  | Not a normal and common situation, but it can happen...

.. rubric:: Odoo integration

- | V14: Connector is improved to handle deep odoo location hierarchies.

- | V14: Extra links from the odoo menus to the frepple screens.

- | V14: Bug fix. Sales orders with an individual as customer were not picked up.
    Only orders from a company did go through.
  | Now we pass the sales order correctly mapped to his/her company.

- | V14: New configuration to send stack traces from the connector back to your frepple
    instance. This is useful to debug data and connector issues. By default this option
    is not active for security reasons.

- | V14: Ability to limit the data to a single odoo company only.
  | By default, the connector extracts data for all allowed companies the connector user
    has access to into a single frepple dataset.
  | With the new option you can separate the frepple datasets per odoo company.

.. rubric:: User interface

- | Bug fix: Editing grid fields of type currency was broken in a previous release.

.. rubric:: System administration

- | The solver now has a built-in protection to avoid excessively large log files.
  | This avoids annoying disk-full issues.

.. rubric:: Third party components - Security

- | Django release is upgraded to 3.2.13 to address a security issue.

6.21.0 (2022/3/25)
==================

.. rubric:: Third party components

- | The django version is bumped up from 2.2 LTS to 3.2 LTS.
  | When upgrading from a previous release, upgrade your python packages with:

  |  sudo -H pip3 uninstall django-admin-bootstrapped
  |  sudo -H pip3 install --force-reinstall -r https://raw.githubusercontent.com/frepple/frepple/6.21.0/requirements.txt

.. rubric:: Production planning

- | The inventory report now uses colors to highlight periods where the onhand goes below
    the safety stock.

- | Bug fix: 6.20 introduced a bug where manufacturing orders aren't correctly restored
    on the assigned alternate resource.

- | Bug fix: Zero-time operations didn't correctly respect the availability calendars
    in some corner cases.

- | Item suppliers records are automatically created for item-locations for which no
    replenishment has been defined. These records, created with an 'Unknown supplier', prevent the
    demand from not being planned.

- | The time window over which the item metrics "late demand count/quantity/value"
    and "unplanned demand count/quantity/value" are computed is now configurable
    with the parameter "metrics.demand_window".
  | This recognizes the fact that planners focus their day to day work to a certain time
    horizon, and all later forecast and sales orders are purely treated as "FYI".
  | For backwards compatibility, the default value is 999 - ie compute with all demand.

- | Bug fix: the effectivity dates of skills were not verified correctly in some corner
    cases.

- | Bug fix: the effectivity dates of operation materials were not verified correctly in some corner
    cases.

- | Bug fix: partially complete routing manufacturing order with some steps in the status
    "closed" were not correctly treated.

.. rubric:: Odoo integration

- | V14: The previous release introduced a bug when exporting manufacturing orders
    from frepple to odoo.

- | v14: The connector is now consistently using the timezone preference of the odoo
    user used by the connector.
  | In previous releases you could see some unexpected time shifts when the odoo
    and frepple servers run in different timezones.

- | v14: Synchronize the workcenter capacity and efficiency.

- | v14: Bug fix, approved purchase orders didn't get the price field populated.

- | It is now possible to approve a workorder in frepple to approve the complete
    manufacturing order to odoo.
  | In previous releases users had to filter out the routing manufacturing orders
    in frepple and only approve those. Quite tedious, isn't it?

6.20.2 (2022/2/18)
==================

.. rubric:: Production planning

- | Bug fix: the effectivity dates of operation materials were not verified correctly in some corner
    cases.

- | Bug fix: partially complete routing manufacturing order with some steps in the status
    "closed" were not correctly treated.

6.20.1 (2022/2/11)
==================

.. rubric:: Production planning

- | Bug fix: the effectivity dates of skills were not verified correctly in some corner
    cases.

6.20.0 (2022/1/22)
==================

.. rubric:: Production planning

- | Improved hovering tooltip with constraints causing backlog in the
    demand report and inventory reports.

- | Removed the "excess material" problem. In practice these alerts were found
    to be too numerous and not actionable.
  | More practical ways to identify excess inventory situations are either
    a) using "period of cover" item attribute, b) using the "inventory status" field
    in the inventory planning screen, c) using the "inventory days of cover" row
    in the inventory report, and/or d) using the "period of cover" field on
    manufacturing orders, purchase orders and distribution orders.

- | Uniqueness of Item suppliers records has been updated. Only one record is now allowed
    with an empty location for an item/supplier/effective start date combination can be created.

- | Special case for setup matrices
  | In the corner case where no setup rule matches a changeover, we used a changeover
    time of 1 year. This default changeover time now becomes 7 days.
  | A small mistake in the matrix no longer messes up your entire plan.
  | It is a best practice to explicitly use a final catch-all setup rule
    (i.e. from .* to .*) in each matrix to avoid running in this corner case altogether.

.. rubric:: Security

- | The application will automatically log users out after a period of inactivity.
  | The threshold is configurable with the new setting "SESSION_LOGOUT_IDLE_TIME" (defaults
    to 1 hour, and can be set to None to disable this feature).

.. rubric:: User interface

- | The popular `data source url <user-interface/getting-around/exporting-data>`__
    feature has been enhanced.
  | The column selection, filtering, sorting and language of the web page are now
    all included in the URL. What you extract in your excel sheet will match what
    you have on the screen.

- | Allow upload of excel files with .xlsm extension.
  | We don't run the macros in them, but process only the data cells.

- | Reviewed Brazilian-Portugese translations. Many thanks to Neerosh!

.. rubric:: Integration

- | The REST API can now also retrieve and update custom attributes.

- | The parameters to upload plan result files to a ftp/sftp/ftps folder
    can be defined per scenario.

.. rubric:: Odoo integration

- | V14: Implemented synchronization of work center availability calendars.

- | V14: The connector now freezes the current date of the plan to the time of the
    import from odoo.

- | V14: Support for the "consumed in operation" field for bill of material components.
  | In previous releases frepple consumed all bill of material components in the
    first routing step. With the extra mapping we can now consume some components
    at other steps.

- | V14: Changed naming convention for operations in frePPLe. With the odoo id at the end, the
    new name "item @ location id" is more readable than "id item @ location".

- | V14: Changed naming convention for customers in frePPLe. With the odoo id at the end, the
    new name "name id" is more readable than "id name".

.. rubric:: Supported operating systems

- | Adding Ubuntu 20 as supported operating system.
  | From v7.0.0 ubuntu 20 will replace ubuntu 18 as the preferred operation system.

6.19.0 (2021/12/1)
==================

.. rubric:: User interface

- | The detail panels in the purchase order, distribution order and manufacturing
    order screens have been restyled and their layout optimized.

- | Fix bug where the time displayed could have an offset of one hour in DST timezones.

.. rubric:: Odoo integration

- | V14: Handling of multi-timezone situations when importing and exporting manufacturing orders,
    purchase orders and distribution orders.
  | When the frepple and odoo servers reside in different timezone things get mixed up in
    previous releases.

6.18.0 (2021/11/5)
==================

.. rubric:: Production planning

- | Easier modeling of resource pools.
  | An operation-resource record with quantity 2 of an aggregate resource
    was interpreted as "we need to find a resource with size 2".
  | If you set the parameter "plan.individualPoolResources" to true, the same
    operation-resource record will now be interpreted as "we need to find
    2 individual resources of size 1".
  | A typical usage for the new feature is for modeling a group of operators.

.. rubric:: User interface

- | The purchase order, distribution order and manufacturing order screens can
    now display the detail panels on the right or the left of the screen.
  | This improves the usability of the screen compared to positioning them at
    the bottom.

.. rubric:: System administration

- | A new command `generatetoken <command-reference.html#generatetoken>`_ is added
    to generate JWT authentication tokens. Such tokens are a more secure way to
    authenticate automated API calls to the application.

.. rubric:: Database

- | Database size is reduced and performance is improved by removing some
    rarely used indexes.

.. rubric:: Security

- | The security HTTP header now includes the newer
    `Content-Security-Policy <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy>`_
    header in addition to the older
    `X-Frame-Options <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options>`_
    header. Both headers can be configured with a setting in your djangosettings.py
    file.
  | Unless you're embedding frePPLe web pages as an iframe in your application
    this change doesn't impact you.

.. rubric:: Odoo integration

- V14: Added support for subcontracting bill of materials.

- V14: Added mapping of the unit of measure, volume and weight of a product.

6.17.1 (2021/10/10)
===================

.. rubric: Docker image

- | Fixed bug with database connection.

6.17.0 (2021/10/10)
===================

.. rubric:: Production planning

- | Enhanced make-to-order planning logic.
  | In previous releases all confirmed and approved
    supply of make-to-order items needed to be marked with the correct batch field in order to
    be usable for a specific demand.
  | With this release we also recognise freely available stock (ie with a blank batch field)
    that can be used for any demand. The algorithm will first exhaust existing supply with the
    matching batch field, then use any existing generic supply and finally plan for new
    supply matching the batch field.
  | This represents business cases where the make-to-order is eg freed up after sales order
    cancellations.

- | Size-based selection of alternates
  | The `operation size-minimum and size-maximum fields <model-reference/operation.html>`_
    are now also used for selection of alternates.
  | An example use case: A small production order will be manufactured on a different machine
    than a large production order.
  | Another example use case: When working on a small manufacturing order, the operators
    will work less efficient than on a larger production order. The time per produced item
    will thus decrease as the required quantity increases.

.. rubric:: User interface

- | Extra field uom / unit of measure on the `item table <model-reference/item.html>`_.
    Typical values are "piece", "kg", "l", "m"...
  | All quantities in the plan for an item are expressed in this unit of measure.

- | Extra robustness when defining custom `attributes <model-reference/attributes.html>`_
    The feature was introduced in the previous release, and we added some checks to
    handle corner cases (such as attribute names starting with handles, adding attributes
    to proxy models, allowing underscores in attribute names, ...)

- The performance of the inventory report is fixed after it degraded in the previous release.

- Correction of the days of cover calculation that could be wrong in the first buckets of the plan.

.. rubric:: Odoo integration

- Addition of batching window in supplier info table.

6.16.0 (2021/08/21)
===================

.. rubric:: Community Edition

- | The `old frepple-user group <https://groups.google.com/g/frepple-users>`_ has
    been closed.
  | `Github Dicussions <https://github.com/frePPLe/frepple/discussions>`_ are the
    new forum for any questions and discussion.

- | The Continuous Integration (CI) software building process is now fully transparent
    run on `Github Actions <https://github.com/frePPLe/frepple/actions>`_.

- | With the above changes, the source code, software builds, tests, and user forum
    are now all living next to each other on github.

.. rubric:: Supported platforms

- | The Windows installer for the Community Edition has been removed. FrePPLe is an
    enterprise and cloud application. A windows desktop version isn't a viable option
    for us to distribute the application.
  | The Enterprise Edition is still available as a Windows installer.

- | The docker container is now fully production ready.
  | They have been experimental for a while already, and we have now brought forward the
    code, tests and documentation.
  | The images for the Community Edition can be pulled from the
    `Github Container Registry <https://github.com/orgs/frePPLe/packages/container/package/frepple-community>`_.
  | The images for the Enterprise Edition can be downloaded from our portal.

.. rubric:: Production planning

- | The logic for choosing a default resource from a resource pool is enhanced.
  | In previous releases, we automatically choose the most efficient resource. In case
    we find multiple resources in the pool with the same efficiency, we now use
    the resource skill priority as a tie breaker.

- | Bug fix: A solver issue with unconstrained resource has been corrected. See
    https://github.com/frePPLe/frepple/issues/381

.. rubric:: User interface

- | An new table `attribute <model-reference/attributes.html>`_ allows users to
    define custom attributes themselves from the user interface.
  | In previous releases this required some programming in the backend.
  | Since adding custom attributes is so common on items, sales orders, etc...
    we're giving this power to the user now.

- The `inventory report <user-interface/plan-analysis/inventory-report.html>`_ got a new
  set of extra fields. We also made it easy to expand and collapse summary rows to
  display more detailed rows.

.. rubric:: System administration

- | The `migrate command <command-reference.html#migrate>`_ now migrates all
    scenarios that are in use.
  | In previous releases the system administrator had to migrate each scenario
    separately. This was inconvenient and often forgotten.
  | You can still migrate a single database only by using the --database argument.

.. rubric:: Integration

- | The `HTTP API <integration-guide/remote-commands.html>`_ already allowed
    launching tasks, canceling task and checking the task status. Now you can
    also retrieve the log file of tasks.

6.15.0 (2021/07/02)
===================

.. rubric:: Production planning

- | The `itemsupplier <model-reference/item-suppliers.html>`_  and
    `itemdistribution <model-reference/item-distributions.html>`_ tables get an extra
    field "batchwindow". It specifies a time window for grouping proposed purchase
    or distribution orders together.
  | This makes is easier to model a purchasing or shipping frequency: "I buy this item
    once a month" / "I ship at least the requirements for the next month".

- | The `itemsupplier <model-reference/item-suppliers.html>`_  table gets an extra
    field "extra safety leadtime". It specifies a time that needs to be added on top
    of standard item supplier lead time for safety reasons.

- | The plan.autoFenceOperations parameter instructs the solver to wait for existing
    supply rather than generating a new replenishment. In this release the logic has been
    refined for corner cases around overdue requirements and safety stock.
  | The new behavior will delay some replenishments that were proposed too early in
    previous releases.

- | Bug fix: A bug in the planning algorithm created more lateness than needed when
    an manufacturing operation produces more than 1 piece per unit (i.e. you have an
    operationmaterial record with a quantity > 1)

- | The "currentdate" parameter now also accepts the keyword "today". It sets the current
    date for planning to today at 00:00 / midnight.
  | In previous releases you could already use the keyword "now" to use the system time
    as current date. A drawback of using "now" is that different planning runs on the same
    day will show slightly different results. For the majority of users, this is confusing and
    not needed. With the new "today" keyword the plan will be stable during the day.

- | A new parameter "WIP.produce_full_quantity" provides finer control on the behavior of
    the completed_quantity field of manufacturing orders.
  | When set to "false" (the default) a partially completed manufacturing order
    is producing only the remaining quantity of material. We assume that the on hand
    inventory has already been incremented to reflect the produced material.
  | When set to "true" a partially completed manufacturing ordre will still produce
    the full quantity of the material. We assume that the produced material will only
    be booked as inventory when the manufacturing order is fully finished.

.. rubric:: User interface

- | Ability to change the number of records on a page.
  | A simple dropdown next to the paging buttons allows to easily see more records
    on the screen.

- | Ability to create a scenario from a backup file.
  | The planner can now select a backup file when creating a scenario. Previously scenarios
    could only be created from other scenarios.
  | Looking back into an older plan allows the planner to go back in time and understand why
    certain decisions where taken then.

- | Improved data table detection when importing Excel files.
  | This feature was introduced in the previous release. User feedback showed that it's
    not uncommon to have data columns outside of the table. These were silently being ignored with 6.14.
  | Columns next to the data table will now still be read, similar to the behavior before 6.14.

- | Addition of 4 fields to the inventory report: Produced by confirmed PO, Produced by proposed PO,
    On order confirmed PO, On order proposed PO. These 4 fields allow the planner to understand in a
    glance if the purchased quantities are coming from a confirmed or a proposed PO.

- | Report time settings are now scenario specific.

- | Bug fix: Editing calendar buckets from the calendar form was broken.

- | Bug fix: Filter widget wasn't shown in custom reports.

.. rubric:: Integration

- | Bug fix: the REST API didn't include the field owner of the resource model.

6.14.0 (2021/05/28)
===================

.. rubric:: Production planning

- | Confirmed manufacturing orders, distribution orders and purchase no longer consume
    or produce material in the past. We now position these right after the current date.
  | This improves the visibility in the plan between what-has-already-happened and
    what-is-about-to-happen.

- | With a new field "quantity_completed" on manufacturing orders, frepple now can
    correctly model partially completed manufacturing orders. The planned end date,
    material consumption and capacity consumption are now computed on the remaining
    quantity to produce.
  | In earlier releases we relied on appropriately preprocessed input data to account
    for such partial completed work-in-progress.

.. rubric:: User interface

- | The calendar views on the purchase orders, manufacturing orders and
    distribution orders now support grouping the results.
  | You get a row with cards for every resource, supplier, item, item category...
    The calendar view then looks pretty much like a spreadsheet grid with
    cards in each cell.

- | Manufacturing orders, purchase orders and distribution orders can now be edited
    from the resource detail and inventory detail screens.

- | Addition of the period of cover as an item attribute, allowing to display, sort and
    filter that value in most of the views and reports.

- | When uploading excel files, we now check for the presence for an autofilter data table
    on a worksheet. When present, we only read the data from that table.
  | By ignoring all other cells, you now have more flexibility to create a custom layout of
    your data file. Eg a header section with comments or instructions.

- | Refreshed Spanish translations. Many thanks to Marilenne Minaya!

- | Bug fix: formatting of negative numbers was showing too many digits after the decimal.

.. rubric:: Integration

- | Addition of the `upload exported reports <command-reference.html#uploadreport>`_
    task in the execute screen, allowing users to export selected reports to a remote
    server (using a ftp, sftp or ftps connection).

- | Bug fix: the REST API didn't include the field available of the operation model.

6.13.0 (2021/04/20)
===================

.. rubric:: Birth of a new product

- | FrePPLe's user interface has quite some nice capabilities that are generic and reusable
    in other domains.
  | We have copied these out into a separate project https://github.com/frePPLe/frepple-data-admin.
  | We believe that a larger community to build on the data-admin product will also be
    beneficial for our planning product.

.. rubric:: Production planning

- | Bug fix: Using the plan.autoFenceOperations parameter can lead to sub-optimal plans
    resulting in demands being planned at a later date.

.. rubric:: User interface

- | The kanban and calendar views on the purchase orders, manufacturing orders and
    distribution orders are now also available on the Community Edition.
  | They have been available on the Enterprise and Cloud Editions for a longer time already.

- | Scenario management: Addition of a command to release a scenario.

.. rubric:: System administration

- | The command to `back up the database <command-reference.html#backup>`_ is now restricted
    to users listed in the setting SUPPORT_USERS.
  | It is now possible to download the database dump from the user interface.

.. rubric:: Odoo integration

- | The `data import and export from Odoo <integration-guide/odoo-connector.html>`_
    are no longer integrated in the plan generation task. They are now tasks that can
    be launched independently.

6.12.0 (2021/03/01)
===================

.. rubric:: Data model

- | Item model now has extra fields "volume" and "weight".
  | The purchase order, distribution order and manufacturing order screens now can display
    the total cost, total volume and total weight of the selected records.

.. rubric:: User interface

- | Inventory report now displays also archived inventory information.
  | We archive the inventory and safety stock values every day/week/month (configurable
    with the parameter archive.frequency).
  | Planners can review how the onhand and safety stock have evolved over time.

- | In the PO/MO/DO screens, the selection of a line happens now by clicking anywhere
    on that line. Previously, the user had to click on the checkbox at the start of the line.

.. rubric:: System administration

- | Self-diagnoses check for required python third party packages.
  | Missing python package will now be reported as an error whenever you run frepplectl.

.. rubric:: Integration

- | REST API didn't support the operator "in" for all fields.


6.11.0 (2021/01/24)
===================

.. rubric:: Production planning

- | Bug fix: when importing approved manufacturing orders assigned to a resource from a
    resource group an incorrect calendar was assigned.

- | Bug fix: Corrected corner cases where size constraints on an operation are contradicting
    each other. Rather than keeping the order unplanned we now automatically resolve the conflict
    by relaxing the constraint.

.. rubric:: User interface

- | Improvements to the messaging and follower features.
  | When you follow an object you can choose to follow also activity on related objects.
    Eg When you follow an item, you can choose to also follow the purchase orders, manufacturing orders
    distribution orders for the item. Eg when you follow a resource, you can choose to follow also the
    manufacturing orders planned on that resource.
  | You can also add other people as followers.

- | FrePPLe now uses machine-assisted translations.
  | As a user, you will no longer see a partially translated user interface. Instead
    you'll see a completely translated user interface, with a few translations that are a bit off.
  | As a translator, your task is now simpler. You no longer need to type everything from scratch.
    Instead you'll just need to review the pre-translated strings and correct them where needed.

- | The create_buckets command now correctly supports ISO 8601 week numbers.

.. rubric:: Development

- | FrePPLe is now using the cmake build system rather than the archaic autotools.
  | End users won't see any change (i.e. the same source code is still compiled into the same
    executables), but the source code meta data is now much cleaner and better.

- | On Windows we no longer support deployments using the apache web server or the cygwin compiler.
  | The Windows installer with the embedded web server and PostgreSQL database remains fully supported.
    It provides an easy start for small deployments and/or trials. Bigger and more scalable deployments
    are only possible with a linux server.

6.10.0 (2020/12/06)
===================

.. rubric:: User interface

- | Restructured the edit forms for all entities. The main fields are now clearly
    separated from advanced fields and related objects.

- | The `comment and audit trail functionality <user-interface/getting-around/messages.html>`_
    has been completely revamped.
  | You can now upload attachments.
  | You can also follow objects. When there are changes to it, you will get a notification
    in your `inbox <user-interface/getting-around/inbox.html>`_.
  | This feature will be further improved in the next releases.

- | Users can now `upload an avatar image <user-interface/getting-around/user-preferences.html>`_.

- | Updated the list of default fields in all reports. By default we keep the
    reports now as lean as possible. More advanced fields are hidden by default.

- | New "is child of" filter operator that makes it easy to filter data for a part
    of the item, location or customer hierarchy.

- Bug fix: filtering on choice fields was broken when a language different from English is used.

.. rubric:: Third party components

- | Added required Python packages: pillow and psutil
  | Install these by running "pip3 install pillow psutil"

.. rubric:: System administration

- | Users can now upload attachments and their avatars. These files are stored in the folder
    /var/log/frepple/uploads.
  | Your backup procedures (don't tell me you don't have any...) should now include this folder.

6.9.0 (2020/11/07)
==================

.. rubric:: User interface

- A new get-started wizard is added to generate forecast for a single item.
  Fill in a simple form with the item, location, customer and recent sales
  history, and we'll populate the data tables and generate the statistical forecast.

- A new get-started wizard is added to generate a production plan for a single
  sales order. Fill in the details of the sales order, define the supply path
  and we'll populate the data tables and generate the production plan.

- A data loading wizard which is already available on the Enterprise and Cloud
  Editions for a long time. It is now also made available on the Community Edition.

- The cockpit is renamed to `home <user-interface/cockpit.html>`_.

- Bug fix: frozen columns were not handled correctly in favorites.

6.8.0 (2020/10/03)
==================

.. rubric:: User interface

- | `Filtering data <user-interface/getting-around/filtering-data.html>`_ has been made more easier.
    The search expression editor is still available, but a simple search for a value in a text
    field can now be performed with less clicks.

- | Addition of the `data source URL <user-interface/getting-around/exporting-data.html>`__ in the export dialog
    for easier export of frePPLe data into Excel. External applications can now directly pull frePPLe
    data online from a URL, which bypasses the export-import steps you do manually now.

- | Updated `demand gantt report <user-interface/plan-analysis/demand-gantt-report.html>`_
    to make zooming in&out easier and to show also item information.

.. rubric:: Integration

- | Authentication to all URLs of the application is now possible with
    `a JSON web token <https://jwt.io/introduction/>`_ or
    `basic authentication with user&password <https://en.wikipedia.org/wiki/Basic_access_authentication>`_.
    This feature makes it easy for other applications to pull data or embed frePPLe.
  | This feature can be disabled by commenting out the HTTPAuthentication middleware
    in your djangosettings.py file.

- `Remote API <integration-guide/remote-commands>`_ to cancel running tasks.

6.7.0 (2020/08/29)
==================

.. rubric:: Production planning

- | Advanced customization: Some python code can now customize the sequence in which
    demands are prioritized and planned.

.. rubric:: User interface

- | New demand history, purchase order history and inventory history widgets on the
    `cockpit <user-interface/cockpit.html>`_ screen.
  | FrePPLe will now record historical plan data. In following releases you can expect
    historical plan information to start appearing in additional screens.

- | The `search box <user-interface/getting-around/navigation.html>`_ now allows
    you to open the search results in a new browser tab. Using different browser tabs is very
    handy when you don't like to lose the previous screen.
  | You can already achieve this on all links by using the right-click menu of your
    browser. We made that a bit easier now in the search box.

- | Addition of a tooltip with column name when hovering on column headers.

- | `Custom reports <user-interface/report-manager.html>`_ now support filtering,
    sorting, customization and favorites. Just as all other screens.

- | Added Ukrainian translations. Thanks Michael!

- | Added Croatian translations. Thanks Blago!

.. rubric:: Odoo integration

- The odoo addon is moved to its own github repository: https://github.com/frePPLe/odoo
  We hope this makes it easier for odoo implementation partners to install the addon and
  contribute enhancements.

.. rubric:: Windows installer

- | The windows installer now has an option to send us anonymous usage information.
  | The usage data will provide us valuable information to guide our roadmap and continue
    improving the tool. The data is anonymous and will never be shared with third parties.
  | The option is disabled by default.

6.6.0 (2020/06/19)
==================

.. rubric:: Production planning

- | Implemented user interface and REST API to switch to manufacturing orders to
    alternate materials.

.. rubric:: User interface

- | Some dialog boxes had the confirmation button on the left, some had it on the right.
    We now consistently place the confirmation button always on the right.

- | Revamped the workflow to identify items with many late demands. A new widget on the
    cockpit "analyze late demand" displays a top 20 of items with late demand. From there
    you can drill down into the "demand report" of an item to review the backlog situation
    and the constraints causing the lateness.

- | Scenario management: Logged user won't see anymore in the scenario management screen
    in use scenarios where he/she is not active.

- | Export dialog: Addition of scenarios in the dialog so that user can export current view and
    scenarios (for which user has permission) in the same spreadsheet/csv file.

- | Manufacturing order, purchase order and distribution order detail: Addition of upstream and downstream
    widgets. When selecting a row, 2 new widgets are displayed to track the source and destination of the material.
    It shows how it has been produced/replenished (upstream widget) and where it will be
    consumed/delivered (downstream widget).

- | There is a change in how rows are selected in grids where multiple selection is allowed.
    Clicking on a the checkbox of a row will extend existing selection to that new row. Clicking anywhere else in the
    row will reset existing selection and only that new row will be selected.

6.5.0 (2020/05/16)
==================

.. rubric:: Production planning

- | The release fence of operations is now expressed in available time, rather than calendar time.

- | Material production or consumption can now be offset with a certain time from
    the start or end of a manufacturing order.
  | This can be used to model a cooldown, drying or testing time: Material is only produced a
    certain amount of time after the end of the manufacturing order.
  | It can also be used to model a material preparation or picking time: Material is consumed
    a certain amount of time before the start of the manufacturing order.

.. rubric:: User interface

- | Supply path: Alternate operation with low priority (less preferred) will be displayed in light-blue.

- | Simplified the tabs on the item screen to ease navigation and give quick access to the
    inventory report for that item.

- | Network status: Completed operations are taken into account to calculate the on hand column
    of the network status widget.

- | Search box: The search box in the menu looks also for a match in the description field. If
    a description exists, it is now displayed next to the name of the object.

- | Simplified the process of
    `translating the user interface <developer-guide/translating-the-user-interface.html>`_.

.. rubric:: Integration

- A `task scheduler <command-reference.html#scheduletasks>`_ allows users to
  a series of tasks automatically based on schedule.

.. rubric:: Odoo connector

- Various fixes contributed by Robinhli, Jiří Kuneš and Kay Häusler. Many thanks to our
  user community!

6.4.0 (2020/04/04)
==================

.. rubric:: Production planning

- | Simpler and more efficient modeling capabilities for
    `make-to-order and configure-to-order supply chains <examples/buffer/make-to-order.html>`_.
    The (complete or partial) supply path can now automatically be made specific to a
    sales order or an item attribute.
  | In earlier releases this was already possible, but required a more complex data interface.

- | Resources can now be assigned to a setup matrix changeover. The extra resource is required
    to perform the changeover - typically a technician to reconfigure the machine or a tool that is
    needed during the setup change.
  | Only unconstrained resources can be assigned for the changeover. The solver can't handle
    constraints on the changeover resource.

.. rubric:: User interface

- | Scenario Management: It is possible now to promote a scenario to production. All data of the scenario
    will be copied to production database.

- | Email exported reports: Reports that have been exported using *Export plan result to folder* command can be
    emailed to one or more recipients with a new command in the
    `execute <command-reference.html#emailreport>`_ screen.

6.3.0 (2020/02/28)
==================

.. rubric:: Production planning

- | Solver enhancement to improve planning with alternate materials.
  | In earlier releases available inventory and committed supply were considered individually
    for each alternate material.
  | From this release onwards, the algorithm checks available stock and supply across all
    alternate materials before generating new replenishments.

.. rubric:: User interface

- You can now `save frequently used report settings as a favorite <user-interface/getting-around/favorites.html>`_.
  This can be huge time saver in your daily review of the plan.

- A new `report manager <user-interface/report-manager.html>`_
  app allows power users to define custom reports using SQL. This greatly enhances
  the flexibility to tailor the plan output into reports that match your
  business process and needs.

.. rubric:: Integration

- Data files in SQL format can now be processed with the command
  `import data files <command-reference.html#importfromfolder>`_.
  For security reasons this functionality is only active when the setting SQL_ROLE is
  set. It should be configured by an administrator to a database role that is correctly
  tuned to a minimal set of privileges.

- Data files in the PostgreSQL COPY format can now be processed with the command
  `import data files <command-reference.html#importfromfolder>`_.
  Data files in this format are uploaded MUCH faster.

- Postgresql foreign key constraint on operationplanmaterial and operationplanresource
  for the operationplan_id field is made cascade delete. As a conseqeunce, there is no need
  anymore to delete the operationplanmaterial (Inventory Detail) and operationplanresource
  (Resource Detail) records before being able to delete an operationplan record (MO/PO/DO).

.. rubric:: Documentation

- Browsing the documentation is now more intuitive. A feature list allows you to find
  your way by functional topic.

- A new section with videos on common use cases is added.

- The `tutorial for developing custom apps <developer-guide/user-interface/creating-an-extension-app>`_
  has been refreshed and extended.

.. rubric:: Odoo connector

- Adding support for odoo v13.

- v12 and v13: Export of multiple POs for the same supplier will create a single PO in odoo
  with multiple lines. If the exported POs also contain multiple lines for the same product,
  then a single PO Line is created in odoo with the sum of the quantities and the minimum
  planned date of all exported records for that product.

6.2.0 (2020/01/17)
==================

.. rubric:: Production planning

- Currentdate parameter now accepts most known formats to represent a date and/or time.

.. rubric:: User interface

- | The last-modified fields and the task execution dates are now shown in the
    local timezone of your browser.
  | For on-premise installations this doesn't change anything. However, our cloud
    customers across the world will be happy to better recognize the timestamps.

- | Ability to filter on json fields such as the "Demands" field of manufacturing/distribution/purchase
    orders table.

- When exporting Excel files, read-only fields are now visually identifiable in the
  header row. A color and comment distinguish read-only fields from fields that can be
  updated when uploading the data file.

.. rubric:: Integration

- Export of duration fields will not be in seconds anymore but will use same format used
  in the tool: "DD HH:MM:SS". This change is effective for both csv and Excel exports.

.. rubric:: Development

- New mechanism to build Linux packages. The new, docker-based process makes supporting
  multiple linux distributions much easier.

.. rubric:: Security

- | A vulnerability in the django web application framework was identified and corrected.
    The password reset form could be tricked to send the new password to a wrong email address.
  | The same patch can be applied to earlier releases. Contact us if you need help for this.
  | See https://www.djangoproject.com/weblog/2019/dec/18/security-releases/ for full details.
  | By default frePPLe doesn't configure an SMTP mail server. The password reset functionality
    isn't active then, and you are NOT impacted by this issue.


6.1.0 (2019/11/29)
==================

.. rubric:: Production planning

- Bug fixes in the solver algorithm when using alternate materials.

- Bug fixes in the solver algorithm when using post-operation times at many
  places in the supply path.

- The `demand Gantt report <user-interface/plan-analysis/demand-gantt-report.html>`_
  got a long overdue refreshed look and now displays more information.

.. rubric:: User interface

- | Filter arguments are now trimmed to provide a more intuitive filtering. The invisible
    leading or trailing whitespace lead to confusion and mistakes.
  | On the other hand, if you were filtering on purpose with such whitespace: this is
    no longer possible.

- Support for user-defined attributes on purchase orders, manufacturing orders and
  distribution orders.

- Bug fix: The  user permissions "can copy a scenario" and "can release a scenario"
  were not working properly.

- Enhancement of the supply path to draw cases where producing operation materials
  record is missing (produced item declared at operation level) or produced item is only
  declared at routing level.

.. rubric:: Integration

- Renamed the command "create_database" to "createdatabase" for consistency with the other commands.

- Bug fix: remote execution API failure on scenarios

- Various fixes to the connector for Odoo 12.

.. rubric:: Development

- A new screen allows to `execute SQL commands on the database <user-interface/executesql.html>`_.
  This new app is only intended to facilitate development and testing, and shouldn't be activated in
  production environments.

6.0.0 (2019/16/09)
==================

.. rubric:: Production planning

- | The name column in the
    `buffer table <model-reference/buffer.html>`_ is removed. The item and location
    fields are what uniquely defines a buffer.
  | This data model simplification makes data interfaces simpler and more robust.

- | Data model simplification: The `suboperation table <model-reference/suboperations.html>`_
    is now deprecated. All data it contained can now be stored in the operation table.
  | This data model simplification makes development of data interfaces easier.

- The default minimum shipment for a demand is changed from "round_down(quantity / 10)"
  to "round_up(quantity / 10)". This provides a better default for planning very slow moving
  forecasts.

- The resource type 'infinite' is now deprecated. It is replaced by a new field 'constrained' on
  resource. This approach allows easier activation and deactivation of certain resources as
  constraints during planning.

- When generating a constrained plan, the material constraint has been removed. It didn't really
  have any impact on the plan algorithm. The constraints actually used by the planning engine are
  capacity, lead time and the operation time fence.

- Improvements to the solver algorithm for bucketized resources and time-per operations.
  The improvements provide a more realistic plan when manufacturing orders span across
  multiple capacity buckets.

- Performance improvements in the evaluation of setup matrices.

- Bug fixes and improved log messages in the propagation of work-in-progress status information.

.. rubric:: User interface

- | Bug fix: When uploading a Purchase/Distribution/Manufacturing orders file with the
    "First delete all existing records AND ALL RELATED TABLES" selected, all purchase,
    manufacturing and distribution records were deleted.

- Addition of the duration, net duration and setups fields in the manufacturing order screen.

- Addition of Hebrew translations, contributed by https://www.minet.co.il/  Many thanks!

- Give a warning when users try to upload spreadsheets in the (very) old .XLS Excel format
  instead of the new .XLSX spreadsheet format.

- Performance improvement for the "supply path" and "where used" reports for complex and
  deep bill of materials.

.. rubric:: Integration

- | The REST API for manufacturing orders now returns the resources and materials it uses.
  | Updated resources and materials can also written back with API.

- Added support for integration with Odoo 12.

.. rubric:: Third party components

- | The third party components we depend on have been upgraded to new releases. Most
    notably upgrades are postgres 11 and django 2.2.
  | Postgres 10 remains supported, so upgrading your database isn't a must for installing
    this release.
  | When upgrading a linux installation from a previous release, use the following command
    to upgrade the Python packages. On Windows the new packages are part of the installer.
      sudo -H pip install --force-reinstall -r https://raw.githubusercontent.com/frepple/frepple/6.0.0/requirements.txt

- Support for running in Python virtualenv environments.

.. rubric:: Documentation

- Addition of "cookbook" example models on the following functionalities: alternate resources, resource efficiency.

5.3.0 (2019/07/06)
==================

.. rubric:: Production planning

- Bug fix: material shortages can be left in the constrained plan, when solving safety stock
  across multiple stages or in the presence of confirmed supply.

.. rubric:: User interface

- | The modelling wizard that guides new users in loading their first data in frePPLe is completely
    redesigned. It now provides a more complete, more structured and deeper guidance for getting
    started with frePPLe.
  | Currently this new wizard is not available in the Community Edition.

- A new guided tour is available. Previous guided tour was a journey around the different pages
  and features of frePPLe. New guided tour is composed of use case questions, illustrated in
  a short video.

- Filters for a report can now be updated easier. Rather than opening the search dialog
  again you can directly edit the filter description in the title.

- Multiple files can now be imported together in a grid. Opening the import box multiple times
  is a bit boring. Selecting or dragging multiple files is cooler.

- Bug fix. When using the Empty Database feature on either manufacturing or distribution or delivery or purchase orders
  then all orders (manufacturing + distribution + delivery + purchase) were deleted.

- Bug fix on backlog calculation of the `demand report <user-interface/plan-analysis/demand-report.html>`_

5.2.0 (2019/05/27)
==================

.. rubric:: Production planning

- | Modeling simplication: In the `operation material table <modeling-wizard/manufacturing-bom/operation-materials.html>`_
    you had to always insert both the produced material and consumed materials.
  | In a lot of models an operation always produces 1 unit of the item. In this type
    of model you can now choose to leave out the records for the produced material.
    We'll automatically add them with makes your modeling and data interfaces easier,
    faster and less error-prone.
  | If an operation produces a quantity different from 1 the producing operation material
    record remains necessary.

- Performance improvements in the solver algorithm.

- Operations loading multiple bucketized resource now use the effiency of that resources.
  In earlier releases we used the minimum efficiency of all resources that operation loads,
  which is the correct behavior for resources of type default but not for bucketized resources.

- Bug fix to avoid creating excess inventory in models with large operation minimum
  sizes.

.. rubric:: User interface

- Various small styling improvements and usability enhancements.

.. rubric:: Odoo connector

- Bug fixes in the mapping of open and closed sales orders.

5.1.0 (2019/04/22)
==================

.. rubric:: Production planning

- Performance improvements for the bucketized resource solver.

- Bug fix and improvements in the way that completed and closed manufacturing order status
  is propagated to upstream materials.

.. rubric:: User interface

- | A new filter type is introduced for date fields. You can now easily filter records
    with a date within a specified time window from today.
  | In earlier versions you had to explicitly change the date argument for the filter every
    day. Which was quite boring, error-prone and not very user friendly.

- The number format in grid no longer has a fixed number of decimals, but flexibly adapts to
  the size and number of decimals in the number to be shown.

- | The login form now offers the option to remember me the login credentials. This avoids that
    a user has to login every time a browser session on frePPLe is started.
  | The user session information is persisted in a cookie in your browser. The session cookie will
    expire after a period of inactivity (configurable with the setting SESSION_COOKIE_AGE), after
    which the user has to log in again.
  | Security sensitive deployments should set this setting equal to 0, which forces users
    to log in for every browser session.

- When logging in, the user names and email address are now evaluated case-insensitively.


5.0.0 (2019/03/16)
==================

.. rubric:: Production planning

- | The identifier of `purchase orders <model-reference/purchase-orders.html>`_,
    `distribution orders <model-reference/purchase-orders.html>`_ and
    `manufacturing orders <model-reference/purchase-orders.html>`_, has been removed.
  | The reference field is now the primary key, and a required input field.
  | The required reference fields is an API-breaking change.

- | A new status "completed" is added on purchase orders, distribution orders and
    manufacturing orders. It models a status where the order has already completed, but the
    ERP hasn't reflected this yet in its inventory status.
  | When changing the status of a manufacturing order to completed, there is also logic to assure
    that sufficient upstream material is available. If required the status of feeding purchase orders,
    distribution orders and manufacturing orders is changed to completed.

- | The `resource detail <model-reference/operationplan-resources.html>`_ and
    `inventory detail  <model-reference/operationplan-materials.html>`_ tables
    are now editable.
  | This allows to import detailed information on allocated resources and consumed materials from
    the ERP system, and model the current work-in-progress in full detail.
  | In earlier releases these tables only contained output generated by the planning algorithm.
    From this release onwards they also contain input information for manufacturing orders
    in the status approved and confirmed.

- | The default of the parameter `plan.autoFenceOperations <model-reference/parameters.html>`_
    is changed from 0 to 999.
  | By default, the planning algorithm now waits for any existing confirmed supply before proposing
    a new replenishment.
  | The new default avoids unnecessary duplicate replenishments and results in more intuitive plans.

- | The search mode to choose among different alternate replenishments can now be controlled by the user.
  | In previous releases this could only be controlled on operations of type 'alternate', and automatically
    generated alternates always used priority as the selection mode.
  | From this release onwards the field 'operation.search mode' can be used to specify the selection
    mode from among 'priority', 'minimum cost', 'minimum penalty' and 'minimum cost + penalty'.

- The item table gets some read-only fields which capture some key metrics:
  - number of late demands
  - quantity of late demands
  - value of late demands
  - number of unplanned demands
  - quantity of unplanned demands
  - value of unplanned demands

- The resource table gets a read-only field to store the number of overloads on the resource.

- The weight field for problems of type 'late' is now indicating the quantity being planned late.
  In earlier releases it represented the delivery delay.

- Performance optimizations for various corner cases.

.. rubric:: Odoo connector

- Workcenters assigned manufacturing orders are now also imported.

- Bug fix: Manufacturing orders in the state "ready to produce" were not being sent to
  frePPLe as work-in-progress.

4.5.0 (2019/01/25)
==================

.. rubric:: Production planning

- The default allowed delivery delay of sales orders and forecasts is changed from indefinite
  to 5 years. This improves the performance of the algorithms in case there are unplannable
  orders.

- A new resource type `time buckets <model-reference/resources.html#>`_ is introduced
  that represents capacity as the number of hours of availability per time bucket.

- The capacity consumption from a bucketized resource now also has a constant component
  and considers the resource efficiency.

- Addition of the field size maximum to the item supplier and item distribution tables.

- | More detailed modeling of work in progress.
  | The parameters WIP.consume_material and WIP.consume_capacity control whether a confirmed
    manufacturing order consumes material and capacity.

- | More detailed modeling of in transit material.
  | By leaving the origin location empty, no inventory will be consumed at the origin location.
    We assume the material has already left the origin location and is in transit.
  | By leaving the destination location, the distribution order doesn't produce any stock.
    This represents a material transfer outside of our supply chain.

- Ability to use powerful regular expressions in the definition of
  `setup matrices rules <model-reference/setup-matrices.html#>`_ .

- Bug fix: calculation of operation time for 0-duration operations was wrong in some situations.

- Bug fix: incorrect operation duration when different resources in an aggregate pool resource
  have different working hours.

- Bug fix: corrected corner cases where the solver got into an infinite loop.

.. rubric:: User interface

- Ability to cancel any running task on the execution screen. Until now only the plan generation
  could be canceled while it was running.

- Improved performance and reduced memory footprint when downloading and exporting big reports.

- Added field duration to the
  `execution screen <user-interface/execute.html>`_

- Added tabs to see the manufacturing orders for a specific item, location or operation.

- Update of the "in progress" fields of the inventory report. Are considered in progress for a given bucket
  all orders starting before the end date of that bucket and ending after the end date of that bucket.

- Improved display of very small durations. All digits up to 1 microsecond are now visible.

.. rubric:: API

- The `database backup command <command-reference.html#backup>`_ and
  `database restore command <command-reference.html#restore>`_ now use the
  faster and smaller compressed binary backup format of PostgreSQL.

4.4.2 (2018/10/20)
==================

.. rubric:: Production planning

- Performance optimization for models with post-operation times by avoiding
  ineffecient search loops.

- The naming convention for distribution operations is changed from
  'Ship ITEM from ITEM @ SOURCE to ITEM @ DESTINATION' to
  the simpler and shorter 'Ship ITEM from SOURCE to DESTINATION'.

- Bug fix for a specific corner case where material requirements for work in progress
  aren't propagated at all.

- New parameter plan.resourceiterationmax allows user control over the number of searches
  for a free capacity slot on a resource. Contributed by Mateusz Knapik.

.. rubric:: User interface

- Added field net duration to the
  `resource detail report <user-interface/plan-analysis/resource-detail-report.html>`_

- Added fields total in progress, work in progress MO, on order PO, in transit DO to the
  `inventory report <user-interface/plan-analysis/inventory-report.html>`_

- Bug fix: Deleting an object from the edit form in a scenario was incorrectly
  deleting the object in the production instead.

- | The `import data files from folder <command-reference.html#importfromfolder>`_
    and `import a spreadsheet <command-reference.html#importworkbook>`_ functionalities
    now ignores spaces, dashes and underscores in the recognition of the content type from the
    file or worksheet name.
  | So far, only a worksheet called 'sales order' was recognized as containing sales order data.
    Now "sales-order", "sales_order" and "salesorder" will also be recognized.

.. rubric:: Third party components

- | The Ubuntu binaries will be compiled on Ubuntu 18 LTS from now onwards.
  | Compiling for Ubuntu 16 LTS remains fully supported, but we recommend to upgrade Ubuntu.

4.4.1 (2018/09/10)
==================

.. rubric:: Production planning

- Bug fix in the calculation of the lateness/earliness of a manufacturing
  order, purchase order or distribution order. The calculation was incorrectly
  based on the start date rather the end date of the operation in question.

- A new field "feasible" is now added to the
  `inventory detail report <user-interface/plan-analysis/inventory-detail-report.html>`_,
  `resource detail report <user-interface/plan-analysis/resource-detail-report.html>`_,
  `operation detail report <user-interface/plan-analysis/operation-detail-report.html>`_,
  `purchase order screen <model-reference/purchase-orders.html>`_,
  `distribution order screen <model-reference/distribution-orders.html>`_ and
  `manufacturing order screen <model-reference/manufacturing-orders.html>`_.
  The read-only boolean field indicates whether the order is violating any material, lead time or capacity
  constraints. This is useful in interpreting the results of an unconstrained plan.

- | The criterion for `before current problems <user-interface/plan-analysis/problem-report.html>`_
    is updated for confirmed orders. The change should result in less problems that are
    also more meaningful to the users.
  | For orders in the status approved or proposed a before-current problem is created when
    the start date is in the past.
  | For orders in the status confirmed the criterion the problem is now created when the
    end date is in the past, i.e. the order is overdue and should have been finished by now.

- The natural key in the `suboperation table <model-reference/suboperations.html>`_
  is changed from operation + suboperation + operation to operation + suboperation +
  effective start date.

.. rubric:: User interface

- Ability to make the data anonymous and obfuscated when
  `exporting an Excel workbook <command-reference.html#exportworkbook>`_.
  The names of all entities are obfuscated in the resulting spreadsheet. You will still
  need to carefully review the output to clean out any remaining sensitive data.

- Ability to customize the names for the time buckets used in the reports.
  The `time bucket generation command <command-reference.html#createbuckets>`_
  now has extra attributes for setting the name of the daily, weekly, monthly, quarterly
  and yearly buckets.

.. rubric:: Third party components

- | Support for Ubuntu 18 LTS.
  | Ubuntu 16 LTS remains fully supported.

- | Windows installer now uses Python 3.6.
  | Python 3.5 remains fully supported.

4.4.0 (2018/08/02)
==================

The Windows installer of this version isn't working correctly due to some packaging mistakes.

.. rubric:: Production planning

- Resources can now have an `efficiency percentage <model-reference/resources.html>`_. This allows
  the resource to perform an operation faster or slower than the standard operation time.

- The `resource report <user-interface/plan-analysis/resource-report.html>`_ now displays the
  available capacity as a line, replacing the green bar in previous releases to show the free capacity.

- | Performance optimization of the solver algorithm. The solver now passes down the minimum shipment
    information from the demand to all upstream entities, which allows the algorithm to perform a more
    efficient search.
  | In complex models, the resulting plan may be slightly different - for the better.

- Resource build-ahead penalty calculation now also working for 0-cost resources.

- New rows to the `purchase order summary <user-interface/plan-analysis/purchase-order-summary.html>`_
  and `distribution order summary <user-interface/plan-analysis/distribution-order-summary.html>`_
  reports to show the quantity on order or in transit.

- New rows to the `inventory report <user-interface/plan-analysis/inventory-report.html>`_
  to show 1) days of cover of the starting inventory, 2) the safety stock and 3) more details
  on the supply and consumption type.

- | The minimum field on the buffer defines a safety stock. In previous releases this safety stock was
    effective from the horizon start in 1971. Now this safety stock is effective from the current
    date of the plan onwards.
  | This change will give a different result for safety stock replenishments in an unconstrained plan.
    In a lead time constrained plan the results will be identical.

- Remove buffers of type procurement from the planning engine code. This buffer type was already long
  deprecated and hasn't been accessible to users for quite some time now.

- Simpler and more generic modeling of fixed material consumption and production by operations.
  The types 'fixed_end' and 'fixed_start' on `operation material <model-reference/operation-materials.html>`_
  records are replaced with a field 'fixed_quantity'.

- Renamed the "demand plan detail" report to `delivery orders <model-reference/operation-materials.html>`_,
  and enable uploading confirmed or approved shipments to customers as input data.

- | When expanding a confirmed manufacturing order on a routing operation, the automatic creation of the
    child manufacturing orders for each routing step now also considers the post-operation time.
  | Note that such child manufacturing orders are only generated if they aren't provided in the input
    data yet.

.. rubric:: User interface

- Bug fix when copying a what-if scenario into another what-if scenario.

- Bug fix when uploading data files using the Microsoft Edge browser.

.. rubric:: Deprecation

- | Operations of types alternate, routing and split should not load any resources,
    or consume or produce materials. The suboperations should model all material and capacity
    usage instead.
  | Note that in the majority of models, the explicit modeling of alternate operations is no
    longer needed. The planning engine detects situations where an item-location can be replenished
    in multiple ways and automatically generates an alternate operation.

4.3.4 (2018/06/08)
==================

.. rubric:: Production planning

- Added new reports `purchase order summary <user-interface/plan-analysis/purchase-order-summary.html>`_
  and `distribution order summary <user-interface/plan-analysis/distribution-order-summary.html>`_
  to summarize the purchase orders or distribution orders per time bucket.

- For consistency with the previous change, the operation report is renamed
  to `manufacturing order summary <user-interface/plan-analysis/manufacturing-order-summary.html>`_.

.. rubric:: Integration

- Extended the `exporttofolder <command-reference.html#exporttofolder>`_
  command to export additional plan results into CSV or Excel files.

- The data type of all numeric fields is changed from 15 digits with 6 decimals
  to 20 digits with 8 decimals. This allows a larger range of numbers to be
  accurately represented in the database.

- The `remote web commands API <integration-guide/remote-commands.html>`_ now
  supports user authentication with `JSON Web Tokens <https://jwt.io/>`_ to launch tasks,
  download data and upload data.

4.3.3 (2018/05/03)
==================

.. rubric:: Production planning

- Solver performance optimization where there are availability calendars.
  The plan generation time can be reduced with a factor 3 to 4 in some models.
- Solver enhancements for planning with setup matrices.
- Solver optimization to handle infinite buffers more efficiently.
- Bug fix: Compilation error with Python 3.6

.. rubric:: User interface

- Bug fix for spreadsheet import: more robust handling of empty rows and rows with
  empty fields at the end

.. rubric:: Odoo connector

- Correction to maintain a single root hierarchy.


4.3.2 (2018/03/19)
==================

.. rubric:: Production planning

- | New operationmaterial policy 'transfer_batch' which allows material production
    or consumption in a number of batches of fixed size at various moments during
    the total duration of the operationplan.
  | A new field operationmaterial.transferbatch is introduced.
- A new field 'end items' is added to the manufacturing order, purchase order and
  distribution orders screens. It is similar to the 'demands' which shows the
  demands

.. rubric:: API

- Bug fix: backward compatibility after command renaming in 4.3.1

.. rubric:: Third party components

- Upgrade to PostgreSQL 10.
  PostgreSQL 9.5 and 9.6 remain fully supported.

4.3.1 (2018/02/17)
==================

.. rubric:: Bug fixes

- The autofence now also considers approved supply, and not only confirmed supply.
- Excel files with some non-standard internal structure are now also recognized.
- Work-in-progress operationplans with quantity 0 are no longer rejected.

.. rubric:: Deprecations

- Command frepple_run is renamed to runplan.
- Command frepple_runserver is renamed to runwebserver.
- Command frepple_copy is renamed to scenario_copy.
- Command frepple_importfromfolder is renamed to importfromfolder.
- Command frepple_exporttofolder is renamed to exportfromfolder.
- Command frepple_flush is renamed to empty.
- Command frepple_backup is renamed to backup.
- Command frepple_restore is renamed to restore.
- Command frepple_simulation is renamed to simulation.
- Command frepple_createbuckets is renamed to createbuckets.
- Command frepple_createmodel is renamed to createmodel.
- Command frepple_loadxml is renamed to loadxml.
- Command frepple_runworker is renamed to runworker.
