// Django sets this variable in the admin/base.html template.
window.__admin_media_prefix__ = "/static/admin/";



// Adjust the breadcrumbs such that it fits on a single line.
// This function is called when the window is resized.
function breadcrumbs_reflow()
{
  var crumbs = $("#breadcrumbs");
  var height_one_line = Math.ceil($("#cockpitcrumb").height()) + 16;

  // Show all elements previously hidden
  crumbs.children("li:hidden").show();
  // Hide the first crumbs till it all fits on a single line.
  var first = true;
  crumbs.children("li").each(function() {
    if (crumbs.height() > height_one_line && !first) $(this).hide();
    first = false;
  });
}


// A function to escape all special characters in a name.
// We escape all special characters in the EXACT same way as the django admin does.
function admin_escape(n)
{
  return n.replace(/_/g,'_5F').replace(/&amp;/g,'_26').replace(/&lt;/g,'_3C')
  .replace(/&gt;/g,'_3E').replace(/&#39;/g,"'").replace(/&quot;/g,'_22')
  .replace(/:/g,'_3A').replace(/\//g,'_2F').replace(/#/g,'_23').replace(/\?/g,'_3F')
  .replace(/;/g,'_3B').replace(/@/g,'_40').replace(/&/g,'_26').replace(/=/g,'_3D')
  .replace(/\+/g,'_2B').replace(/\$/g,'_24').replace(/,/g,'_2C').replace(/"/g,'_22')
  .replace(/</g,'_3C').replace(/>/g,'_3E').replace(/%/g,'_25').replace(/\\/g,'_5C');
}


/// <reference path="jquery.js" />
/*
jquery-resizable
Version 0.14 - 1/4/2015
© 2015 Rick Strahl, West Wind Technologies
www.west-wind.com
Licensed under MIT License
*/

    $.fn.resizable = function fnResizable(options) {
        var opt = {
            // selector for handle that starts dragging
            handleSelector: null,
            // resize the width
            resizeWidth: true,
            // resize the height
            resizeHeight: true,
            // hook into start drag operation (event passed)
            onDragStart: null,
            // hook into stop drag operation (event passed)
            onDragEnd: null,
            // hook into each drag operation (event passed)
            onDrag: null,
            // disable touch-action on $handle
            // prevents browser level actions like forward back gestures
            touchActionNone: true
        };
        if (typeof options == "object") opt = $.extend(opt, options);

        return this.each(function () {
            var startPos, startTransition;

            var $el = $(this);
            if ($(this).hasClass("ui-jqgrid")) return; //fix for Firefox bug that adds resize to the grid, we want only to resize the grid parent div ex: "content-main"

            var $handle = opt.handleSelector ? $(opt.handleSelector) : $el;

            if (opt.touchActionNone)
                $handle.css("touch-action", "none");

            $el.addClass("resizable");
            $handle.bind('mousedown.rsz touchstart.rsz', startDragging);

            function noop(e) {
                e.stopPropagation();
                e.preventDefault();
            };

            function startDragging(e) {
                startPos = getMousePos(e);
                startPos.width = parseInt($el.width(), 10);
                startPos.height = parseInt($el.height(), 10);

                startTransition = $el.css("transition");
                $el.css("transition", "none");

                if (opt.onDragStart) {
                    if (opt.onDragStart(e, $el, opt) === false)
                        return;
                }
                opt.dragFunc = doDrag;

                $(document).bind('mousemove.rsz', opt.dragFunc);
                $(document).bind('mouseup.rsz', stopDragging);
                if (window.Touch || navigator.maxTouchPoints) {
                    $(document).bind('touchmove.rsz', opt.dragFunc);
                    $(document).bind('touchend.rsz', stopDragging);
                }
                $(document).bind('selectstart.rsz', noop); // disable selection
            }

            function doDrag(e) {
                var pos = getMousePos(e);

                if (opt.resizeWidth) {
                    var newWidth = startPos.width + pos.x - startPos.x;
                    $el.width(newWidth);
                }

                if (opt.resizeHeight) {
                    var newHeight = startPos.height + pos.y - startPos.y;
                    $el.height(newHeight);
                }

                if (opt.onDrag)
                    opt.onDrag(e, $el, opt);
            }

            function stopDragging(e) {
                e.stopPropagation();
                e.preventDefault();

                $(document).unbind('mousemove.rsz', opt.dragFunc);
                $(document).unbind('mouseup.rsz', stopDragging);

                if (window.Touch || navigator.maxTouchPoints) {
                    $(document).unbind('touchmove.rsz', opt.dragFunc);
                    $(document).unbind('touchend.rsz', stopDragging);
                }
                $(document).unbind('selectstart.rsz', noop);

                // reset changed values
                $el.css("transition", startTransition);

                if (opt.onDragEnd)
                    opt.onDragEnd(e, $el, opt);

                return false;
            }

            function getMousePos(e) {
                var pos = { x: 0, y: 0, width: 0, height: 0 };
                if (typeof e.clientX === "number") {
                    pos.x = e.clientX;
                    pos.y = e.clientY;
                } else if (e.originalEvent.touches) {
                    pos.x = e.originalEvent.touches[0].clientX;
                    pos.y = e.originalEvent.touches[0].clientY;
                } else
                    return null;

                return pos;
            }
        });
    }
// end of jquery-resizable copy

//----------------------------------------------------------------------------
// A class to handle changes to a grid.
//----------------------------------------------------------------------------
var upload = {
  warnUnsavedChanges: function()
  {
    $(window).off('beforeunload', upload.warnUnsavedChanges);
    return gettext("There are unsaved changes on this page.");
  },

  undo : function ()
  {
    if ($('#undo').hasClass("btn-primary")) return;
    $("#grid").trigger("reloadGrid");
    $("#grid").closest(".ui-jqgrid-bdiv").scrollTop(0);
    $('#save, #undo').addClass("btn-primary").removeClass("btn-danger").prop('disabled', true);
    $('#actions1').prop('disabled', true);

    $('#filter').prop('disabled', false);
    $(window).off('beforeunload', upload.warnUnsavedChanges);
  },

  select : function ()
  {
    $('#filter').prop('disabled', true);
    $.jgrid.hideModal("#searchmodfbox_grid");
    $('#save, #undo').removeClass("btn-primary").addClass("btn-danger").prop('disabled', false);
    $(window).off('beforeunload', upload.warnUnsavedChanges);
    $(window).on('beforeunload', upload.warnUnsavedChanges);
  },

  save : function()
  {
    if ($('#save').hasClass("btn-primary")) return;

    // Pick up all changed cells. If a function "getData" is defined on the
    // page we use that, otherwise we use the standard functionality of jqgrid.
    $("#grid").saveCell(editrow, editcol);
    if (typeof getDirtyData == 'function')
      var rows = getDirtyData();
    else
      var rows = $("#grid").getChangedCells('dirty');
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
              $('#timebuckets').modal('hide');
            $.jgrid.hideModal("#searchmodfbox_grid");
              $('#popup').html('<div class="modal-dialog">'+
                      '<div class="modal-content">'+
                        '<div class="modal-header">'+
                          '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true" class="fa fa-times"></span></button>'+
                          '<h4 class="modal-title alert alert-danger">'+ gettext("Error saving data")+'</h4>'+
                        '</div>'+
                        '<div class="modal-body">'+
                          '<p>'+result.responseText+'</p>'+
                        '</div>'+
                        '<div class="modal-footer">'+
                          '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="'+gettext('Close')+'">'+
                        '</div>'+
                      '</div>'+
                  '</div>' )
                  .modal('show');
            }
        });
  },

  validateSort: function(event)
  {
    if ($(this).attr('id') == 'grid_cb') return;
    if ($("body").hasClass("popup"))  return;
    if ($('#save').hasClass("btn-primary"))
      jQuery("#grid").jqGrid('resetSelection');
    else
    {
      $('#timebuckets').modal('hide');
      $.jgrid.hideModal("#searchmodfbox_grid");
      $('#popup').html('<div class="modal-dialog">'+
          '<div class="modal-content">'+
          '<div class="modal-header">'+
            '<h4 class="modal-title alert-warning">'+ gettext("Save or cancel your changes first") +'</h4>'+
          '</div>'+
          '<div class="modal-body">'+
            '<p>'+""+'</p>'+
          '</div>'+
          '<div class="modal-footer">'+
            '<input type="submit" id="savebutton" role="button" class="btn btn-primary pull-right" value="'+gettext('Save')+'">'+
            '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" value="'+gettext('Cancel')+'">'+
          '</div>'+
        '</div>'+
      '</div>' )
      .modal('show');
      $('#savebutton').on('click', function() {
                upload.save();
        $('#popup').modal('hide');
      });
      $('#cancelbutton').on('click', function() {
                upload.undo();
        $('#popup').modal('hide');
        });
      event.stopPropagation();
    }
  }
}

//----------------------------------------------------------------------------
// Custom formatter functions for the grid cells.
//----------------------------------------------------------------------------

function opendetail(event) {
  var curlink = $(event.target).parent().attr('href');
  var objectid = $(event.target).parent().parent().text();
  objectid = admin_escape(objectid);

  event.preventDefault();
  event.stopImmediatePropagation();
  window.location.href = url_prefix + curlink.replace('key', objectid);
}

