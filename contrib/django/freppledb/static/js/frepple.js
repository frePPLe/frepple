
// Django sets this variable in the admin/base.html template.
window.__admin_media_prefix__ = "/media/";

// A class to store changes in memory till the save button is hit.
var upload = {
  _data : [],

  add : function (e)
  {
    upload._data.push(e);
    $('#filter').addClass("ui-state-disabled");
    $.jgrid.hideModal("#searchmodfbox_grid");
    $('#save').removeClass("ui-state-disabled").addClass("bold");
    $('#undo').removeClass("ui-state-disabled").addClass("bold");
  },

  undo : function ()
  {
    if ($('#undo').hasClass("ui-state-disabled")) return;
    $("#grid").trigger("reloadGrid"); 
    $('#save').addClass("ui-state-disabled").removeClass("bold");
    $('#undo').addClass("ui-state-disabled").removeClass("bold");
    $('#filter').removeClass("ui-state-disabled");
  },

  select : function ()
  {
    // Refresh the page
    $('#filter').addClass("ui-state-disabled");
    $.jgrid.hideModal("#searchmodfbox_grid");
    $('#save').removeClass("ui-state-disabled").addClass("bold");
    $('#undo').removeClass("ui-state-disabled").addClass("bold");
  },

  save : function (e)
  {
    if ($('#save').hasClass("ui-state-disabled")) return;
    rows = $("#grid").getChangedCells('dirty');
    if (rows != null && rows.length > 0) 
      // Send the update to the server    
      $.ajax({
          url: location.pathname,
          data: JSON.stringify(rows),
          type: "POST",
          contentType: "application/json",
          success: function () {
            upload.undo();
            },
          error: function (result, stat) {
            alert(result + " ERROR  " + stat);
            },
        });        
  }
}


//----------------------------------------------------------------------------
// Popup row selection
//----------------------------------------------------------------------------

var selected;

function setSelectedRow(id) {  
  if (selected!=undefined)
   	$(this).jqGrid('setCell', selected, 'select', null); 
  selected = id;
  $(this).jqGrid('setCell', id, 'select', '<button onClick="opener.dismissRelatedLookupPopup(window, selected);" class="ui-button ui-button-text-only ui-widget ui-state-default ui-corner-all"><span class="ui-button-text" style="font-size:66%">'+gettext('Select')+'</span></button>');
}


//----------------------------------------------------------------------------
// Custom formatter functions for the grid cells.
//----------------------------------------------------------------------------


function linkunformat (cellvalue, options, cell) {
	  return cellvalue;
	}

jQuery.extend($.fn.fmatter, {
  item : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='item'></span>";
  },
  customer : function(cellvalue, options, rowdata) {
  	if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
  	return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='customer'></span>";
  },
  buffer : function(cellvalue, options, rowdata) {
  	if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
  	return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='buffer'></span>";
  },
  resource : function(cellvalue, options, rowdata) {
  	if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
  	return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='resource'></span>";
  },
  forecast : function(cellvalue, options, rowdata) {
  	if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
  	return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='forecast'></span>";
  },
  demand : function(cellvalue, options, rowdata) {
  	if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
  	return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='demand'></span>";
  },
  operation : function(cellvalue, options, rowdata) {
  	if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
  	return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='operation'></span>";
  },
  calendar : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='calendar'></span>";
  },
  location : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='location'></span>";
  },
  setupmatrix : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='setupmatrix'></span>";
  },
  user : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='user'></span>";
  },
  group : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined) return ''; 
    if (options['colModel']['popup']) return cellvalue;     
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='group'></span>";
  },
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
jQuery.extend($.fn.fmatter.location, {
  unformat : linkunformat
});
jQuery.extend($.fn.fmatter.calendar, {
  unformat : linkunformat
});
jQuery.extend($.fn.fmatter.setupmatrix, {
  unformat : linkunformat
});
jQuery.extend($.fn.fmatter.user, {
  unformat : linkunformat
});
jQuery.extend($.fn.fmatter.group, {
  unformat : linkunformat
});


//----------------------------------------------------------------------------
// Code for customized autocomplete widget
//----------------------------------------------------------------------------

