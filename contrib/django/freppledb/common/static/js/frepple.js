
// Django sets this variable in the admin/base.html template.
window.__admin_media_prefix__ = "/static/admin/";


//----------------------------------------------------------------------------
// A class to handle changes to a grid.
//----------------------------------------------------------------------------
var upload = {

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
    $('#filter').addClass("ui-state-disabled");
    $.jgrid.hideModal("#searchmodfbox_grid");
    $('#save').removeClass("ui-state-disabled").addClass("bold");
    $('#undo').removeClass("ui-state-disabled").addClass("bold");
  },

  save : function()
  {
    if ($('#save').hasClass("ui-state-disabled")) return;

    // Pick up all changed cells. If a function "getData" is defined on the
    // page we use that, otherwise we use the standard functionality of jqgrid.
    if (typeof getDirtyData == 'function')
      rows = getDirtyData();
    else
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
          error: function (result, stat, errorThrown) {
            $('#popup').html(result.responseText)
              .dialog({
                title: gettext("Error saving data"),
                autoOpen: true,
                resizable: false,
                width: 'auto',
                height: 'auto'
              });
            $('#timebuckets').dialog('close');
            $.jgrid.hideModal("#searchmodfbox_grid");
            }
        });
  },

  validateSort: function(event)
  {

    if ($('#save').hasClass("ui-state-disabled"))
      jQuery("#grid").jqGrid('resetSelection');
    else
    {
      $('#popup').html("")
        .dialog({
          title: gettext("Save or undo your changes first"),
          autoOpen: true,
          resizable: false,
          width: 'auto',
          height: 'auto',
          buttons: [
            {
              text: gettext("Save"),
              click: function() {
                upload.save();
                $('#popup').dialog('close');
                }
            },
            {
              text: gettext("Undo"),
              click: function() {
                upload.undo();
                $('#popup').dialog('close');
                }
            }
            ]
        });
      event.stopPropagation();
    }
  }
}


//----------------------------------------------------------------------------
// Popup row selection.
// The popup window present a list of objects. The user clicks on a row to
// select it and a "select" button appears. When this button is clicked the
// popup is closed and the selected id is passed to the calling page.
//----------------------------------------------------------------------------

var selected;

function setSelectedRow(id) {
  if (selected!=undefined)
    $(this).jqGrid('setCell', selected, 'select', null);
  selected = id;
  $(this).jqGrid('setCell', id, 'select', '<button onClick="opener.dismissRelatedLookupPopup(window, selected);" class="ui-button ui-button-text-only ui-widget ui-state-default ui-corner-all"><span class="ui-button-text" style="font-size:66%">'+gettext('Select')+'</span></button>');
}


//----------------------------------------------------------------------------
// Custom formatter functions for the grid cells. Most of the custom handlers
// just add an appropriate context menu.
//----------------------------------------------------------------------------

function linkunformat (cellvalue, options, cell) {
  return cellvalue;
}