jQuery.extend($.fn.fmatter, {
  percentage : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue === '' || cellvalue === null) return '';
    return cellvalue + "%";
  },
  duration : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue === '' || cellvalue === null) return '';
    if (typeof cellvalue === "number")
      var seconds = cellvalue;
    else {
      var d = cellvalue.split(" ");
      if (d.length == 1)
      {
        var t = cellvalue.split(":");
        var days = 0;
      }
      else
      {
        var t = d[1].split(":");
        var days = (d[0]!='' ? parseFloat(d[0]) : 0);
      }
      switch (t.length)
      {
        case 0: // Days only
          var seconds = days * 86400;
          break;
        case 1: // Days, seconds
          var seconds = days * 86400 + (t[0]!='' ? parseFloat(t[0]) : 0);
          break;
        case 2: // Days, hours and seconds
          var seconds = days * 86400 + (t[0]!='' ? parseFloat(t[0]) : 0) * 60 + (t[1]!='' ? parseFloat(t[1]) : 0);
          break;
        default:
          // Days, hours, minutes, seconds
          var seconds = days * 86400 + (t[0]!='' ? parseFloat(t[0]) : 0) * 3600 + (t[1]!='' ? parseFloat(t[1]) : 0) * 60 + (t[2]!='' ? parseFloat(t[2]) : 0);
      }
    }
    var days   = Math.floor(seconds / 86400);
    var hours   = Math.floor((seconds - (days * 86400)) / 3600);
    var minutes = Math.floor((seconds - (days * 86400) - (hours * 3600)) / 60);
    var seconds = seconds - (days * 86400) - (hours * 3600) - (minutes * 60);
    if (days > 0)
      return days + ((hours < 10) ? " 0" : " ") + hours + ((minutes < 10) ? ":0" : ":") + minutes + ((seconds < 10) ? ":0" : ":") + seconds;
    if (hours > 0)
      return hours + ((minutes < 10) ? ":0" : ":") + minutes + ((seconds < 10) ? ":0" : ":") + seconds;
    if (minutes > 0)
      return minutes + ((seconds < 10) ? ":0" : ":") + seconds;
    return seconds;
  },

  detail : function(cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue === '' || cellvalue === null) return '';
    if (options['colModel']['popup'] || rowdata.showdrilldown == '0') return cellvalue;
    return cellvalue + "<a href='/detail/" + options.colModel.role + "/key/' onclick='opendetail(event)'><span class='leftpadding fa fa-caret-right' role='" + options.colModel.role + "'></span></a>";
  },

  demanddetail : function(cellvalue, options, rowdata) {
    // TODO This function is not very generic.
    if (cellvalue === undefined || cellvalue === '') return '';
    if (options['colModel']['popup']) return cellvalue;
    var result = '';
    var dmds = cellvalue.split(", ");
    for (var i in dmds)
    {
      var detail = dmds[i].split(" : ");
      if (result != '') result += ', ';
      result += detail[0] + " : <span>" + detail[1] + "<a href='/detail/input/demand/key/' onclick='opendetail(event)'><span class='leftpadding fa fa-caret-right' role='" + options.colModel.role + "'></span></a></span>"
    }
    return result;
  },

  graph : function (cellvalue, options, rowdata) {
    return '<div class="graph" style="height:80px"></div>';
  }
});
jQuery.extend($.fn.fmatter.percentage, {
    unformat : function(cellvalue, options, cell) {
      return cellvalue;
      }
});


//
// Functions related to jqgrid
//

