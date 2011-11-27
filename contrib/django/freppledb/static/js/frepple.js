
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


function import_show(list_or_table)
{
  $('#popup').html(
    '<form id="uploadform" enctype="multipart/form-data" method="post" action="">'+
    '<input type="hidden" name="csrfmiddlewaretoken" value="' + getToken() + '"/>' +
    gettext('Load a CSV-formatted text file.') + '<br/>' +
    gettext('The first row should contain the field names.') + '<br/>' +
    gettext('Data file') + ':<input type="file" id="csv_file" name="csv_file"/></form>'
    ).dialog({
      title: gettext("Import data"),
      autoOpen: true,
      resizable: false,
      buttons: [
        {
          text: gettext("Import"),
          click: function() { $("#uploadform").submit(); },
        },
        {
          text: gettext("Cancel"),
          click: function() { $(this).dialog("close"); }
        }
        ]
    });
  $('#timebuckets,#fbox_jsonmap').dialog('close');  
}


function filter_show()
{
  $('#timebuckets,#popup').dialog('close');
  jQuery("#jsonmap").jqGrid('searchGrid', {
    closeOnEscape: true,
    multipleSearch:true,
    multipleGroup:true,
    overlay: 0,
    sopt: ['eq','ne','lt','le','gt','ge','bw','bn','in','ni','ew','en','cn','nc'],
    onSearch : function() {
      $('#curfilter').html(gettext("Filtered where") + " " + jQuery("#fbox_jsonmap").jqFilter('toSQLString'));
      },
    onReset : function() {
      $('#curfilter').html('');
      },
    });
}

function edit_show()
{
  var selectedrow = $("#jsonmap").jqGrid('getGridParam', 'selrow');
  if (selectedrow == null) return;
  $('#timebuckets,#popup').dialog('close');
  jQuery("#jsonmap").jqGrid('editGridRow', selectedrow, {
    closeOnEscape: true,
    });
}


function export_show(list_or_table)
{
  // The argument is true when we show a "list" report.
  // It is false for "table" reports.
  $('#popup').html(
    gettext("CSV style") + '&nbsp;&nbsp;:&nbsp;&nbsp;<select name="csvformat" id="csvformat"' + (list_or_table ? ' disabled="true"' : '')+ '>'+
    '<option value="csvtable"' + (list_or_table ? '' : ' selected="selected"') + '>' + gettext("Table") +'</option>'+
    '<option value="csvlist"' + (list_or_table ?  ' selected="selected"' : '') + '>' + gettext("List") +'</option></select>'
    ).dialog({
      title: gettext("Export data"),
      autoOpen: true, resizable: false,
      buttons: [
        {
          text: gettext("Export"),
          click: function() { export_close(); },
        },
        {
          text: gettext("Cancel"),
          click: function() { $(this).dialog("close"); }
        }
        ]
      });
  $('#timebuckets').dialog('close');
}


function export_close()
{
  // Fetch the report data
  var url = location.href;
  if (location.search.length > 0)
    // URL already has arguments
    url += "&format=" + $('#csvformat').val();
  else if (url.charAt(url.length - 1) == '?')
    // This is the first argument for the URL, but we already have a question mark at the end
    url += "format=" + $('#csvformat').val();
  else
    // This is the first argument for the URL
    url += "?format=" + $('#csvformat').val();
  // Append current filter and sort settings to the URL
  var postdata = $("#jsonmap").jqGrid('getGridParam', 'postData');
  url +=  "&" + jQuery.param(postdata);
  // Open the window
  window.open(url,'_blank');
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
     autoOpen: true, resizable: false,	 
     buttons: [
       {
         text: gettext("OK"),
         click: function() { export_close(); },
       },
       {
         text: gettext("Cancel"),
         click: function() { $(this).dialog("close"); }
       }
       ]
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



function installLoadHandler()
{
  // Disable the django-supplied event handler to initialize calendar menus.
  try {removeEvent(window,'load',DateTimeShortcuts.init);} catch (error) {;};
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