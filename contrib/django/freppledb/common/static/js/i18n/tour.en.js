var tourdata = [
   // Main page of the tour
   {
     description: '<h2>Main</h2>' +
        'Jump to <span class="underline"><a href="/admin/?tour=1,0,0">Navigation</a></span> (5 steps)<br/>' +
        'Jump to <span class="underline"><a href="/admin/?tour=2,0,0">Data entry</a></span> (10 steps)<br/>' +
        'Jump to <span class="underline"><a href="/admin/?tour=3,0,0">Modeling</a></span> (3 steps)<br/>' +
        'Jump to <span class="underline"><a href="/admin/?tour=4,0,0">Generating the plan</a></span> (9 steps)<br/>' +
        'Jump to <span class="underline"><a href="/admin/?tour=5,0,0">Plan analysis</a></span> (25 steps)<br/>',
     delay: 5,
     steps: [
             {
               url: "/admin/",
               element : '.tourguide',
               description : "Welcome to frePPLe.<br/>" +
                 "This tutorial will show you around.<br/><br/>" +
                 "During the first 5 days of use this page<br/>" +
                 "will suggest you to take the tour.<br/>" +
                 "Later you can always start the tour from the menu.",
               position : 'TL'
             }
             ]
   },

   // Navigation
   {
     description: '<h2><span class="underline"><a href="/admin/?tour=0,0,0">Main</a></span> &gt; Navigation</h2>' +
        'The menu bar, the index page, breadcrumbs and a search allow easy and intuitive navigation',
     delay: 5,
     steps:
        [
         {
           url: "/admin/",
           element : '.menuBar',
           description : "The menu bar gives access to all screens.<br/>" +
                   "Screens that are not accessible with your profile won't be shown in the list.",
           position : 'BL'
         },
         {
           url: "/admin/",
           element : '#content-main',
           description : 'The home page also shows you the same screens as the menu, organized in folders.',
           position : 'TL'
         },
         {
           url: "/admin/",
           element : '.breadcrumbs',
           description : 'A breadcrumb trail shows the history of screens you have accessed.<br/>' +
                   'You can easily step back.',
           position : 'BL'
         },
         {
           url: "/admin/",
           element : '#recent-actions',
           description : 'This section of the screen shows your recent edit activities.',
           position : 'TL'
         },
         {
           url: "/admin/",
           element : '#search',
           description : 'You can type in a search string here.<br/>' +
                   'Automatically a list of matching entities is displayed.<br/>' +
                   'This allows you to jump immediately to the relevant screen of that entity.',
           position : 'B'
         }
       ]
    },

    // Data entry
    {
     description: '<h2><span class="underline"><a href="/admin/?tour=0,0,0">Main</a></span> &gt; Data entry</h2>' +
        'Data can be entered directly in a data grid or edit forms.<br/>' +
        'You can also import and export CSV-files.',
     delay: 5,
     steps:
        [
         {
           url: "/admin/",
           element : '.ui-accordion-content',
           description : "All entities have a data table in the input section.",
           position : 'R'
         },
         {
           url: "/data/input/demand/",
           element : "#jqgh_grid_customer",
           description : "We selected the demand table as an example.<br/>" +
             "Click a column header to sort the data.<br/>" +
             "Clicking a second time will reverse the sorting order.",
           position : 'BL'
         },
         {
           url: "/data/input/demand/",
           element : 'span[role="item"]',
           description : "A triangle on a field indicates a drill-drown menu.<br/>" +
             "Click the icon to display the detailed screens for the selected entity.<br/>" +
             "Screens that are not accessible with your profile won't be shown in this menu.",
           position : 'B'
         },
         {
           url: "/data/input/demand/",
           element : "#filter",
           description : "You can define filters to see a subset of the data.<br/>" +
             "The filter expression can use all attributes from the table<br/>" +
             "and combine them using AND and OR criteria",
           position : 'T'
         },
         {
           url: "/data/input/demand/",
           element : "#save",
           description : "You can directly edit data cells in the grid.<br/>" +
             "Click 'save' to store the changes in the database.<br/>" +
             "Clicking 'undo' will restore the original data.",
           position : 'T'
         },
         {
           url: "/data/input/demand/",
           element : "#add",
           description : "Clicking 'add' opens a form in which you can enter data for a new record.",
           position : 'T'
         },
         {
           url: "/data/input/demand/",
           element : "#copy_selected",
           description : "You can select some rows with the checkbox at the start of the row.<br/>" +
             "Click 'copy' to duplicate the records.<br/>" +
             "Click 'delete' to remove the selected records.",
           position : 'T'
         },
         {
           url: "/data/input/demand/",
           element : "#csvexport",
           description : "Click 'export' to export all data from the grid<br/>" +
              "to a CSV-file that can be edited in Excel.",
           position : 'L'
         },
         {
           url: "/data/input/demand/",
           element : "#csvimport",
           description : "The same CSV-files can also be imported.<br/>" +
             "The data are validated and any errors are reported.",
           position : 'L'
         },
         {
           url: "/data/input/demand/",
           element : ".tools",
           description : "Users of the <strong>Enterprise Edition</strong> also have the<br/>" +
             "ability to customize the report:<br/>" +
             "&nbsp;- Hide columns</br>" +
             "&nbsp;- Change the order of columns<br/>" +
             "&nbsp;- Choose the number of frozen columns<br/>" +
             "&nbsp;- Adjust the column width<br/>" +
             "These settings are saved for each individual user.",
           position : 'B'
         }
        ]
    },

    // Modeling
    {
     description: '<h2><span class="underline"><a href="/admin/?tour=0,0,0">Main</a></span> &gt; Modeling</h2>' +
        "Modeling your manufacturing environment.",
     delay: 5,
     steps:
        [
         {
           url: "/admin/",
           element : '.ui-accordion-content',
           description : "All entities have a data table in the input section.<br/>" +
             "A complete description of all entities and their relationships<br/>" +
             "is beyond the scope of this tour.<br/>" +
             "Check out the documentation.<br/><br/>" +
             "In this tour we'll only show the concepts at a very high level.",
           position : 'R'
         },
         {
           url: "/supplypath/item/product/",
           element : "#graph",
           description : "This report shows the bill of material of a particular item.<br/>" +
             "The top section visualizes the data as a network graph.<br/>" +
             "The bottom section displays the data as hierarchical tree.<br/><br/>" +
             "The network graph is very important in modeling in frePPLe.<br/>" +
             "Every single graphical object in this graph is stored as a single<br/>" +
             "record in the frePPLe model. The graph allows you to verify that<br/>" +
             "you have correctly filled in all data." +
             "&nbsp;- <i>Operations</i> are shown as rectangles.<br/>" +
             "&nbsp;- <i>Resources</i> are shown as circles.<br/>" +
             "&nbsp;- <i>Buffers</i>/SKUs are shown as triangles.<br/>" +
             "&nbsp;- The lines between operations and buffers are <i>flows</i>.<br/>" +
             "&nbsp;- The dotted lines between operations and resources are <i>loads</i>.<br/>",
           position : 'BL'
         },
         {
           url: "/supplypath/item/product/",
           element : "#tabs ul li:nth-child(2)",
           description : "The supply path report displays the structure upstream,<br/>" +
             "ie walking from end item towards the raw materials.<br/><br/>" +
             "The where-used report displays the structure downstream,<br/>" +
             "ie walking from the raw material towards the end items.<br/>" +
             "It thus displays which end items the selected entity is used for.",
           position : 'BL'
         },
        ]
    },

    // Planning tasks
    {
     description: '<h2><span class="underline"><a href="/admin/?tour=0,0,0">Main</a></span> &gt; Generating the plan</h2>' +
        "Generating plans and performing other tasks.",
     delay: 5,
     steps:
        [
         {
           url: "/admin/",
           element : '.ui-accordion-content',
           beforestep: '$("#content-main").accordion({active:2,animate:false})',
           description : "Once you have loaded all data, you are now<br/>" +
             "ready to generate the plan.",
           position : 'R'
         },
         {
           url: "/execute/",
           element : '#content h1',
           beforestep: '$("#tasks").accordion({active:false,animate:false})',
           description : "The top section show the log and status<br/>" +
             "of all tasks.",
           position : 'R'
         },
         {
           url: "/execute/",
           element : '#content-main h1',
           description : "The bottom section allows you to interactively launch new tasks.<br/><br/>" +
             "To automate tasks they can also be launched from the command line.",
           position : 'TL'
         },
         {
           url: "/execute/",
           element : 'a[href="#plan"]',
           beforestep: '$("a[href=\\"#plan\\"]").parent().click()',
           description : "You can generate constrained or unconstrained plans<br/>" +
             "and select which constraints to consider.<br/><br/>" +
             "A constrained plan will respect all constraints<br/>" +
             "but some demands can be planned late or incomplete.<br/><br/>" +
             "In an unconstrained plan all demand will be met at its due date<br/>" +
             "but some constraints can be violated.",
           position : 'TL'
         },
         {
           url: "/execute/",
           element : 'a[href="#scenarios"]',
           beforestep: '$("a[href=\\"#scenarios\\"]").parent().click()',
           description : "Here you can copy your dataset into a whatif scenario.<br/><br/>" +
             "A scenario is a complete copy of all data in a separate database.<br/>" +
             "All data and plans can thus be vary independently.<br/><br/>" +
             "Once a scenario has been copied, a dropdown list shows up<br/>" +
             "in the upper right corner of the screen. Here you select the scenario you want to work with.",
           position : 'TL'
         },
         {
           url: "/execute/",
           element : 'a[href="#backup"]',
           beforestep: '$("a[href=\\"#backup\\"]").parent().click()',
           description : "You can create a backup of the database.",
           position : 'TL'
         },
         {
           url: "/execute/",
           element : 'a[href="#empty"]',
           beforestep: '$("a[href=\\"#empty\\"]").parent().click()',
           description : "This task erases all data content from the selected database.<br/><br/>" +
             "Users, permissions, task logs, etc are obviously not erased.",
           position : 'TL'
         },
         {
           url: "/execute/",
           element : 'a[href="#load"]',
           beforestep: '$("a[href=\\"#load\\"]").parent().click()',
           description : "We provide some sample datasets.<br/>" +
             "With this action you can load them into your database.<br/><br/>" +
             "A dataset is loaded incrementally, without erasing the existing data.<br/>" +
             "In most cases you'll want to erase the database contents before loading a new dataset.",
           position : 'TL'
         },
         {
           url: "/execute/",
           element : '#content-main h1',
           beforestep: '$("#tasks").accordion({active:false})',
           description : "There are some additional tasks which are less commonly used.<br/>" +
              "See the documentation for more info.<br/><br/>" +
              "Custom tasks can also be added in an extension app.",
           position : 'TL'
         }
        ]
      },

      // Plan review analysis
      {
       description: '<h2><span class="underline"><a href="/admin/?tour=0,0,0">Main</a></span> &gt; Plan analysis</h2>' +
          'Review and analyze the plan from different angles:<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/resource/?tour=5,1,0">Resource utilization</a></span> (8 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/buffer/?tour=5,8,0">Inventory profile</a></span> (3 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/operation/?tour=5,11,0">Planned operations</a></span> (3 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/demand/?tour=5,14,0">Demand plans</a></span> (4 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/problem/?tour=5,18,0">Exceptions and problems</a></span> (2 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/demand/?tour=5,20,0">Order plan</a></span> (5 steps)',
       delay: 5,
       steps:
          [
           {
             url: "/admin/",
             element : '.ui-accordion-content',
             beforestep: '$("#content-main").accordion({active:1,animate:false})',
             description : "Once you have loaded all data and generated<br/>" +
               "the plan, you are now ready to review and<br/>" +
               "analyze the planning results.",
             position : 'R'
           },
           {
             url: "/resource/",
             element : 'h1',
             description : "This report shows the utilization of all<br/>" +
               "resources, aggregated in time buckets.<br/><br/>" +
               "Users of the Enterprise Edition also have a second report<br/>" +
               "to visualize the resource plan in a Gantt chart.<br/>" +
               "The Gantt chart shows all invidual operations on the resource<br/>" +
               "as blocks on a timeline.",
             position : 'BL'
           },
           {
             url: "/resource/",
             element : '#bucketconfig',
             description : "The result in this report (and the ones we'll see next) are " +
                "aggregated by time buckets.<br/>" +
                "You can adjust the bucket size and the report horizon here.<br/><br/>" +
                "Note that the planning algorithm itself doesn't use buckets.<br/>" +
                "Time buckets are only used for reporting purposes.",
             position : 'B'
           },
           {
             url: "/resource/",
             element : '.flotr-canvas',
             description : "The sparkline graphics give a quick and intuitive<br/>" +
               "overview of the resource utilization.",
             position : 'T'
           },
           {
             url: "/resource/",
             element : 'td[aria-describedby="grid_columns"]',
             description : "For each resource and time bucket the report shows:<br/>" +
               "&nbsp;&nbsp;- Available resource-hours<br/>" +
               "&nbsp;&nbsp;- Unvailable resource-hours, suchs off-shift time, weekends and holidays<br/>" +
               "&nbsp;&nbsp;- Setup resource-hours, ie time involved in changeovers<br/>" +
               "&nbsp;&nbsp;- Load resource-hours<br/>" +
               "&nbsp;&nbsp;- Utilization percentage, defined as load / available time<br/>",
             position : 'T'
           },
           {
             url: "/resource/",
             element : 'span[role="detail"]',
             description : "When there is a load in a bucket, clicking on the triangle<br/>" +
                "gives more detail:<br/>" +
                "&nbsp;&nbsp;- detailed list of operations planned<br/>" +
                "&nbsp;&nbsp;- pegging of the load to the customer demand<br/><br/>" +
                "We'll find the same drill-down capabilities in the reports we'll see next.",
             position : 'T'
           },
           {
             url: "/resource/",
             element : 'span[role="resource"]',
             description : "The drilldown menu allows you to look<br/>" +
               "at the plan of that particular resource<br/>" +
               "The graphics will then shown much bigger.",
             position : 'R'
           },
           {
             url: "/loadplan/",
             element : 'h1',
             description : "This report shows the details of all operations<br/>" +
               "planned on a resource: start date, end date, operation, quantity.<br/><br/>" +
               "This list can be used to communicate the plan to operators<br/>" +
               "on the shop floor, or integrate it to ERP and other systems.",
             position : 'BL'
           },
           {
             url: "/buffer/",
             element : 'h1',
             description : "This report shows the inventory profile of all SKUs.<br/>" +
               "It displays how much inventory we plan to have for each raw<br/>" +
               "material, end product or intermediate product.",
             position : 'BL'
           },
           {
             url: "/buffer/",
             element : 'td[aria-describedby="grid_columns"]',
             description : "For each buffer and time bucket the report shows:<br/>" +
               "&nbsp;&nbsp;- Start Inventory: on hand at the start of the bucket<br/>" +
               "&nbsp;&nbsp;- Produced: quantity added during the bucket<br/>" +
               "&nbsp;&nbsp;- Consumed: quantity consumed during the bucket<br/>" +
               "&nbsp;&nbsp;- End Inventory: on hand at the start of the bucket<br/>",
             position : 'T'
           },
           {
             url: "/flowplan/",
             element : 'h1',
             description : "This report shows the detailed list of all material<br/>" +
               "consumed and produced.<br/><br/>" +
               "This list can be used to communicate the plan to operators<br/>" +
               "on the shop floor, or integrate it to ERP and other systems.",
             position : 'BL'
           },
           {
             url: "/operation/",
             element : 'h1',
             description : "This report summarizes the planned operations.<br/>" +
               "It displays what operations we are planned to start and finish.",
             position : 'BL'
           },
           {
             url: "/operation/",
             element : 'td[aria-describedby="grid_columns"]',
             description : "For each operation and time bucket the report shows:<br/>" +
               "&nbsp;&nbsp;- Locked starts: work-in-progress or frozen quantity started in the bucket<br/>" +
               "&nbsp;&nbsp;- Total starts: total quantity of operations starting in the bucket<br/>" +
               "&nbsp;&nbsp;- Locked ends: work-in-progress or frozen quantity ending in the bucket<br/>" +
               "&nbsp;&nbsp;- Total ends: total quantity of operations ending in the bucket<br/>",
             position : 'T'
           },
           {
             url: "/operationplan/",
             element : 'h1',
             description : "This report shows the detailed list of all planned operations.<br/><br/>" +
               "This list would be typically be used to communicate the plan to operators<br/>" +
               "on the shop floor, or integrate it to ERP and other systems.",
             position : 'BL'
           },
           {
             url: "/demand/",
             element : 'h1',
             description : "This report summarizes the demand for each item.<br/>" +
               "It displays the customer demand for the item and the planned supply.",
             position : 'BL'
           },
           {
             url: "/demand/",
             element : 'td[aria-describedby="grid_columns"]',
             description : "For each item and time bucket the report shows:<br/>" +
               "&nbsp;&nbsp;- Demand: customer demand due in the bucket<br/>" +
               "&nbsp;&nbsp;- Supply: supply of the item in the bucket<br/>" +
               "&nbsp;&nbsp;- Backlog: Difference between the demand and supply<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;of the item, cumulated over time<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;A positive value indicates that some<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;orders are satisfied late",
             position : 'T'
           },
           {
             url: "/demand/",
             element : 'span[role="detail1"]',
             description : "Clicking on the triangles allows you to drill<br/>" +
               "down to the individual orders due in the bucket",
             position : 'T'
           },
           {
             url: "/demandplan/",
             element : 'h1',
             description : "This report shows the detailed list of all<br/>" +
               "planned deliveries of each order.<br/><br/>" +
               "It can be used for more detailed analysis of<br/>" +
               "delays or shortages.",
             position : 'BL'
           },
           {
             url: "/problem/",
             element : '#gbox_grid',
             description : "This report shows problem areas in the plan.<br/>" +
               "Rather than browsing through all orders, resources and materials, this report allows you to focus<br/>" +
               "directly on the exceptions.<br/><br/>" +
               "The main exception types are:<br/>" +
               "&nbsp;&nbsp;- Demand:<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- unplanned: No plan exists yet to satisfy this demand.<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- excess: A demand is planned for more than the requested quantity.<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- short: A demand is planned for less than the requested quantity.<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- late: A demand is satisfied later after its due date.<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- early: A demand is satisfied earlier than the due date.<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- invalid data: Some data problem prevents this object from being planned.<br/>" +
               "&nbsp;&nbsp;- Resource:<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- overload: A resource is being overloaded during a certain period of time.<br/>" +
               "&nbsp;&nbsp;- Buffer:<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- material excess: A buffer is carrying too much material during a certain period of time.<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- material shortage: A buffer is having a material shortage during a certain period of time.<br/>" +
               "&nbsp;&nbsp;- Operation:<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- before current: Flagged when an operationplan is being planned in the past.<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;- before fence: Flagged when an operationplan is being planned within a frozen time window.",
             position : 'C'
           },
           {
             url: "/problem/",
             element : '#grid_owner',
             description : "Let's analyze a late demand...<br/><br/>" +
               "Search a demand problem of type 'late',<br/>" +
               "click on the demand to display the popup menu,<br/>" +
               "and select 'plan' from the menu.",
             position : 'T'
           },
           {
             url: "/demandpegging/Demand%201/",
             element : 'h1',
             description : "This report visualizes the plan of a particular demand.",
             position: "BL"
           },
           {
             url: "/demandpegging/Demand%201/",
             element : '#jqgh_grid_depth',
             description : "All levels in the supply path / bill of material<br/>" +
               "are displayed as a hierarchical tree.<br/>" +
               "You can collapse and expand branches<br/>" +
               "by clicking on the icons.",
             position: "TL"
           },
           {
             url: "/demandpegging/Demand%201/",
             element : '#jqgh_grid_operationplans',
             description : "The Gantt chart visualizes the timing of the steps.<br/><br/>" +
               "The icons above the chart allow you to scroll and zoom.<br/>" +
               "The red line in the graph marks the due date.<br/>" +
               "The black line in the graph marks the current date",
             position: "L"
           },
           {
             url: "/demandpegging/Demand%201/",
             element : '#tabs ul li:nth-child(1)',
             description : "This tab allows us to see the constraints which<br/>" +
               "prevented this demand to be planned on time.",
             position: "TL"
           },
           {
             url: "/constraint/Demand%201/",
             element : '#gbox_grid',
             description : "This report quickly learns us why a particular demand is late or short.<br/>" +
               "This information assists the planner in resolving the bottlenecks.<br/><br/>" +
               "The reasons can be:<br/>"  +
               "&nbsp;&nbsp;- Capacity overload<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;A resource shows up as a bottleneck. Can you do some overtime here?<br/>" +
               "&nbsp;&nbsp;- Before current<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;There isn't enough time. Can you expedite some operations?<br/>" +
               "&nbsp;&nbsp;- Material shortage<br/>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;You're short of material. Please get some more.<br/><br/>" +
               "Some care is when interpreting these results: if a certain resource is identified<br/>" +
               "as the cause, it doesn't mean the resource is completely unavailable. It only<br/>" +
               "indicates that other demands with higher priority already used up all available<br/>" +
               "capacity.",
             position: "C"
           }
           ]
      }
];