var grid = {

   // Popup row selection.
   // The popup window present a list of objects. The user clicks on a row to
   // select it and a "select" button appears. When this button is clicked the
   // popup is closed and the selected id is passed to the calling page.
   selected: undefined,

   setSelectedRow: function(id)
   {
     if (grid.selected != undefined)
       $(this).jqGrid('setCell', grid.selected, 'select', null);
     grid.selected = id;
     $(this).jqGrid('setCell', id, 'select', '<input type="checkbox" onClick="opener.dismissRelatedLookupPopup(window, grid.selected);" class="btn btn-primary" style="width: 18px; height: 18px;" data-toggle="tooltip" title="'+gettext('Click to select record')+'"></input>');
   },

   runAction: function(next_action) {
    if ($("#actions").val() != "no_action")
       actions[$("#actions").val()]();
   },

   setStatus : function(newstatus)
   {
    var sel = jQuery("#grid").jqGrid('getGridParam','selarrrow');
    for ( i in sel ) {
      jQuery("#grid").jqGrid("setCell", sel[i], "status", newstatus, "dirty-cell");
      jQuery("#grid").jqGrid("setRowData", sel[i], false, "edited");
    };
    $("#actions1").html($("#actionsul").children().first().text() + '  <span class="caret"></span>');
    $('#save').removeClass("btn-primary").addClass("btn-danger").prop("disabled",false);
    $('#undo').removeClass("btn-primary").addClass("btn-danger").prop("disabled",false);
   },

  // Renders the cross list in a pivot grid
  pivotcolumns : function  (cellvalue, options, rowdata)
  {
    var result = '';
    for (i in cross)
    {
      if (result != '') result += '<br/>';
      if (cross[i]['editable'])
        result += '<span class="editablepivotcol">' + cross[i]['name'] + '</span>';
      else
        result += cross[i]['name'];
    }
    return result;
  },

  //This function is called when a cell is just being selected in an editable
  //grid. It is used to either a) select the content of the cell (to make
  //editing it easier) or b) display a date picker it the field is of type
  //date.
  afterEditCell: function (rowid, cellname, value, iRow, iCol)
  {
  var colmodel = $(this).jqGrid('getGridParam', 'colModel')[iCol];
  iconslist = {
      time: 'fa fa-clock-o',
      date: 'fa fa-calendar',
      up: 'fa fa-chevron-up',
      down: 'fa fa-chevron-down',
      previous: 'fa fa-chevron-left',
      next: 'fa fa-chevron-right',
      today: 'fa fa-bullseye',
      clear: 'fa fa-trash',
      close: 'fa fa-remove'
    };

  if (colmodel.formatter == 'date')
  {
    if (colmodel.formatoptions['srcformat'] == "Y-m-d")
      $("#" + iRow + '_' + cellname).on('focusin', function() {
        $(this).parent().css({'position': 'relative', 'overflow': 'visible'});
        $(this).datetimepicker({format: 'YYYY-MM-DD', useCurrent: false, calendarWeeks: true, icons: iconslist, locale: document.documentElement.lang, widgetPositioning: {horizontal: 'auto', vertical: (iRow < 11 ?'bottom':'auto')}});
      });
    else
      $("#" + iRow + '_' + cellname).on('focusin', function() {
        $(this).parent().css({'position': 'relative', 'overflow': 'visible'});
        $(this).datetimepicker({format: 'YYYY-MM-DD HH:mm:ss', useCurrent: false, calendarWeeks: true, icons: iconslist, locale: document.documentElement.lang, widgetPositioning: {horizontal: 'auto', vertical: (iRow < 11 ?'bottom':'auto')}});
      });
  }
  else
	$("#" + iRow + '_' + cellname).select();
  },

  showExport: function(only_list)
  {
    $('#timebuckets').modal('hide');
    $.jgrid.hideModal("#searchmodfbox_grid");
    // The argument is true when we show a "list" report.
    // It is false for "table" reports.
    if (only_list)
      $('#popup').html('<div class="modal-dialog" style="width: 350px;">'+
          '<div class="modal-content">'+
            '<div class="modal-header">'+
              '<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>'+
              '<h4 class="modal-title">'+gettext("Export CSV or Excel file")+'</h4>'+
            '</div>'+
            '<div class="modal-body">'+
              '<label class="control-label">' + gettext("Export format") +
                '<div class="radio" name="csvformat" id="csvformat" value="spreadsheetlist">' +
                  '&nbsp;&nbsp;&nbsp;&nbsp;<label><input type="radio" name="csvformat" value="spreadsheetlist" checked="">' + gettext("Spreadsheet list") + '</label></br>' +
                  '&nbsp;&nbsp;&nbsp;&nbsp;<label><input type="radio" name="csvformat" value="csvlist">' + gettext("CSV list") + '</label></br>' +
                '</div>' +
              '</label>' +
            '</div>'+
            '<div class="modal-footer">'+
              '<input type="submit" id="exportbutton" role="button" class="btn btn-danger pull-left" value="'+gettext('Export')+'">'+
              '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="'+gettext('Cancel')+'">'+
            '</div>'+
          '</div>'+
      '</div>' )
      .modal('show');
    else
      $('#popup').html('<div class="modal-dialog" style="width: 350px;">'+
          '<div class="modal-content">'+
            '<div class="modal-header">'+
              '<h4 class="modal-title">'+gettext("Export CSV or Excel file")+'</h4>'+
            '</div>'+
            '<div class="modal-body">'+
              '<label class="control-label">' + gettext("Export format") +
                '<div class="radio" name="csvformat" id="csvformat" value="spreadsheettable">' +
                  '&nbsp;&nbsp;&nbsp;&nbsp;<label><input type="radio" name="csvformat" value="spreadsheettable" checked="">' + gettext("Spreadsheet table") + '</label></br>' +
                  '&nbsp;&nbsp;&nbsp;&nbsp;<label><input type="radio" name="csvformat" value="spreadsheetlist">' + gettext("Spreadsheet list") + '</label></br>' +
                  '&nbsp;&nbsp;&nbsp;&nbsp;<label><input type="radio" name="csvformat" value="csvtable">' + gettext("CSV table") + '</label></br>' +
                  '&nbsp;&nbsp;&nbsp;&nbsp;<label><input type="radio" name="csvformat" value="csvlist">' + gettext("CSV list") + '</label></br>' +
                '</div>' +
              '</label>' +
            '</div>'+
            '<div class="modal-footer">'+
              '<input type="submit" id="exportbutton" role="button" class="btn btn-danger pull-left" value="'+gettext('Export')+'">'+
              '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="'+gettext('Cancel')+'">'+
            '</div>'+
          '</div>'+
      '</div>' )
      .modal('show');
    $('#exportbutton').on('click', function() {
      // Fetch the report data
      var url = (location.href.indexOf("#") != -1 ? location.href.substr(0,location.href.indexOf("#")) : location.href);
      if (location.search.length > 0)
        // URL already has arguments
        url += "&format=" + $('#csvformat input:radio:checked').val();
      else if (url.charAt(url.length - 1) == '?')
        // This is the first argument for the URL, but we already have a question mark at the end
        url += "format=" + $('#csvformat input:radio:checked').val();
      else
        // This is the first argument for the URL
        url += "?format=" + $('#csvformat input:radio:checked').val();
      // Append current filter and sort settings to the URL
      var postdata = $("#grid").jqGrid('getGridParam', 'postData');
      url +=  "&" + jQuery.param(postdata);
      // Open the window
      window.open(url,'_blank');
      $('#popup').modal('hide');
    })
  },


  // Display time bucket selection dialog
  showBucket: function()
  {
    // Show popup
    $('#popup').modal('hide');
    $.jgrid.hideModal("#searchmodfbox_grid");
    iconslist = {
      time: 'fa fa-clock-o',
      date: 'fa fa-calendar',
      up: 'fa fa-clock-o',
      down: 'fa fa-chevron-down',
      previous: 'fa fa-chevron-left',
      next: 'fa fa-chevron-right',
      today: 'fa fa-bullseye',
      clear: 'fa fa-trash',
      close: 'fa fa-remove'
    };
    $( "#horizonstart" ).datetimepicker({format: 'YYYY-MM-DD', calendarWeeks: true, icons: iconslist, locale: document.documentElement.lang});
    $( "#horizonend" ).datetimepicker({format: 'YYYY-MM-DD', calendarWeeks: true, icons: iconslist, locale: document.documentElement.lang});
    $("#horizonstart").on("dp.change", function (selected) {
      $("#horizonend").data("DateTimePicker").minDate(selected.date);
      });
    $( "#okbutton" ).on('click', function() {
            // Compare old and new parameters
            var params = $('#horizonbuckets').val() + '|' +
              $('#horizonstart').val() + '|' +
              $('#horizonend').val() + '|' +
              ($('#horizontype').is(':checked') ? "True" : "False") + '|' +
              $('#horizonlength').val() + '|' +
              $('#horizonunit').val();

            if (params == $('#horizonoriginal').val())
              // No changes to the settings. Close the popup.
              $("#timebuckets").modal('hide');
            else {
              // Ajax request to update the horizon preferences
              $.ajax({
                  type: 'POST',
                  url: '/horizon/',
                  data: {
                    horizonbuckets: $('#horizonbuckets').val() ?
                      $('#horizonbuckets').val() :
                      $("#horizonbucketsul li a").first().text(),
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
            }});
    $('#timebuckets').modal('show');
         },

  //Display dialog for copying or deleting records
  showDelete : function()
  {
    if ($('#delete_selected').hasClass("disabled")) return;
    var sel = jQuery("#grid").jqGrid('getGridParam','selarrrow');
    if (sel.length == 1)
    {
      // Redirect to a page for deleting a single entity
      location.href = location.pathname + encodeURI(sel[0]) + '/delete/';
    }
    else if (sel.length > 0)
    {
     $('#timebuckets').modal('hide');
     $.jgrid.hideModal("#searchmodfbox_grid");
     $('#popup').html('<div class="modal-dialog">'+
             '<div class="modal-content">'+
               '<div class="modal-header">'+
                 '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true" class="fa fa-times"></span></button>'+
                 '<h4 class="modal-title">'+gettext('Delete data')+'</h4>'+
               '</div>'+
               '<div class="modal-body">'+
                 '<p>'+interpolate(gettext('You are about to delete %s objects AND ALL RELATED RECORDS!'), [sel.length], false)+'</p>'+
               '</div>'+
               '<div class="modal-footer">'+
                 '<input type="submit" id="delbutton" role="button" class="btn btn-danger pull-left" value="'+gettext('Confirm')+'">'+
                 '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="'+gettext('Cancel')+'">'+
               '</div>'+
             '</div>'+
         '</div>' )
         .modal('show');
     $('#delbutton').on('click', function() {
               $.ajax({
                 url: location.pathname,
                 data: JSON.stringify([{'delete': sel}]),
                 type: "POST",
                 contentType: "application/json",
                 success: function () {
               $("#delete_selected").prop("disabled", true).removeClass("bold");
               $("#copy_selected").prop("disabled", true).removeClass("bold");
                   $('.cbox').prop("checked", false);
                   $('#cb_grid.cbox').prop("checked", false);
                   $("#grid").trigger("reloadGrid");
               $('#popup').modal('hide');
                   },
                 error: function (result, stat, errorThrown) {
               $('#popup .modal-body p').html(result.responseText);
               $('#popup .modal-title').addClass("alert alert-danger").html(gettext("Error deleting data"));
               $('#delbutton').prop("disabled", true).hide();
                   }
           })
         })
             }
           },

  showCopy: function()
  {
   if ($('#copy_selected').hasClass("disabled")) return;
   var sel = jQuery("#grid").jqGrid('getGridParam','selarrrow');
   if (sel.length > 0)
   {
     $('#timebuckets').modal('hide');
     $.jgrid.hideModal("#searchmodfbox_grid");
     $('#popup').html('<div class="modal-dialog">'+
             '<div class="modal-content">'+
               '<div class="modal-header">'+
                 '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true" class="fa fa-times"></span></button>'+
                 '<h4 class="modal-title">'+gettext("Copy data")+'</h4>'+
                 '</div>'+
                 '<div class="modal-body">'+
                   '<p>'+interpolate(gettext('You are about to duplicate %s objects'), [sel.length], false)+'</p>'+
                   '</div>'+
                   '<div class="modal-footer">'+
                     '<input type="submit" id="copybutton" role="button" class="btn btn-danger pull-left" value="'+gettext('Confirm')+'">'+
                     '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="'+gettext('Cancel')+'">'+
                   '</div>'+
                 '</div>'+
             '</div>' )
     .modal('show');
     $('#copybutton').on('click', function() {
               $.ajax({
                 url: location.pathname,
                 data: JSON.stringify([{'copy': sel}]),
                 type: "POST",
                 contentType: "application/json",
                 success: function () {
           $("#delete_selected").prop("disabled", true).removeClass("bold");
           $("#copy_selected").prop("disabled", true).removeClass("bold");
                   $('.cbox').prop("checked", false);
                   $('#cb_grid.cbox').prop("checked", false);
                   $("#grid").trigger("reloadGrid");
           $('#popup').modal('hide');
                   },
                 error: function (result, stat, errorThrown) {
           $('#popup .modal-body p').html(result.responseText);
           $('#popup .modal-title').addClass("alert alert-danger").html(gettext("Error copying data"));
           $('#copybutton').prop("disabled", true).hide();
                   }
       })
     })
   }
  },

  showPlanExportModal: function ()
  {
      //test purposes
      var data = {
	  'labels': ['name', 'type', 'quantity', 'value', 'startdate', 'enddate', 'criticality'],
	  'values': [['somename0', 'atype', '1000', '1000000', '2015-02-31', '2016-04-31', '1'],['some very long name that almost has no end', 'atype', '1000', '1000000', '2015-02-31', '2016-04-31', '1']]
        };
      //end test

      $('#timebuckets').modal('hide');
      $.jgrid.hideModal("#searchmodfbox_grid");
      var tableheadercontent = '';
      var tablebodycontent = '';
      for (i = 0; i<data.labels.length; i++) {
	    tableheadercontent += '<th>'+gettext(data.labels[i])+'</th>';
          };
      for (i = 0; i<data.values.length; i++) {
	  tablebodycontent += '<tr><td><input id="cb_modaltable-'+i+'" class="cbox" type="checkbox" aria-checked="false"></td>';
	  for (j = 0; j<data.values[i].length; j++) {
	        tablebodycontent += '<td>'+gettext(data.values[i][j])+'</td>';
	      };
          tablebodycontent += '</tr>';
          };

      $('#popup').html('<div class="modal-dialog">'+
        '<div class="modal-content">'+
          '<div class="modal-header">'+
            '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true" class="fa fa-times"></span></button>'+
            '<h4 class="modal-title">'+gettext("Export Plan")+'</h4>'+
          '</div>'+
          '<div class="modal-body">'+
            '<div class="table-responsive">'+
              '<table class="table-condensed table-hover" id="forecastexporttable">'+
                '<thead class="thead-default">'+
                  '<tr>'+
                    '<th>'+
                      '<input id="cb_modaltableall" class="cbox" type="checkbox" aria-checked="false">'+
                    '</th>'+
                    tableheadercontent+
                  '</tr>'+
                '</thead>'+
                '<tbody>'+
                  '<tr>'+
                    tablebodycontent+
                  '</tr>'+
                '</tbody>'+
              '</table>'+
            '</div>'+
          '</div>'+
          '<div class="modal-footer">'+
            '<input type="submit" id="exportbutton" role="button" class="btn btn-danger pull-left" value="'+gettext('Export')+'">'+
            '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="'+gettext('Cancel')+'">'+
          '</div>'+
          '</div>'+
          '</div>' ).modal('show');
    $('#exportbutton').on('click', function() {
      $('#popup').modal('hide');
    });
    $('#cancelbutton').on('click', function() {
      $('#popup').modal('hide');
    });
    $('#cb_modaltableall').on('click', function() {
      if ($("#cb_modaltableall").is(':checked')) {
          $("#forecastexporttable input[type=checkbox]").each(function () {
              $(this).prop("checked", true);
          });
          $("#forecastexporttable tr").each(function () {
              $(this).addClass("selected");
          });
      } else {
	  $("#forecastexporttable input[type=checkbox]").each(function () {
              $(this).prop("checked", false);
          });
	  $("#forecastexporttable tr.selected").each(function () {
              $(this).removeClass("selected");
          });
      };

    });
  },

  // Display filter dialog
  showFilter: function()
  {
    if ($('#filter').hasClass("disabled")) return;
    $('.modal').modal('hide');
    jQuery("#grid").jqGrid('searchGrid', {
      closeOnEscape: true,
      multipleSearch:true,
      multipleGroup:true,
      overlay: 0,
      sopt: ['eq','ne','lt','le','gt','ge','bw','bn','in','ni','ew','en','cn','nc'],
      onSearch : function() {

        var s = grid.getFilterGroup(jQuery("#fbox_grid").jqFilter('filterData'), true);
        if (s)
        {
          $('#curfilter').html(gettext("Filtered where") + " " + s);
          $('#filter').addClass("btn-danger").removeClass("btn-primary");
        }
        else
        {
          $('#filter').removeClass("btn-danger").addClass("btn-primary");
          $('#curfilter').html("");
        }
        },
      onReset : function() {
        if (typeof initialfilter !== 'undefined' )
        {
          $("#grid").jqGrid('getGridParam','postData').filters = JSON.stringify(initialfilter);
          $('#curfilter').html(gettext("Filtered where") + " " + grid.getFilterGroup(initialfilter, true) );
          $('#filter').addClass("btn-danger").removeClass("btn-primary");
        }
        else
        {
          $('#curfilter').html("");
          $('#filter').removeClass("btn-danger").addClass("btn-primary");
        }

        return true;
        }
      });
  },

  getFilterRule: function (rule)
  {
    // Find the column
    var val, i, col, oper;
    var columns = jQuery("#grid").jqGrid ('getGridParam', 'colModel');
    for (i = 0; i < columns.length; i++)
    {
      if(columns[i].name === rule.field)
      {
        col = columns[i];
        break;
      }
    }
    if (col == undefined) return "";

    // Find operator
    for (var firstKey in $.jgrid.locales)
      var operands = $.jgrid.locales[firstKey].search.odata;
    for (i = 0; i < operands.length; i++)
      if (operands[i].oper == rule.op)
      {
        oper = operands[i].text;
        break;
      }
    if (oper == undefined) oper = rule.op;

    // Final result
    return col.label + ' ' + oper + ' "' + rule.data + '"';
  },

  getFilterGroup: function(group, first)
  {
    var s = "", index;

    if (!first) s = "(";

    if (group.groups !== undefined)
    {
      for (index = 0; index < group.groups.length; index++)
      {
        if (s.length > 1)
        {
          if (group.groupOp === "OR")
            s += " || ";
          else
            s += " && ";
        }
        s += grid.getFilterGroup(group.groups[index], false);
      }
    }

    if (group.rules !== undefined)
    {
      for (index = 0; index < group.rules.length; index++)
      {
        if (s.length > 1)
        {
          if (group.groupOp === "OR")
            s += " || ";
          else
            s += " && ";
        }
        s += grid.getFilterRule(group.rules[index]);
      }
    }

    if (!first) s += ")";

    if (s === "()")
      return ""; // ignore groups that don't have rules
    return s;
  },

  markSelectedRow: function(id)
  {
    var sel = jQuery("#grid").jqGrid('getGridParam','selarrrow').length;
    if (sel > 0)
    {
      $("#copy_selected").prop('disabled', false).addClass("bold");
      $("#delete_selected").prop('disabled', false).addClass("bold");
      $("#actions1").prop('disabled', false);
    }
    else
    {
      $("#copy_selected").prop('disabled', true).removeClass("bold");
      $("#delete_selected").prop('disabled', true).removeClass("bold");
      $("#actions1").prop('disabled', true);
    }
  },

  markAllRows: function()
  {
    if ($(this).is(':checked'))
    {
      $("#copy_selected").prop('disabled', false).addClass("bold");
      $("#delete_selected").prop('disabled', false).addClass("bold");
      $("#actions1").prop('disabled', false);
      $('.cbox').prop("checked", true);
    }
    else
    {
      $("#copy_selected").prop('disabled', true).removeClass("bold");
      $("#delete_selected").prop('disabled', true).removeClass("bold");
      $("#actions1").prop('disabled', true);
      $('.cbox').prop("checked", false);
    }
  },

  displayMode: function(m)
  {
    var url = (location.href.indexOf("#") != -1 ? location.href.substr(0,location.href.indexOf("#")) : location.href);
    if (location.search.length > 0)
      // URL already has arguments
      url = url.replace("&mode=table","").replace("&mode=graph","").replace("mode=table","").replace("mode=graph","") + "&mode=" + m;
    else if (url.charAt(url.length - 1) == '?')
      // This is the first argument for the URL, but we already have a question mark at the end
      url += "mode=" + m;
    else
      // This is the first argument for the URL
      url += "?mode=" + m;
    window.location.href = url;
  }
}

//----------------------------------------------------------------------------
// Code for ERP integration
//----------------------------------------------------------------------------

var ERPconnection = {
    IncrementalExport: function(grid, transactiontype, ERPsystem) {
      // Collect all selected rows in the status 'proposed'
      var sel = grid.jqGrid('getGridParam','selarrrow');
      if (sel === null || sel.length == 0)
        return;
      var data = [];

      for (var i in sel)
      {
        var r = grid.jqGrid('getRowData', sel[i]);
        if (r.type === undefined)
          r.type = transactiontype;
        if (r.status == 'proposed')
          data.push(r);
      }
      if (data == [])
        return;

      // Send to the server for upload into openbravo
      $('#timebuckets').modal('hide');
      $.jgrid.hideModal("#searchmodfbox_grid");
      $('#popup').html(''+
          '<div class="modal-dialog">'+
          '<div class="modal-content">'+
          '<div class="modal-header">'+
          '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true" class="fa fa-times"></span></button>'+
          '<h4 class="modal-title text-capitalize">'+gettext("export")+'</h4>'+
          '</div>'+
          '<div class="modal-body">'+
          '<p class="text-capitalize">'+gettext("export selected records to ")+ ERPsystem + '</p>'+
          '</div>'+
          '<div class="modal-footer">'+
          '<input type="submit" id="button_export" role="button" class="btn btn-danger pull-left" value="'+gettext('Confirm')+'">'+
          '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="'+gettext('Cancel')+'">'+
          '</div>'+
          '</div>'+
      '</div>' ).modal('show');

      $('#button_export').on('click', function() {
        $('#popup .modal-body p').html(gettext('connecting to ')+ERPsystem+'...');
        $.ajax({
          url: url_prefix + "/" + ERPsystem + "/upload/",
          data: JSON.stringify(data),
          type: "POST",
          contentType: "application/json",
          success: function () {
            $('#popup .modal-body p').html(gettext("Export successful"));
            $('#cancelbutton').val(gettext('Close'));
            $('#button_export').removeClass("btn-primary").prop('disabled', true);
            // Mark selected rows as "approved" if the original status was "proposed".
            for (var i in sel) {
              var cur = grid.jqGrid('getCell', sel[i], 'status');
              if (cur == 'proposed')
                grid.jqGrid('setCell', sel[i], 'status', 'approved');
            };
          },
          error: function (result, stat, errorThrown) {
            fmts = ngettext("Error during export");
            $('#popup .modal-title').addClass('alert alert-danger').html(gettext("Error during export"));
            $('#popup .modal-body p').html(gettext("Error during export") + ':' + result.responseText);
            $('#button_export').text(gettext('retry'));
          }
        });
      });
      $("#actions1").html($("#actionsul").children().first().text() + '  <span class="caret"></span>');
    },


//  ----------------------------------------------------------------------------
//  Sales Orders dependencies export
//  ----------------------------------------------------------------------------


    SODepExport: function(grid, transactiontype, ERPsystem) {
      // Collect all selected rows in the status 'proposed'
      var sel = grid.jqGrid('getGridParam','selarrrow');
      if (sel === null || sel.length == 0)
        return;
      var data = [];

      for (var i in sel)
      {
        var r = grid.jqGrid('getRowData', sel[i]);
        if (r.type === undefined)
          r.type = transactiontype;
          data.push(r);
      }
      if (data == [])
        return;

      $('#timebuckets').modal('hide');
      $.jgrid.hideModal("#searchmodfbox_grid");
      $('#popup').html(''+
          '<div class="modal-dialog" style="max-height: 80%; width: 90%; visibility: hidden">'+
          '<div class="modal-content">'+
          '<div class="modal-header">'+
          '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true" class="fa fa-times"></span></button>'+
          '<h4 class="modal-title text-capitalize">'+gettext("export")+'</h4>'+
          '</div>'+
          '<div class="modal-body">'+

          '</div>'+
          '<div class="modal-footer">'+
          '<input type="submit" id="button_export" role="button" class="btn btn-danger pull-left" disabled value="'+gettext('Confirm')+'">'+
          '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="'+gettext('Cancel')+'">'+
          '</div>'+
          '</div>'+
      '</div>' );

      // compose url
      var components='?demand=';
      for (i=0; i<sel.length; i++) {
        var r = grid.jqGrid('getRowData', sel[i]);
        if (r.type === undefined)
          r.type = transactiontype;
        if (r.status == 'open' || r.status == 'proposed') {
          if (i==0) components+=encodeURIComponent(sel[i]);
          else components+='&demand='+encodeURIComponent(sel[i]);
        };
      };

      //get demandplans
      $.ajax({
        url: url_prefix + "/demand/operationplans/" + components,
        type: "GET",
        contentType: "application/json",
        success: function (data) {
          $('#popup .modal-body').html('<div class="table-responsive">'+
              '<table class="table-condensed table-hover" id="forecastexporttable">'+
              '<thead class="thead-default">'+
              '</thead>'+
              '</table>'+
          '</div>');

          labels = ["id","type","item","value","quantity","location","origin","startdate","enddate","criticality"];

          var bodycontent='';
          if (transactiontype == 'SO') {
            var tableheadercontent = $('<tr/>');

            tableheadercontent.append($('<th/>').html('<input id="cb_modaltableall" class="cbox" type="checkbox" aria-checked="false">'));
            for (i = 0; i<labels.length; i++) {
              tableheadercontent.append( $('<th/>').addClass('text-capitalize').text(gettext(labels[i])) );
            };

            var tablebodycontent = $('<tbody/>');
            for (i = 0; i<data.length; i++) {
              var row = $('<tr/>');
              var td = $('<td/>');

              td.append( $('<input/>').attr({'id':"cb_modaltable-"+i, 'class':"cbox", 'type':"checkbox", 'aria-checked':"false"}));
              row.append(td);
              for (j = 0; j<labels.length; j++) {
                row.append( $('<td/>').text(data[i][labels[j]]) );
              };
              tablebodycontent.append( row );
            };

          };

          $('#popup table').append(tablebodycontent);
          $('#popup thead').append(tableheadercontent);

          $('#popup').modal({backdrop: 'static', keyboard: false}).on('shown.bs.modal', function () {
            $(this).find('.modal-dialog').css({
              'max-width': 50+$('#forecastexporttable').width()+'px',
              'visibility': 'visible'
            });
          }).modal('show');

          $('#button_export').on('click', function() {
            //get selected row data
            data=[];
            var row1 = [];
            var row1data = {};
            var rows=$('#forecastexporttable tr.selected');

            $.each(rows, function( key, value ) {
              row1=value.children;
              row1data['id'] = row1[1].textContent;
              row1data['type'] = row1[2].textContent;
              row1data['item'] = row1[3].textContent;
              row1data['value'] = row1[4].textContent;
              row1data['quantity'] = row1[5].textContent;
              row1data['location'] = row1[6].textContent;
              row1data['origin'] = row1[7].textContent;
              row1data['startdate'] = row1[8].textContent;
              row1data['enddate'] = row1[9].textContent;
              row1data['criticality'] = row1[10].textContent;
              data.push(row1data);
            });

            $('#popup .modal-body').html(gettext('connecting to ')+ERPsystem+'...');
            $.ajax({
              url: url_prefix + "/" + ERPsystem + "/upload/",
              data: JSON.stringify(data),
              type: "POST",
              contentType: "application/json",
              success: function () {
                $('#popup .modal-body').html(gettext("Export successful"));
                $('#cancelbutton').val(gettext('Close'));
                $('#button_export').toggleClass("btn-primary").prop('disabled', true );
                // Mark selected rows as "approved" if the original status was "proposed".
                for (var i in sel) {
                  var cur = grid.jqGrid('getCell', sel[i], 'status');
                  if (cur == 'proposed')
                    grid.jqGrid('setCell', sel[i], 'status', 'approved');
                };
              },
              error: function (result, stat, errorThrown) {
                fmts = ngettext("Error during export");
                $('#popup .modal-title').addClass('alert alert-danger').html(gettext("Error during export"));
                $('#popup .modal-body').css({'overflow-y':'auto'}).html('<div style="overflow-y:auto; height: 300px; resize: vertical">' + result.responseText + '</div>');
                $('#button_export').val(gettext('Retry'));
                $('#popup .modal-dialog').css({'visibility':'visible'})
                $('#popup').modal('show');
              }
            });
          });

          $("#cb_modaltableall").click( function() {
            $("#forecastexporttable input[type=checkbox]").prop("checked", $(this).prop("checked"));
            $("#forecastexporttable tbody tr").toggleClass('selected');
            if ( $("#forecastexporttable tbody input[type=checkbox]:checked").length > 0 ) {
              $('#button_export').removeClass("active").addClass("active").prop('disabled', false );;
            } else {
              $('#button_export').removeClass("active").prop('disabled', true );
            };
          });
          $("#forecastexporttable tbody input[type=checkbox]").click( function() {
            $(this).parent().parent().toggleClass('selected');
            $("#cb_modaltableall").prop("checked",$("#forecastexporttable tbody input[type=checkbox]:not(:checked)").length == 0);
            if ( $("#forecastexporttable tbody input[type=checkbox]:checked").length > 0 ) {
              $('#button_export').removeClass("active").addClass("active").prop('disabled', false );;
            } else {
              $('#button_export').removeClass("active").prop('disabled', true );
            };
          });
          $("#actions1").html($("#actionsul").children().first().text() + '  <span class="caret"></span>');
        },
        error: function (result, stat, errorThrown) {
          fmts = gettext("Error getting data");
          $('#popup .modal-title').addClass('alert alert-danger').html(fmts);
          $('#popup .modal-body').css({'overflow-y':'auto'}).html('<div style="overflow-y:auto; height: 300px; resize: vertical">' + result.responseText + '</div>');
          $('#button_export').val(gettext('Retry'));
          $('#popup .modal-dialog').css({'visibility':'visible'})
          $('#popup').modal('show');
        }
      });

    }
} //end Code for ERP integration

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
      var pos = button.position();
      menu.css({
        left: pos.left + "px",
        top: (pos.top + button.outerHeight() + 3) + "px",
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
  var searchsource = new Bloodhound({
    datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
    queryTokenizer: Bloodhound.tokenizers.whitespace,
    //prefetch: '/search/',
    remote: {
      url: url_prefix + '/search/?term=%QUERY',
      wildcard: '%QUERY'
    }
  });
  $('#search').typeahead({minLength: 2}, {
    limit:1000,
    highlight: true,
    name: 'search',
    display: 'value',
    source: searchsource,
    templates: {
      suggestion: function(data){
        if (data.value === null)
          return '<span><p style="margin-top: 5px; margin-bottom: 1px;">'+data.label+'</p><li  role="separator" class="divider"></li></span>';
        else
          return '<li><a href="'+ url_prefix + data.url + admin_escape(data.value) + '/" >' + data.value + '</a></li>';
      },
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

    // Get the entity name.
    if ($(event.target).hasClass('cross'))
    {
      var item = $(event.target).closest("tr.jqgrow")[0].id;
      item = admin_escape(item);
      var params = jQuery("#grid").jqGrid ('getGridParam', 'colModel')[jQuery.jgrid.getCellIndex($(event.target).closest("td,th"))];
      params['value'] = item;
    }
    else
    {
      var item = $(event.target).parent().text();
      item = admin_escape(item);
      var params = {value: item};
    }

    // Build the URLs for the menu
    contextMenu.find('a').each( function() {
      $(this).attr('href', $(this).attr('id').replace(/{\w+}/g, function(match, number) {
        var key = match.substring(1,match.length-1);
        return key in params ? params[key] : match;
        }))
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
  for (var i = allcookies.length; i >= 0; i-- )
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
//Display About dialog
//----------------------------------------------------------------------------

function about_show()
{

  $.ajax({
    url: "/about/",
    type: "GET",
    contentType: "application/json",
    success: function (data) {
      $('#timebuckets').modal('hide');
      $.jgrid.hideModal("#searchmodfbox_grid");
      $('#popup').modal({keyboard: false, backdrop:'static'});
      var content = '<div class="modal-dialog" style="width: 450px;">'+
         '<div class="modal-content">'+
           '<div class="modal-header">'+
             '<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true" class="fa fa-times"></span></button>'+
             '<h4 class="modal-title">About frePPLe ' + data.version + ' Community Edition</h4>'+
           '</div>'+
           '<div class="modal-body">'+
             '<div class="row">';
      content += '<div class="col-sm-5"><br/><br/>' +
         '<p><a target="_blank" href="https://frepple.com/"><strong>frePPLe website &nbsp;<span class="fa fa-caret-right"></span></strong></a></p><br/>' +
         '<p><a target="_blank" href="https://frepple.com/docs/' + data.version.replace(".beta","") + '/license.html"><strong>License information &nbsp;<span class="fa fa-caret-right"></span></strong></a></p><br/>' +
         '<p><a target="_blank" href="https://frepple.com/docs/' + data.version.replace(".beta","") + '/index.html"><strong>Documentation &nbsp;<span class="fa fa-caret-right"></span></strong></a></p>' +
         '</div>' +
         '<div class="col-sm-7"><strong>' + gettext("Installed apps") + ":</strong>";
      for (var i in data.apps)
          content += '<br>&nbsp;&nbsp;' + data.apps[i];
      content += '</div>' +
             '</div>'+
           '</div>'+
         '</div>'+
       '</div>';
       $('#popup').html(content).modal('show');
      },
    error: function (result, stat, errorThrown) {
        $('#timebuckets').modal('hide');
        $.jgrid.hideModal("#searchmodfbox_grid");
        $('#popup').html('<div class="modal-dialog style="width: 400px;">'+
                '<div class="modal-content">'+
                  '<div class="modal-header">'+
                    '<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true" class="fa fa-times"></span></button>'+
                    '<h4 class="modal-title">About frePPLe ' + data.version + '</h4>'+
                  '</div>'+
                  '<div class="modal-body">'+
                    '<p>'+'<h4 class="modal-title alert alert-danger">'+ gettext("Error reading version information")+'</h4>'+'</p>'+
                  '</div>'+
                '</div>'+
            '</div>' )
            .modal('show');
      }
  });
}
//----------------------------------------------------------------------------
// Display import dialog for CSV-files
//----------------------------------------------------------------------------

function import_show(url)
{
  $('#timebuckets').modal('hide');
  $.jgrid.hideModal("#searchmodfbox_grid");
  $('#popup').modal({keyboard: false, backdrop:'static'});
  $('#popup').html('<div class="modal-dialog">'+
      '<div class="modal-content">'+
        '<div class="modal-header">'+
          '<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>'+
          '<h4 class="modal-title">'+ gettext("Import CSV or Excel file") +'</h4>'+
        '</div>'+
        '<div class="modal-body">'+
    '<form id="uploadform">' +
            '<p>'+gettext('Load an Excel file or a CSV-formatted text file.') + '<br/>' +
    gettext('The first row should contain the field names.') + '<br/><br/>' +
            '</p>'+
            '<input type="checkbox"  autocomplete="off" name="erase" value="yes"/>&nbsp;&nbsp;' + gettext('First delete all existing records AND ALL RELATED TABLES') + '<br/><br/>' +
            gettext('Data file') + ':<input type="file" id="csv_file" name="csv_file"/>'+
          '</form>' +
          '<br/><div style="margin: 5px 0"><textarea id="uploadResponse" class="form-control" rows="10" style="resize: vertical; display: none; background-color: inherit; border: none;" readonly="readonly"></textarea></div>'  +
        '</div>'+
        '<div class="modal-footer">'+
            '<input type="submit" id="importbutton" role="button" class="btn btn-danger pull-left" value="'+gettext('Import')+'">'+
            '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="'+gettext('Close')+'">'+
        '</div>'+
      '</div>'+
    '</div>' )
  .modal('show');

  $('#importbutton').on('click', function() {
    if ($("#csv_file").val() == "") return;
    $('#uploadResponse').css('display','block');
    $('#uploadResponse').text(gettext('Importing... pressing Close button will not stop the process.'));
    $('#importbutton').css('display','none');
    $('#uploadform').css('display','none');
    $.ajax({
      type: 'post',
      url: typeof(url) != 'undefined' ? url : '',
      cache: false,
      data: new FormData($("#uploadform")[0]),
      success: function (data) {
        var el = $('#uploadResponse');
        el.val(data);
        el.scrollTop(el[0].scrollHeight - el.height());
        $('#cancelbutton').val(gettext('Close'));
        $('#importbutton').hide();
        $("#grid").trigger("reloadGrid");
      },
      xhrFields: {
        onprogress: function (e) {
          var el = $('#uploadResponse');
          el.val(e.currentTarget.response);
          el.scrollTop(el[0].scrollHeight - el.height());
        }
      },
      processData: false,
      contentType: false
    });
   }
  )
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
// Dropdown list to select the model.
//----------------------------------------------------------------------------

function selectDatabase()
{
  // Find new database and current database
  var db = $(this).attr("data-database");

  // Change the location
  if (database == db)
    return;
  else if (database == 'default')
  {
    if (window.location.pathname == '/')
      window.location.href = "/" + db + "/";
    else
      window.location.href = window.location.href.replace(window.location.pathname, "/" + db + window.location.pathname);
  }
  else if (db == 'default')
    window.location.href = window.location.href.replace("/"+database+"/", "/");
  else
    window.location.href = window.location.href.replace("/"+database+"/", "/" + db + "/");
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


//
// Graph functions
//

var graph = {

  header: function()
  {
    var el = $("#grid_graph");
    el.html("");
    var bucketwidth = (el.width() - 50) / numbuckets;
    var svg = d3.select(el.get(0)).append("svg");
    svg.attr('height','15px');
    svg.attr('width', el.width());
    var w = 50 + bucketwidth / 2;
    var wt = w;
    for (var i in timebuckets)
    {
      if (wt <= w)
      {
        var t = svg.append('text')
          .attr('class','svgheadertext')
          .attr('x', w)
          .attr('y', '12')
          .attr('class','graphheader')
          .text(timebuckets[i]['name']);
        wt = w + t.node().getComputedTextLength() + 12;
      }
      w += bucketwidth;
    }
  },

  showTooltip: function(txt)
  {
    // Find or create the tooltip div
    var tt = d3.select("#tooltip");
    if (tt.empty())
      tt = d3.select("body")
        .append("div")
        .attr("id", "tooltip")
        .attr("role", "tooltip")
        .attr("class", "popover fade right in")
        .style("position", "absolute");

    // Update content and display
    tt.html('' + txt)
      .style('display', 'block');
    graph.moveTooltip();
  },

  hideTooltip: function()
  {
    d3.select("#tooltip").style('display', 'none');
    d3.event.stopPropagation();
  },

  moveTooltip: function()
  {
    var xpos = d3.event.pageX + 5;
    var ypos = d3.event.pageY - 28;
    var xlimit = $(window).width() - $("#tooltip").width() - 20;
    var ylimit = $(window).height() - $("#tooltip").height() - 20;
    if (xpos > xlimit)
    {
      // Display tooltip under the mouse
      xpos = xlimit;
      ypos = d3.event.pageY + 5;
    }
    if (ypos > ylimit)
      // Display tooltip above the mouse
      ypos = d3.event.pageY - $("#tooltip").height() - 25;
    d3.select("#tooltip")
      .style({
        'left': xpos + "px",
        'top': ypos + "px"
        });
    d3.event.stopPropagation();
  },

  miniAxis: function(s)
  {
    var sc = this.scale().range();
    var dm = this.scale().domain();
    // Draw the scale line
    s.append("path")
     .attr("class", "domain")
     .attr("d", "M-10 0 H0 V" + (sc[0]-2) + " H-10");
    // Draw the maximum value
    s.append("text")
     .attr("x", -2)
     .attr("y", 13) // Depends on font size...
     .attr("text-anchor", "end")
     .text(Math.round(dm[1], 0));
    // Draw the minimum value
    s.append("text")
    .attr("x", -2)
    .attr("y", sc[0] - 5)
    .attr("text-anchor", "end")
    .text(Math.round(dm[0], 0));
  }
};

//
// Gantt chart functions
//

var gantt = {

  // Used to follow the mous when dragging the timeline
  startmousemove: null,
  resizing: null,

  // Height of the blocks
  rowsize: 25,

  header : function ()
  {
    // "scaling" stores the number of pixels available to show a day.
    var scaling = 86400000 / (viewend.getTime() - viewstart.getTime()) * $("#jqgh_grid_operationplans").width();
    var result = [
      '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="100%" height="34px">',
      '<line class="time" x1="0" y1="17" x2="' + $("#jqgh_grid_operationplans").width() + '" y2="17"/>'
      ];
    var x = 0;
    if (scaling < 5)
    {
      // Quarterly + monthly buckets
      var bucketstart = new Date(viewstart.getFullYear(), viewstart.getMonth(), 1);
      while (bucketstart < viewend)
      {
        var x1 = (bucketstart.getTime() - viewstart.getTime()) / 86400000 * scaling;
        var bucketend = new Date(bucketstart.getFullYear(), bucketstart.getMonth()+1, 1);
        var x2 = (bucketend.getTime() - viewstart.getTime()) / 86400000 * scaling;
        result.push('<text class="svgheadertext" x="' + Math.floor((x1+x2)/2) + '" y="31">' + moment(bucketstart).format("MMM") + '</text>');
        if (bucketstart.getMonth() % 3 == 0)
        {
          var quarterend = new Date(bucketstart.getFullYear(), bucketstart.getMonth()+3, 1);
          x2 = (quarterend.getTime() - viewstart.getTime()) / 86400000 * scaling;
          var quarter = Math.floor((bucketstart.getMonth()+3)/3);
          result.push('<line class="time" x1="' + Math.floor(x1) + '" y1="0" x2="' + Math.floor(x1) + '" y2="34"/>');
          result.push('<text class="svgheadertext" x="' + Math.floor((x1+x2)/2) + '" y="13">' + bucketstart.getFullYear() + " Q" + quarter + '</text>');
        }
        else
          result.push('<line class="time" x1="' + Math.floor(x1) + '" y1="17" x2="' + Math.floor(x1) + '" y2="34"/>');
        bucketstart = bucketend;
      }
    }
    else if (scaling < 10)
    {
      // Monthly + weekly buckets, short style
      x -= viewstart.getDay() * scaling;
      var bucketstart = new Date(viewstart.getTime() - 86400000 * viewstart.getDay());
      while (bucketstart < viewend)
      {
        result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling*3.5) + '" y="31">' + moment(bucketstart).format("MM-DD") + '</text>');
        x = x + scaling*7;
        bucketstart.setTime(bucketstart.getTime() + 86400000 * 7);
      }
      bucketstart = new Date(viewstart.getFullYear(), viewstart.getMonth(), 1);
      while (bucketstart < viewend)
      {
        x1 = (bucketstart.getTime() - viewstart.getTime()) / 86400000 * scaling;
        bucketend = new Date(bucketstart.getFullYear(), bucketstart.getMonth()+1, 1);
        x2 = (bucketend.getTime() - viewstart.getTime()) / 86400000 * scaling;
        result.push('<line class="time" x1="' + Math.floor(x1) + '" y1="0" x2="' + Math.floor(x1) + '" y2="17"/>');
        result.push('<text class="svgheadertext" x="' + Math.floor((x1+x2)/2) + '" y="13">' + moment(bucketstart).format("MMM YY") + '</text>');
        bucketstart = bucketend;
      }
    }
    else if (scaling < 20)
    {
      // Monthly + weekly buckets, long style
      x -= viewstart.getDay() * scaling;
      var bucketstart = new Date(viewstart.getTime() - 86400000 * viewstart.getDay());
      while (bucketstart < viewend)
      {
        result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        result.push('<text class="svgheadertext" x="' + (x + scaling*7.0/2.0) + '" y="31">' + moment(bucketstart).format("YY-MM-DD") + '</text>');
        x = x + scaling*7.0;
        bucketstart.setTime(bucketstart.getTime() + 86400000 * 7);
      }
      bucketstart = new Date(viewstart.getFullYear(), viewstart.getMonth(), 1);
      while (bucketstart < viewend)
      {
        x1 = (bucketstart.getTime() - viewstart.getTime()) / 86400000 * scaling;
        bucketend = new Date(bucketstart.getFullYear(), bucketstart.getMonth()+1, 1);
        x2 = (bucketend.getTime() - viewstart.getTime()) / 86400000 * scaling;
        result.push('<line class="time" x1="' + Math.floor(x1) + '" y1="0" x2="' + Math.floor(x1) + '" y2="17"/>');
        result.push('<text class="svgheadertext" x="' + Math.floor((x1+x2)/2) + '" y="13">' + moment(bucketstart).format("MMM YY") + '</text>');
        bucketstart = bucketend;
      }
    }
    else if (scaling <= 40)
    {
      // Weekly + daily buckets, short style
      var bucketstart = new Date(viewstart.getTime());
      while (bucketstart < viewend)
      {
        if (bucketstart.getDay() == 0)
        {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="0" x2="' + Math.floor(x) + '" y2="34"/>');
          result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling*7/2) + '" y="13">' + moment(bucketstart).format("YY-MM-DD") + '</text>');
        }
        else
        {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        }
        result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling/2) + '" y="31">' + moment(bucketstart).format("DD") + '</text>');
        x = x + scaling;
        bucketstart.setDate(bucketstart.getDate()+1);
      }
    }
    else if (scaling <= 75)
    {
      // Weekly + daily buckets, long style
      var bucketstart = new Date(viewstart.getTime());
      while (bucketstart < viewend)
      {
        if (bucketstart.getDay() == 0)
        {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="0" x2="' + Math.floor(x) + '" y2="34"/>');
          result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling*7/2) + '" y="13">' + moment(bucketstart).format("YY-MM-DD") + '</text>');
        }
        else
        {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        }
        result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling/2) + '" y="31">' + moment(bucketstart).format("DD MM") + '</text>');
        x = x + scaling;
        bucketstart.setDate(bucketstart.getDate()+1);
      }
    }
    else if (scaling < 350)
    {
      // Weekly + daily buckets, very long style
      var bucketstart = new Date(viewstart.getTime());
      while (bucketstart < viewend)
      {
        if (bucketstart.getDay() == 0)
        {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="0" x2="' + Math.floor(x) + '" y2="34"/>');
          result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling*3.5) + '" y="13">' + moment(bucketstart).format("YY-MM-DD") + '</text>');
        }
        else
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling/2) + '" y="31">' + moment(bucketstart).format("ddd DD MMM") + '</text>');
        x = x + scaling;
        bucketstart.setDate(bucketstart.getDate()+1);
      }
    }
    else
    {
      // Daily + hourly buckets
      var bucketstart = new Date(viewstart.getTime());
      while (bucketstart < viewend)
      {
        if (bucketstart.getHours() == 0)
        {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="0" x2="' + Math.floor(x) + '" y2="34"/>');
          result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling/2) + '" y="13">' + moment(bucketstart).format("ddd YY-MM-DD") + '</text>');
        }
        else
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling/48) + '" y="31">' + bucketstart.getHours() + '</text>');
        x = x + scaling/24;
        bucketstart.setTime(bucketstart.getTime() + 3600000);
      }
    }
    result.push( '</svg>' );
    $("#jqgh_grid_operationplans")
       .html(result.join(''))
       .unbind('mousedown')
       .bind('mousedown', function(event) {
          gantt.startmousemove = event.pageX;
          $(window).bind('mouseup', function(event) {
            $(window).unbind('mousemove');
            $(window).unbind('mouseup');
            event.stopPropagation();
            })
          $(window).bind('mousemove', function(event) {
            var delta = event.pageX - gantt.startmousemove;
            if (Math.abs(delta) > 3)
            {
              gantt.zoom(1, delta > 0 ? -86400000 : 86400000);
              gantt.startmousemove = event.pageX;
            }
            event.stopPropagation();
          });
          event.stopPropagation();
         });
  },

  reset: function()
  {
    var scale = $("#jqgh_grid_operationplans").width() / 10000;
    viewstart = new Date(horizonstart.getTime());
    viewend = new Date(horizonend.getTime());
    $('.transformer').each(function() {
      var layers = $(this).attr("title");
      $(this).attr("transform", "scale(" + scale + ",1) translate(0," + ((layers-1)*gantt.rowsize+3) + ")");
      });
    gantt.header();
  },

  redraw: function()
  {
    // Determine the conversion between svg units and the screen
    var scale = (horizonend.getTime() - horizonstart.getTime())
       / (viewend.getTime() - viewstart.getTime())
       * $("#jqgh_grid_operationplans").width() / 10000;
    $('.transformer').each(function() {
      var layers = $(this).attr("title");
      $(this).attr("transform", "scale(" + scale + ",1) translate(0," + ((layers-1)*gantt.rowsize+3) + ")");
      });
    gantt.header();
  },

  zoom: function(zoom_in_or_out, move_in_or_out)
  {
    // Determine the window to be shown. Min = 1 day. Max = 3 years.
    var delta = Math.min(1095,Math.max(1,Math.ceil((viewend.getTime() - viewstart.getTime()) / 86400000.0 * zoom_in_or_out)));
    // Determine the start and end date global variables.
    viewstart.setTime(viewstart.getTime() + move_in_or_out);
    viewend.setTime(viewstart.getTime() + delta * 86400000);
    // Determine the conversion between svg units and the screen
    var scale = (horizonend.getTime() - horizonstart.getTime()) / (delta * 864000000) * $("#jqgh_grid_operationplans").width() / 1000;
    var offset = (horizonstart.getTime() - viewstart.getTime()) / (horizonend.getTime() - horizonstart.getTime()) * 10000;
    // Transform all svg elements
    $('.transformer').each(function() {
      var layers = $(this).attr("title");
      $(this).attr("transform", "scale(" + scale + ",1) translate(" + offset + "," + ((layers-1)*gantt.rowsize+3) + ")");
      });
    // Redraw the header
    gantt.header();
  }
}


