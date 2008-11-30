
// A class to store changes in memory till the save button is hit.
var upload = {
  _data : [],

  add : function (e)
  {
    upload._data.push(e);
    $('save').style.display = 'inline';
    $('undo').style.display = 'inline';
  },

  undo : function ()
  {
    // Refresh the page
    window.location.href=window.location.href;
  },

  save : function (e)
  {
    // Send the update to the server, synchronously
    var payload =
      '--7d79\r\nContent-Disposition: form-data; name="data";'
      + 'filename="data"\r\nContent-Type: application/json\r\n\r\n'
      + Object.toJSON(upload._data)
      + '\r\n\r\n--7d79--\r\n'
    new Ajax.Request("/edit/", {
        method: 'post',
        asynchroneous: false,
        contentType: 'multipart/form-data; boundary=7d79',
        postBody: payload,
        onSuccess: function(transport) {},
        onFailure: function(transport) {}
        });

    // Refresh the page
    window.location.href=window.location.href;
  }
}


var ContextMenu = {

	// private attributes
	_attachedElement : null,
	_menuElement : null,

  // A private hash mapping each class to a menu id
  _menus : {
    'buffer': 'buffercontext',
		'resource': 'resourcecontext',
		'operation': 'operationcontext',
		'location': 'locationcontext',
		'item': 'itemcontext',
    'demand': 'demandcontext',
		'forecast': 'forecastcontext',
		'customer': 'customercontext',
		'calendar': 'calendarcontext',
		'numfilteroper': 'datefilter',
    'datefilteroper': 'datefilter',
    'textfilteroper': 'textfilter'
	},

	// private method. Get which context menu to show
	_getMenuElementId : function (e)
	{
	  ContextMenu._attachedElement = Prototype.Browser.IE ?
	    event.srcElement :
	    e.target;

		while(ContextMenu._attachedElement != null)
		{
			var className = ContextMenu._attachedElement.className;

			if (typeof(className) != "undefined")
			{
				className = className.replace(/^\s+/g, "").replace(/\s+$/g, "")
				var classArray = className.split(/[ ]+/g);

				for (i = 0; i < classArray.length; i++)
					if (ContextMenu._menus[classArray[i]])
						return ContextMenu._menus[classArray[i]];
			}

		  ContextMenu._attachedElement = Prototype.Browser.IE ?
		    ContextMenu._attachedElement.parentElement :
		    ContextMenu._attachedElement.parentNode;
		}
		return null;
	},


	// private method. User clicked somewhere in the screen
	_onclick : function (e)
	{

		// Hide the previous context menu, and update operator
		if (ContextMenu._menuElement)
	  {
	    // Hide
			ContextMenu._menuElement.style.display = 'none';

			// If we are closing an operator menu, update the operator
			if (ContextMenu._menuElement.hasClassName("OperatorMenu") && ContextMenu._attachedElement)
			{
			  // Operator selected, or clicked somewhere else?
			  x = Prototype.Browser.IE ? event.srcElement : e.target;
        if ($(x).up().hasClassName("OperatorMenu"))
        {
			    // Update the span displaying the choosen operator
			    ContextMenu._attachedElement.innerHTML = x.innerHTML;

			    // Update the name of the filter input field
			    filterfield = ContextMenu._attachedElement.id.replace("operator","filter");
          $(filterfield).name = $(filterfield).name.substr(0,$(filterfield).name.lastIndexOf("__")+2) + x.id;
        }
		  }
		}

    // No further handling for rightclicks
    if (e!=undefined && !Event.isLeftClick(e)) return true;

    // Find the id of the menu to display
		var menuElementId = ContextMenu._getMenuElementId(e);
		if (menuElementId)
		{
			var m = ContextMenu._getMousePosition(e);
			var s = ContextMenu._getScrollPosition(e);

			ContextMenu._menuElement = $(menuElementId);

      // Get the entity name
			var item = ContextMenu._attachedElement.innerHTML;

			// Unescape all escaped characters and urlencode the result for usage as a url
			item = encodeURIComponent(item.replace(/&amp;/g,'&').replace(/&lt;/g,'<')
			  .replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"'));

			// Build the urls for the menu
			var l = ContextMenu._menuElement.getElementsByTagName("a");
			for (x=0; x<l.length; x++)
			  l[x].href = l[x].id.replace(/%s/,item);

      // Display the menu at the right location
			ContextMenu._menuElement.style.left = m.x + s.x + 'px';
			ContextMenu._menuElement.style.top = m.y + s.y + 'px';
			ContextMenu._menuElement.style.display = 'block';
			return false;
		}

		var returnValue = true;
		var evt = Prototype.Browser.IE ? window.event : e;

		if (evt.button != 1)
		{
			if (evt.target) var el = evt.target;
			else if (evt.srcElement) var el = evt.srcElement;
			var tname = el.tagName.toLowerCase();
			if ((tname == "input" || tname == "textarea")) return true;
		}
	  else
		  return  false;
	},


	// private method. Returns mouse position
	_getMousePosition : function (e)
	{
		e = e ? e : window.event;
		return {'x' : e.clientX, 'y' : e.clientY}
	},


	// private method. Get document scroll position
	_getScrollPosition : function ()
	{
		if( typeof( window.pageYOffset ) == 'number' )
		  return {'x' : window.pageXOffset, 'y' : window.pageYOffset}
		else if( document.documentElement && ( document.documentElement.scrollLeft || document.documentElement.scrollTop ) )
		  return {'x' : document.documentElement.scrollLeft, 'y' : document.documentElement.scrollTop}
		else if( document.body && ( document.body.scrollLeft || document.body.scrollTop ) )
		  return {'x' : document.body.scrollLeft, 'y' : document.body.scrollTop}
		return {'x' : 0, 'y' : 0}
	},

  // Hide the menu
  hide : function ()
  {
		if (ContextMenu._menuElement)
			ContextMenu._menuElement.style.display = 'none';
  }
}

// Install a handler for all clicks on the page
document.onclick = ContextMenu._onclick;


//----------------------------------------------------------------------------
// Code for handling the menu bar and active button.
//----------------------------------------------------------------------------

var activeButton = null;

// Capture mouse clicks on the page so any active button can be deactivated.
document.observe('mousedown',  function (event) {

  // If there is no active button, exit.
  if (activeButton == null) return;

  // Find the element that was clicked on.
  var el = Event.element(event);

  // If the active button was clicked on, exit.
  if (el == activeButton) return;

  // If the element is not part of a menu, reset and clear the active button.
  if (el.up('div.menu') == undefined) {
    resetButton(activeButton);
    activeButton = null;
  }
}, true);


function buttonClick(event, menuId)
{
  // Get the target button element.
  var button = $(Event.element(event));

  // Blur focus from the link to remove that annoying outline.
  button.blur();

  // Associate the named menu to this button if not already done.
  // Additionally, initialize menu display.
  if (button.menu == null) button.menu = $(menuId);

  // Reset the currently active button, if any.
  if (activeButton != null) resetButton(activeButton);

  // Activate this button, unless it was the currently active one.
  if (button != activeButton)
  {
    // Update the button's style class to make it look like it's depressed.
    button.addClassName("menuButtonActive");

    // Position the associated drop down menu under the button and show it.
    var pos = button.cumulativeOffset();
    pos[1] += button.getHeight();
    button.menu.style.left = pos[0] + "px";
    button.menu.style.top  = pos[1] + "px";

    button.menu.style.visibility = "visible";
    activeButton = button;
  }
  else
    activeButton = null;

  return false;
}


function buttonMouseover(event, menuId)
{
  // If any other button menu is active, make this one active instead.
  if (activeButton != null && activeButton != $(Event.element(event)))
    buttonClick(event, menuId);
}


function resetButton(button)
{
  // Restore the button's style class.
  button.removeClassName("menuButtonActive");

  // Hide the button's menu
  if (button.menu != null) button.menu.style.visibility = "hidden";
}


function filterform()
{
  // The filter header has a lot of fields. To keep the urls clean we use only
  // the non-empty fields in the form URL.
  var data = $$('.filter').inject({ }, function(result, element) {
    key = element.name;
    value = $(element).getValue();
    if (value != '' && element.type != 'submit')
    {
      if (key in result)
      {
        // a key is already present; construct an array of values
        if (!Object.isArray(result[key])) result[key] = [result[key]];
        result[key].push(value);
       }
       else result[key] = value;
    }
    return result;
    });

  // Examine the current url, and extract optional sort and popup arguments
  var args = location.href.toQueryParams();
  if ('o' in args) data['o'] = args['o'];
  if ('pop' in args) data['pop'] = args['pop'];

  // Go to the new url
  location.href = "?" + Object.toQueryString(data);
}


function import_show(list_or_table)
{
  var element = $('popup');
  element.innerHTML = '<h2>Import data</h2><br/>'+
    '<form enctype="multipart/form-data" method="post" action="' + location.href + '"><table><tr>'+
    '<td colspan="2">Load data from a CSV-formatted text file in the database.<br/>'+
    'The first row should contain the field names.</td></tr>'+
    '<tr><td>Data file:</td><td><input type="file" id="csv_file" name="csv_file"/></td></tr>'+
    '<tr><td><input id="upload" type="submit" value="Upload"/></td>'+
    '<td><input type="button" value="Close" onclick="$(\'popup\').style.display = \'none\';"/></td></tr>'+
    '</table></form>';
  var position = $('csvexport').cumulativeOffset();
  position[0] -= 252;
  position[1] += 20;
  element.style.width = '290px';
  element.style.left = position[0]+'px';
  element.style.top  = position[1]+'px';
  element.style.position = "absolute";
  element.style.display  = "block";
}


function export_show(list_or_table)
{
  // The argument is true when we show a "list" report.
  // It is false for "table" reports.
  var element = $('popup');
  element.innerHTML = '<h2>Export data</h2><br/>'+
    '<form method="get" action="javascript:export_close()"><table>'+
    '<tr><th>CSV style:</th><td><select name="csvformat" id="csvformat"' + (list_or_table ? ' disabled="true"' : '')+ '>'+
    '<option value="csv"' + (list_or_table ? '' : ' selected="selected"') + '>Table</option>'+
    '<option value="csvlist"' + (list_or_table ?  ' selected="selected"' : '') + '>List</option></select></td></tr>'+
    '<tr><td><input type="submit" value="Export"/></td>'+
    '<td><input type="button" value="Close" onclick="$(\'popup\').style.display = \'none\';"/></td></tr>'+
    '</table></form>';
  var position = $('csvexport').cumulativeOffset();
  position[0] -= 132;
  position[1] += 20;
  element.style.width = '170px';
  element.style.left = position[0]+'px';
  element.style.top  = position[1]+'px';
  element.style.position = "absolute";
  element.style.display  = "block";
}


function export_close()
{
  // Fetch the report data
  var url = location.href;
  if (location.search.length > 0)
    // URL already has arguments
    url += "&reporttype=" + $('csvformat').value;
  else
    // This is the first argument for the URL
    url += "?reporttype=" + $('csvformat').value;
  window.open(url,'_blank');
  // Hide the popup window
  $('popup').style.display = 'none';
}


function bucket_show()
{
  // Pick up the arguments
  var buckets = $('timebuckets').innerHTML.split(',');
  // Show popup
  var element = $('popup');
  element.innerHTML = '<h2>Time bucketization</h2><br/>'+
    '<form method="get" action="javascript:bucket_close()"><table>'+
    '<tr><th>Buckets:</th><td><select name="buckets" id="reportbucket">'+
    '<option value="default"' + (buckets[0]=='default' ? 'selected="selected"' : '') + '>Default</option>'+
    '<option value="day"' + (buckets[0]=='day' ? 'selected="selected"' : '') + '>Day</option>'+
    '<option value="week"' + (buckets[0]=='week' ? 'selected="selected"' : '') + '>Week</option>'+
    '<option value="month"' + (buckets[0]=='month' ? 'selected="selected"' : '') + '>Month</option>'+
    '<option value="quarter"' + (buckets[0]=='quarter' ? 'selected="selected"' : '') + '>Quarter</option>'+
    '<option value="year"' + (buckets[0]=='year' ? 'selected="selected"' : '') + '>Year</option>'+
    '</select></td></tr>'+
    '<tr><th>Report start date:</th><td><input id="reportstart" type="text" size="10" class="vDateField" value="' + buckets[1] + '" name="startdate"/></td></tr>'+
    '<tr><th>Report end date:</th><td><input id="reportend" type="text" size="10" class="vDateField" value="' + buckets[2] + '" name="enddate" /></td></tr>'+
    '<tr><td><input type="submit" value="OK"/></td>'+
    '<td><input type="button" value="Cancel" onclick="$(\'popup\').style.display = \'none\';"/></td></tr>'+
    '</table></form>';
  var position = $('csvexport').cumulativeOffset();
  position[0] -= 132;
  position[1] += 20;
  element.style.width = '170px';
  element.style.left = position[0]+'px';
  element.style.top  = position[1]+'px';
  element.style.position = "absolute";
  DateTimeShortcuts.addCalendar($('reportstart'));
  DateTimeShortcuts.addCalendar($('reportend'));
  element.style.display  = "block";
}

function bucket_close()
{
  // Determine the URL arguments
  var currentvalues = $('timebuckets').innerHTML.split(',');
  var args = new Hash(location.search.toQueryParams());
  var changed = false;
  if ($('reportbucket').value != currentvalues[0])
  {
    args.set('reportbucket', $('reportbucket').value);
    changed = true;
  }
  else
    args.unset('reportbucket');
  if ($('reportstart').value != currentvalues[1])
  {
    args = args.merge({'reportstart': $('reportstart').value});
    changed = true;
  }
  else
    args.unset('reportstart');
  if ($('reportend').value != currentvalues[2])
  {
    args = args.merge({'reportend':  $('reportend').value});
    changed = true;
  }
  else
    args.unset('reportend');

  if (!changed)
    // No changes to the settings. Just close the popup.
    $('popup').style.display = 'none';
  else
    // Fetch the new report. This also hides the popup again.
    location.href = location.pathname + "?" + args.toQueryString();
}


var dr,dl,ur,ul,dlt,drt,ult,urt;
var scrollbarSize = 16;


/* The scrolling table is built from 4 divs, each with a nested table in it:
     div ul             div ur
       |-> table ult      |-> table urt
     div dl             div dr
       |-> table dlt      |-> table drt
   Javascript is used to:
   - resize the height of the rows such that they match
   - resize the height of the columns such that they match
   - apply the scrolling in drt also to urt and dlt
   - resize the scrollable table such that the available screen space is used optimally
*/

function installLoadHandler()
{
  // Disable the django-supplied event handler to initialize calendar menus.
  try {removeEvent(window,'load',DateTimeShortcuts.init);} catch (error) {;};

  // Install our own handler, which will explicitly call the django function.
  // This is the only cross-browser method to garantuee that the django handler is
  // called before our own one.
  Event.observe(window, 'load', syncInitialize);
}


function syncInitialize()
{
  // Variables for the data grid
  dr = $('dr');
  dl = $('dl');
  ur = $('ur');
  ul = $('ul');
  dlt = $('dlt');
  drt = $('drt');
  ult = $('ult');
  urt = $('urt');

  var hasFrozenColumns = dlt ? true : false;
  var hasData = drt.down('tr') ? true : false;

  // Call the django-supplied javascript function to initialize calendar menus.
  // This needs to be done upfront to make sure that the elements get their
  // correct size right away.
  try {DateTimeShortcuts.init();} catch (error) {;};

  // Variables for the cell dimensions
  var CellFrozenWidth = new Array();
  var CellWidth = new Array();
  var CellHeight = new Array();
  var TotalFrozenWidth = 0;
  var i;

  if (hasData)
  {

    // First step: Measure the dimensions of the rows and columns

    // Measure cell width
    var columnheaders = urt.getElementsBySelector('th');
    var columndata = drt.down('tr').getElementsBySelector('td');
    var left;
    var right;
    i = 0;
    var TotalWidth = 0;
    columndata.each(function(s) {
      left = s.getWidth();
      right = columnheaders[i].getWidth();
      CellWidth[i] = right > left ? right : left;
      TotalWidth += CellWidth[i++];
      });

    if (hasFrozenColumns)
    {
      // Measure frozen cell width
      var columnheaders = ult.getElementsBySelector('th');
      var columndata = dlt.down('tr').getElementsBySelector('td');
      i = 0;
      columndata.each(function(s) {
        left = s.getWidth();
        right = columnheaders[i].getWidth();
        CellFrozenWidth[i] = right > left ? right : left;
        TotalFrozenWidth += CellFrozenWidth[i++];
        });

      // Sync cell height
      var rowheaders = dlt.getElementsBySelector('tr');
      var rowdata = drt.getElementsBySelector('tr');
      i = 0;
      rowheaders.each(function(s) {
        left = s.getHeight();
        right = rowdata[i].getHeight();
        CellHeight[i++] = right > left ? right : left;
        });
    }

    // Second step: Updates the dimensions of the rows and columns
    // We only start resizing after all cells are measured, because the
    // updating also could influence the measuring...

    var cellPadding = 10; // Hardcoded... I know it is 10.

    // Resize the width of the scrollable columns, up and down.
    var columnheaders = urt.getElementsBySelector('th');
    var columndata = drt.down('tr').getElementsBySelector('td');
    i = 0;
    columndata.each(function(s) {
      columnheaders[i].style.width = (CellWidth[i]-cellPadding) + 'px';
      s.style.width = (CellWidth[i++]-cellPadding) + 'px';
      });
    drt.style.width = TotalWidth + 'px';
    urt.style.width = TotalWidth + 'px';

    if (hasFrozenColumns)
    {
      // Resize the height of the header row, frozen and scrolling sides
      var left = ult.getHeight();
      var right = urt.getHeight();
      if (left < right) left = right;
      urt.style.height = ult.style.height = left + 'px';

      // Resize the width of the frozen columns, up and down.
      // The constant 10 is taking into account the padding... Ugly hardcode.
      var columnheaders = ult.getElementsBySelector('th');
      var columndata = dlt.down('tr').getElementsBySelector('td');
      i = 0;
      columndata.each(function(s) {
        columnheaders[i].style.width = (CellFrozenWidth[i]-cellPadding) + 'px';
        s.style.width = (CellFrozenWidth[i++]-cellPadding) + 'px';
        });
      dlt.style.width = ult.style.width = TotalFrozenWidth + 'px';

      // Resize the height of the data rows, frozen and scrolling sides
      var rowheaders = dlt.getElementsBySelector('tr');
      var rowdata = drt.getElementsBySelector('tr');
      i = 0;
      rowheaders.each(function(s) {
        rowdata[i].style.height = CellHeight[i] + 'px';
        s.style.height = CellHeight[i++] + 'px';
        });
    }
  }

  // Resize the available size for the table.
  syncResize();

  // Watch all changes in window size
  Event.observe(window, 'resize', syncResize);
}


function syncResize()
{
  // Resize the available size for the table. This needs to be done at the
  // end, when rows and columns have taken on their correct size.
  // Respect also a minimum size for the table. If the height decreases further
  // we use a scrollbar on the window rather than resizing the container.
  // Assumption: The table in the down right corner of the grid is the only
  // container that can be resized for this purpose.

  // Measure the total screen size and the resizable part of the grid
  var currentResizable = dr.getDimensions();
  var totalAvailable = document.viewport.getDimensions();
  var totalResizableX = $(document.documentElement).scrollWidth;
  var totalResizableY = $(document.documentElement).scrollHeight;

  // Calculate width
  var delta = totalAvailable.width - totalResizableX;
  var width = currentResizable.width + delta;
  //size += 16;
  if (width < 150) width = 150;
  if (width > dr.scrollWidth) width = dr.scrollWidth;

  // Calculate height
  delta = totalAvailable.height - totalResizableY;
  var height = currentResizable.height + delta;
  //height += 16;
  if (height < 150) height = 150;
  if (height > dr.scrollHeight) height = dr.scrollHeight;

  // Update the size of the grid
  ur.style.width = dr.style.width = width + "px";
  if (dl) dl.style.height = dr.style.height = height + "px";

  ///alert (" xxx  " + totalAvailable.width +  "   " +  totalResizable + "  " + currentResizable.width + "  " + delta);
}


function syncScroll(left_or_right)
{
  // Synchronize the scrolling in the header row and frozen column
  // with the scrolling in the data pane.
  if (left_or_right == 1)
  {
    // Scrolling the main data panel down right
    if (dlt) dlt.style.bottom = dr.scrollTop + 'px';
    urt.style.right = dr.scrollLeft + 'px';
  }
  else
  {
    // Scrolling the panel with the pinned data column.
    // How does one scroll it when there is no scrollbar? Well, you can scroll
    // down using the search function of your browser
    alert ('xxx ' + dlt.scrollTop +  '  ' + dl.scrollTop);
    dr.style.bottom = dl.scrollTop + 'px';
  }
  ContextMenu.hide();

}
