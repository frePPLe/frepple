
// Django sets this variable in the admin/base.html template.
window.__admin_media_prefix__ = "/media/";

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
      '--7d79\r\nContent-Disposition: form-data; name="csrfmiddlewaretoken"\r\n\r\n'
      + getToken()
      + '\r\n--7d79\r\nContent-Disposition: form-data; name="data";'
      + 'filename="data"\r\nContent-Type: application/json\r\n\r\n'
      + Object.toJSON(upload._data)
      + '\r\n\r\n--7d79--\r\n';
    el = $("database");
    if (el == undefined)
      u = "/edit/";
    else if (el.name == "default")
      u = "/edit/";
    else
      u = "/" + el.name + "/edit/";
    new Ajax.Request(u, {
        method: 'post',
        asynchronous: false,
        contentType: 'multipart/form-data; boundary=7d79',
        postBody: payload,
        onComplete: function(transport) {
          // Refresh the page
          window.location.href=window.location.href;
          }
        });
  }
}


var ContextMenu = {

	// private attributes
	_attachedElement : null,
	_menuElement : null,

  // A private hash mapping each class to a menu id
  _menus : {
    'detail': 'detailcontext',
    'buffer': 'buffercontext',
		'resource': 'resourcecontext',
		'operation': 'operationcontext',
		'location': 'locationcontext',
		'item': 'itemcontext',
    'demand': 'demandcontext',
		'forecast': 'forecastcontext',
		'customer': 'customercontext',
		'calendar': 'calendarcontext',
		'setupmatrix': 'setupmatrixcontext'
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

		// Hide the previous context menu
		if (ContextMenu._menuElement)
			ContextMenu._menuElement.style.display = 'none';

    // No further handling for rightclicks
    if (e!=undefined && !Event.isLeftClick(e)) return true;

    // Find the id of the menu to display
		var menuElementId = ContextMenu._getMenuElementId(e);
		if (menuElementId)
		{
			var m = ContextMenu._getMousePosition(e);
			var s = ContextMenu._getScrollPosition(e);

			ContextMenu._menuElement = $(menuElementId);
      if (ContextMenu._menuElement == null) return false;

      // Get the entity name:
      // If href is equal to '#' we use the inner html of the link.
      // Otherwise we use the href value.
			var item = $(ContextMenu._attachedElement).readAttribute('href');
			if (item == '#')
			{
			  item = ContextMenu._attachedElement.innerHTML;
			  // Unescape all escaped characters and urlencode the result for usage as a URL
			  item = encodeURIComponent(item.replace(/&amp;/g,'&').replace(/&lt;/g,'<')
			    .replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/\//g,"_2F"));
      }

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


// Return the value of the csrf-token
function getToken() 
{
  var allcookies = document.cookie.split(';');
  for ( i = 0; i < allcookies.length; i++ ) 
    if (allcookies[i].strip().indexOf("csrftoken=") == 0)
      return allcookies[i].strip().substr(10).strip();
  return 'none';
}


// A javascript class implementing all functionality of the filter popup
var filter = {
  
  // Description of all operators
  description : {
    'icontains': gettext('contains (no case)'), 
    'contains': gettext('contains'),
    'istartswith': gettext('starts (no case)'),  
    'startswith': gettext('starts'),  
    'iendswith': gettext('ends (no case)'), 
    'endswith': gettext('ends'),  
    'iexact': gettext('equals (no case)'), 
    'exact': gettext('equals'),
    'isnull': gettext('is null'),
    '': '=',
    'lt': '&lt;',
    'gt': '&gt;',
    'lte': '&lt;=',
    'gte': '&gt;='
  },
  
  // Operator list for text fields
  textoperators : [
    'icontains','contains','istartswith','startswith',
    'iendswith','endswith','iexact','exact',
    'isnull','lt','lte','gt','gte'
  ],
  
  // Operator list for numberic and data fields
  numberoperators : [
    '','lt','lte','gt','gte','isnull'
  ],

  // Function called when submitting the form popup
  submit : function ()
  {
    // Collect the value of all filters.
    var data = {}
    $('popup').select('span').each(function(element) {
        if (element.id.indexOf('filter') == 0 && !element.hasClassName('datetimeshortcuts'))
        {
          index = element.id.substring(6);
          tmp = element.select('[name="filterfield' + index + '"]')[0];
          field = tmp.options[tmp.selectedIndex].value;
          tmp = element.select('[name="filterval' + index + '"]')[0];
          if (tmp.type == 'select-one')
          {
            value = tmp.options[tmp.selectedIndex].value;
            data[field] = value;
          }
          else
          {
            tmp = element.select('[name="filteroper' + index + '"]')[0];
            oper = tmp.options[tmp.selectedIndex].value;
            value = element.select('[name="filterval' + index + '"]')[0].value;
            if (value.length > 0)
            { 
              if (oper.length > 0)
                data[field + "__" + oper] = value;
              else
                data[field] = value;
            }
          }
        }
      });
  
    // Examine the current URL, and extract optional sort and popup arguments
    var args = location.href.toQueryParams();
    if ('o' in args) data['o'] = args['o'];
    if ('pop' in args) data['pop'] = args['pop'];
  
    // Go to the new URL
    location.href = "?" + Object.toQueryString(data);
  },

  // A function to construct and display the filter popup
  show : function()
  {  
  
    // Set form header
    data = '<h2>' + gettext("Filter data") 
      + '</h2><br/>\n<form method="get" action="javascript:filter.submit();">';
    
    // Display form fields for existing filters
    counter = 0;
    element = $('filters');
    if (element != null)
      element.childElements().each(function(element) {
        
        // Find value
        if (element.type == 'text')
          value = element.value;
        else if (element.type == 'select-one')
          value = element.options[element.selectedIndex].value;
        else
          // Not an input element
          return;
          
        // Find field and operator name
        counter++;
        tmp = element.name.lastIndexOf("__");  
        if (tmp == -1)
        {
          oper = 'exact';
          field = element.name;
        }
        else
        {
          field = element.name.substring(0,tmp);
          oper = element.name.substring(tmp+2);
        }
        
        // Create the field select list
        $('fields').select('span').each(function(element) {          
          if (element.title == field) thefield = element;
        })
        data += '<span id="filter' + counter + '" class="' + thefield.className + '">';
        data += '<a href="javascript:filter.remove(' +  counter + ');"><img style="float:right;" src="/media/img/admin/icon_deletelink.gif"/></a>';
        data += '<select name="filterfield' + counter + '" onchange="filter.change_field(this)">';
        $('fields').select('span').each(function(element) {          
          d = element.innerHTML.indexOf('<');
          if (d > 0)
            n = element.innerHTML.substring(0,d);
          else
            n = element.innerHTML;
          if (element.title == field) 
            data += '<option value="' + element.title + '" selected="yes">' + n + '</option>';
          else
            data += '<option value="' + element.title + '">' + n + '</option>';
        })
        data += '</select>';
        
        // Append the operator and value fields
        data += filter._build_row(thefield, oper, value, counter);
        
        // Append an icon
        data += '<br/></span>';    
      });
    
    // Display form field for adding a new filter
    data += '<span id="newfilter">';
    data += '<a href="javascript:filter.add();"><img id="newfiltericon" style="float:right;" src="/media/img/admin/icon_addlink.gif"/></a>';
    data += '<select onchange="filter.change_field(this);"><option value=""></option>';
    $('fields').select('span').each(function(element) {
      if (element.hasClassName('FilterChoice') || element.hasClassName('FilterText') || 
          element.hasClassName('FilterNumber') || element.hasClassName('FilterDate'))    
      {
        d = element.innerHTML.indexOf('<');
        if (d > 0)
          data += '<option value="' + element.title + '">' + element.innerHTML.substring(0,d) + '</option>';
        else
          data += '<option value="' + element.title + '">' + element.innerHTML + '</option>';
      }
    })
    data += '</select><br/></span>';
    
    // Set form footer
    data += '<br/><input type="submit" value="' + gettext("Filter") + '"/>&nbsp;&nbsp;';
    data += '<input type="button" value="' + gettext("Cancel");
    data += '" onclick="$(\'popup\').style.display = \'none\';"/></form></div>';
  
    // Replace the popup content
    var element = $('popup');
    element.innerHTML = data;
    
    // Add date picker
    element.select('input').each(function(element) {
      if (element.hasClassName('vDateField'))
       DateTimeShortcuts.addCalendar(element);
    })

    // Position the popup
    var position = $('csvexport').cumulativeOffset();
    position[0] -= 352;
    position[1] += 20;
    element.style.width = '350px';
    element.style.left = position[0]+'px';
    element.style.top  = position[1]+'px';
    element.style.position = "absolute";
    element.style.display  = "block";
  },
  
  // Function called when changing the field of a filter
  change_field : function(me)
  {
    var span = $(me).up('span');
    var tmp = span.select('select')[0];
      
    // Find the field
    field = tmp.options[tmp.selectedIndex].value;
    $('fields').select('span').each(function(element) {          
      if (element.title == field) thefield = element;
    });
    if (span.id == "newfilter")
    {
      // Find a free index number
      counter = 0;
      do 
        y = $('popup').select('#filter' + (++counter));
      while (y.length > 0);
        
      // Change the span element
      span.id = 'filter' + counter;
      span.className = thefield.className;
      
      // Change the field selector
      tmp.name = 'filterfield' + counter;
      
      // Append operator and value 
      tmp.insert({after: filter._build_row(thefield, '', '', counter)});
    }
    else
    {
      // Changing the field of an existing filter
      // Same field type - leave operator and value field unchanged
      if (thefield.className == span.className && !thefield.hasClassName('FilterChoice')) 
        return;        
      index = span.id.substring(6);
      // Delete fields of previous type
      span.removeChild(span.select('[name="filteroper' + index + '"]')[0]);
      span.removeChild(span.select('[name="filterval' + index + '"]')[0]);
      // Inser fields of the new type
      tmp.insert({after: filter._build_row(thefield, '', '', index)});
    }
        
    // Add date picker
    span.select('input').each(function(element) {
      if (element.hasClassName('vDateField'))
       DateTimeShortcuts.addCalendar(element);
    });
  },
  
  // Function called when deleting a filter
  remove : function(row)
  {
    // Remove a filter from the popup window
    var x = $('popup').select('#filter' + row)[0];
    x.parentNode.removeChild(x);  
  },
  
  // Function called when adding a filter
  add : function ()
  {
    var x = document.getElementById('popup').select('#newfiltericon')[0];
    tmp = x.up('span').select('select')[0];
  
    // Exit if no filter information is available
    if (tmp.selectedIndex == 0) return;
    field = tmp.options[tmp.selectedIndex].value;
  
    // Change the "add" icon to a "delete" icon
    index = x.up('span').id.substring(6);
    x.id = null;
    x.src = "/media/img/admin/icon_deletelink.gif";
    x.up('a').href = 'javascript:filter.remove(' + index + ');';
  
    // Append a new filter
    data = '<span id="newfilter"><a href="javascript:filter.add();"><img id="newfiltericon" style="float:right;" src="/media/img/admin/icon_addlink.gif"/></a><select onchange="filter.change_field(this);"><option value=""></option>';
    $('fields').select('span').each(function(element) {
      d = element.innerHTML.indexOf('<');
      if (d>0)
        data += '<option value="' + element.title + '">' + element.innerHTML.substring(0,d) + '</option>';
      else
        data += '<option value="' + element.title + '">' + element.innerHTML + '</option>';
    });
    data += '</select><br/></span>';
    x.up('span').insert({after: data});
  },
  
  // Internal function returning the HTML code for a filter operator and filter value
  _build_row : function(thefield, oper, value, index)
  {
    var result = '';
    if (thefield.hasClassName('FilterNumber'))
    {
      // Filter for number fields
      result += '</select>\n<select name="filteroper' + index + '">';
      filter.numberoperators.each(function(curoper) {
        if (oper == curoper)
           result += '<option value="' + curoper + '" selected="yes">' + filter.description[curoper] + '</option>';
        else
           result += '<option value="' + curoper + '">' + filter.description[curoper] + '</option>';
      })
      result += '</select>';
      result += '<input type="text" name="filterval' + index + '" value="' + value + '" size="10"/>\n';
    } 
    else if (thefield.hasClassName('FilterDate'))
    {
      // Filter for date fields
      result += '<select name="filteroper' + index + '">';
      filter.numberoperators.each(function(curoper) {
        if (oper == curoper)
           result += '<option value="' + curoper + '" selected="yes">' + filter.description[curoper] + '</option>';
        else
           result += '<option value="' + curoper + '">' + filter.description[curoper] + '</option>';
      })
      result += '</select>';
      result += '<input type="text" class="vDateField" name="filterval' + index + '" value="' + value + '" size="10"/>\n';
    } 
    else if (thefield.hasClassName('FilterBool'))
    {
      // Filter for boolean fields
      result += '<span name="filteroper' + index + '">equals </span><select name="filterval' + index + '">';
      if (value == '0') 
      {
        result += '<option value="0" selected="yes">' + gettext('False') + '</option>';
        result += '<option value="1">' + gettext('True') + '</option>';
      }
      else
      {
        result += '<option value="0">' + gettext('False') + '</option>';
        result += '<option value="1" selected="yes">' + gettext('True') + '</option>';
      }
      result += '</select>';
    } 
    else if (thefield.hasClassName('FilterChoice'))
    {
      // Filter for choice fields
      result += '<span name="filteroper' + index + '">equals </span><select name="filterval' + index + '">';
      thefield.select('option').each(function(element) {
        if (element.value == value) 
          result += '<option value="' + element.value + '" selected="yes">' + element.text + '</option>';
        else
          result += '<option value="' + element.value + '">' + element.text + '</option>';
        });
      result += '</select>';    
    } 
    else 
    {
      // Filter for text fields, also used as default
      result += '<select name="filteroper' + index + '">';
      filter.textoperators.each(function(curoper) {
        if (oper == curoper)
           result += '<option value="' + curoper + '" selected="yes">' + filter.description[curoper] + '</option>';
        else
           result += '<option value="' + curoper + '">' + filter.description[curoper] + '</option>';
      })
      result += '</select>';
      result += '<input type="text" name="filterval' + index + '" value="' + value + '" size="10"/>\n';
    } 
    return result;
  }

}


function import_show(list_or_table)
{
  var element = $('popup');
  // Replace the content
  element.innerHTML = '<h2>' + gettext("Import data") + '</h2><br/>' +
    '<form enctype="multipart/form-data" method="post" action=""><table><tr>'+
    '<input type="hidden" name="csrfmiddlewaretoken" value="' + getToken() + '"/>' +
    '<td colspan="2">' + gettext('Load data from a CSV-formatted text file in the database.') + '<br/>'+
    gettext('The first row should contain the field names.') + '</td></tr>'+
    '<tr><td>'+gettext('Data file') + ':</td><td><input type="file" id="csv_file" name="csv_file"/></td></tr>'+
    '<tr><td><input id="upload" type="submit" value="' + gettext('Upload') + '"/></td>'+
    '<td><input type="button" value="' + gettext('Cancel') + '" onclick="$(\'popup\').style.display = \'none\';"/></td></tr>'+
    '</table></form>';
  // Position the popup
  var position = $('csvexport').cumulativeOffset();
  position[0] -= 292;
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
  // Replace the content
  element.innerHTML = '<h2>' + gettext("Export data") +'</h2><br/>'+
    '<form method="get" action="javascript:export_close()"><table>'+
    '<tr><th>' + gettext("CSV style") + ':</th><td><select name="csvformat" id="csvformat"' + (list_or_table ? ' disabled="true"' : '')+ '>'+
    '<option value="csv"' + (list_or_table ? '' : ' selected="selected"') + '>' + gettext("Table") +'</option>'+
    '<option value="csvlist"' + (list_or_table ?  ' selected="selected"' : '') + '>' + gettext("List") +'</option></select></td></tr>'+
    '<tr><td><input type="submit" value="' + gettext("Export") +'"/></td>'+
    '<td><input type="button" value="' + gettext("Cancel") +'" onclick="$(\'popup\').style.display = \'none\';"/></td></tr>'+
    '</table></form>';
  // Position the popup
  var position = $('csvexport').cumulativeOffset();
  position[0] -= 202;
  position[1] += 20;
  element.style.width = '200px';
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
  else if (url.charAt(url.length - 1) == '?')
    // This is the first argument for the URL, but we already have a question mark at the end
    url += "reporttype=" + $('csvformat').value;
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
  element.innerHTML = '<h2>' + gettext("Time buckets") + '</h2><br/>'+
    '<form method="get" action="javascript:bucket_close()"><table>'+
    '<tr><th>' + gettext("Buckets") + ':</th><td><select name="buckets" id="reportbucket">'+
    '<option value="standard"' + (buckets[0]=='standard' ? 'selected="selected"' : '') + '>' + gettext("Standard") + '</option>'+
    '<option value="day"' + (buckets[0]=='day' ? 'selected="selected"' : '') + '>' + gettext("Day") + '</option>'+
    '<option value="week"' + (buckets[0]=='week' ? 'selected="selected"' : '') + '>' + gettext("Week") + '</option>'+
    '<option value="month"' + (buckets[0]=='month' ? 'selected="selected"' : '') + '>' + gettext("Month") + '</option>'+
    '<option value="quarter"' + (buckets[0]=='quarter' ? 'selected="selected"' : '') + '>' + gettext("Quarter") + '</option>'+
    '<option value="year"' + (buckets[0]=='year' ? 'selected="selected"' : '') + '>' + gettext("Year") + '</option>'+
    '</select></td></tr>'+
    '<tr><th>' + gettext("Start&nbsp;date") + ':</th><td><input id="reportstart" type="text" size="10" class="vDateField" value="' + buckets[1] + '" name="startdate"/></td></tr>'+
    '<tr><th>' + gettext("End&nbsp;date") + ':</th><td><input id="reportend" type="text" size="10" class="vDateField" value="' + buckets[2] + '" name="enddate" /></td></tr>'+
    '<tr><td><input type="submit" value="' + gettext("OK") + '"/></td>'+
    '<td><input type="button" value="' + gettext("Cancel") + '" onclick="$(\'popup\').style.display = \'none\';"/></td></tr>'+
    '</table></form>';
  var position = $('csvexport').cumulativeOffset();
  position[0] -= 202;
  position[1] += 20;
  element.style.width = '200px';
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
if (navigator.userAgent.toUpperCase().indexOf('MSIE') != -1)
  scrollbarSize = 11;


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
    var columnheaders = urt.select('th');
    var columndata = drt.down('tr').select('td');
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
      var columnheaders = ult.select('th');
      var columndata = dlt.down('tr').select('td');
      i = 0;
      columndata.each(function(s) {
        left = s.getWidth();
        right = columnheaders[i].getWidth();
        CellFrozenWidth[i] = right > left ? right : left;
        TotalFrozenWidth += CellFrozenWidth[i++];
        });

      // Sync cell height
      var rowheaders = dlt.select('tr');
      var rowdata = drt.select('tr');
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
    var columnheaders = urt.select('th');
    var columndata = drt.down('tr').select('td');
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
      var columnheaders = ult.select('th');
      var columndata = dlt.down('tr').select('td');
      i = 0;
      columndata.each(function(s) {
        columnheaders[i].style.width = (CellFrozenWidth[i]-cellPadding) + 'px';
        s.style.width = (CellFrozenWidth[i++]-cellPadding) + 'px';
        });
      dlt.style.width = ult.style.width = TotalFrozenWidth + 'px';

      // Resize the height of the data rows, frozen and scrolling sides
      var rowheaders = dlt.select('tr');
      var rowdata = drt.select('tr');
      i = 0;
      rowheaders.each(function(s) {
        rowdata[i].style.height = CellHeight[i] + 'px';
        s.style.height = CellHeight[i++] + 'px';
        });
    }
  }

  // Resize the available size for the table.
  syncResize();

  // Watch all changes in window size (except in broken IE)
  if (navigator.userAgent.toUpperCase().indexOf('MSIE') == -1)
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
  var currentPosition = dr.viewportOffset();
  var totalAvailable = document.viewport.getDimensions();
  var totalResizableY = $(document.documentElement).scrollHeight;

  // Calculate width
  var width = totalAvailable.width - currentPosition.left - scrollbarSize;
  if (width < 150)
  {
    width = 150;
    $(document.documentElement).style.overflowX = 'scroll';
  }
  else
    $(document.documentElement).style.overflowX = 'auto';
  if (width > dr.scrollWidth + scrollbarSize)
    width = dr.scrollWidth + scrollbarSize;
  
  // Calculate height
  var height = currentResizable.height + totalAvailable.height - totalResizableY + scrollbarSize;
  if (height < 150)
  {
    height = 150;
    $(document.documentElement).style.overflowY = 'scroll';
  }
  else
    $(document.documentElement).style.overflowY = 'auto';
  if (height > dr.scrollHeight + scrollbarSize) 
    height = dr.scrollHeight + scrollbarSize;
  
  // Update the size of the grid
  ur.style.width = dr.style.width = width + "px";
  if (dl) dl.style.height = dr.style.height = height + "px";
  else dr.style.height = height + "px";
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
    dr.style.bottom = dl.scrollTop + 'px';
  }
  ContextMenu.hide();

}


//
// Functions to convert units for the duration fields
//

var _currentunits = null;

var _factors = {
  'seconds': 1,
  'minutes': 60,
	'hours': 3600,
	'days': 86400,
	'weeks': 604800
};
	
function getUnits(unitselector)
{
  _currentunits = unitselector.value;
}

function setUnits(unitselector)
{
  var field = $(unitselector).previous();
  if (field.value && _currentunits!="" && unitselector.value!="") 
  {
    var val = parseFloat(field.value);
    val *= _factors[_currentunits];
    val /= _factors[unitselector.value];
    field.value = val;
  }
  _currentunits = unitselector.value;
}


function selectDatabase()
{
  el = $("database");
  // Find new database
  db = el.options[el.selectedIndex].value;
  // Current database
  cur = el.name;
  // Change the location
  if (cur != db)
  {
    if (cur == 'default')
      window.location.href = window.location.href.replace(window.location.pathname, "/"+db+window.location.pathname);
    else if (db == 'default')
      window.location.href = window.location.href.replace("/"+cur+"/", "/");
    else
      window.location.href = window.location.href.replace("/"+cur+"/", "/"+db+"/");
  }
}