var tour = {

  autoplay: 0,
  tooltip: null,
  chapter: 0,
  step: 0,
  intro: null,
  timeout: null,

  tooltip: '<div class="popover tourpopover" role="tooltip">' +
    '<div class="arrow"></div>' +
    '<div class="popover-content"></div>' +
    '</div>',

  introtip: '<div class="popover tourpopover" role="tooltip">' +
    '<div class="arrow"></div>' +
    '<div class="popover-content" style="padding-bottom: 0"></div>' +
    '<div class="popover-footer small"><label>' +
    '<input style="vertical-align: bottom" type="checkbox" checked onclick="tour.displayHints(this.checked, true)">&nbsp;' +
    gettext('Show hints') +
    '</label></div></div>',

  displayHints: function(show, warn) {
    if (show) {
      // Reinitialize the intro hints
      localStorage.removeItem("intro");
      $("#showHints").addClass("toggle-on").removeClass("toggle-off");
      tour.showIntroPage(null);
    }
    else {
      // Marks the complete tour as seen
      localStorage.setItem("intro", "{}");
      $("#showHints").addClass("toggle-off").removeClass("toggle-on");
      //if (warn): TODO not working yet
      //  $('.tourpopover-content').html("You can activate the hints again from the Help menu");
      $('.tourpopover').popover('destroy');
    }
  },

  showIntroPage: function(pagestxt) {
    // Get the intro data
    if (pagestxt == null)
    {
      // First time visitor without intro list
      var pages = {};
      for (var key in introdata)
        pages[key] = 0;
      localStorage.setItem("intro", JSON.stringify(pages));
    }
    else
    {
      // Intro list already exists
      if (pagestxt == '')
        pagestxt = localStorage.getItem("intro");
      var pages = JSON.parse(pagestxt);
    }

    // Check if the page has an intro
    if (location.pathname in pages) {
      // Display the page
      tour.intro = introdata[location.pathname][pages[location.pathname]];
      tour.showStep();
      tour.intro = null;

      // Add an event handler to move to the next intro hint
      $('html').on('click', function (event) {
        if (!$(event.target).is("a"))
          tour.showIntroPage('');
        });

      // Remove the page from the to-see list
      pages[location.pathname] += 1;
      if (pages[location.pathname] >= introdata[location.pathname].length)
        delete pages[location.pathname];
      localStorage.setItem("intro", JSON.stringify(pages));
    }
    else
      // No hints for this page
      $('.tourpopover').popover('destroy');
  },

  start: function (args)
  {
    // Parse the arguments
    var splitargs = args.split(",");
    tour.chapter = parseInt(splitargs[0]);
    tour.step = parseInt(splitargs[1]);
    tour.autoplay = parseInt(splitargs[2]);
    // Load and execute the tutorial
    jQuery.ajax( {
        url: "/static/js/i18n/tour.en.js",
        dataType: "script",
        cache: true
      })
      .success( tour.init )
      .fail( function() {
        console.log('Error loading the tutorial: ' + arguments[2].toString());
      });
  },

  init: function()
  {
     // Display the main dialog of the tour
    $('#timebuckets').modal('hide');
    $.jgrid.hideModal("#searchmodfbox_grid");

    $('#popup').removeClass("in").addClass("tourguide").html('<div class="modal-dialog" id="tourModal" role="dialog" style="width: 390px; position: absolute; bottom: 10px; left: auto; right: 15px;">'+
        '<div class="modal-content">'+
        '<div class="modal-header">'+
          '<h4 id="modalTitle" class="modal-title"><strong>'+ gettext("Guided tour") +
          '</strong><button type="button" id="tourcancelbutton" class="close" data-dismiss="modal" aria-hidden="true"><span class="fa fa-times"</button>'+'</h4>'+
        '</div>'+
        '<div class="modal-body" id="tourmodalbody" style="padding-bottom:20px;">'+
            tourdata[tour.chapter]['description']+
        '</div>'+
        '<div class="modal-footer"><div class="btn-group control-form" role="group" aria-label="tour buttons">'+
          '<button type="submit" id="tourprevious" role="button" class="btn btn-primary">'+'<span class="fa fa-step-backward"></span>&nbsp;'+gettext('Previous')+'</button>'+
          '<button type="submit" id="playbutton" role="button" class="btn btn-primary">'+ gettext(tour.autoplay === 0 ? 'Play' : 'Pause')+ '&nbsp;<span class= ' + ((tour.autoplay === 0) ? '"fa fa-play"' : '"fa fa-pause"') + '></span></button>'+
          '<button type="submit" id="tournext" role="button" class="btn btn-primary">'+gettext('Next')+'&nbsp;<span class="fa fa-step-forward"></span></button>'+
        '</div></div>'+
      '</div>'+
    '</div>' )
    .modal({ //these 2 lines disable close when clicking outside the modal
      //backdrop: 'static',
      //keyboard: false
    }).on('hidden.bs.modal', function () {
      $('.tourpopover').popover('destroy');
    })
    .on('shown.bs.modal', function () {
      tour.showStep();
    })
    .modal('show');
    $('#tourmodalbody').append( '<div id="tour" style="padding-bottom:20px; display:none">' +
         tourdata[tour.chapter]['description']  + '<br/><br/><br/></div>');
    $('#tourprevious').on('click', function() {
      tour.prev();
    });
    $('#playbutton').on('click', function() {
      tour.toggleAutoplay();
    });
    $('#tournext').on('click', function() {
      tour.next();
    });
    $('#tourcancelbutton').on('click', function() {
      $('.tourpopover').popover('destroy');
      $('#tourModal').modal('hide');
    });
  },

  next: function()
  {
    $(tourdata[tour.chapter]['steps'][tour.step]['element']).popover('destroy');
    tour.step++;
    if (tour.step >= tourdata[tour.chapter]['steps'].length)
    {
      tour.chapter++;
      tour.step = 0;
      if (tour.chapter >= tourdata.length)
        // Restart from the beginning
        tour.chapter = 0;
    }
    tour.showStep();
  },

  prev: function()
  {
    $(tourdata[tour.chapter]['steps'][tour.step]['element']).popover('destroy');
    tour.step--;
    if (tour.step < 0)
    {
      tour.chapter--;
      if (tour.chapter < 0)
      {
        // Stay at the very first step
        tour.step = 0;
        tour.chapter = 0;
        return;
      }
      else
        tour.step = tourdata[tour.chapter]['steps'].length - 1;
    }
    tour.showStep();
  },

  showStep: function()
  {
    $('.tourpopover').popover('destroy');
    if (tour.intro)
      // Intro popup
      var stepData = tour.intro;
    else {
      // Guided tour
      var stepData = tourdata[tour.chapter]['steps'][tour.step];
      // Switch url if required
      var nexthref = '';
      var currsearch = '';
      if ( location.search.lastIndexOf('&')>-1 )
        currsearch = location.search.replace(location.search.slice(location.search.lastIndexOf('&')),''); //delete &tour=x,y,z
      else
        currsearch = ''; //delete ?tour=x,y,z
      if (location.pathname+currsearch != url_prefix+stepData['url']) {
        nexthref = url_prefix + stepData['url'] + "?tour=" + tour.chapter + "," + tour.step + "," + tour.autoplay;
        if (nexthref.match(/\?/g || []).length == 2)
          nexthref = url_prefix + stepData['url'] + "&tour=" + tour.chapter + "," + tour.step + "," + tour.autoplay;
        window.location.href = nexthref;
        return;
      };
    }

    // Callback
    if ('beforestep' in stepData)
      eval(stepData['beforestep']);
    // Display the tooltip
    var tooltipPos = (typeof stepData.position == 'undefined') ? 'BL' : stepData['position'];
    $(stepData['element']).attr('role', 'button').attr('tabindex', '0');
    $(stepData['element']).popover({
      'html': true,
      'container': 'body',
      'template': tour.intro ? tour.introtip : tour.tooltip,
      'title':'',
      'content': stepData['description'],
      'placement': stepData['position'],
      'trigger': 'manual'
      });
    $(stepData['element'])
    .popover('show')
    .on('shown.bs.popover', function () {
      var postop = $('.tourpopover').css('top').replace('px','');
      if (postop < window.pageYOffset || postop > window.pageYOffset+window.innerHeight/2) window.scrollTo(0,postop-window.innerHeight/2);
    })

    // Update tour dialog
    if (tour.intro == null) {
      $('#tourmodalbody').html(tourdata[tour.chapter]['description']);
      // Previous button
      if (tour.chapter == 0 && tour.step == 0)
        $("#tourprevious").prop('disabled', true);
      else
        $("#tourprevious").prop('disabled', false);
      // Next button
      if ((tour.chapter >= tourdata.length-1) && (tour.step >= tourdata[tour.chapter]['steps'].length-1))
        $("#tournext").prop('disabled', true);
      else
        $("#tournext").prop('disabled', false);
      // Autoplay
      if (tour.autoplay)
        tour.timeout = setTimeout(tour.next, tourdata[tour.chapter]['delay'] * 1000);
    }

    // Callback
    if ('afterstep' in stepData)
      eval(stepData['afterstep']);
  },

  toggleAutoplay: function()
  {
    if (tour.autoplay > 0)
    {
      $("#playbutton").html(gettext('Play')+'&nbsp;<span class="fa fa-play"></span>');
      tour.autoplay = 0;
      clearTimeout(tour.timeout);
      tour.timeout = null;
    }
    else
    {
      $("#playbutton").html(gettext('Pause')+'&nbsp;<span class="fa fa-pause"></span>');
      tour.autoplay = 1;
      tour.next();
    }
  }
}