jQuery.extend($.fn.fmatter, {
  percentage : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    return cellvalue + "%";
  },
  item : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='item'></span>";
  },
  customer : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='customer'></span>";
  },
  buffer : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='buffer'></span>";
  },
  resource : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='resource'></span>";
  },
  forecast : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='forecast'></span>";
  },
  demand : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='demand'></span>";
  },
  operation : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='operation'></span>";
  },
  calendar : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='calendar'></span>";
  },
  location : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='location'></span>";
  },
  setupmatrix : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='setupmatrix'></span>";
  },
  user : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='user'></span>";
  },
  group : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='group'></span>";
  },
  flow : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='flow'></span>";
  },
  load : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='load'></span>";
  },
  bucket : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='bucket'></span>";
  },
  parameter : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='parameter'></span>";
  },
  skill : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='skill'></span>";
  },
  resourceskill : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='resourceskill'></span>";
  },
  project : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='project'></span>";
  },
  projectdeel : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue ==='') return '';
    if (options['colModel']['popup']) return cellvalue;
    return cellvalue + "<span class='context ui-icon ui-icon-triangle-1-e' role='projectdeel'></span>";
  }
});
jQuery.extend($.fn.fmatter.percentage, {
    unformat : function(cellvalue, options, cell) {
      return cellvalue;
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
jQuery.extend($.fn.fmatter.flow, {
  unformat : linkunformat
});
jQuery.extend($.fn.fmatter.load, {
  unformat : linkunformat
});
jQuery.extend($.fn.fmatter.bucket, {
  unformat : linkunformat
});
jQuery.extend($.fn.fmatter.parameter, {
  unformat : linkunformat
});
jQuery.extend($.fn.fmatter.skill, {
  unformat : linkunformat
});
jQuery.extend($.fn.fmatter.resourceskill, {
  unformat : linkunformat
});


//----------------------------------------------------------------------------
// This function is called when a cell is just being selected in an editable
// grid. It is used to either a) select the content of the cell (to make
// editing it easier) or b) display a date picker it the field is of type
// date.
//----------------------------------------------------------------------------

function afterEditCell(rowid, cellname, value, iRow, iCol)
{
  var cell = document.getElementById(iRow+'_'+cellname);
  var colmodel = jQuery("#grid").jqGrid ('getGridParam', 'colModel')[iCol];
  if (colmodel.formatter == 'date')
  {
  if (colmodel.formatoptions['srcformat'] == "Y-m-d")
      $(cell).datepicker({
        showOtherMonths: true, selectOtherMonths: true,
        dateFormat: "yy-mm-dd", changeMonth:true,
        changeYear:true, yearRange: "c-1:c+5"
        });
    else
      $(cell).datepicker({
        showOtherMonths: true, selectOtherMonths: true,
        dateFormat: "yy-mm-dd 00:00:00", changeMonth:true,
        changeYear:true, yearRange: "c-1:c+5"
        });
  }
  else
    $(cell).select();
}


//----------------------------------------------------------------------------
// Code for customized autocomplete widget.
// The customization creates unselectable categories and selectable list
// items.
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

  // Never cache ajax results
  $.ajaxSetup({ cache: false });

  // Autocomplete search functionality
  var database = $('#database').val();
  database = (database===undefined || database==='default') ? '' : '/' + database;
  $("#search").catcomplete({
    source: database + "/search/",
    minLength: 2,
    select: function( event, ui ) {
      window.location.href = database + "/data/" + ui.item.app + '/' + ui.item.label + "/" + ui.item.value + "/";
    }
  });

});


// Capture mouse clicks on the page so any active menu can be deactivated.
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


//----------------------------------------------------------------------------
// Return the value of the csrf-token
//----------------------------------------------------------------------------

function getToken()
{
  var allcookies = document.cookie.split(';');
  for ( i = allcookies.length; i >= 0; i-- )
    if (jQuery.trim(allcookies[i]).indexOf("csrftoken=") == 0)
      return jQuery.trim(jQuery.trim(allcookies[i]).substr(10));
  return 'none';
}


//----------------------------------------------------------------------------
// Check whether a URL is on the same domain as the current location or not.
// We use it to avoid send the CSRF-token to ajax requests submitted to other
// sites - for security reasons.
//----------------------------------------------------------------------------

function sameOrigin(url) {
    // URL could be relative or scheme relative or absolute
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

//----------------------------------------------------------------------------
// Display dialog for copying or deleting records
//----------------------------------------------------------------------------

function delete_show()
{
  if ($('#delete_selected').hasClass("ui-state-disabled")) return;
  var sel = jQuery("#grid").jqGrid('getGridParam','selarrrow');
  if (sel.length == 1)
  {
    // Redirect to a page for deleting a single entity
    location.href = location.pathname + encodeURI(sel[0]) + '/delete/';
  }
  else if (sel.length > 0)
  {
    $('#popup').html(
      interpolate(gettext('You are about to delete %s objects AND ALL RELATED RECORDS!'), [sel.length], false)
      ).dialog({
        title: gettext("Delete data"),
        autoOpen: true,
        resizable: false,
        width: 'auto',
        height: 'auto',
        buttons: [
          {
            text: gettext("Confirm"),
            click: function() {
              $.ajax({
                url: location.pathname,
                data: JSON.stringify([{'delete': sel}]),
                type: "POST",
                contentType: "application/json",
                success: function () {
                  $("#delete_selected").addClass("ui-state-disabled").removeClass("bold");
                  $("#copy_selected").addClass("ui-state-disabled").removeClass("bold");
                  $('.cbox').prop("checked", false);
                  $('#cb_grid.cbox').prop("checked", false);
                  $("#grid").trigger("reloadGrid");
                  $('#popup').dialog('close');
                  },
                error: function (result, stat, errorThrown) {
                  $('#popup').html(result.responseText)
                    .dialog({
                      title: gettext("Error deleting data"),
                      autoOpen: true,
                      resizable: true,
                      width: 'auto',
                      height: 'auto'
                    });
                  $('#timebuckets').dialog('close');
                  $.jgrid.hideModal("#searchmodfbox_grid");
                  }
              });
            }
          },
          {
            text: gettext("Cancel"),
            click: function() { $(this).dialog("close"); }
          }
          ]
      });
    $('#timebuckets').dialog().dialog('close');
    $.jgrid.hideModal("#searchmodfbox_grid");
  }
}


function copy_show()
{
  if ($('#copy_selected').hasClass("ui-state-disabled")) return;
  var sel = jQuery("#grid").jqGrid('getGridParam','selarrrow');
  if (sel.length > 0)
  {
    $('#popup').html(
      interpolate(gettext('You are about to duplicate %s objects'), [sel.length], false)
      ).dialog({
        title: gettext("Copy data"),
        autoOpen: true,
        resizable: false,
        width: 'auto',
        height: 'auto',
        buttons: [
          {
            text: gettext("Confirm"),
            click: function() {
              $.ajax({
                url: location.pathname,
                data: JSON.stringify([{'copy': sel}]),
                type: "POST",
                contentType: "application/json",
                success: function () {
                  $("#delete_selected").addClass("ui-state-disabled").removeClass("bold");
                  $("#copy_selected").addClass("ui-state-disabled").removeClass("bold");
                  $('.cbox').prop("checked", false);
                  $('#cb_grid.cbox').prop("checked", false);
                  $("#grid").trigger("reloadGrid");
                  $('#popup').dialog().dialog('close');
                  },
                error: function (result, stat, errorThrown) {
                  $('#popup').html(result.responseText)
                    .dialog({
                      title: gettext("Error copying data"),
                      autoOpen: true,
                      resizable: true,
                      width: 'auto',
                      height: 'auto'
                    });
                  $('#timebuckets').dialog().dialog('close');
                  $.jgrid.hideModal("#searchmodfbox_grid");
                  }
              });
            }
          },
          {
            text: gettext("Cancel"),
            click: function() { $(this).dialog("close"); }
          }
          ]
      });
    $('#timebuckets').dialog().dialog('close');
    $.jgrid.hideModal("#searchmodfbox_grid");
  }
}

function markSelectedRow(id)
{
  var sel = jQuery("#grid").jqGrid('getGridParam','selarrrow').length;
  if (sel > 0)
  {
    $("#copy_selected").removeClass("ui-state-disabled").addClass("bold");
    $("#delete_selected").removeClass("ui-state-disabled").addClass("bold");
  }
  else
  {
  $("#copy_selected").addClass("ui-state-disabled").removeClass("bold");
  $("#delete_selected").addClass("ui-state-disabled").removeClass("bold");
  }
}

function markAllRows()
{
  if ($(this).is(':checked'))
  {
    $("#copy_selected").removeClass("ui-state-disabled").addClass("bold");
    $("#delete_selected").removeClass("ui-state-disabled").addClass("bold");
    $('.cbox').prop("checked", true);
  }
  else
  {
    $("#copy_selected").addClass("ui-state-disabled").removeClass("bold");
    $("#delete_selected").addClass("ui-state-disabled").removeClass("bold");
    $('.cbox').prop("checked", false);
  }
}


//----------------------------------------------------------------------------
// Display import dialog for CSV-files
//----------------------------------------------------------------------------

function import_show(url)
{
  $('#popup').html(
    '<form id="uploadform" enctype="multipart/form-data" method="post" action="'
    + (typeof(url) != 'undefined' ? url : '') + '">' +
    '<input type="hidden" name="csrfmiddlewaretoken" value="' + getToken() + '"/>' +
    gettext('Load a CSV-formatted text file.') + '<br/>' +
    gettext('The first row should contain the field names.') + '<br/><br/>' +
    '<input type="checkbox" name="erase" value="yes"/>&nbsp;&nbsp;' + gettext('First delete all existing records AND ALL RELATED TABLES') + '<br/><br/>' +
    gettext('Data file') + ':<input type="file" id="csv_file" name="csv_file"/></form>'
    ).dialog({
      title: gettext("Import data"),
      autoOpen: true, resizable: false, width: 390, height: 'auto',
      buttons: [
        {
          text: gettext("Import"),
          click: function() { if ($("#csv_file").val() != "") $("#uploadform").submit(); }
        },
        {
          text: gettext("Cancel"),
          click: function() { $(this).dialog("close"); }
        }
        ]
    });
  $('#timebuckets').dialog().dialog('close');
  $.jgrid.hideModal("#searchmodfbox_grid");
}


//----------------------------------------------------------------------------
// Display filter dialog
//----------------------------------------------------------------------------

function filter_show()
{
  if ($('#filter').hasClass("ui-state-disabled")) return;
  $('#timebuckets,#popup').dialog().dialog('close');
  jQuery("#grid").jqGrid('searchGrid', {
    closeOnEscape: true,
    multipleSearch:true,
    multipleGroup:true,
    overlay: 0,
    sopt: ['eq','ne','lt','le','gt','ge','bw','bn','in','ni','ew','en','cn','nc'],
    onSearch : function() {
      saveColumnConfiguration();
      var s = jQuery("#fbox_grid").jqFilter('toSQLString');
      if (s) $('#curfilter').html(gettext("Filtered where") + " " + s);
      else $('#curfilter').html("");
      },
    onReset : function() {
      if (initialfilter != '') $('#curfilter').html(gettext("Filtered where") + " " + jQuery("#fbox_grid").jqFilter('toSQLString'));
      else $('#curfilter').html("");
      }
    });
}


//----------------------------------------------------------------------------
// Display and close export dialog for CSV-files
//----------------------------------------------------------------------------

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
      autoOpen: true, resizable: false, width: 390, height: 'auto',
      buttons: [
        {
          text: gettext("Export"),
          click: function() { export_close(); }
        },
        {
          text: gettext("Cancel"),
          click: function() { $(this).dialog("close"); }
        }
        ]
      });
  $('#timebuckets').dialog().dialog('close');
  $.jgrid.hideModal("#searchmodfbox_grid");
}


