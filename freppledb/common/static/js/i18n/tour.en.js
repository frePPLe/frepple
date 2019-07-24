var tourdata = [
   // Main page of the tour
   {
     description:
    	 '<div class="panel-group" id="touraccordion">' + 
    	 '<div class="panel panel-default">' +
    	   '<div class="panel-heading" data-toggle="collapse" data-parent="#touraccordion" href="#accordionproduction">' +
    	   '<h4 class="panel-title">' +
    	   'Production Planning&nbsp;&nbsp;<small><span class="fa fa-plus fa-xs"></span></small>' +
    	   '</h4></div>' +
         '<div id="accordionproduction" class="panel-collapse collapse">' +
         '<div class="panel-body"><div style="margin: .5em">' +
        '<span class="underline"><a href="{url_prefix}/?tour=1,0,0">How can I update my plan when a machine breaks down?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=2,0,0">How can I change the assigned resource of a manufacturing order?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=3,0,0">How can I detect manufacturing orders that need expediting?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=4,0,0">How can I prioritize a sales order over another?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=5,0,0">How can I input my operators shifts or holidays?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=6,0,0">How can I spot and review late orders?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=7,0,0">How can I track down bottleneck resources?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=8,0,0">...and their unconstrained requirement?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=9,0,0">How can I measure the impact of rush orders?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=10,0,0">How precisely can I quote a delivery date for a new customer order?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=11,0,0">How can I optimize my plan in the GANTT chart of plan editor?</a></span><br>' +
        '</div></div>' +
        '</div>' +
        '</div>' +
     	  '<div class="panel panel-default">' +
  	    '<div class="panel-heading" data-toggle="collapse" data-parent="#touraccordion" href="#accordionintegration">' +
  	    '<h4 class="panel-title">' +
  	    'Integration / API / Automation&nbsp;&nbsp;<small><span class="fa fa-plus fa-xs"></span></small>' +
  	    '</h4></div>' +
        '<div id="accordionintegration" class="panel-collapse collapse">' +
        '<div class="panel-body"><div style="margin: .5em">' +
        '<span class="underline"><a href="{url_prefix}/?tour=27,0,0">How can I export proposed purchase orders to an ERP system?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=28,0,0">What is the meaning of each MO/PO/DO status?</a></span><br>' +
        '<span class="underline"><a href="{url_prefix}/?tour=29,0,0">How do I synchronize data in frePPLe with my ERP system?</a></span><br>' +
        '</div></div>' +
        '</div>' +
        '</div>' +
     	  '<div class="panel panel-default">' +
  	    '<div class="panel-heading" data-toggle="collapse" data-parent="#touraccordion" href="#accordionscenario">' +
  	    '<h4 class="panel-title">' +
  	    'What-if scenarios&nbsp;&nbsp;<small><span class="fa fa-plus fa-xs"></span></small>' +
  	    '</h4></div>' +
  	    '<div id="accordionscenario" class="panel-collapse collapse">' +
  	    '<div class="panel-body"><div style="margin: .5em">' +
        '<span class="underline"><a href="{url_prefix}/execute/?tour=30,0">How do what-if scenarios work?</a></span><br>' +
        '</div></div>' +
        '</div>' +
        '</div>' +
        '</div>'
   }, 
   
// PRODUCTION PLANNING
   //How can I update my plan when a machine breaks down?   1,0,0
   {
     description: 
    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
    	 '<h2>How can I update my plan when a machine breaks down?</h2>' +
    	 '1) Navigate to <span class="underline"><a href="{url_prefix}/data/input/resource/?tour=1,0,0">Resources</a></span> in the Capacity menu.<br><br>' +
    	 '2) Click on  the search icon in the upper right corner and filter for your machine.<br><br>' +
    	 '3) If the machine maximum calendar field is not populated, simply set the maximum field to 0.<br><br>' +
    	 '4) If the maximum calendar is populated, edit the calendar and make sure the default value is 0 and all the calendar buckets also have a value of 0. <br><br>' +
    	 '5) Relaunch the plan.<br>' +    	    
       '<br>' +       
       '<br>' +
       '<iframe width="560" height="315" src="https://www.youtube.com/embed/WGs8R62F3UU" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   //How can I change the assigned resource for a manufacturing order (MO)?	2,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
	    	 '<h2>How can I change the assigned resource for a manufacturing order (MO)?</h2>' +
	    	 '1) Navigate to <span class="underline"><a href="{url_prefix}/data/input/manufacturingorder/?tour=2,0,0">Manufacturing Orders</a></span> in the Manufacturing menu and select the manufacturing order (MO) you wish to edit. <br><br>' +
	    	 '2) In the bottom panes, look for the Resources widget.<br><br>' +
	    	 '3) Select the new resource you wish to assign to the MO and save.<br>' +
	       '<br>' +	       
	       '<br>' +
	       '<iframe width="560" height="315" src="https://www.youtube.com/embed/JtyD5SvZIz4" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   //How can I detect manufacturing orders that need expediting?	3,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
	    	 '<h2>How can I detect manufacturing orders that need expediting?</h2>' +
	    	 '1) Navigate to <span class="underline"><a href="{url_prefix}/data/input/manufacturingorder/?tour=3,0,0">Manufacturing Orders</a></span> in the Manufacturing menu.<br><br>' +
	    	 '2) Click on  the search icon in the upper right corner and click on Reset to remove all filters.<br><br>' +
	    	 '3) Click on the Inventory Status column to sort the orders by inventory status ascending. <br><br>' +
	    	 '4) The cells in red show the orders that need to be expedited<br>' +
	       '<br>' +	       
	       '<br>' +
	       '<iframe width="560" height="315" src="https://www.youtube.com/embed/gj2GD6o7qc8" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   //How can I prioritize a sales order over another? 4,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
	    	 '<h2>How can I prioritize a sales order over another?</h2>' +
	    	 '1) Navigate to <span class="underline"><a href="{url_prefix}/data/input/demand/?tour=4,0,0">Sales Orders</a></span> in the Sales menu.<br><br>' +
	    	 '2) Click on  the search icon in the upper right corner and filter for the sales orders you want to prioritize.<br><br>' +
	    	 '3) Update the priority column and save. Note that top priority is 1 in frePPLe.<br>' +
	       '<br>' +	      
	       '<br>' +
	       '<iframe width="560" height="315" src="https://www.youtube.com/embed/y3kFr2p-CsY" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   //How can I input my operators' shifts or holidays?	5,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
	    	 '<h2>How can I input my operators\' shifts or holidays?</h2>' +
	    	 '1) Navigate to <span class="underline"><a href="{url_prefix}/data/input/calendar/?tour=5,0,0">Calendars</a></span> in the Manufacturing menu.<br><br>' +
	    	 '2) Click on the + icon in the upper right corner and add a new calendar for your operator with default value = 0 (for instance: Calendar for Antonio).<br><br>' +
	    	 '3) In Calendars Buckets, add another calendar bucket line with value = 1 for each availability of the operator.<br><br>' +
	    	 '4) For a shift, input a start date in the past and an end date far in the future, then select the days, start and end time of the shift.<br><br>' +
	    	 '5) For holidays, simply set the start date and end date of the period.<br><br>' +
	    	 '6) Navigate to <span class="underline"><a href="{url_prefix}/data/input/resource/?tour=5,0,0">Resources</a></span> in the Capacity menu and input the calendar\'s name in the Available column.<br>' +
	       '<br>' +	       
	       '<br>' +
	       '<iframe width="560" height="315" src="https://www.youtube.com/embed/1d5lcQCPZ1M" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   //How can I spot and review late orders?	6,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
	    	 '<h2>How can I spot and review late orders?</h2>' +
	    	 '1) Navigate to <span class="underline"><a href="{url_prefix}/data/input/demand/?tour=6,0,0">Sales Orders</a></span> screen in the Sales menu.<br><br>' +
	    	 '2) Click on  the search icon in the upper right corner and filter for status not equal closed.<br><br>' +
	    	 '3) Click on the Delay column to sort the orders by delay descending.<br><br>' +
	    	 '4) For each late order, drill down into details by clicking on the pointing triangle in the Name column.<br><br>' +
	    	 '5) Then, pick the ""Why short or late?"" tab in the upper right corner to check why it\'s late.<br>' +
	       '<br>' +	       
	       '<br>' +
	       '<iframe width="560" height="315" src="https://www.youtube.com/embed/gJN7IkqDx90" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   //How can I track down bottleneck resources ? 7,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
	    	 '<h2>How can I track down bottleneck resources ?</h2>' +
	    	 '1) Navigate to <span class="underline"><a href="{url_prefix}/resource/?tour=7,0,0">Resource report</a></span> in the Capacity menu.<br><br>' +
	    	 '2) Click on  the clock icon in the upper right corner to adjust the buckets.<br><br>' +
	    	 '3) Click on the Utilization column to sort the resources by utilization descending.<br>' +
	       '<br>' +	       
	       '<br>' +
	       '<iframe width="560" height="315" src="https://www.youtube.com/embed/9cIbk1-hl_s" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   // And their unconstrained requirements	8,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
	    	 '<h2>...and their unconstrained capacity requirements?</h2>' +
	    	 '1) Navigate to <span class="underline"><a href="{url_prefix}/execute/?tour=8,0,0">execute</a></span> in the Admin menu.<br><br>' +
	    	 '2) Execute a constrained plan but make sure that the capacity constrained is unchecked.<br><br>' +
	    	 '3) Navigate to <span class="underline"><a href="{url_prefix}/resource/?tour=7,0,0">Resource report</a></span> in the Capacity menu and review capacityconsumption.<br><br>' +	    	 
	       '<br>' +	       
	       '<br>' +
	       '<iframe width="560" height="315" src="https://www.youtube.com/embed/engf6K5KVEs" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   
   //How can I measure the impact of rush orders? 9,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
	    	 '<h2>How can I measure the impact of rush orders?</h2>' +
	    	 '1) Navigate to <span class="underline"><a href="{url_prefix}/execute/?tour=9,0,0">Execute</a></span> in the Admin menu.<br><br>' +
	    	 '2) Pick the Scenario management tab in the Launch tasks menu.<br><br>' +
	    	 '3) Select a Scenario and Copy default into selected scenarios. Then click on Copy.<br><br>' +
	    	 '4) In the dropdown section in the upper right corner, select the scenario you\'ve just created.<br><br>' +
	    	 '5) Navigate to "Sales Orders" in the Sales menu.<br><br>' +
	    	 '6) Click on the search icon in the upper right corner and filter for the rush order.<br><br>' +
	    	 '7) Update the priority column to make the order top priority (1) and save.<br><br>' +
	    	 '8) Navigate to "Execute" in the Admin menu and click on Launch to re-execute the plan.<br><br>' +
	    	 '9) To review the impact of the rush order, compare your scenario\'s delivery dates with your production environment.<br>' +
	       '<br>' +	       
	       '<br>' +
	       '<iframe width="560" height="315" src="https://www.youtube.com/embed/QZlikQNC8jI" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   //How precisely can I quote a delivery date for a new customer order? 10,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
	    	 '<h2>How precisely can I quote a delivery date for a new customer order?</h2>' +
	    	 '1) Navigate to the <span class="underline"><a href="{url_prefix}/quote/?tour=10,0,0">Quotes</a></span> under the Sales menu.<br><br>' +
	    	 '2) Populate the required fields in the Quote Form.<br><br>' + 
	    	 '3) Click on the inquiry button and check in the Operations widget the proposed end date corresponding to the first promise date for the sales order.<br>'+
	       '<br>' +	       
	       '<br>' +
	       '<iframe width="560" height="315" src="https://www.youtube.com/embed/bW8UjI_ZEF8" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   //How can I optimize my plan in the GANTT chart plan editor?	11,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Production Planning</h2>' +
	    	 '<h2>How can I optimize my plan in the GANTT chart plan editor?</h2>' +
	    	 'Navigate to <span class="underline"><a href="{url_prefix}/planningboard/?tour=11,0,0">Plan Editor</a></span> in the Manufacturing menu and select an order on the GANTT chart.<br>' +
	    	 'From there, you can:<br><br>'+
	    	 '1) modify the start/end time of an order by dragging and dropping the block or editing dates in the Manufacturing Order widget.<br><br>' +
	    	 '2) Pick an alternate operation when possible.<br><br>' +
	    	 '3) Pick an alternate resource when possible.<br><br>' +
	    	 'Any of the above change will trigger a plan update, frePPLe will make sure that the plan remains feasible.<br><br>' +	    	 
	       '<br>' +	       
	       '<br>' +
	       '<iframe width="560" height="315" src="https://www.youtube.com/embed/j6O-WmqxgHQ" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   
   // INTEGRATION
   //How do I export proposed purchase orders to an ERP system? 12,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Integration</h2>' +
	    	 '<h2>How do I export proposed purchase orders to an ERP system?</h2>' +
	    	 '1) Navigate to <span class="underline"><a href="{url_prefix}/execute/?tour=12,0,0">Execute</a></span> in the Admin menu.<br><br>' +
	    	 '2) Pick the Export plan result to folder tab in the Launch tasks menu and click on Export. <br><br>' +
	    	 '3) You can see it has been exported in the Tasks status above.<br><br>' +
	    	 '<br>' +	    	 
	    	 '<br>' +
	    	 '<iframe width="560" height="315" src="https://www.youtube.com/embed/Fd6SRvH6d7w" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   //What is the meaning of each MO/PO/DO status? 13,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Integration</h2>' +
	    	 '<h2>What is the meaning of each MO/PO/DO status?</h2>' +	    	 
	    	 '1) Proposed: This is a proposition from frePPLe to plan the demand.<br><br>' +
	    	 '2) Confirmed: This order is confirmed in the ERP and frePPLe will execute it without question.<br><br>' +
	    	 '3) Approved: A proposed order that has been approved by the planner and that should be exported to ERP.<br><br>' +
	    	 '4) Note that approved order could be moved by the solver to satisfy feasibility of the plan.<br><br>' +
	    	 '<br>' +	    	 
	    	 '<br>' +
	    	 '<iframe width="560" height="315" src="https://www.youtube.com/embed/zZ7LQDyeis4" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   //How do I synchronize data in frePPLe with my ERP system? 14,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; Integration</h2>' +
	    	 '<h2>How do I synchronize data in frePPLe with my ERP system?</h2>' +
	    	 'To synchronize your ERP with frePPLe, you can either:<br>' +
	    	 '1) upload Excel or csv files into each table of frePPLe.<br><br>' +
	    	 '2) upload all csv files in the import folder of the Execute screen using the ""import data from folder"" feature.<br><br>' +
	    	 '3) use the available REST api to upload data.<br><br>' +
	    	 '4) automate step 2) or 3) with nighly workflows as explained in the integration chapter of the documentation.<br><br>' +
	    	 '<br>' +	    	 
	    	 '<br>' +
	    	 '<iframe width="560" height="315" src="https://www.youtube.com/embed/-neYh_jV3_s" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   },
   
   // USER INTERFACE
   //How do what-if scenarios work?	15,0,0
   {
	   description: 
	    	 '<h2><span class="underline"><a href="{url_prefix}/?tour=0,0,0"><i class="fa fa-home" aria-hidden="true"></i></a></span> &gt; What-if scenarios</h2>' +
	    	 '<h2>How do what-if scenarios work?</h2>' +
	    	 'Documentation is available <span class="underline"><a href="https://frepple.com/docs/5.3/user-guide/user-interface/what-if-scenarios.php">here</a></span>.' +
	    	 '<br>' +	    	 
	    	 '<br>' +
	    	 '<iframe width="560" height="315" src="https://www.youtube.com/embed/1lN-ozMOM7g" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
   }
   
];