// Gauge for widgets on dashboard
// Copied from https://gist.github.com/tomerd/1499279

function Gauge(placeholderName, configuration)
{
  this.placeholderName = placeholderName;

  var self = this; // for internal d3 functions

  this.configure = function(configuration)
  {
    this.config = configuration;

    this.config.size = this.config.size * 0.9;

    this.config.raduis = this.config.size * 0.97 / 2;
    this.config.cx = this.config.size / 2;
    this.config.cy = this.config.size / 2;

    this.config.min = undefined != configuration.min ? configuration.min : 0;
    this.config.max = undefined != configuration.max ? configuration.max : 100;
    this.config.range = this.config.max - this.config.min;

    this.config.majorTicks = configuration.majorTicks || 5;
    this.config.minorTicks = configuration.minorTicks || 2;

    this.config.greenColor  = configuration.greenColor || "#109618";
    this.config.yellowColor = configuration.yellowColor || "#FF9900";
    this.config.redColor  = configuration.redColor || "#DC3912";

    this.config.transitionDuration = configuration.transitionDuration || 500;
  }

  this.render = function()
  {
    this.body = d3.select("#" + this.placeholderName)
              .append("svg:svg")
              .attr("class", "gauge")
              .attr("width", this.config.size)
              .attr("height", this.config.size);

    this.body.append("svg:circle")
          .attr("cx", this.config.cx)
          .attr("cy", this.config.cy)
          .attr("r", this.config.raduis)
          .style("fill", "#ccc")
          .style("stroke", "#000")
          .style("stroke-width", "0.5px");

    this.body.append("svg:circle")
          .attr("cx", this.config.cx)
          .attr("cy", this.config.cy)
          .attr("r", 0.9 * this.config.raduis)
          .style("fill", "#fff")
          .style("stroke", "#e0e0e0")
          .style("stroke-width", "2px");

    for (var index in this.config.greenZones)
    {
      this.drawBand(this.config.greenZones[index].from, this.config.greenZones[index].to, self.config.greenColor);
    }

    for (var index in this.config.yellowZones)
    {
      this.drawBand(this.config.yellowZones[index].from, this.config.yellowZones[index].to, self.config.yellowColor);
    }

    for (var index in this.config.redZones)
    {
      this.drawBand(this.config.redZones[index].from, this.config.redZones[index].to, self.config.redColor);
    }

    if (undefined != this.config.label)
    {
      var fontSize = Math.round(this.config.size / 9);
      this.body.append("svg:text")
            .attr("x", this.config.cx)
            .attr("y", this.config.cy / 2 + fontSize / 2)
            .attr("dy", fontSize / 2)
            .attr("text-anchor", "middle")
            .text(this.config.label)
            .style("font-size", fontSize + "px")
            .style("fill", "#333")
            .style("stroke-width", "0px");
    }

    var fontSize = Math.round(this.config.size / 16);
    var majorDelta = this.config.range / (this.config.majorTicks - 1);
    for (var major = this.config.min; major <= this.config.max; major += majorDelta)
    {
      var minorDelta = majorDelta / this.config.minorTicks;
      for (var minor = major + minorDelta; minor < Math.min(major + majorDelta, this.config.max); minor += minorDelta)
      {
        var point1 = this.valueToPoint(minor, 0.75);
        var point2 = this.valueToPoint(minor, 0.85);

        this.body.append("svg:line")
              .attr("x1", point1.x)
              .attr("y1", point1.y)
              .attr("x2", point2.x)
              .attr("y2", point2.y)
              .style("stroke", "#666")
              .style("stroke-width", "1px");
      }

      var point1 = this.valueToPoint(major, 0.7);
      var point2 = this.valueToPoint(major, 0.85);

      this.body.append("svg:line")
            .attr("x1", point1.x)
            .attr("y1", point1.y)
            .attr("x2", point2.x)
            .attr("y2", point2.y)
            .style("stroke", "#333")
            .style("stroke-width", "2px");

      if (major == this.config.min || major == this.config.max)
      {
        var point = this.valueToPoint(major, 0.63);

        this.body.append("svg:text")
              .attr("x", point.x)
              .attr("y", point.y)
              .attr("dy", fontSize / 3)
              .attr("text-anchor", major == this.config.min ? "start" : "end")
              .text(major)
              .style("font-size", fontSize + "px")
              .style("fill", "#333")
              .style("stroke-width", "0px");
      }
    }

    var pointerContainer = this.body.append("svg:g").attr("class", "pointerContainer");

    var midValue = (this.config.min + this.config.max) / 2;

    var pointerPath = this.buildPointerPath(midValue);

    var pointerLine = d3.svg.line()
                  .x(function(d) { return d.x })
                  .y(function(d) { return d.y })
                  .interpolate("basis");

    pointerContainer.selectAll("path")
              .data([pointerPath])
              .enter()
                .append("svg:path")
                  .attr("d", pointerLine)
                  .style("fill", "#dc3912")
                  .style("stroke", "#c63310")
                  .style("fill-opacity", 0.7)

    pointerContainer.append("svg:circle")
              .attr("cx", this.config.cx)
              .attr("cy", this.config.cy)
              .attr("r", 0.12 * this.config.raduis)
              .style("fill", "#4684EE")
              .style("stroke", "#666")
              .style("opacity", 1);

    var fontSize = Math.round(this.config.size / 10);
    pointerContainer.selectAll("text")
              .data([midValue])
              .enter()
                .append("svg:text")
                  .attr("x", this.config.cx)
                  .attr("y", this.config.size - this.config.cy / 4 - fontSize)
                  .attr("dy", fontSize / 2)
                  .attr("text-anchor", "middle")
                  .style("font-size", fontSize + "px")
                  .style("fill", "#000")
                  .style("stroke-width", "0px");

    this.redraw(this.config.value, 0);
  }

  this.buildPointerPath = function(value)
  {
    var delta = this.config.range / 13;

    var head = valueToPoint(value, 0.85);
    var head1 = valueToPoint(value - delta, 0.12);
    var head2 = valueToPoint(value + delta, 0.12);

    var tailValue = value - (this.config.range * (1/(270/360)) / 2);
    var tail = valueToPoint(tailValue, 0.28);
    var tail1 = valueToPoint(tailValue - delta, 0.12);
    var tail2 = valueToPoint(tailValue + delta, 0.12);

    return [head, head1, tail2, tail, tail1, head2, head];

    function valueToPoint(value, factor)
    {
      var point = self.valueToPoint(value, factor);
      point.x -= self.config.cx;
      point.y -= self.config.cy;
      return point;
    }
  }

  this.drawBand = function(start, end, color)
  {
    if (0 >= end - start) return;

    this.body.append("svg:path")
          .style("fill", color)
          .attr("d", d3.svg.arc()
            .startAngle(this.valueToRadians(start))
            .endAngle(this.valueToRadians(end))
            .innerRadius(0.65 * this.config.raduis)
            .outerRadius(0.85 * this.config.raduis))
          .attr("transform", function() { return "translate(" + self.config.cx + ", " + self.config.cy + ") rotate(270)" });
  }

  this.redraw = function(value, transitionDuration)
  {
    var pointerContainer = this.body.select(".pointerContainer");

    pointerContainer.selectAll("text").text(Math.round(value));

    var pointer = pointerContainer.selectAll("path");
    pointer.transition()
          .duration(undefined != transitionDuration ? transitionDuration : this.config.transitionDuration)
          //.delay(0)
          //.ease("linear")
          //.attr("transform", function(d)
          .attrTween("transform", function()
          {
            var pointerValue = value;
            if (value > self.config.max) pointerValue = self.config.max + 0.02*self.config.range;
            else if (value < self.config.min) pointerValue = self.config.min - 0.02*self.config.range;
            var targetRotation = (self.valueToDegrees(pointerValue) - 90);
            var currentRotation = self._currentRotation || targetRotation;
            self._currentRotation = targetRotation;

            return function(step)
            {
              var rotation = currentRotation + (targetRotation-currentRotation)*step;
              return "translate(" + self.config.cx + ", " + self.config.cy + ") rotate(" + rotation + ")";
            }
          });
  }

  this.valueToDegrees = function(value)
  {
    // thanks @closealert
    //return value / this.config.range * 270 - 45;
    return value / this.config.range * 270 - (this.config.min / this.config.range * 270 + 45);
  }

  this.valueToRadians = function(value)
  {
    return this.valueToDegrees(value) * Math.PI / 180;
  }

  this.valueToPoint = function(value, factor)
  {
    return {  x: this.config.cx - this.config.raduis * factor * Math.cos(this.valueToRadians(value)),
          y: this.config.cy - this.config.raduis * factor * Math.sin(this.valueToRadians(value))    };
  }

  // initialization
  this.configure(configuration);
}
