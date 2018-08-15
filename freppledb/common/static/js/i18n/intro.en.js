var introdata = {
  '/': [
    {
      element : '#cockpitcrumb',
      description : "The cockpit is a <strong>dashboard</strong> providing an overview of " +
      		"the overall health of the supply chain.<br><br>" +
          "The dashboard can be personalized by each user.",
      position : 'right'
    }
  ],
  "/data/input/demand/": [
    {
      element : 'h1 small',
      description : 'The <strong>sales orders table</strong> represent all the orders placed by your customers.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Name: Unique name of the demand.</li>' +
        '<li style="list-style:initial">Quantity: Requested quantity.</li>' +
        '<li style="list-style:initial">Item: Requested item.</li>' +
        '<li style="list-style:initial">Location: Requested shipping location.</li>' +
        '<li style="list-style:initial">Due: Due date of the demand.</li>' +
        '<li style="list-style:initial">Customer: Customer placing the demand.</li>' +
        '<li style="list-style:initial">Status: Status of the demand. Possible values are "open", "closed".</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/deliveryorder/": [
      {
        element : 'h1 small',
        description : 'The report shows the details of the <strong>deliveries planned for each demand</strong>. ' +
          'Late and short deliveries can easily be identified.<br><br>' +
          'This report is typically accessed as a drilldown from other reports, or to export the delivery ' +
          'plan to external systems.',
        position : 'right'
      }
  ],
  "/demand/": [
    {
      element : 'h1 small',
      description : 'This report shows the <strong>demand and supply</strong> of all items.<br><br>' +
        'For each item and time bucket the report shows:' +
        '<ul><li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#2B95EC"></i>&nbsp;Demand: demands with due date in that bucket.</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#F6BD0F"></i>&nbsp;Supply: planned shipments in that bucket</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#8BBA00"></i>&nbsp;Backlog: Represents the cumulative delta between the demand and the supply.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/constraint/": [
    {
      element : 'h1 small',
      description : 'This report shows the reason(s) <strong>why a demand is planned short or late</strong>.<br><br>'+
        'This can be:' +
        '<ul><li style="list-style:initial">before current: not enough lead time to buy, transport or produce.</li>' +
        '<li style="list-style:initial">overload: not enough capacity available.</li>' +
        '<li style="list-style:initial">material shortage: not enough material is available.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/problem/": [
    {
      element : 'h1 small',
      description : 'This screen shows a list of <strong>alerts</strong> requiring the planner’s attention.<br><br>' +
        'Check out the documentation page for a list of available alert types.',
      position : 'right'
    }
  ],
  "/data/input/customer/": [
    {
      element : 'h1 small',
      description : 'The <strong>customers table</strong> contains all the customers passing orders to your business.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Name: Unique name of the customer.</li>' +
        '<li style="list-style:initial">Description: Free format description.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/item/": [
    {
      element : 'h1 small',
      description : 'The <strong>items table</strong> contains all the items that you want to manage in your supply chain.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Name: Unique name of the item.</li>' +
        '<li style="list-style:initial">Description: Free format description.</li>' +
        '<li style="list-style:initial">Cost: Cost or price of the item.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/location/": [
    {
      element : 'h1 small',
      description : 'The <strong>locations table</strong> contains the different locations included in ' +
        'your model. A location can be a warehouse, a distribution center, a factory, a shop...<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Name: Unique name of the location.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/buffer/": [
    {
      element : 'h1 small',
      description : 'A buffer is a storage for a item. It is a unique item x location ' +
        'combination where inventory is kept.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Name: Name of the buffer. Use the ' +
        'format "item @ location".</li>' +
        '<li style="list-style:initial">Location: Location of the buffer.</li>' +
        '<li style="list-style:initial">Item: Item of the buffer.</li>' +
        '<li style="list-style:initial">Onhand: Inventory level at the start of the time horizon. ' +
        'Considered as 0 if left empty.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/flowplan/": [
    {
      element : 'h1 small',
      description : 'The report shows the <strong>details of all material production and consumption</strong>.<br><br>' +
        'This report is typically accessed as a drilldown from other reports, or to export detailed ' +
        'plan information to external systems.',
      position : 'right'
    }
  ],
  "/buffer/": [
    {
      element : 'h1 small',
      description : 'This report shows the <strong>inventory profile</strong> of all SKUs.<br>' +
        'It displays how much inventory we plan to have for each raw ' +
        'material, end product or intermediate product.<br><br>' +
        'For each buffer and time bucket the report shows:' +
        '<ul><li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#8BBA00"></i>&nbsp;Start Inventory: on hand at the start of the bucket</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#2B95EC"></i>&nbsp;Produced: quantity added during the bucket</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#F6BD0F"></i>&nbsp;Consumed: quantity consumed during the bucket</li>' +
        '<li style="list-style:initial">End Inventory: on hand at the start of the bucket</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/resource/": [
     {
      element : 'h1 small',
      description : 'This report shows the <strong>resource utilization</strong> per time bucket.<br><br>' +
        'For each resource and time bucket the report shows:<br>' +
        '<ul><li style="list-style:initial">Available resource-hours</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#F6BD0F"></i>&nbsp;Unvailable resource-hours due to off-shift, weekends and holidays</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#2B95EC"></i>&nbsp;Setup resource-hours, ie time involved in changeovers</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#AFD8F8"></i>&nbsp;Load resource-hours</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#8BBA00"></i>&nbsp;Free resource-hours, available capacity not yet utilized</li>' +
        '<li style="list-style:initial">Utilization percentage, defined as load / available time</li>' +
        '</ul>',
      position : 'right'
      }
     ],
  "/loadplan/": [
    {
      element : 'h1 small',
      description : 'The report shows the <strong>details of all loading on the resources</strong>.<br><br>' +
        'This report is typically accessed as a drilldown from other reports, or to export detailed ' +
        'plan information to external systems.',
      position : 'right'
    }
  ],
  "/data/input/resource/": [
    {
      element : 'h1 small',
      description : 'The <strong>resource table</strong>defines the machines and operators of your supply chain.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Name: Unique name of the resource.</li>' +
        '<li style="list-style:initial">Location: Location of the resource.</li>' +
        '<li style="list-style:initial">Maximum: Resource capacity.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/skill/": [
    {
      element : 'h1 small',
      description : 'A <strong>skill</strong> defines a certain property that can be assigned to resources.<br><br>' +
        'A load models the association of an operation and a resource. A load can specify a skill required on the resource.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Name: Name of the buffer. We recommend that you use the ' +
        'format "item @ location"</li>' +
        '<li style="list-style:initial">Location: Location of the buffer.</li>' +
        '<li style="list-style:initial">Item: Item of the buffer.</li>' +
        '<li style="list-style:initial">Onhand: Inventory level at the start of the time horizon. ' +
        'Considered as 0 if left empty.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/resourceskill/": [
    {
      element : 'h1 small',
      description : 'The <strong>resource skill table</strong> associates a certain skill with a resource.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Skill: Name of the skill.</li>' +
        '<li style="list-style:initial">Resource: Name of the resource.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/setupmatrix/": [
    {
      element : 'h1 small',
      description : 'The <strong>setup matrix table</strong> defines the time and cost of setup conversions on a resource. ' +
        'Within a setup matrix rules are used to define the changeover cost and duration.<br><br>' +
        '<strong>This feature is not ready for production use yet.</strong>',
      position : 'right'
    }
  ],
  "/data/input/purchaseorder/": [
    {
      element : 'h1 small',
      description : 'This table contains the <strong>open purchase orders with your suppliers</strong>.<br><br>' +
        'When generating a plan frepple will add new proposed purchase orders to this table.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Status: Possible values are "proposed", "confirmed" and "closed".</li>' +
        '<li style="list-style:initial">Item: The item purchased from that supplier.</li>' +
        '<li style="list-style:initial">Location: The location where the items will be received.</li>' +
        '<li style="list-style:initial">Supplier: The supplier the items are purchased from.</li>' +
        '<li style="list-style:initial">End date: The date of the purchase order delivery.</li>' +
        '<li style="list-style:initial">Quantity: The ordered quantity.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/supplier/": [
    {
      element : 'h1 small',
      description : 'This table contains all suppliers you are purchasing items from.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Name: Name of the supplier.</li>' +
        '<li style="list-style:initial">Resource: Free format description.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/itemsupplier/": [
    {
      element : 'h1 small',
      description : 'This table defines <strong>which items can be procured from which supplier</strong>.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Supplier: Name of the skill.</li>' +
        '<li style="list-style:initial">Item: The name of the item you procure from that supplier.</li>' +
        '<li style="list-style:initial">Location: The name of the location where the supplier can be used to purchase this item.</li>' +
        '<li style="list-style:initial">Lead time: Procurement lead time.</li>' +
        '<li style="list-style:initial">Cost: Purchasing cost. This info is optional.</li>' +
        '<li style="list-style:initial">Priority: Priority of this supplier among all suppliers from which this item can be procured.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/distributionorder/": [
    {
      element : 'h1 small',
      description : 'This table contains the <strong>open distribution orders</strong> of your supply chain.<br><br>' +
        'When generating a plan frepple will add new proposed purchase orders to this table.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Status: Possible values are "proposed", "confirmed" and "closed".</li>' +
        '<li style="list-style:initial">Item: The item purchased from that supplier.</li>' +
        '<li style="list-style:initial">Origin: The location where the item is transfered from.</li>' +
        '<li style="list-style:initial">Destination: The location where the item will be received.</li>' +
        '<li style="list-style:initial">End date: The date of the distribution order delivery.</li>' +
        '<li style="list-style:initial">Quantity: The quantity being transferred.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/itemdistribution/": [
    {
      element : 'h1 small',
      description : 'This table allows you to <strong>authorize the transfer of an item from one location to another location</strong> in your model.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Item: The item to transfer.</li>' +
        '<li style="list-style:initial">Location: The destination location where the item can be transfered.</li>' +
        '<li style="list-style:initial">Origin: The origin location where the item is transfered from.</li>' +
        '<li style="list-style:initial">Lead time: Transfer lead time.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/manufacturingorder/": [
    {
      element : 'h1 small',
      description : 'The manufacturing orders table contains <strong>the open manufacturing orders</strong> in your supply chain.<br><br>' +
        'When generating a plan frepple will add new proposed manufacturing orders to this table.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Status: Possible values are "proposed", "confirmed" and "closed".</li>' +
        '<li style="list-style:initial">Operation: The operation that should be run for the manufacturing orders.</li>' +
        '<li style="list-style:initial">End date: The date the manufacturing order ends.</li>' +
        '<li style="list-style:initial">Quantity: The produced item quantity.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/calendar/": [
    {
      element : 'h1 small',
      description : 'A calendar represents <strong>a numeric value that is varying over time</strong>.<br><br>' +
        'Calendars are used in a number of places:<ul>' +
        '<li style="list-style:initial">Working hours of locations.</li>' +
        '<li style="list-style:initial">Resource capacity when it varies over time</li>' +
        '<li style="list-style:initial">Safety stock of a buffer when it varies over time</li>' +
        '</ul>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Name: Unique name of the calendar.</li>' +
        '<li style="list-style:initial">Default: Default value.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/calendarbucket/": [
    {
      element : 'h1 small',
      description : 'A calendar bucket defines a <strong>calendar value valid for a specific period</strong>.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Value: The actual time-varying value.</li>' +
        '<li style="list-style:initial">Start: Start date of the validity of this bucket.</li>' +
        '<li style="list-style:initial">End: End date of the validity of this bucket.</li>' +
        '<li style="list-style:initial">Priority: Priority of this bucket when multiple buckets are effective for the same date.</li>' +
        '<li style="list-style:initial">Days: Bit pattern representing the days on which the calendar bucket is valid.</li>' +
        '<li style="list-style:initial">Starttime: Time when this entry becomes effective on valid days in the valid date horizon.</li>' +
        '<li style="list-style:initial">Endtime: Time when this entry becomes ineffective on valid days in the valid date horizon.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/operation/": [
    {
      element : 'h1 small',
      description : 'This table defines <strong>manufacturing operations</strong> consuming some items (a bill of material) ' +
        'to produce a new item. It also loads a number of resources during this process.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Name: Unique name of the operation.</li>' +
        '<li style="list-style:initial">Duration: Fixed operation time in seconds, independent of the units produced.</li>' +
        '<li style="list-style:initial">Duration_per: The operation time in seconds, per unit produced.</li>' +
        '<li style="list-style:initial">Type: Possible values : "time_per", "fixed_time", "routing", "alternate”, "split".</li>' +
        '<li style="list-style:initial">Location: The location where the operation takes place.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/operationmaterial/": [
    {
      element : 'h1 small',
      description : 'This table defines what <strong>item(s) an operation is consuming and producing</strong>.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Operation: The operation name consuming and producing items.</li>' +
        '<li style="list-style:initial">Quantity: The quantity of item consumed or produced. A negative quantity ' +
        'should be used for consumed items and positive quantity should be used for produced items.</li>' +
        '<li style="list-style:initial">Item: The item being consumed or produced.</li>' +
        '<li style="list-style:initial">Type: specify whether the stock should be consumed/produced at the ' +
        'start or at the end of the operation.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/operationresource/": [
    {
      element : 'h1 small',
      description : 'The operation resources table is <strong>associating a resource to an operation</strong>.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Operation: The operation name.</li>' +
        '<li style="list-style:initial">Resource: The resource name.</li>' +
        '<li style="list-style:initial">Quantity: How much capacity this operation is consuming from the resource.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/data/input/suboperation/": [
    {
      element : 'h1 small',
      description : 'Suboperations apply to operations of type "routing", "alternate", "split".<br>' +
        '<strong>Such operations own a number of child operations</strong>.<br><br>' +
        'The main fields are:<ul>' +
        '<li style="list-style:initial">Operation:  Sub-operation.</li>' +
        '<li style="list-style:initial">Resource: Parent operation.</li>' +
        '<li style="list-style:initial">Priority: For alternate operations: Priority of this alternate.<br>' +
        'For routing operations: Sequence number of the step.<br>' +
        'For split operations: Proportion of the demand planned along this suboperation.</li>' +
        '</ul>',
      position : 'right'
    }
  ],
  "/execute/": [
    {
      element : 'h1 small',
      description : 'From this screen you can launch <strong>a number of administrative actions</strong>.<br><br>' +
        'The main one is the <strong>plan generation</strong>, the top one in the list.',
      position : 'right'
    }
  ],
  "/kpi/": [
    {
      element : 'h1 small',
      description : 'This report shows some <strong>key metrics of the generated plan</strong>.<br><br>' +
        'In this way it allows quick review of the plan quality, comparisons between different plans, ' +
        'and validation of model or parameter changes.',
      position : 'right'
    }
  ],
  "/data/common/parameter/": [
    {
      element : 'h1 small',
      description : 'This table stores <strong>global settings and parameters</strong>.<br><br>' +
        'Only administrators need access to this table.',
      position : 'right'
    }
  ],
  "/data/common/bucket/": [
    {
      element : 'h1 small',
      description : 'Buckets are used to group time into smaller periods.<br><br>' +
        "<strong>This table is normally prepopulated upfront and you don't to worry about it.</strong>",
      position : 'right'
    }
  ],
  "/data/common/bucketdetail/": [
    {
      element : 'h1 small',
      description : 'Buckets are used to group time into smaller periods.<br><br>' +
        "<strong>This table is normally prepopulated upfront and you don't to worry about it.</strong>",
      position : 'right'
    }
  ],
  "/data/common/comment/": [
    {
      element : 'h1 small',
      description : 'Users can maintain <strong>free-text comments on objects</strong>.<br><br>' +
        "This table gives a list of comments users have entered.",
      position : 'right'
    }
  ],
  "/data/common/user/": [
    {
      element : 'h1 small',
      description : 'In this screen administrators can <strong>define users and their access rights</strong>.<br><br>' +
        'Read, write and delete permissions can be set per object type. Object types to which a certain user has no ' +
        'permissions will not show up in their menu bar.',
      position : 'right'
    }
  ],
  "/data/auth/group/": [
    {
      element : 'h1 small',
      description : 'In this screen administrators can <strong>define user groups or roles</strong>.<br><br>' +
        'Using roles makes maintenance of the user permissions easier and more flexible.',
      position : 'right'
    }
  ]
};