function export_close()
{
  // Fetch the report data
  var url = (location.href.indexOf("#") != -1 ? location.href.substr(0,location.href.indexOf("#")) : location.href);
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
  $('#popup').dialog().dialog('close');
}


//----------------------------------------------------------------------------
// Display time bucket selection dialog
//----------------------------------------------------------------------------

function bucket_show()
{
  // Show popup
  $('#popup').dialog().dialog('close');
  $.jgrid.hideModal("#searchmodfbox_grid");
  $( "#horizonstart" ).datepicker({
      showOtherMonths: true, selectOtherMonths: true,
      changeMonth:true, changeYear:true, yearRange: "c-1:c+5", dateFormat: 'yy-mm-dd'
    });
  $( "#horizonend" ).datepicker({
      showOtherMonths: true, selectOtherMonths: true,
      changeMonth:true, changeYear:true, yearRange: "c-1:c+5", dateFormat: 'yy-mm-dd'
    });
  $('#timebuckets').dialog({
     autoOpen: true, resizable: false, width: 390,
     buttons: [
       {
         text: gettext("OK"),
         click: function() {
          // Compare old and new parameters
          var params = $('#horizonbuckets').val() + '|' +
            $('#horizonstart').val() + '|' +
            $('#horizonend').val() + '|' +
            ($('#horizontype').is(':checked') ? "True" : "False") + '|' +
            $('#horizonlength').val() + '|' +
            $('#horizonunit').val();
          if (params == $('#horizonoriginal').val())
            // No changes to the settings. Close the popup.
            $(this).dialog('close');
          else {
            // Ajax request to update the horizon preferences
            $.ajax({
                type: 'POST',
                url: '/horizon/',
                data: {
                  horizonbuckets: $('#horizonbuckets').val(),
                  horizonstart: $('#horizonstart').val(),
                  horizonend: $('#horizonend').val(),
                  horizontype: ($('#horizontype').is(':checked') ? '1' : '0'),
                  horizonlength: $('#horizonlength').val(),
                  horizonunit: $('#horizonunit').val()
                  },
                dataType: 'text/html',
                async: false  // Need to wait for the update to be processed!
              });
          // Reload the report
          window.location.href = window.location.href;
          }
         }
       },
       {
         text: gettext("Cancel"),
         click: function() { $(this).dialog("close"); }
       }
       ]
    });
}


