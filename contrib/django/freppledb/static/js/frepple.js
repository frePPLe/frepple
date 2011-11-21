
// Django sets this variable in the admin/base.html template.
window.__admin_media_prefix__ = "/media/";

// A class to store changes in memory till the save button is hit.
var upload = {
  _data : [],

  add : function (e)
  {
    upload._data.push(e);
    $('#save').css('display', 'inline');
    $('#undo').css('display', 'inline');
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
    el = $("#database");
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


//----------------------------------------------------------------------------
// Customer formatter functions for the grid cells.
//----------------------------------------------------------------------------

function linkunformat (cellvalue, options, cell) {
  return cellvalue;
}

jQuery.extend($.fn.fmatter, {
  item : function(cellvalue, options, rowdata) {
    return '<a href="' + cellvalue + '" class="item context">' + cellvalue + "</a>";
  },
  customer : function(cellvalue, options, rowdata) {
    return '<a href="' + cellvalue + '" class="customer context">' + cellvalue + "</a>";
  },
  buffer : function(cellvalue, options, rowdata) {
    return '<a href="' + cellvalue + '" class="buffer context">' + cellvalue + "</a>";
  },  
  resource : function(cellvalue, options, rowdata) {
    return '<a href="' + cellvalue + '" class="resource context">' + cellvalue + "</a>";
  },
  forecast : function(cellvalue, options, rowdata) {
    return '<a href="' + cellvalue + '" class="forecast context">' + cellvalue + "</a>";
  },
  demand : function(cellvalue, options, rowdata) {
    return '<a href="' + cellvalue + '" class="demand context">' + cellvalue + "</a>";
  },
  operation : function(cellvalue, options, rowdata) {
    return '<a href="' + cellvalue + '" class="operation context">' + cellvalue + "</a>";
  },
  calendar : function(cellvalue, options, rowdata) {
    return '<a href="' + cellvalue + '" class="calendar context">' + cellvalue + "</a>";
  }
});
jQuery.extend($.fn.fmatter.item, {
    unformat : linkunformat
});
jQuery.extend($.fn.fmatter.buffer, {
    unformat : linkunformat
});
jQuery.extend($.fn.fmatter.resource, {
    unformat : linkunformat
});
jQuery.extend($.fn.fmatter.forecast, {
    unformat : linkunformat
});
jQuery.extend($.fn.fmatter.customer, {
    unformat : linkunformat
});
jQuery.extend($.fn.fmatter.operation, {
    unformat : linkunformat
});
jQuery.extend($.fn.fmatter.demand, {
    unformat : linkunformat
});
jQuery.extend($.fn.fmatter.calendar, {
    unformat : linkunformat
});


//----------------------------------------------------------------------------
// Code for handling the menu bar, context menu and active button.
//----------------------------------------------------------------------------

var activeButton = null;
var contextMenu = null;
  
$(function() {
  
  // Install code executed when you click on a menu button
  $(".menuButton").click( function(event) {
    // Get the target button element
    var button = $(event.target);
    var menu = button.next(".menu");
    
    // Blur focus from the link to remove that annoying outline.
    button.blur();
  
    // Reset the currently active button, if any.
    if (activeButton) {
      activeButton.removeClass("menuButtonActive");
      activeButton.next(".menu").css('visibility', "hidden");      
    }
  
    // Activate this button, unless it was the currently active one.
    if (button != activeButton)
    {
      // Update the button's style class to make it look like it's depressed.
      button.addClass("menuButtonActive");
  
      // Position the associated drop down menu under the button and show it.
      var pos = button.offset();
      menu.css({
        left: pos.left + "px",
        top: (pos.top + button.outerHeight() + 1) + "px",
        visibility: "visible"
        });
      activeButton = button;
    }
    else    
      activeButton = null;
  });
  
  $('.menuButton').mouseenter( function(event) {
    // If another button menu is active and we move the mouse into a new menu button, 
    // we make this one active instead.
    if (activeButton != null && activeButton != $(event.target))
      $(event.target).click();
  });

  // Send django's CRSF token with every POST request to the same site
  $(document).ajaxSend(function(event, xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type) && sameOrigin(settings.url)) 
      xhr.setRequestHeader("X-CSRFToken", getToken());
    });

});


