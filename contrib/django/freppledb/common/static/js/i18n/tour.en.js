var tourdata = [
   // Main page of the tour
   {
     description: '<h2>Main</h2>' +
        'Jump to <span class="underline"><a href="/admin/?tour=1,0,0">Navigation</a></span> (5 steps)<br/>' +
        'Jump to <span class="underline"><a href="/admin/?tour=2,0,0">Data entry</a></span> (10 steps)<br/>' +
        'Jump to <span class="underline"><a href="/admin/?tour=3,0,0">Plan generation</a></span><br/>' +
        'Jump to <span class="underline"><a href="/admin/?tour=4,0,0">Plan analysis</a></span><br/>',
     delay: 1,
     steps: [
             {
               url: "/admin/",
               element : '.tourguide',
               description : "Welcome to frePPLe.<br/>" +
                 "This tutorial will show you around.<br/><br/>" +
                 "During the first 5 days after joining this home page " +
                 "will suggest you to take the tour.<br/>" +
                 "Later you can start it from the menu.",
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
         },
        ]
    }
];
