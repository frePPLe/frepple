var tourdata = [
   // Main page of the tour
   {
     description: '<h3>Getting around</h3>' +
        '<span class="underline"><a href="/?tour=1,0,0">Navigation</a></span><br>' +
        '<span class="underline"><a href="/data/input/demand/?tour=2,0,0">Data maintenance</a></span><br>' +
        '<span class="underline"><a href="/?tour=3,0,0">Modeling</a></span><br>' +
        '<span class="underline"><a href="/?tour=4,0,0">Generating the plan</a></span><br>' +
        '<h3>Plan analysis</h3>' +
        '<span class="underline"><a href="/resource/?tour=5,1,0">Resource utilization</a></span><br>' +
        '<span class="underline"><a href="/buffer/?tour=5,8,0">Inventory profile</a></span><br>' +
        '<span class="underline"><a href="/operation/?tour=5,11,0">Planned operations</a></span><br>' +
        '<span class="underline"><a href="/demand/?tour=5,14,0">Demand plans</a></span><br>' +
        '<span class="underline"><a href="/problem/?tour=5,18,0">Exceptions and problems</a></span><br>' +
        '<span class="underline"><a href="/demandpegging/Demand%2001/?tour=5,20,0">Order plan</a></span>' +
        '<h3>Daily workflows</h3>' +
        '<span class="underline"><a href="/?tour=6,0,0">A day in the life of a manufacturing planner</a></span><br>',
     delay: 5,
     steps: [
             {
               url: "/",
               element : '#tourModal',
               description : "<strong>Welcome to frePPLe.</strong><br>" +
                 "This guided tour will show you around.<br><br>" +
                 "During the first 5 days of use you will see this message to take " +
                 "the tour. Later you can always start the tour from the menu.",
               position : 'top'
             }
             ]
   },

   // Navigation
   {
     description: '<h2><span class="underline"><a href="/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Navigation</h2>' +
        'The main dashboard, the menu bar, breadcrumbs and a quick search option allow easy and intuitive navigation',
     delay: 5,
     steps:
        [
         {
           url: "/",
           element : '.row:eq(1)',
           description : "The main screen is organized as a <b>dashboard with widgets</b> " +
                "to show the overall health of the supply chain and provide access to the most common activities:" +
                "<ul><li style='list-style:initial'>Purchase orders</li>" +
                "<li style='list-style:initial'>Manufacturing orders</li>" +
                "<li style='list-style:initial'>Distribution orders</li>" +
                "<li style='list-style:initial'>Late orders</li>" +
                "<li style='list-style:initial'>Resource utilization</li>" +
                "<li style='list-style:initial'>Delivery performance</li>" +
                "<li style='list-style:initial'>Forecast</li>" +
                "<li style='list-style:initial'>Forecast Error</li>" +
                "<li style='list-style:initial'>Inventory By Item</li>" +
                "<li style='list-style:initial'>Inventory by Item</li>" +
                "<li style='list-style:initial'>Stockout risk</li>" +
                "<li style='list-style:initial'>...</li></ul>" +
                "The <b>widgets and layout of the dashboard are fully configurable</b>.<br>" +
                "In the Enterprise Edition every user can personalize the cockpit.",
           position : 'bottom',
           afterstep : '$("div.arrow").remove()'
         },
         {
           url: "/",
           element : '#nav-menu',
           description : "The <b>menu bar</b> gives access to all screens.<br><br>" +
               "Screens that are not accessible with your profile<br>won't be shown in the list.",
           position : 'bottom'
         },
         {
           url: "/",
           element : '#search',
           description : '<b>Search field:</b> As you type string here ' +
                   'a list of matching entities will be displayed.<br>' +
                   'This allows you to jump immediately to the screen of that entity.',
           position : 'bottom'
         },
         {
           url: "/",
           element : '#breadcrumbs',
           description : 'A <b>breadcrumb</b> trail shows the history of screens you have accessed.<br>' +
                   'You can easily step back and forth.',
           position : 'bottom'
         }
       ]
    },

    // Data entry
    {
     description: '<h2><span class="underline"><a href="/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Data maintenance</h2>' +
        'Data can be entered in different ways:<br>' +
        '&nbsp;&nbsp;- Directly in a data grid<br>' +
        '&nbsp;&nbsp;- Using an edit form<br>' +
        '&nbsp;&nbsp;- By importing an Excel spreadsheet<br>' +
        '&nbsp;&nbsp;- By importing a CSV-formatted flat file.',
     delay: 5,
     steps:
        [
         {
           url: "/",
           element : '#nav-menu',
//           beforestep: '$("#nav-menu").first().hover()',
//           beforestep: 'document.getElementById().hover()',
           description : "Entities (items, locations, suppliers, ...) in the <b>menu</b><br>" + "have reports, and table views to <b>add/change/detete data</b>.",
           position : 'bottom'
         },
         {
           url: "/data/input/demand/",
           element : "#content-main",
           description : "FrePPLe has <strong>data maintenance</strong> capabilities.<br><br>" +
             "All data objects have a table editor. Here we selected the sales order table as an example.<br>" +
             "Click a column header to <b>sort the data</b>.<br>" +
             "Clicking a second time will reverse the sorting order.",
           position : 'top'
         },
         {
           url: "/data/input/demand/",
           element : 'span[role="input/item"]:first()',
           description : "A <b>triangle</b> on a field indicates gives <b>access to details</b>.<br>" +
             "Click the icon to display the detailed screens for the selected entity.<br>" +
             "Screens that are not accessible with your profile won't be shown in this menu.",
           position : 'bottom'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-search",
           description : "You can define <b>filters</b> to see a subset of the data.<br>" +
             "The filter expression can use all attributes from<br>" +
             "the table and combine them using AND and OR criteria.",
           position : 'bottom'
         },
         {
           url: "/data/input/demand/",
           element : "#undo",
           description : "You can directly edit data cells in the grid.<br>" +
             "Click <b>'save' to store</b> the changes in the database.<br>" +
             "Clicking <b>'undo' will restore</b> the original data.",
           position : 'right'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-plus",
           description : "Clicking <b>'add'</b> (+ sign) opens a form where you can enter <b>data for a new record</b>.",
           position : 'left'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-copy",
           description : "You can select some rows with the checkbox at the start of the row.<br>" +
             "Click <b>'copy' to duplicate</b> the records.<br>" +
             "Click <b>'delete' to remove</b> the selected records.",
           position : 'left'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-arrow-down",
           description : "Click 'export' to <strong>export a CSV or Excel file</strong> with all data from the grid.",
           position : 'bottom'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-arrow-up",
           description : "Spreadsheets and CSV-files can also be <strong>imported</strong> again.<br>" +
             "The data is validated and any errors are reported.",
           position : 'bottom'
         },
         {
           url: "/data/input/demand/",
           element : ".fa-wrench",
           description : "Users of the Enterprise Edition also have the " +
             "ability to <strong>customize the report</strong>:<br>" +
             "<ul><li style='list-style:initial'>Hide columns</li>" +
             "<li style='list-style:initial'>Change the order of columns</li>" +
             "<li style='list-style:initial'>Choose the number of frozen columns</li>" +
             "<li style='list-style:initial'>Adjust the column width</li></ul>" +
             "These settings are saved for each individual user.",
           position : 'bottom'
         }
        ]
    },

    // Modeling
    {
     description: '<h2><span class="underline"><a href="/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Modelling</h2>' +
        "Modelling your manufacturing environment.",
     delay: 5,
     steps:
        [
         {
           url: "/supplypath/item/product/",
           element : ".container-fluid h1 small",
           description : "This report shows the <strong>bill of material</strong> or <strong>supply path</strong> of a particular item.<br>" +
             "The top section visualizes the data as a network graph.<br>" +
             "The bottom section displays the data as hierarchical tree.<br><br>" +
             "The network graph is very important in modelling in frePPLe. " +
             "Every single graphical object in this graph is stored as a single " +
             "record in the frePPLe model. The graph allows you to verify that " +
             "you have correctly filled in all data.<br>" +
             "&nbsp;- <i>Operations</i> are shown as rectangles.<br>" +
             "&nbsp;- <i>Resources</i> are shown as circles.<br>" +
             "&nbsp;- <i>Buffers</i>/item @ location are shown as triangles.<br>" +
             "&nbsp;- The lines between operations and buffers are <i>flows</i>.<br>" +
             "&nbsp;- The dotted lines between operations and resources are <i>loads</i>.<br>",
           position : 'bottom'
         },
         {
           url: "/whereused/buffer/thread%20%40%20factory%201/",
           element : "#tabs ul li:nth-child(3)",
           description : "The <strong>supply path</strong> report displayed the structure upstream, i.e. walking from end item towards the raw materials.<br><br>" +
             "The <strong>where-used</strong> report displays the structure downstream, i.e. walking from the raw material towards the end items.<br>" +
             "It thus displays which end items the selected entity is used for.",
           position : 'bottom'
         }
        ]
    },

    // Planning tasks
    {
     description: '<h2><span class="underline"><a href="/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Generating the plan</h2>' +
        "Generating plans and performing other tasks.",
     delay: 5,
     steps:
        [
         {
           url: "/execute/",
           element : '#content-main',
           description : "The <strong>execution screen</strong> allows to runs commands.<br><br>" +
             "The top section show the log and status of all tasks.<br><br>" +
             "The bottom section allows you to interactively launch new tasks. " +
             "To automate operations they can also be launched from the command line.",
           position : 'top'
         },
         {
           url: "/execute/",
           element : '#eersteHeading',
           beforestep: '$("#eersteAccord").addClass("in")',
           description : "You can <strong>generate constrained or unconstrained plans</strong><br>" +
             "and select which constraints to consider.<br><br>" +
             "A constrained plan will respect all constraints<br>" +
             "but some demands can be planned late or incomplete.<br><br>" +
             "In an unconstrained plan all demand will be met at its due date<br>" +
             "but some constraints can be violated.",
           position : 'top'
         },
         {
           url: "/execute/",
           element : '#tweedeHeading',
           beforestep: '$("#eersteAccord").removeClass("in"); $("#tweedeAccord").addClass("in")',
           description : "You can <strong>export a spreadsheet</strong> with all input data.<br>" +
             "Each entity gets a seperate tab.",
           position : 'top'
         },
         {
           url: "/execute/",
           element : '#derdeHeading',
           beforestep: '$("#tweedeAccord").removeClass("in"); $("#derdeAccord").addClass("in")',
           description : "With this option you can <strong>import a spreadsheet</strong>.<br>" +
             "The spreadsheet must match the structure exported with the task above.<br><br>" +
             "You can thus export all data, edit in Excel and then reload the updated spreadsheet.",
           position : 'top'
         },
         {
           url: "/execute/",
           element : '#vertiendeHeading',
           beforestep: '$("#derdeAccord").removeClass("in"); $("#vertiendeAccord").addClass("in")',
           description : "With this option you can <strong>import a set of CSV-formatted data files</strong>.<br><br>" +
             "Data interfaces from external systems or users will copy data files in a specific folder. " +
             "This command will then process all input data from the folder. Any data errors are reported in the log file.",
           position : 'top'
         },
         {
           url: "/execute/",
           element : '#vierdeHeading',
           beforestep: '$("#vertiendeAccord").removeClass("in"); $("#vierdeAccord").addClass("in")',
           description : "Here you can copy your dataset into a <strong>what-if scenario</strong>.<br><br>" +
             "A scenario is a complete copy of all data in a separate database. " +
             "All data and plans can thus be vary independently.<br><br>" +
             "All data and plans can thus be vary independently.<br><br>" +
             "Once a scenario has been copied, a dropdown list shows up in the upper right corner " +
             "of the screen. Here you select the scenario you want to work with.",
           position : 'top'
         },
         {
           url: "/execute/",
           element : '#vijfdeHeading',
           beforestep: '$("#vierdeAccord").removeClass("in"); $("#vijfdeAccord").addClass("in")',
           description : "You can create a <strong>backup</strong> of the database.<br><br>" +
             "There is a restore command as well. As restoring the database requires some " +
             "downtime (and also for data security) it is only available from the command line.",
           position : 'top'
         },
         {
           url: "/execute/",
           element : '#zesdeHeading',
           beforestep: '$("#vijfdeAccord").removeClass("in"); $("#zesdeAccord").addClass("in")',
           description : "This task <strong>erases the data</strong> from the selected tables.<br><br>" +
             "When you mark a certain entities for erasing, all entities which " +
             "depend on it will automatically also be selected.",
           position : 'top'
         },
         {
           url: "/execute/",
           element : '#zevendeHeading',
           beforestep: '$("#zesdeAccord").removeClass("in"); $("#zevendeAccord").addClass("in")',
           description : "With this action you can <strong>load demo datasets</strong> into your database.<br><br>" +
             "A dataset is loaded incrementally, without erasing the existing data. " +
             "In most cases you'll want to erase the database contents before loading a new dataset.",
           position : 'top'
         },
         {
           url: "/execute/",
           element : '#tasks',
           beforestep: '$("#zevendeAccord").removeClass("in")',
           description : "There are some additional tasks which are less commonly used.<br>" +
              "<b>See the documentation for more info</b>.<br><br>" +
              "Custom tasks can also be added in an extension app.",
           position : 'top'
         }
        ]
      },

      // Plan analysis
      {
       description: '<h2><span class="underline"><a href="/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Plan analysis</h2>' +
          'Review and analyze the plan from different angles:<br>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/resource/?tour=5,1,0">Resource utilization</a></span><br>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/buffer/?tour=5,8,0">Inventory profile</a></span><br>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/operation/?tour=5,11,0">Planned operations</a></span><br>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/demand/?tour=5,14,0">Demand plans</a></span><br>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/problem/?tour=5,18,0">Exceptions and problems</a></span><br>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/demandpegging/Demand%2001/?tour=5,20,0">Order plan</a></span>',
       delay: 5,
       steps:
          [
           {
             url: "/resource/",
             element : 'h1 small',
             description : "This report shows the <strong>resource utilization</strong>" +
               ", aggregated in time buckets.<br><br>" +
               "Users of the Enterprise Edition also have a second report" +
               "to visualize the resource plan in a <strong>Gantt chart</strong>." +
               "The Gantt chart shows all individual operations on the resource<br>" +
               "as blocks on a timeline.",
             position : 'bottom'
           },
           {
             url: "/resource/",
             element : '.fa-clock-o',
             description : "Many reports display the plan aggregated by time buckets. " +
                "You can <b>adjust the time bucket size and the report horizon</b> here.<br><br>" +
                "Note that the planning algorithm itself doesn't use buckets. " +
                "Time buckets are only used for reporting purposes.",
             position : 'bottom'
           },
           {
             url: "/resource/",
             element : '.fa-table',
             description : "You can display the report in <b>graphical format</b> or in <b>table format</b>.",
             position : 'bottom'
           },
           {
             url: "/resource/",
             element : 'td[aria-describedby="grid_columns"]:eq(0)',
             description : "<b>For each resource and time bucket</b> the report shows:<br>" +
               "&nbsp;&nbsp;- Available resource-hours<br>" +
               "&nbsp;&nbsp;- Unvailable resource-hours, suchs off-shift time, weekends and holidays<br>" +
               "&nbsp;&nbsp;- Setup resource-hours, ie time involved in changeovers<br>" +
               "&nbsp;&nbsp;- Load resource-hours<br>" +
               "&nbsp;&nbsp;- Utilization percentage, defined as load / available time<br>",
             position : 'top',
           },
           {
             url: "/resource/",
             element : 'span.context.cross.fa.fa-caret-right:eq(0)',
             description : "If there is a load in a bucket, a <b>click on the triangle</b> gives more detail:<br>" +
                "&nbsp;&nbsp;- detailed list of operations planned<br>" +
                "&nbsp;&nbsp;- pegging of the load to the customer demand<br><br>" +
                "We'll find the same drill-down capabilities in the reports we'll see next.",
             position : 'top'
           },
           {
             url: "/resource/",
             element : 'span[role="input/resource"]:eq(0)',
             description : "The <b>drilldown menu</b> allows you to look<br>" +
               "at the plan of that particular resource<br>" +
               "The graphics will then shown much bigger.",
             position : 'right'
           },
           {
             url: "/loadplan/",
             element : 'h1 small',
             description : "This report shows the <b>details of all operations</b> planned on a resource: start date, end date, operation, quantity.<br>" +
               "This list can be used to communicate the plan to operators on the shop floor, or integrate it to ERP and other systems.",
             position : 'right'
           },
           {
             url: "/buffer/",
             element : 'h1 small',
             description : "This report shows the <b>inventory profile</b> of all item @ locations.<br>" +
               "It displays how much inventory we plan to have for each raw<br>" +
               "material, end product or intermediate product.",
             position : 'right'
           },
           {
             url: "/buffer/",
             element : '#gview_grid',
             description : "<b>For each buffer and time bucket</b> the report shows:<br>" +
               "&nbsp;&nbsp;- Start Inventory: on hand at the start of the bucket<br>" +
               "&nbsp;&nbsp;- Produced: quantity added during the bucket<br>" +
               "&nbsp;&nbsp;- Consumed: quantity consumed during the bucket<br>" +
               "&nbsp;&nbsp;- End Inventory: on hand at the start of the bucket<br>",
             position : 'top'
           },
           {
             url: "/flowplan/",
             element : 'h1 small',
             description : "This report shows the <strong>detailed list of all material consumed and produced</strong>.<br>" +
               "This list can be used to communicate the plan to operators on the shop floor, or integrate it to ERP and other systems.",
             position : 'right'
           },
           {
             url: "/operation/",
             element : 'h1 small',
             description : "This report summarizes the <b>planned operations</b>.<br>" +
               "It displays what operations we are planned to start and finish.",
             position : 'right'
           },
           {
             url: "/operation/",
             element : '#gview_grid',
             description : "<b>For each operation and time bucket</b> the report shows:<br>" +
               "&nbsp;&nbsp;- Locked starts: work-in-progress or frozen quantity started in the bucket<br>" +
               "&nbsp;&nbsp;- Total starts: total quantity of operations starting in the bucket<br>" +
               "&nbsp;&nbsp;- Locked ends: work-in-progress or frozen quantity ending in the bucket<br>" +
               "&nbsp;&nbsp;- Total ends: total quantity of operations ending in the bucket<br>",
             position : 'top'
           },
           {
             url: "/data/input/manufacturingorder/",
             element : 'h1 small',
             description : "This report shows the <strong>detailed list of all planned operations</strong>.<br>" +
               "This list would be typically be used to communicate the plan to operators<br>" +
               "on the shop floor, or integrate it to ERP and other systems.",
             position : 'right'
           },
           {
             url: "/demand/",
             element : 'h1 small',
             description : "This report summarizes the <strong>demand for each item</strong>.<br>" +
               "It displays the customer demand for the item and the planned supply.",
             position : 'right'
           },
           {
             url: "/demand/",
             element : '#gview_grid',
             description : "<b>For each item and time bucket</b> the report shows:<br>" +
               "&nbsp;&nbsp;- Demand: customer demand due in the bucket<br>" +
               "&nbsp;&nbsp;- Supply: supply of the item in the bucket<br>" +
               "&nbsp;&nbsp;- Backlog: Difference between the demand and supply<br>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;of the item, cumulated over time<br>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;A positive value indicates that some<br>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;orders are satisfied late",
             position : 'top'
           },
           {
             url: "/demand/",
             element : 'a[href="/detail/input/item/key/"]:eq(1)',
             description : "Clicking on the item <b>triangles allows you to drill down</b> to the individual orders due in the bucket",
             position : 'top'
           },
           {
             url: "/data/input/deliveryorder/",
             element : 'h1 small',
             description : "This report shows the detailed list of all <strong>planned deliveries</strong> of each order.<br>" +
               "It can be used for more detailed analysis of delays or shortages.",
             position : 'right'
           },
           {
             url: "/problem/",
             element : 'h1 small',
             description : "This report shows <b>problem areas in the plan</b>.<br>" +
               "Rather than browsing through all orders, resources and materials, this report allows you to focus" +
               "directly on the exceptions." +
               "The main exception types are:<br>" +
               "&nbsp;<b>Demand:</b><br>" +
               "&nbsp;&nbsp;- unplanned: No plan exists yet to satisfy this demand.<br>" +
               "&nbsp;&nbsp;- excess: A demand is planned for more than the requested quantity.<br>" +
               "&nbsp;&nbsp;- short: A demand is planned for less than the requested quantity.<br>" +
               "&nbsp;&nbsp;- late: A demand is satisfied later after its due date.<br>" +
               "&nbsp;&nbsp;- early: A demand is satisfied earlier than the due date.<br>" +
               "&nbsp;&nbsp;- invalid data: Some data problem prevents this object from being planned.<br>" +
               "&nbsp;<b>Resource:</b><br>" +
               "&nbsp;&nbsp;- overload: A resource is being overloaded during a certain period of time.<br>" +
               "&nbsp;<b>Buffer:</b><br>" +
               "&nbsp;&nbsp;- material excess: A buffer is carrying too much material during a certain period of time.<br>" +
               "&nbsp;&nbsp;- material shortage: A buffer is having a material shortage during a certain period of time.<br>" +
               "&nbsp;<b>Operation:</b><br>" +
               "&nbsp;&nbsp;- before current: Flagged when an operationplan is being planned in the past.<br>" +
               "&nbsp;&nbsp;- before fence: Flagged when an operationplan is being planned within a frozen time window.",
             position : 'bottom'
           },
           {
             url: "/problem/?entity=material",
             element : '#grid_owner',
             description : "Let's <b>analyze a late demand...</b><br><br>" +
               "Search a demand problem of type 'late',<br>" +
               "click on the demand to display the popup menu,<br>" +
               "and select 'plan' from the menu.",
             position : 'top'
           },
           {
             url: "/demandpegging/Demand%2001/",
             element : 'h1 small',
             description : "This report visualizes the <b>plan of a particular demand</b>.",
             position: "right"
           },
           {
             url: "/demandpegging/Demand%2001/",
             element : '#jqgh_grid_depth',
             description : "All levels in the supply path / bill of material " +
               "are displayed as a <b>hierarchical tree</b>.<br>" +
               "You can <b>collapse</b> and <b>expand</b> branches " +
               "by clicking on the icons.",
             position : "top"
           },
           {
             url: "/demandpegging/Demand%2001/",
             element : '#zoom_in',
             description : "The <b>Gantt chart</b> visualizes the timing of the steps.<br><br>" +
               "The icons above the chart allow you to scroll and zoom.<br>" +
               "The red line in the graph marks the due date.<br>" +
               "The black line in the graph marks the current date",
             position : "left"
           },
           {
             url: "/demandpegging/Demand%2001/",
             element : '#tabs ul li:nth-child(1)',
             description : "This tab allows us to <b>see the constraints</b> which prevented this demand to be planned on time.",
             position : "top"
           },
           {
             url: "/constraintdemand/Demand%2001/",
             element : 'h1 small',
             description : "This report shows <b>why a particular demand is late or short</b>.<br>" +
               "This information assists the planner in resolving the bottlenecks.<br><br>" +
               "The reasons can be:<br>"  +
               "&nbsp;&nbsp;- Capacity overload<br>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A resource shows up as a bottleneck.<br>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Can you do some overtime here?<br>" +
               "&nbsp;&nbsp;- Before current<br>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;There isn't enough time.<br>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Can you expedite some operations?<br>" +
               "&nbsp;&nbsp;- Material shortage<br>" +
               "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;You're short of material. Please get some more.<br><br>" +
               "Some care is when interpreting these results: if a certain resource is identified " +
               "as the cause, it doesn't mean the resource is completely unavailable. It only " +
               "indicates that other demands with higher priority already used up all available " +
               "capacity.",
             position: "bottom"
           }
           ]
      },


      // A day in the life of a manufacturing planner
      {
       description: '<h2><span class="underline"><a href="/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; A day in the life of a manufacturing planner</h2>' +
        'The manufacturing planner\'s role is to make sure that demand is delivered on time ' +
        ' by reviewing the supply chain capacity and material constraints.<br><br>',
       delay: 5,
       steps:
        [
         {
           url: "/",
           element : '#cockpitcrumb',
           description : "The cockpit is a dashboard with widgets to give an overall health of the supply chain</b>:" +
                         "<ul><li style='list-style:initial'>Purchase orders</li>" +
                         "<li style='list-style:initial'>Manufacturing orders</li>" +
                         "<li style='list-style:initial'>Distribution orders</li>" +
                         "<li style='list-style:initial'>Late orders</li>" +
                         "<li style='list-style:initial'>Resource utilization</li>" +
                         "<li style='list-style:initial'>Delivery performance</li>" +
                         "<li style='list-style:initial'>...</li></ul>" +
                         "From the widgets you can jump to more detailed information.<br>" +
                         "The dashboard can easily be personalized by each user.",
           position : 'right'
         },
         {
           url: "/",
           element : 'div.panel[data-cockpit-widget="late_orders"]',
           description : "The late orders widget will display the delay of the orders that cannot be planned on time",
           position : 'top'
         },
         {
           url: "/",
           element : 'div.panel[data-cockpit-widget="purchase_orders"]',
           description : "The purchase orders widget let you review the proposed and confirmed purchase orders",
           position : 'top'
         },
         {
           url: "/",
           element : 'div.panel[data-cockpit-widget="distribution_orders"]',
           description : "The distribution orders widget let you review the proposed and confirmed distribution orders",
           position : 'top'
         },
         {
           url: "/",
           element : '#Manufacturing',
           description : "The manufacturing section contains :<br>" +
           "The manufacuring orders widget to review the value associated with the proposed and confirmed manufacturing orders<br>" +
           "The resource utilization widget lets you find out how loaded your resources are<br>" +
           "The capacity alerts widget displays any alert associated to capacity",
           position : 'top'
         },
         {
           url: "/problem/",
           element : "#jqgh_grid_owner",
           description : "The problem report (under the sales menu) will display all late/early/short demands for review<br>" ,
           position : 'top'
         },
         {
           url: "/data/input/manufacturingorder/",
           element : "#jqgh_grid_enddate",
           description : "The operation plan screen let you review and confirm any proposed manufacturing order",
           position : 'top'
         },
         {
           url: "/resource/",
           element : "#grid_graph",
           description : "The resource report displays the resource utilization per time bucket",
           position : 'top'
         },
         {
           url: "/resource/",
           element : ".fa-table",
           description : "By clicking on the table button, the planner will switch to the table view",
           position : 'top'
         }
        ]
    }
];
