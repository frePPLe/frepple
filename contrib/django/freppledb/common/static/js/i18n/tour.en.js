var tourdata = [
   // Main page of the tour
   {
     description: '<h2>Main</h2>' +
        'Jump to <span class="underline"><a href="/data/?tour=1,0,0">Navigation</a></span> (5 steps)<br/>' +
        'Jump to <span class="underline"><a href="/data/?tour=2,0,0">Data entry</a></span> (10 steps)<br/>' +
        'Jump to <span class="underline"><a href="/data/?tour=3,0,0">Modeling</a></span> (3 steps)<br/>' +
        'Jump to <span class="underline"><a href="/data/?tour=4,0,0">Generating the plan</a></span> (11 steps)<br/>' +
        'Jump to <span class="underline"><a href="/data/?tour=5,0,0">Plan analysis</a></span> (25 steps)<br/>',
     delay: 5,
     steps: [
             {
               url: "/data/",
               element : '.tourguide',
               description : "Welcome to frePPLe.<br/>" +
                 "This guided tour will show you around.<br/><br/>" +
                 "During the first 5 days of use this page<br/>" +
                 "will suggest you to take the tour.<br/>" +
                 "Later you can always start the tour from the menu.",
               position : 'TL'
             }
             ]
   },

   // Navigation
   {
     description: '<h2><span class="underline"><a href="/data/?tour=0,0,0">Main</a></span> &gt; Navigation</h2>' +
        'The main dashboard, the menu bar, breadcrumbs and a quick search option allow easy and intuitive navigation',
     delay: 5,
     steps:
        [
         {
           url: "/data/",
           element : 'h1',
           description : 'The main screen is organized as a dashboard with widgets<br/>' +
                'for the most common activities, such as:<br/>' +
                '&nbsp;&nbsp;- A list of planned operations on each resource<br/>' +
                '&nbsp;&nbsp;- A list of materials to be purchased<br/>' +
                '&nbsp;&nbsp;- A list of customers orders planned to be shipped<br/>' +
                '&nbsp;&nbsp;- Alerts on problem situations<br/>' +
                '&nbsp;&nbsp;- Key performance indicators<br/><br/>' +
                'The widgets and layout of the dashboard are fully configurable.<br/>' +
                'In the Enterprise Edition every user can customize his own cockpit.',
           position : 'B'
         },
         {
           url: "/data/",
           element : '#nav-menu',
           description : "The menu bar gives access to all screens.<br/><br/>" +
               "Screens that are not accessible with your profile<br/>won't be shown in the list.",
           position : 'B'
         },
         {
           url: "/data/",
           element : '#search',
           description : 'You can enter a search string here.<br/>' +
                   'A list of matching entities will be displayed.<br/>' +
                   'This allows you to jump immediately to the screen of that entity.',
           position : 'B'
         },
         {
           url: "/data/",
           element : '.breadcrumbs a',
           description : 'A breadcrumb trail shows the history of screens you have accessed.<br/>' +
                   'You can easily step back and forth.',
           position : 'R'
         }
       ]
    },

    // Data entry
    {
     description: '<h2><span class="underline"><a href="/data/?tour=0,0,0">Main</a></span> &gt; Data entry</h2>' +
        'Data can be entered in different ways:<br/>' +
        '&nbsp;&nbsp;- Directly in a data grid<br/>' +
        '&nbsp;&nbsp;- Using an edit form<br/>' +
        '&nbsp;&nbsp;- By importing an Excel spreadsheet<br/>' +
        '&nbsp;&nbsp;- By importing a CSV-formatted flat file.',
     delay: 5,
     steps:
        [
         {
           url: "/data/",
           element : '#nav-menu',
//           beforestep: '$("#nav-menu").first().hover()',
//           beforestep: 'document.getElementById().hover()',
           description : "Entities (items, locations, suppliers, ...) <br/>" + "have reports, and table views to add/change/detete data.",
           position : 'B'
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
           element : 'span[role="input/item"]',
           description : "A triangle on a field indicates gives access to details.<br/>" +
             "Click the icon to display the detailed screens for the selected entity.<br/>" +
             "Screens that are not accessible with your profile won't be shown in this menu.",
           position : 'B'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-search",
           description : "You can define filters to see a subset of the data.<br/>" +
             "The filter expression can use all attributes from<br/>" +
             "the table and combine them using AND and OR criteria.",
           position : 'L'
         },
         {
           url: "/data/input/demand/",
           element : "#undo",
           description : "You can directly edit data cells in the grid.<br/>" +
             "Click 'save' to store the changes in the database.<br/>" +
             "Clicking 'undo' will restore the original data.",
           position : 'R'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-plus",
           description : "Clicking 'add' (+ sign) opens a form where you can enter data for a new record.",
           position : 'B'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-copy",
           description : "You can select some rows with the checkbox at the start of the row.<br/>" +
             "Click 'copy' to duplicate the records.<br/>" +
             "Click 'delete' to remove the selected records.",
           position : 'B'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-arrow-down",
           description : "Click 'export' to export all data from the grid<br/>" +
              "to a CSV-file or an Excel spreadsheet.",
           position : 'B'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-arrow-up",
           description : "Spreadsheets and CSV-files can also be imported again.<br/>" +
             "The data is validated and any errors are reported.",
           position : 'B'
         },
         {
           url: "/data/input/demand/",
           element : "#toolicons",
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
     description: '<h2><span class="underline"><a href="/data/?tour=0,0,0">Main</a></span> &gt; Modelling</h2>' +
        "Modelling your manufacturing environment.",
     delay: 5,
     steps:
        [
         {
           url: "/data/",
           element : '#nav-menu',
//           beforestep: '$(".menuButton").first().click()',
           description : "Entities have a data table view.<br/>" +
             "A complete description of all entities and their relationships<br/>" +
             "is beyond the scope of this tour.<br/>" +
             "In this tour we'll only show the concepts at a very high level.<br/>" +
             "Check out the documentation for more detail.<br/>",
           position : 'B'
         },
         {
           url: "/supplypath/item/product/",
           element : "#graph",
           description : "This report shows the bill of material of a particular item.<br/>" +
             "The top section visualizes the data as a network graph.<br/>" +
             "The bottom section displays the data as hierarchical tree.<br/><br/>" +
             "The network graph is very important in modelling in frePPLe.<br/>" +
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
           url: "/whereused/buffer/thread%20%40%20factory%201/",
           element : "#tabs ul li:nth-child(1)",
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
     description: '<h2><span class="underline"><a href="/data/?tour=0,0,0">Main</a></span> &gt; Generating the plan</h2>' +
        "Generating plans and performing other tasks.",
     delay: 5,
     steps:
        [
         {
           url: "/data/",
           element : '.ui-menu:eq(2) .ui-menu-item',
           beforestep: '$(".menuButton:eq(2)").click()',
           description : "Once you have loaded all data, you are now<br/>" +
             "ready to generate the plan.",
           position : 'R'
         },
         {
           url: "/execute/",
           element : '#content h1',
           beforestep: '$("#tasks").accordion({active:false,animate:false})',
           description : "The top section show the log and status of all tasks.",
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
           element : 'a[href="#exportworkbook"]',
           beforestep: '$("a[href=\\"#exportworkbook\\"]").parent().click()',
           description : "You can export all input data in single spreadsheet<br/>" +
             "Each entity gets a seperate tab.",
           position : 'TL'
         },
         {
           url: "/execute/",
           element : 'a[href="#importworkbook"]',
           beforestep: '$("a[href=\\"#importworkbook\\"]").parent().click()',
           description : "With this option you can import a spreadsheet.<br/>" +
             "The spreadsheet must match the structure exported with the task above.<br/><br/>" +
             "You can thus export all data, edit in Excel and then reload the updated spreasheet.",
           position : 'TL'
         },
         {
           url: "/execute/",
           element : 'a[href="#scenarios"]',
           beforestep: '$("a[href=\\"#scenarios\\"]").parent().click()',
           description : "Here you can copy your dataset into a whatif scenario.<br/><br/>" +
             "A scenario is a complete copy of all data in a separate database.<br/>" +
             "All data and plans can thus be vary independently.<br/><br/>" +
             "Once a scenario has been copied, a dropdown list shows up in the upper right corner<br/>" +
             "of the screen. Here you select the scenario you want to work with.",
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
           description : "This task erases the content from the selected tables.<br/><br/>" +
             "When you mark a certain entities for erasing, all entities which<br/>" +
             "depend on it will automatically also be selected.",
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
       description: '<h2><span class="underline"><a href="/data/?tour=0,0,0">Main</a></span> &gt; Plan analysis</h2>' +
          'Review and analyze the plan from different angles:<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/demand/?tour=5,1,0">Cockpit</a></span> (1 step)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/resource/?tour=5,2,0">Resource utilization</a></span> (8 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/buffer/?tour=5,9,0">Inventory profile</a></span> (3 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/operation/?tour=5,12,0">Planned operations</a></span> (3 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/demand/?tour=5,15,0">Demand plans</a></span> (4 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/problem/?tour=5,19,0">Exceptions and problems</a></span> (2 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/demand/?tour=5,21,0">Order plan</a></span> (5 steps)',
       delay: 5,
       steps:
          [
           {
             url: "/data/",
             element : '.ui-menu:eq(1)',
             beforestep: '$(".menuButton:eq(1)").click()',
             description : "Once you have loaded all data and generated<br/>" +
               "the plan, you are now ready to review and<br/>" +
               "analyze the results.",
             position : 'R'
           },
           {
             url: "/data/",
             element : 'h1',
             description : 'In their day to day usage planners will be using the main<br/>' +
                  'cockpit screen for the common analysis tasks.<br/><br/>' +
                  'The main screen is organized as a dashboard with widgets<br/>' +
                  'for the most common activities, such as:<br/>' +
                  '&nbsp;&nbsp;- A list of new planned operations on each resource<br/>' +
                  '&nbsp;&nbsp;- A list of new materials to be purchased<br/>' +
                  '&nbsp;&nbsp;- A list of customers orders planned to be shipped<br/>' +
                  '&nbsp;&nbsp;- Analysis of the urgency of open purchase and manufacturing orders<br/>' +
                  '&nbsp;&nbsp;- Alerts on problem situations<br/>' +
                  '&nbsp;&nbsp;- Key performance indicators<br/><br/>' +
                  'The widgets and layout of the dashboard are fully configurable.<br/>' +
                  'In the Enterprise Edition every user can customize his own cockpit.',
             position : 'B'
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
             element : '.fa-clock-o',
             description : "The result in this report (and the ones we'll see next) are " +
                "aggregated by time buckets.<br/>" +
                "You can adjust the bucket size and the report horizon here.<br/><br/>" +
                "Note that the planning algorithm itself doesn't use buckets.<br/>" +
                "Time buckets are only used for reporting purposes.",
             position : 'LT'
           },
           {
             url: "/resource/",
             element : '.fa-table',
             description : "You can display the report in graphical format<br/>" +
               "or in table format.",
             position : 'L'
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
             description : "This report shows the details of all operations planned on a resource: start date, end date, operation, quantity.<br/>" +
               "This list can be used to communicate the plan to operators on the shop floor, or integrate it to ERP and other systems.",
             position : 'R'
           },
           {
             url: "/buffer/",
             element : 'h1',
             description : "This report shows the inventory profile of all SKUs.<br/>" +
               "It displays how much inventory we plan to have for each raw<br/>" +
               "material, end product or intermediate product.",
             position : 'R'
           },
           {
             url: "/buffer/",
             element : '#gview_grid',
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
             description : "This report shows the detailed list of all material consumed and produced.<br/>" +
               "This list can be used to communicate the plan to operatorson the shop floor, or integrate it to ERP and other systems.",
             position : 'R'
           },
           {
             url: "/operation/",
             element : 'h1',
             description : "This report summarizes the planned operations.<br/>" +
               "It displays what operations we are planned to start and finish.",
             position : 'R'
           },
           {
             url: "/operation/",
             element : '#gview_grid',
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
             description : "This report shows the detailed list of all planned operations.<br/>" +
               "This list would be typically be used to communicate the plan to operators<br/>" +
               "on the shop floor, or integrate it to ERP and other systems.",
             position : 'R'
           },
           {
             url: "/demand/",
             element : 'h1',
             description : "This report summarizes the demand for each item.<br/>" +
               "It displays the customer demand for the item and the planned supply.",
             position : 'R'
           },
           {
             url: "/demand/",
             element : '#gview_grid',
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
             element : 'thead',
             description : "Clicking on the item triangles allows you to drill<br/>" +
               "down to the individual orders due in the bucket",
             position : 'TL'
           },
           {
             url: "/demandplan/",
             element : 'h1',
             description : "This report shows the detailed list of all planned deliveries of each order.<br/>" +
               "It can be used for more detailed analysis of delays or shortages.",
             position : 'R'
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
             url: "/constraintdemand/Demand%201/",
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