$.widget( "custom.catcomplete", $.ui.autocomplete, {
  _renderItem: function( ul, item) {
    if (item.value == undefined)
      return $( "<li class='ui-autocomplete-category'>" + item.label + "</li>" ).appendTo( ul );
    else
      return $( "<li></li>" )
      .data( "item.autocomplete", item )
      .append( $( "<a></a>" ).text( item.value ) )
      .appendTo( ul );
  }
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
    var menu = button.next("div");

    // Blur focus from the link to remove that annoying outline.
    button.blur();

    // Reset the currently active button, if any.
    if (activeButton) {
      activeButton.removeClass("menuButtonActive");
      activeButton.next("div").css('visibility', "hidden");
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

  // Autocomplete search functionality
  var database = $('#database').val();
  database = (database===undefined || database==='default') ? '' : '/' + database;
  $("#search").catcomplete({
    source: database + "/search/",
    minLength: 2,
    select: function( event, ui ) {
      window.location.href = database + "/admin/input/" + ui.item.label + "/" + ui.item.value + "/";
    }
  });

  $( "#tabs" ).tabs({
    selected: 1,
    select: function(event, ui) 
    {
      var url = $.data(ui.tab, 'load.tabs');
      if(url) 
      {
        location.href = url;
        return false;       
      }
      return true;
    }
  });
});


// Capture mouse clicks on the page so any active button can be deactivated.
$(document).mousedown(function (event) {

  if (contextMenu && $(event.target).parent('.ui-menu-item').length < 1)
  {
    // Hide any context menu
    contextMenu.css('display', 'none');
    contextMenu = null;
  }

  // We clicked on a context menu. Display that now.
  if ($(event.target).hasClass('context'))
  {        
    // Find the id of the menu to display   
    contextMenu = $('#' + $(event.target).attr('role') + "context");
	
    // Get the entity name. Unescape all escaped characters and urlencode the result.
	if ($(event.target).hasClass('cross'))
	{
      var item = $(event.target).closest("tr.jqgrow")[0].id;
 	  item = encodeURIComponent(item.replace(/&amp;/g,'&').replace(/&lt;/g,'<')
		.replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/\//g,"_2F"));    
      var params = jQuery("#grid").jqGrid ('getGridParam', 'colModel')[jQuery.jgrid.getCellIndex($(event.target).closest("td,th"))];
      params['value'] = item;
	}
    else
    {
      var item = $(event.target).parent().text();
 	  item = encodeURIComponent(item.replace(/&amp;/g,'&').replace(/&lt;/g,'<')
		.replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/\//g,"_2F"));    
      var params = {value: item};
    }

	// Build the URLs for the menu
	contextMenu.find('a').each( function() {
	  $(this).attr('href', $(this).attr('id').replace(/{\w+}/g, function(match, number) { 
		var key = match.substring(1,match.length-1);
		return key in params ? params[key] : match;
		}
	  ))
	});

    // Display the menu at the right location
	$(contextMenu).css({
	  left: event.pageX,
	  top: event.pageY,
	  display: 'block'
	  });
	event.preventDefault();
    event.stopImmediatePropagation();
	}

  // If there is no active button, exit.
  if (!activeButton || event.target == activeButton) return;

  // If the element is not part of a menu, hide the menu
  if ($(event.target).parent('.ui-menu-item').length < 1) {
    activeButton.removeClass("menuButtonActive");
    activeButton.next("div").css('visibility', "hidden");
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


function import_show(url)
{
  $('#popup').html(
    '<form id="uploadform" enctype="multipart/form-data" method="post" action="' 
	  + (typeof(url) != 'undefined' ? url : '') + '">' +
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
  $('#timebuckets').dialog('close');  
  $.jgrid.hideModal("#searchmodfbox_grid");
}


function filter_show()
{
  if ($('#filter').hasClass("ui-state-disabled")) return;
  $('#timebuckets,#popup').dialog('close');
  jQuery("#grid").jqGrid('searchGrid', {
    closeOnEscape: true,
    multipleSearch:true,
    multipleGroup:true,
    overlay: 0,
    sopt: ['eq','ne','lt','le','gt','ge','bw','bn','in','ni','ew','en','cn','nc'],
    onSearch : function() {
      var s = jQuery("#fbox_grid").jqFilter('toSQLString');
      if (s) $('#curfilter').html(gettext("Filtered where") + " " + s);
      else $('#curfilter').html("");
      },
    onReset : function() {
      if (initialfilter != '') $('#curfilter').html(gettext("Filtered where") + " " + jQuery("#fbox_grid").jqFilter('toSQLString'));
      else $('#curfilter').html("");
      },
    });
}

function edit_show()
{
  var selectedrow = $("#grid").jqGrid('getGridParam', 'selrow');
  if (selectedrow == null) return;
  $('#timebuckets,#popup').dialog('close');
  jQuery("#grid").jqGrid('editGridRow', selectedrow, {
    closeOnEscape: true,
    });
}


function export_show(only_list)
{
  // The argument is true when we show a "list" report.
  // It is false for "table" reports.
  $('#popup').html(
    gettext("CSV style") + '&nbsp;&nbsp;:&nbsp;&nbsp;<select name="csvformat" id="csvformat"' + (only_list ? ' disabled="true"' : '')+ '>'+
    '<option value="csvtable"' + (only_list ? '' : ' selected="selected"') + '>' + gettext("Table") +'</option>'+
    '<option value="csvlist"' + (only_list ?  ' selected="selected"' : '') + '>' + gettext("List") +'</option></select>'
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
  $.jgrid.hideModal("#searchmodfbox_grid");
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
  var postdata = $("#grid").jqGrid('getGridParam', 'postData');
  url +=  "&" + jQuery.param(postdata);
  // Open the window
  window.open(url,'_blank');
  $('#popup').dialog('close');
}


function bucket_show()
{
  // Show popup
  $('#popup').dialog('close');
  $.jgrid.hideModal("#searchmodfbox_grid");
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
         click: function() { 
        	// Determine the URL arguments
        	var args = getURLparameters();
        	var changed = false;
        	var original = $('#reportoriginal').val().split('|');
			if ($('#reportbucket').val() != original[0])
			{
			  args['reportbucket'] = $('#reportbucket').val();
			  changed = true;
			}
			else
			  delete args['reportbucket'];
			if ($('#reportstart').val() != original[1])
			{
			  args['reportstart'] = $('#reportstart').val();
			  changed = true;
			}
			else
			  delete args['reportstart'];
			if ($('#reportend').val() != original[2])
			{
			  args['reportend'] = $('#reportend').val();
			  changed = true;
			}
			else
			  delete args['reportend'];
        	if (!changed)
        	  // No changes to the settings. Close the popup.
        	  $(this).dialog('close');
        	else
        	  // Fetch the new report. This also hides the popup again.
        	  location.href = location.pathname + "?" + $.param(args);
         },
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