//----------------------------------------------------------------------------
// Display report customization screen
//----------------------------------------------------------------------------

function customize_show()
{
  $.jgrid.hideModal("#searchmodfbox_grid");
  //val = "<select id='configure' multiple='multiple' class='multiselect' name='fields' style='width:360px; height:200px; margin:10px; padding:10px'>" +
  //"<optgroup label='Rows'>";
  val = "<select id='configure' multiple='multiple' class='multiselect' name='fields' style='width:360px; height:200px; margin:10px; padding:10px'>";
  var colModel = $("#grid")[0].p.colModel;
  for (var i = 0; i < colModel.length; i++)
  {
    if (colModel[i].name != "rn" && colModel[i].name != "cb" && colModel[i].counter != null && colModel[i].label != '')
    {
      val += "<option value='" + (i) + "'";
      if (!colModel[i].hidden) val += " selected='selected'";
      //if (colModel[i].key) val += " disabled='disabled'";
      val += ">" + colModel[i].label + "</option>";
    }
    else if (colModel[i].name == 'columns')
    {
        console.log('ok');
          val += "</optgroup><optgroup label='Crosses'>";
          for (var j = 0; j < colModel[i].crosses.length; j++)
          {
            val += "<option value='" + (100+j) + "'";
              if (!colModel[i].crosses[j].hidden) val += " selected='selected'";
              val += ">" + colModel[i].crosses[j].name + "</option>";
          }
          break;
    }
  }
  //val += "</optgroup></select>";
  val += "</select>";
  $('#popup').html(val);
  console.log(val);
  $("#configure").multiselect({
	  moveEffect: 'blind',
      moveEffectOptions: {direction:'vertical'},
      moveEffectSpeed: 'fast',
      collapsableGroups: false,
      sortable: true
      // searchField: false   // Doesn't display well
      });
  $('#popup').dialog({
     title: gettext("Customize"),
     width: 390,
     height: 'auto',
     autoOpen: true,
     resizable: false,
     buttons: [
               {
                 text: gettext("OK"),
                 click: function()
                 {
                   var colModel = $("#grid")[0].p.colModel;
                     $('#configure option').each(function() {
                         if (this.selected) {
                             $("#grid").jqGrid("showCol", colModel[parseInt(this.value,10)].name);
                         } else {
                             $("#grid").jqGrid("hideCol", colModel[parseInt(this.value,10)].name);
                         }
                     });

                     var perm = [0];
                     $('#configure option').each(function() { perm.push(parseInt(this.value,10)); });
                     /*$.each(perm, function() { delete colMap[colModel[parseInt(this,10)].name]; });
                     $.each(colMap, function() {
                         var ti = parseInt(this,10);
                         perm = insert(perm,ti,ti);
                     });*/

                   $("#grid").jqGrid("remapColumns", perm, true);
                   saveColumnConfiguration();
                   $(this).dialog("close");
                 }
               },
               {
                 text: gettext("Cancel"),
                 click: function() { $(this).dialog("close"); }
               }
               ]
     });

  /*$("#grid").jqGrid('columnChooser', {
    done: function(perm) {
       if (perm) {
           alert(perm);
         $("#grid").jqGrid("remapColumns", perm, true);
         saveColumnConfiguration();
         }
      }
    });*/

}


