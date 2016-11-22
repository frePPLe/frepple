var introdata = {
  '/': [
    {
      element : '#cockpitcrumb',
      description : "The <strong>cockpit</strong> is a dashboard with widgets to give an overall health of the supply chain:" +
                    "<ul><li style='list-style:initial'>Purchase orders</li>" +
                    "<li style='list-style:initial'>Manufacturing orders</li>" +
                    "<li style='list-style:initial'>Distribution orders</li>" +
                    "<li style='list-style:initial'>Late orders</li>" +
                    "<li style='list-style:initial'>Resource utilization</li>" +
                    "<li style='list-style:initial'>Delivery performance</li>" +
                    "<li style='list-style:initial'>...</li></ul>" +                     
                    "The dashboard can easily be personalized by each user.",
      position : 'right'
    },
    {
      element : '#Purchasing',
      description : "The purchasing section contains:<br>" +
      "<ul><li style='list-style:initial'>The <strong>purchase orders widget</strong> provides as quick summary of the purchase orders</li>" +
      "<li style='list-style:initial'>The <strong>purchase order analysis</strong> highlights purchase orders that are critical and need expediting</li>" +
      "</ul>",
      position : 'top'      
    },
    {
      element : '#Distribution',
      description : "The distribution section contains:<br>" +
      "<ul><li style='list-style:initial'>The <strong>distribution orders widget</strong> provides as quick summary of the distribution orders</li>" +
      "<li style='list-style:initial'>The <strong>stockout risk widget</strong> shows per location how many items are running low on inventory</li>" +
      "</ul>",
      position : 'top'
    },
    {
      element : '#Manufacturing',
      description : "The manufacturing section contains :<br>" +
      "<ul><li style='list-style:initial'>The <strong>manufacuring orders widget</strong> provides as quick summary of the manufacturing orders</li>" +
      "<li style='list-style:initial'>The <strong>resource utilization widget</strong> lets you find out how loaded your resources are</li>" +
      "<li style='list-style:initial'>The <strong>capacity alerts widget</strong> displays any alert associated to capacity</li>" +
      "</ul>",
      position : 'top'
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
        '<li style="list-style:initial">Status: Status of the demand. Possible values are “open”, “closed”.</li>' +
        '</ul>',
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
        '<li style="list-style:initial">Price: Cost or price of the item.</li>' +
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
        description : 'A buffer is a storage for a item. It represents a place where inventory of an item is kept. ' +
          "It's often called SKU, i.e. it’s a unique item-location combination.<br><br>" +
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
    "/data/input/skill/": [
      {
        element : 'h1 small',
        description : 'A <strong>skill</strong> defines a certain property that can be assigned to resources.<br><br>' +
          'A load models the association of an operation and a resource. A load can specify a skill required on the resource.<br><br>" +
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
  "/resource/": [
     {
      element : 'h1 small',
      description : 'This report shows the <strong>resource utilization</strong> per time bucket.<br><br>' +
        'For each resource and time bucket the report shows:<br>' +
        '<ul><li style="list-style:initial">Available resource-hours</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#F6BD0F"></i>&nbsp;Unvailable resource-hours, suchs off-shift time, weekends and holidays</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#2B95EC"></i>&nbsp;Setup resource-hours, ie time involved in changeovers</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#AFD8F8"></i>&nbsp;Load resource-hours</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#8BBA00"></i>&nbsp;Free resource-hours, available capacity not yet utilized</li>' +
        '<li style="list-style:initial">Utilization percentage, defined as load / available time</li>' +
        '</ul>',
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
  "/operation/": [
    {
      element : 'h1 small',
      description : 'This report summarizes the <strong>planned operations</strong>.<br>' +
        'It displays what operations we are planned to start and finish.<br><br>' +
        'For each operation and time bucket the report shows:' +
        '<ul><li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#113C5E"></i>&nbsp;Confirmed starts: work-in-progress or frozen quantity started in the bucket</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#2B95EC"></i>&nbsp;Proposed starts: quantity of new operations to start in the bucket</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#7B5E08"></i>&nbsp;Confirmed ends: work-in-progress or frozen quantity ending in the bucket</li>' +
        '<li style="list-style:initial"><i class="fa fa-square" aria-hidden="true" style="color:#F6BD0F"></i>&nbsp;Proposed ends: quantity of new operations to end in the bucket</li>' +
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
  "/data/input/itemdistribution/": [
    {
      element : 'h1 small',
      description : 'Item distributions define that a location can be replenished ' +
        'with a <strong>transport from another location</strong>.<br><br>' +
        'The main fields are:' +
        '<ul><li style="list-style:initial">Item: The item to transfer.</li>' +
        '<li style="list-style:initial">Destination location: The destination location where the item can be transfered.</li>' +
        '<li style="list-style:initial">Origin location: The origin location where the item is transfered from.</li>' +
        '<li style="list-style:initial">Lead time: Transfer lead time.</li>' +
        '</ul>',
      position : 'right'
    }
    ]
};