// Capture mouse clicks on the page so any active button can be deactivated.
$(document).mousedown(function (event) {

  // Hide any context menu
	if (contextMenu)
	{
		contextMenu.css('display', 'none');
		contextMenu = null;
	}

  // We clicked not on a context menu. Display that now.
  if ($(event.target).hasClass('context')) 
  {      
    // Find the id of the menu to display    
    contextMenu = $('#' + $(event.target).attr('class').replace(" ",""));

    // Get the entity name:
    // If href is equal to '#' we use the inner html of the link.
    // Otherwise we use the href value.
		var item = $(event.target).attr('href');
		if (item == '#')
		{
		  item = $(contextMenu).html();
		  // Unescape all escaped characters and urlencode the result for usage as a URL
		  item = encodeURIComponent(item.replace(/&amp;/g,'&').replace(/&lt;/g,'<')
		    .replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/\//g,"_2F"));
    }
  
		// Build the urls for the menu
		contextMenu.find('a').each( function(i) {
		  $(this).attr('href', $(this).attr('id').replace(/%s/,item));
		});

    // Display the menu at the right location
		$(contextMenu).css({
		  left: event.pageX,
		  top: event.pageY,
		  display: 'block'
		  });
		event.preventDefault();
		event.stopImmediatePropagation();
	};

  // If there is no active button, exit.
  if (!activeButton || event.target == activeButton) return;

  // If the element is not part of a menu, hide the menu
  if ($(event.target).parent('div.menu').length < 1) {
    activeButton.removeClass("menuButtonActive");
    activeButton.next(".menu").css('visibility', "hidden");      
    activeButton = null;
  }
});


// Return the value of the csrf-token
function getToken() 
{
  var allcookies = document.cookie.split(';');
  for ( i = allcookies.length; i >= 0; i-- ) 
    if (jQuery.trim(allcookies[i]).indexOf("csrftoken=") == 0)
      return jQuery.trim(jQuery.trim(allcookies[i]).substr(10));
  return 'none';
}


function sameOrigin(url) {
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
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
    $('#popup').find('span').each(function() {
        var element = $(this);
        if (element.id.indexOf('filter') == 0 && !element.hasClass('datetimeshortcuts'))
        {
          index = element.id.substring(6);
          tmp = element.find('[name="filterfield' + index + '"]')[0];
          field = tmp.options[tmp.selectedIndex].value;
          tmp = element.find('[name="filterval' + index + '"]')[0];
          if (tmp.type == 'select-one')
          {
            value = tmp.options[tmp.selectedIndex].value;
            data[field] = value;
          }
          else
          {
            tmp = element.find('[name="filteroper' + index + '"]')[0];
            oper = tmp.options[tmp.selectedIndex].value;
            value = element.find('[name="filterval' + index + '"]')[0].value;
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
    element = $('#filters');
    if (element != null)
      element.children().each(function() {
        
        // Find value
        var element = $(this);
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
        $('#fields').find('span').each(function() {          
          if ($(this).title == field) thefield = $(this);
        })
        data += '<span id="filter' + counter + '" class="' + thefield.className + '">';
        data += '<a href="javascript:filter.remove(' +  counter + ');"><img style="float:right;" src="/media/img/admin/icon_deletelink.gif"/></a>';
        data += '<select name="filterfield' + counter + '" onchange="filter.change_field(this)">';
        $('#fields').find('span').each(function() {  
          var element = $(this);        
          d = element.html().indexOf('<');
          if (d > 0)
            n = element.html().substring(0,d);
          else
            n = element.html();
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
    $('#fields').find('span').each(function() {
      var element = $(this);
      if (element.hasClass('FilterChoice') || element.hasClass('FilterText') || 
          element.hasClass('FilterNumber') || element.hasClass('FilterDate'))    
      {
        d = element.html().indexOf('<');
        if (d > 0)
          data += '<option value="' + element.title + '">' + element.html().substring(0,d) + '</option>';
        else
          data += '<option value="' + element.title + '">' + element.html() + '</option>';
      }
    })
    data += '</select><br/></span>';
    
    // Set form footer
    data += '<br/><input type="submit" value="' + gettext("Filter") + '"/>&nbsp;&nbsp;';
    data += '<input type="button" value="' + gettext("Cancel");
    data += '" onclick="$(\'#popup\').css(\'display\',\'none\');"/></form></div>';
  
    // Replace the popup content
    var element = $('#popup');
    element.html(data);
    
    // Add date picker
    element.find('input').each(function() {
      if ($(this).hasClass('vDateField'))
       DateTimeShortcuts.addCalendar($(this));
    })

    // Position the popup
    var position = $('#csvexport').offset();
    element.css({
      width: "350px",
      left: (position[0] - 352) + 'px',
      top: (position.top + 20) + 'px',
      position: "absolute"
      });
    var x = $('#timebuckets');
    if (x) x.css('display', 'none');
    element.css('display', "block");
  },
  
  // Function called when changing the field of a filter
  change_field : function(me)
  {
    var span = $(me).up('span');
    var tmp = span.find('select')[0];
      
    // Find the field
    field = tmp.options[tmp.selectedIndex].value;
    $('#fields').find('span').each(function() {          
      if ($(this).attr('title') == field) thefield = $(this);
    });
    if (span.id == "newfilter")
    {
      // Find a free index number
      counter = 0;
      do 
        y = $('#popup').find('#filter' + (++counter));
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
      if (thefield.className == span.className && !thefield.hasClass('FilterChoice')) 
        return;        
      index = span.id.substring(6);
      // Delete fields of previous type
      span.removeChild(span.find('[name="filteroper' + index + '"]')[0]);
      span.removeChild(span.find('[name="filterval' + index + '"]')[0]);
      // Inser fields of the new type
      tmp.insert({after: filter._build_row(thefield, '', '', index)});
    }
        
    // Add date picker
    span.find('input').each(function() {
      if ($(this).hasClass('vDateField'))
       DateTimeShortcuts.addCalendar($(this));
    });
  },
  
  // Function called when deleting a filter
  remove : function(row)
  {
    // Remove a filter from the popup window
    var x = $('#popup').find('#filter' + row)[0];
    x.parentNode.removeChild(x);  
  },
  
  // Function called when adding a filter
  add : function ()
  {
    var x = document.getElementById('popup').find('#newfiltericon')[0];
    tmp = x.up('span').find('select')[0];
  
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
    $('#fields').find('span').each(function() {
      d = $(this).html().indexOf('<');
      if (d>0)
        data += '<option value="' + $(this).title + '">' + $(this).html().substring(0,d) + '</option>';
      else
        data += '<option value="' + $(this).title + '">' + $(this).html() + '</option>';
    });
    data += '</select><br/></span>';
    x.up('span').insert({after: data});
  },
  
  // Internal function returning the HTML code for a filter operator and filter value
  _build_row : function(thefield, oper, value, index)
  {
    var result = '';
    if (thefield.hasClass('FilterNumber'))
    {
      // Filter for number fields
      result += '</select>\n<select name="filteroper' + index + '">';
      filter.numberoperators.each(function() {
        if (oper == $(this))
           result += '<option value="' + $(this) + '" selected="yes">' + filter.description[curoper] + '</option>';
        else
           result += '<option value="' + $(this) + '">' + filter.description[curoper] + '</option>';
      })
      result += '</select>';
      result += '<input type="text" name="filterval' + index + '" value="' + value + '" size="10"/>\n';
    } 
    else if (thefield.hasClass('FilterDate'))
    {
      // Filter for date fields
      result += '<select name="filteroper' + index + '">';
      filter.numberoperators.each(function() {
        if (oper == $(this))
           result += '<option value="' + $(this) + '" selected="yes">' + filter.description[curoper] + '</option>';
        else
           result += '<option value="' + $(this) + '">' + filter.description[curoper] + '</option>';
      })
      result += '</select>';
      result += '<input type="text" class="vDateField" name="filterval' + index + '" value="' + value + '" size="10"/>\n';
    } 
    else if (thefield.hasClass('FilterBool'))
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
    else if (thefield.hasClass('FilterChoice'))
    {
      // Filter for choice fields
      result += '<span name="filteroper' + index + '">equals </span><select name="filterval' + index + '">';
      thefield.find('option').each(function() {
        if ($(this).value == value) 
          result += '<option value="' + $(this).value + '" selected="yes">' + $(this).text + '</option>';
        else
          result += '<option value="' + $(this).value + '">' + $(this).text + '</option>';
        });
      result += '</select>';    
    } 
    else 
    {
      // Filter for text fields, also used as default
      result += '<select name="filteroper' + index + '">';
      filter.textoperators.each(function() {
        if (oper == $(this))
           result += '<option value="' + $(this) + '" selected="yes">' + filter.description[$(this)] + '</option>';
        else
           result += '<option value="' + $(this) + '">' + filter.description[$(this)] + '</option>';
      })
      result += '</select>';
      result += '<input type="text" name="filterval' + index + '" value="' + value + '" size="10"/>\n';
    } 
    return result;
  }

}


function import_show(list_or_table)
{
  $('#popup').html(    
    '<form enctype="multipart/form-data" method="post" action=""><table><tr>'+
    '<input type="hidden" name="csrfmiddlewaretoken" value="' + getToken() + '"/>' +
    '<td colspan="2">' + gettext('Load data from a CSV-formatted text file in the database.') + '<br/>'+
    gettext('The first row should contain the field names.') + '</td></tr>'+
    '<tr><td>'+gettext('Data file') + ':</td><td><input type="file" id="csv_file" name="csv_file"/></td></tr>'+
    '<tr><td><input id="upload" type="submit" value="' + gettext('Upload') + '"/></td>'+
    '<td><input type="button" value="' + gettext('Cancel') + '" onclick="$(\'#popup\').dialog(\'close\');"/></td></tr>'+
    '</table></form>'
    ).dialog({
      title: gettext("Import data"), autoOpen: true, resizable: false, 
    });
  $('#timebuckets').dialog('close');;
}


function filter_show() 
{
  $('#timebuckets').dialog('close');
  $('#popup').dialog('close');
  jQuery("#jsonmap").jqGrid('searchGrid', {
    closeOnEscape: true, 
    multipleSearch:true,
    multipleGroup:true, 
    onSearch : function() {
      var postdata = $("#jsonmap").jqGrid('getGridParam', 'postData');
      $('#curfilter').html(postdata.filters);
      },
    onReset : function() {
      $('#curfilter').html('');
      },
    });
}

function export_show(list_or_table)
{
  // The argument is true when we show a "list" report.
  // It is false for "table" reports.  
  $('#popup').html(    
    '<form method="get" action="javascript:export_close()"><table>'+
    '<tr><th>' + gettext("CSV style") + ':</th><td><select name="csvformat" id="csvformat"' + (list_or_table ? ' disabled="true"' : '')+ '>'+
    '<option value="csv"' + (list_or_table ? '' : ' selected="selected"') + '>' + gettext("Table") +'</option>'+
    '<option value="csvlist"' + (list_or_table ?  ' selected="selected"' : '') + '>' + gettext("List") +'</option></select></td></tr>'+
    '<tr><td><input type="submit" value="' + gettext("Export") +'"/></td>'+
    '<td><input type="button" value="' + gettext("Cancel") +'" onclick="$(\'#popup\').dialog(\'close\');"/></td></tr>'+
    '</table></form>'
    ).dialog({ 
      title: gettext("Export data"), autoOpen: true, resizable: false  
      });
  $('#timebuckets').dialog('close');
}


function export_close()
{
  // Fetch the report data
  var url = location.href;
  if (location.search.length > 0)
    // URL already has arguments
    url += "&reporttype=" + $('#csvformat').val();
  else if (url.charAt(url.length - 1) == '?')
    // This is the first argument for the URL, but we already have a question mark at the end
    url += "reporttype=" + $('#csvformat').val();
  else
    // This is the first argument for the URL
    url += "?reporttype=" + $('#csvformat').val();
  window.open(url,'_blank');
  // Hide the popup window
  $('#popup').dialog('close');
}


function bucket_show()
{
  // Show popup
  $('#popup').dialog('close');
  $( "#reportstart" ).datepicker({
      showOtherMonths: true, selectOtherMonths: true,
      dateFormat: 'yy-mm-dd'
    });  
  $( "#reportend" ).datepicker({
      showOtherMonths: true, selectOtherMonths: true,
      dateFormat: 'yy-mm-dd'
    });
  $('#timebuckets').dialog({
     autoOpen: true, resizable: false
    });
}


function getURLparameters() 
{
  // This function returns all arguments in the current URL as an associated array.
  if (window.location.search.length == 0) return {};
  var params = {};
	jQuery.each(window.location.search.match(/^\??(.*)$/)[1].split('&'), function(i,p){
		p = p.split('=');
		p[1] = unescape(p[1]).replace(/\+/g,' ');
		params[p[0]] = params[p[0]]?((params[p[0]] instanceof Array)?(params[p[0]].push(p[1]),params[p[0]]):[params[p[0]],p[1]]):p[1];
	});
	return params;
}


function bucket_close(canceled, curBuckets, curStart, curEnd)
{
  // Determine the URL arguments
  var args = getURLparameters();
  var changed = false;
  if (!canceled) 
  {
	  if ($('#reportbucket').val() != curBuckets)
	  {
	    args['reportbucket'] = $('#reportbucket').val();
	    changed = true;
	  }
	  else
	    delete args['reportbucket'];
	  if ($('#reportstart').val() != curStart)
	  {
	    args['reportstart'] = $('#reportstart').val();
	    changed = true;
	  }
	  else
	    delete args['reportstart'];
	  if ($('#reportend').val() != curEnd)
	  {
	    args['reportend'] = $('#reportend').val();
	    changed = true;
	  }
	  else
	    delete args['reportend'];
  }
  if (!changed)
  {
    // No changes to the settings. Close the popup.
    $('#timebuckets').dialog('close');
    return true;
  }
  else
    // Fetch the new report. This also hides the popup again.
    location.href = location.pathname + "?" + $.param(args);    
}


var dr,dl,ur,ul,dlt,drt,ult,urt;
var scrollbarSize = $.browser.msie ? 16 : 11;


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
  $(window).load(syncInitialize);
}


function syncInitialize()
{
  // Variables for the data grid
  dr = $('#dr');
  dl = $('#dl');
  ur = $('#ur');
  ul = $('#ul');
  dlt = $('#dlt');
  drt = $('#drt');
  ult = $('#ult');
  urt = $('#urt');
  
  var hasFrozenColumns = dlt.length > 0 ? true : false;
  var hasData = drt.find('tr').length > 0 ? true : false;

  // Variables for the cell dimensions
  var CellFrozenWidth = new Array();
  var CellWidth = new Array();
  var CellHeight = new Array();
  var TotalFrozenWidth = 0;

  if (hasData)
  {
    // First step: Measure the dimensions of the rows and columns

    // Measure cell width
    var columnheaders = urt.find('th');
    var columndata = $(drt.find('tr')[0]).find('td');
    var left;
    var right;
    var TotalWidth = 0;
    columndata.each(function(index) {
      left = $(this).width();
      right = $(columnheaders[index]).width();
      CellWidth[index] = right > left ? right : left;
      TotalWidth += CellWidth[index];
      });

    if (hasFrozenColumns)
    {
      // Measure frozen cell width
      var columnheaders = ult.find('th');
      var columndata = $(dlt.find('tr')[0]).find('td');
      columndata.each(function(index) {
        left = $(this).width();
        right = $(columnheaders[index]).width();
        CellFrozenWidth[index] = right > left ? right : left;
        TotalFrozenWidth += CellFrozenWidth[index];
        });

      // Measure cell height
      var rowheaders = dlt.find('tr');
      var rowdata = drt.find('tr');
      rowheaders.each(function(index) {
        left = $(this).height();
        right = $(rowdata[index]).height();
        CellHeight[index] = right > left ? right : left;
        });
    }

    // Second step: Updates the dimensions of the rows and columns
    // We only start resizing after all cells are measured, because the
    // updating also influences the measuring...

    var cellPadding = 10; // Hardcoded... I know it is 10.

    // Resize the width of the scrollable columns, up and down.
    var columnheaders = urt.find('th');
    var columndata = $(drt.find('tr')[0]).find('td');
    columndata.each(function(index) {
      $(columnheaders[index]).width(CellWidth[index]-cellPadding);
      $(this).width(CellWidth[index]-cellPadding);
      });
    drt.width(TotalWidth);
    urt.width(TotalWidth);

    if (hasFrozenColumns)
    {
      // Resize the height of the header row, frozen and scrolling sides
      var left = ult.height();
      var right = urt.height();
      if (left < right) left = right;
      urt.height(left);
      ult.height(left);

      // Resize the width of the frozen columns, up and down.
      // The constant 10 is taking into account the padding... Ugly hardcode.
      var columnheaders = ult.find('th');
      var columndata = $(dlt.find('tr')[0]).find('td');
      columndata.each(function(index) {
        $(columnheaders[index]).width(CellFrozenWidth[index]-cellPadding);
        $(this).width(CellFrozenWidth[index]-cellPadding);
        });
      dlt.width(TotalFrozenWidth);
      ult.width(TotalFrozenWidth);

      // Resize the height of the data rows, frozen and scrolling sides
      var rowheaders = dlt.find('tr');
      var rowdata = drt.find('tr');
      rowheaders.each(function(index) {
        $(rowdata[index]).height(CellHeight[index]);
        $(this).height(CellHeight[index]);
        });
    }
  }

  // Resize the available size for the table.
  syncResize();

  // Watch all changes in window size (except in broken IE)
  if (!$.browser.msie)
    $(window).resize(syncResize);
}


function syncResize()
{
  // Resize the available size for the table. This needs to be done at the
  // end, when rows and columns have taken on their correct size.
  // Respect also a minimum size for the table. If the height decreases further
  // we use a scrollbar on the window rather than resizing the container.
  // Assumption: The table in the down right corner of the grid is the only
  // container that can be resized for this purpose.
  
  // Calculate width
  var width = $(window).width() - dr.offset().left - scrollbarSize;
  if (width < 150)
  {
    width = 150;
    $(document.documentElement).css('overflowX', 'scroll');
  }
  else
    $(document.documentElement).css('overflowX', 'auto');
  if (width > dr.scrollWidth + scrollbarSize)
    width = dr.scrollWidth + scrollbarSize;
  
  // Calculate height
  var height = dr.height() + $(window).height() - $(document).attr('scrollHeight') + scrollbarSize;
  if (height < 150)
  {
    height = 150;
    $(document.documentElement).css('overflowY', 'scroll');
  }
  else
    $(document.documentElement).css('overflowY', 'auto');
  if (height > dr.scrollHeight + scrollbarSize) 
    height = dr.scrollHeight + scrollbarSize;
  
  // Update the size of the grid
  ur.width(width);
  dr.width(width);
  if (dl) dl.height(height);
  dr.height(height);
}


function syncScroll(left_or_right)
{
  // Synchronize the scrolling in the header row and frozen column
  // with the scrolling in the data pane.
  if (left_or_right == 1)
  {
    // Scrolling the main data panel down right
    if (dlt) dlt.css('bottom', dr.scrollTop() + 'px');
    urt.css('right', dr.scrollLeft() + 'px');
  }
  else
  {
    // Scrolling the panel with the pinned data column.
    // How does one scroll it when there is no scrollbar? Well, you can scroll
    // down using the search function of your browser
    dr.css('bottom', dl.scrollTop() + 'px');
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
  // Find new database and current database
  var el = $('#database');
  var db = el.val();
  var cur = el.attr('name');
  // Change the location
  if (cur == db) 
    return;
  else if (cur == 'default')
    window.location.href = window.location.href.replace(window.location.pathname, "/"+db+window.location.pathname);
  else if (db == 'default')
    window.location.href = window.location.href.replace("/"+cur+"/", "/");
  else
    window.location.href = window.location.href.replace("/"+cur+"/", "/"+db+"/");
}