//----------------------------------------------------------------------------
// Save report settings as preferences
//----------------------------------------------------------------------------

function saveColumnConfiguration()
{
  var colArray = new Array();
  var colModel = $("#grid")[0].p.colModel;
  for (var i = 0; i < colModel.length; i++)
  {
    if (colModel[i].name != "rn" && colModel[i].name != "cb" && colModel[i].counter != null)
      colArray.push([colModel[i].counter, colModel[i].hidden, colModel[i].width]);
  }
  var result = {};
  result[reportkey] = {
     "rows": colArray,
     "page": $('#grid').getGridParam('page'),
     "sidx": $('#grid').getGridParam('sortname'),
     "sord": $('#grid').getGridParam('sortorder'),
     "filter": $('#grid').getGridParam("postData").filters
  }
  if(typeof extraPreference == 'function')
  {
    var extra = extraPreference();
    for (var idx in extra) {result[reportkey][idx] = extra[idx];}
  }
  $.ajax({
      url: '/settings/',
      type: 'POST',
      contentType: 'application/json; charset=utf-8',
      data: JSON.stringify(result),
      error: function (result, stat, errorThrown) {
        $('#popup').html(result.responseText)
          .dialog({
            title: gettext("Error saving report settings"),
            autoOpen: true,
            resizable: false,
            width: 'auto',
            height: 'auto'
          });
        }
  });
}


