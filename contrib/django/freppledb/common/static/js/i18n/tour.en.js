var tourdata = [
   // Main page of the tour
   {
     description: '<h2>Main</h2>' +
        'Jump to <span class="underline"><a href="/admin/?tour=1,0,0">Navigation</a></span> (5 steps)<br/>' +
        'Jump to <span class="underline"><a href="/admin/?tour=2,0,0">Data entry</a></span> (10 steps)<br/>' +
        'Jump to <span class="underline"><a href="/admin/?tour=3,0,0">Generating the plan</a></span> (8 steps)<br/>' +
        'Jump to <span class="underline"><a href="/admin/?tour=4,0,0">Plan analysis</a></span> ( steps)<br/>',
     delay: 1,
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
             },
             ]
   },

   // Navigation
   {
     description: '<h2><span class="underline"><a href="/admin/?tour=0,0,0">Main</a></span> &gt; Navigation</h2>' +
        'The menu bar, the index page, breadcrumbs and a search allow easy and intuitive navigation',
     delay: 1,
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
     delay: 1,
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

    // Planning tasks
    {
     description: '<h2><span class="underline"><a href="/admin/?tour=0,0,0">Main</a></span> &gt; Generating the plan</h2>' +
        "Generating plans and performing other tasks.",
     delay: 1,
     steps:
        [
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
        ],
      },

      // Planning analysis
      {
       description: '<h2><span class="underline"><a href="/admin/?tour=0,0,0">Main</a></span> &gt; Plan analysis</h2>' +
          'Reviewing and analyzing the plan:<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/resource/?tour=4,1,0">Resource utilization</a></span> (6 steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/buffer/?tour=4,7,0">Inventory profile</a></span> ( steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/operation/?tour=4,1,0">Planned operations</a></span> ( steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/resource/?tour=4,1,0">Order plans</a></span> ( steps)<br/>' +
          '&nbsp;&nbsp;- <span class="underline"><a href="/problem/?tour=4,1,0">Exceptions and problems</a></span> ( steps)',
       delay: 1,
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
             position : 'R'
           },
           {
             url: "/resource/",
             element : '#bucketconfig',
             description : "The result in this report (and the ones we'll see next) are<br/>" +
                "aggregated by time buckets.<br/>" +
                "You can adjust the bucket size and the report horizon here.<br/><br/>" +
                "Note that the planning algorithm itself doesn't use buckets.<br/>" +
                "Time buckets are only used for reporting purposes.",
             position : 'T'
           },
           {
             url: "/resource/",
             element : '.flotr-canvas',
             description : "The sparkline graphics give a quick and intuitive<br/>" +
               "overview of the resource utilization",
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
             description : "The drilldown menu of a resource allows you to look<br/>" +
               "at the plan of that particular resource<br/>" +
               "The graphics will then shown much bigger.",
             position : 'T'
           },
           {
             url: "/buffer/",
             element : 'h1',
             description : "This report shows the inventory profile of all SKUs.<br/>",
             position : 'R'
           },
           {
             url: "/buffer/",
             element : 'td[aria-describedby="grid_columns"]',
             description : "For each buffer and time bucket the report shows:<br/>" +
               "&nbsp;&nbsp;- xxxx<br/>",
             position : 'T'
           },
           ]
      }
];