function savePagingConfiguration(pgButton)
{
  // JQgrid paging gives only the current page
  var newValue = 0;
  var currentValue = $("#grid").getGridParam('page');
  if (pgButton.indexOf("next") >= 0)
    newValue = ++currentValue;
  else if (pgButton.indexOf("prev") >= 0)
    newValue = --currentValue;
  else if (pgButton.indexOf("last") >= 0)
    newValue = $("#grid").getGridParam('lastpage');
  else if (pgButton.indexOf("first") >= 0)
    newValue = 1;
  else if (pgButton.indexOf("user") >= 0)
    newValue = $('input.ui-pg-input').val();
  // Save the settings
  var colArray = new Array();
  var colModel = $("#grid")[0].p.colModel;
  for (var i = 0; i < colModel.length; i++)
  {
    if (colModel[i].name != "rn" && colModel[i].name != "cb" && colModel[i].counter != null)
      colArray.push([colModel[i].counter, colModel[i].hidden, colModel[i].width]);
  }
  var result = {};
  result[reportkey] = {
     "rows": colArray,
     "page": newValue,
     "sidx": $('#grid').getGridParam('sortname'),
     "sord": $('#grid').getGridParam('sortorder'),
     "filter": $('#grid').getGridParam("postData").filters
  }
  $.ajax({
      url: '/settings/',
      type: 'POST',
      contentType: 'application/json; charset=utf-8',
      data: JSON.stringify(result),
      error: function (result, stat, errorThrown) {
        $('#popup').html(result.responseText)
          .dialog({
            title: gettext("Error saving report settings"),
            autoOpen: true,
            resizable: false,
            width: 'auto',
            height: 'auto'
          });
        }
  });
}


//----------------------------------------------------------------------------
// This function returns all arguments in the current URL as a dictionary.
//----------------------------------------------------------------------------

function getURLparameters()
{

  if (window.location.search.length == 0) return {};
  var params = {};
  jQuery.each(window.location.search.match(/^\??(.*)$/)[1].split('&'), function(i,p){
    p = p.split('=');
    p[1] = unescape(p[1]).replace(/\+/g,' ');
    params[p[0]] = params[p[0]]?((params[p[0]] instanceof Array)?(params[p[0]].push(p[1]),params[p[0]]):[params[p[0]],p[1]]):p[1];
  });
  return params;
}


//----------------------------------------------------------------------------
// Functions to convert units for the duration fields
//----------------------------------------------------------------------------

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


//----------------------------------------------------------------------------
// Dropdown list to select the model.
//----------------------------------------------------------------------------

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


//----------------------------------------------------------------------------
// Jquery utility function to bind an event such that it fires first.
//----------------------------------------------------------------------------

$.fn.bindFirst = function(name, fn) {
    // bind as you normally would
    // don't want to miss out on any jQuery magic
    this.on(name, fn);

    // Thanks to a comment by @Martin, adding support for
    // namespaced events too.
    this.each(function() {
        var handlers = $._data(this, 'events')[name.split('.')[0]];
        // take out the handler we just inserted from the end
        var handler = handlers.pop();
        // move it at the beginning
        handlers.splice(0, 0, handler);
    });
};
