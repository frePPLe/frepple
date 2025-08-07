//check for browser features
function isDragnDropUploadCapable() {
  var adiv = document.createElement('div');
  return (('draggable' in adiv) || ('ondragstart' in adiv && 'ondrop' in adiv)) && 'FormData' in window && 'FileReader' in window;
}

var _scrollBarWidth;
function getScrollBarWidth() {
  if (!_scrollBarWidth) {
    var div = $("<div style='overflow:scroll;position:absolute;top:-99999px'></div>").appendTo("body");
    _scrollBarWidth = div.prop("offsetWidth") - div.prop("clientWidth");
    div.remove();
  }
  return _scrollBarWidth;
}


// Adjust the breadcrumbs such that it fits on a single line.
// This function is called when the window is resized.
function breadcrumbs_reflow() {
  var crumbs = $("#breadcrumbs");
  var crumbrow = $(".breadcrumbrow");
  var maxwidth = crumbrow.parent().width();
  var scenariowidth = $("#database").closest(".navbar-nav").width();
  if (scenariowidth) maxwidth -= scenariowidth;

  // Show all elements previously hidden
  crumbs.children("li.d-none").removeClass("d-none");
  // Hide the first crumbs till it all fits on a single line.
  var first = true;
  crumbs.children("li").each(function () {
    if (crumbrow.width() > maxwidth && !first) $(this).addClass("d-none");
    first = false;
  });
}


// A function to escape all special characters in a name.
// We escape all special characters in the EXACT same way as the django admin does.
function admin_escape(n) {
  if (!n) return "";
  return n.replace(/_/g, '_5F')
    .replace(/:/g, '_3A').replace(/\//g, '_2F').replace(/#/g, '_23').replace(/\?/g, '_3F')
    .replace(/;/g, '_3B').replace(/@/g, '_40').replace(/&/g, '_26').replace(/=/g, '_3D')
    .replace(/\+/g, '_2B').replace(/\$/g, '_24').replace(/,/g, '_2C').replace(/"/g, '_22')
    .replace(/</g, '_3C').replace(/>/g, '_3E').replace(/%/g, '_25').replace(/\\/g, '_5C')
    .replace(/\t/g, '%09');
}


// A function to unescape all special characters in a name.
// We unescape all special characters in the EXACT same way as the django admin does.
function admin_unescape(n) {
  return n.replace(/%09/g, '\t').replace(/_5C/g, '\\')
    .replace(/_25/g, '%').replace(/_3E/g, '>').replace(/_3C/g, '<').replace(/_22/g, '"')
    .replace(/_2C/g, ',').replace(/_24/g, '$').replace(/_2B/g, '+').replace(/_3D/g, '=')
    .replace(/_26/g, '&').replace(/_40/g, '@').replace(/_3B/g, ';').replace(/_3F/g, '?')
    .replace(/_23/g, '#').replace(/_2F/g, '/').replace(/_3A/g, ':').replace(/_5F/g, '_');
}

function escapeAttribute(val) {
  if (typeof val === 'string' || val instanceof String)
    return val.replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  else
    return val;
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
    touchActionNone: true,
    reverse: false
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
        var newWidth = opt.reverse ?
          startPos.width - pos.x + startPos.x :
          startPos.width + pos.x - startPos.x;
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


function ajaxerror(result, stat, errorThrown) {
  if (result.status == 401) {
    location.reload();
    return;
  }
  var msg;
  if (result.readyState == 0)
    // Network errors: network down, server down, access denied...
    msg = gettext("Connection failed");
  else if (errorThrown)
    msg = "<strong>" + errorThrown + "</strong><br>" + result.responseText;
  else
    msg = result.responseText;
  hideModal('timebuckets');
  $("#save i").addClass('hidden');
  $.jgrid.hideModal("#searchmodfbox_grid");
  $('#popup').html(
    '<div class="modal-dialog">' +
    '<div class="modal-content">' +
    '<div class="modal-header bg-danger">' +
    '<h5 class="modal-title">' + gettext("Error") + '</h5>' +
    '<button type="button" class="btn-close" data-bs-dismiss="modal"></button>' +
    '</div>' +
    '<div class="modal-body">' +
    '<p>' + msg + '</p>' +
    '</div>' +
    '<div class="modal-footer">' +
    '<input type="submit" role="button" class="btn btn-primary" data-bs-dismiss="modal" value="' + gettext('Close') + '">' +
    '</div>' +
    '</div>' +
    '</div>'
  );
  showModal('popup');
}

//----------------------------------------------------------------------------
// A class to handle changes to a grid.
//----------------------------------------------------------------------------
var upload = {
  warnUnsavedChanges: function () {
    $(window).off('beforeunload', upload.warnUnsavedChanges);
    return gettext("There are unsaved changes on this page.");
  },

  undo: function () {
    if ($('#undo').hasClass("btn-primary")) return;
    if (typeof extraSearchUpdate == 'function') {
      var f = $('#grid').getGridParam("postData").filters;
      if (!extraSearchUpdate(f ? JSON.parse(f) : null))
        $("#grid").trigger("reloadGrid");
    }
    else
      $("#grid").trigger("reloadGrid");
    $("#grid").closest(".ui-jqgrid-bdiv").scrollTop(0);
    $('#save, #undo').addClass("btn-primary").removeClass("btn-danger").prop('disabled', true);
    $('#gridactions').prop('disabled', true);
    $(".ng-dirty").removeClass('ng-dirty');
    $(window).off('beforeunload', upload.warnUnsavedChanges);
  },

  select: function () {
    $.jgrid.hideModal("#searchmodfbox_grid");
    $('#save, #undo').removeClass("btn-primary").addClass("btn-danger").prop('disabled', false);
    $(window).off('beforeunload', upload.warnUnsavedChanges);
    $(window).on('beforeunload', upload.warnUnsavedChanges);
  },

  selectedRows: [],

  restoreSelection: function () {
    grid.markSelectedRow(upload.selectedRows.length);
    for (var r in upload.selectedRows)
      $("#grid").jqGrid('setSelection', upload.selectedRows[r], false);
    upload.selectedRows = [];
  },

  save: function (ok_callback) {
    if ($('#save').hasClass("btn-primary")) return;

    // Pick up all changed cells. If a function "getData" is defined on the
    // page we use that, otherwise we use the standard functionality of jqgrid.
    $("#grid").saveCell(editrow, editcol);
    if (typeof getDirtyData == 'function')
      var rows = getDirtyData();
    else
      var rows = $("#grid").getChangedCells('dirty');

    // Remember the selected rows, which will be restored in the loadcomplete event
    var tmp = $("#grid").jqGrid("getGridParam", "selarrrow");
    upload.selectedRows = tmp ? tmp.slice() : null;

    if (rows != null && rows.length > 0) {
      // Send the update to the server
      $("#save i").removeClass('hidden');
      if (typeof saveData !== 'undefined')
        saveData(rows, ok_callback);
      else
        $.ajax({
          url: location.pathname,
          data: JSON.stringify(rows),
          type: "POST",
          contentType: "application/json",
          success: function () {
            upload.undo();
            $("#save i").addClass('hidden');
            $(".ng-dirty").removeClass('ng-dirty');
            if (typeof ok_callback !== 'undefined') ok_callback();
          },
          error: ajaxerror
        });
    }
  },

  validateSort: function (event) {
    if ($(this).attr('id') == 'grid_cb') return;
    if ($("body").hasClass("popup")) return;
    if ($('#save').hasClass("btn-primary"))
      jQuery("#grid").jqGrid('resetSelection');
    else {
      hideModal('timebuckets');
      $.jgrid.hideModal("#searchmodfbox_grid");
      $('#popup').html('<div class="modal-dialog">' +
        '<div class="modal-content">' +
        '<div class="modal-header alert-warning" style="border-top-left-radius: inherit; border-top-right-radius: inherit">' +
        '<h5 class="modal-title">' + gettext("Save or cancel your changes first") + '</h5>' +
        '</div>' +
        '<div class="modal-body">' +
        gettext("There are unsaved changes on this page.") +
        '</div>' +
        '<div class="modal-footer justify-content-between">' +
        '<input type="submit" id="savebutton" role="button" class="btn btn-danger" value="' + gettext('Save') + '">' +
        '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary" value="' + gettext('Return to page') + '">' +
        '</div>' +
        '</div>' +
        '</div>');
      showModal('popup');
      $('#savebutton').on('click', function () {
        upload.save();
        hideModal('popup');
      });
      $('#cancelbutton').on('click', function () {
        upload.undo();
        hideModal('popup');
      });
      event.stopPropagation();
    }
  }
}

//----------------------------------------------------------------------------
// Custom formatter functions for the grid cells.
//----------------------------------------------------------------------------

function opendetail(event) {
  var el = $(event.target).parent();
  var curlink = el.attr('href');
  var objectid = el.attr('objectid');
  if (objectid === undefined || objectid == false)
    objectid = el.parent().text().trim();
  event.preventDefault();
  event.stopImmediatePropagation();
  window.location.href = url_prefix + curlink.replace('key', admin_escape(objectid));
}


function formatDuration(cellvalue, options, rowdata) {
  var days = 0;
  var hours = 0;
  var minutes = 0;
  var seconds = 0;
  var sign;
  var d = [];
  var t = [];

  if (cellvalue === undefined || cellvalue === '' || cellvalue === null) return '';
  if (typeof cellvalue === "number") {
    seconds = cellvalue;
    sign = Math.sign(seconds);
  } else {
    sign = ($.trim(cellvalue).charAt(0) == '-') ? -1 : 1;
    d = cellvalue.replace(/ +/g, " ").split(" ");
    if (d.length == 1) {
      t = cellvalue.split(":");
      days = 0;
    }
    else {
      t = d[1].split(":");
      days = (d[0] != '' ? parseFloat(d[0]) : 0);
    }
    switch (t.length) {
      case 0: // Days only
        seconds = Math.abs(days) * 86400;
        break;
      case 1: // Days, seconds
        seconds = Math.abs(days) * 86400 + (t[0] != '' ? Math.abs(parseFloat(t[0])) : 0);
        break;
      case 2: // Days, minutes and seconds
        seconds = Math.abs(days) * 86400 + (t[0] != '' ? Math.abs(parseFloat(t[0])) : 0) * 60 + (t[1] != '' ? parseFloat(t[1]) : 0);
        break;
      default:
        // Days, hours, minutes, seconds
        seconds = Math.abs(days) * 86400 + (t[0] != '' ? Math.abs(parseFloat(t[0])) : 0) * 3600 + (t[1] != '' ? parseFloat(t[1]) : 0) * 60 + (t[2] != '' ? parseFloat(t[2]) : 0);
    }
  }
  seconds = Math.abs(seconds); //remove the sign
  days = Math.floor(seconds / 86400);
  hours = Math.floor((seconds - (days * 86400)) / 3600);
  minutes = Math.floor((seconds - (days * 86400) - (hours * 3600)) / 60);
  seconds = seconds - (days * 86400) - (hours * 3600) - (minutes * 60);

  if (days > 365 * 5)
    // When it's more than 5 years, we assume you meant infinite
    return 'N/A';
  if (days > 0)
    return (sign * days).toString()
      + " " + ((hours < 10) ? "0" : "") + hours + ((minutes < 10) ? ":0" : ":")
      + minutes + ((seconds < 10) ? ":0" : ":")
      + Number((seconds).toFixed((seconds === Math.floor(seconds)) ? 0 : 6));
  else
    return ((sign < 0) ? "-" : "") + ((hours < 10) ? "0" : "") + hours
      + ((minutes < 10) ? ":0" : ":") + minutes
      + ((seconds < 10) ? ":0" : ":")
      + Number((seconds).toFixed((seconds === Math.floor(seconds)) ? 0 : 6));
}

jQuery.extend($.fn.fmatter, {
  percentage: function (cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue === '' || cellvalue === null) return '';
    return grid.formatNumber(cellvalue) + "%";
  },

  duration: formatDuration,

  currencyWithBlanks: function (cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue === null)
      return '';
    else
      return $.fn.fmatter.call(this, "currency", cellvalue, options);
  },

  image: function (cellvalue, options, rowdata) {
    return cellvalue ?
      '<img class="avatar-sm" src="/uploads/' + cellvalue + '">' :
      '';
  },

  admin: function (cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue === '' || cellvalue === null)
      return '';
    if (options['colModel']['popup'] || rowdata.showdrilldown === '0')
      return $.jgrid.htmlEncode(cellvalue);
    return $.jgrid.htmlEncode(cellvalue)
      + "<a href=\"" + url_prefix + "/data/" + options.colModel.role + "/" + admin_escape(cellvalue)
      + "/change/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a>";
  },

  detail: function (cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue === '' || cellvalue === null)
      return '';
    if (options['colModel']['popup'])
      return $.jgrid.htmlEncode(cellvalue);
    if (options.colModel.name == "operation") {
      if (rowdata.hasOwnProperty('type')
        && (rowdata.type === 'PO' || rowdata.type === 'DO' || rowdata.type === 'DLVR' || rowdata.type === 'STCK'))
        return $.jgrid.htmlEncode(cellvalue); //don't show links for non existing operations
      if (rowdata.hasOwnProperty('operationplan__type')
        && (rowdata.operationplan__type === 'PO' || rowdata.operationplan__type === 'DO'
          || rowdata.operationplan__type === 'DLVR' || rowdata.operationplan__type === 'STCK'))
        return $.jgrid.htmlEncode(cellvalue); //don't show links for non existing operations
    }
    return $.jgrid.htmlEncode(cellvalue)
      + "<a href=\"" + url_prefix + "/detail/" + options.colModel.role + "/" + admin_escape(cellvalue)
      + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a>";
  },

  demanddetail: function (cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue === '')
      return '';
    if (options['colModel']['popup'])
      return $.jgrid.htmlEncode(cellvalue);
    var result = '';
    var count = cellvalue.length;
    for (var i = 0; i < count; i++) {
      if (result != '')
        result += ', ';
      if (cellvalue[i][2] == 'F') {
        result += cellvalue[i][0] + " : " + $.jgrid.htmlEncode(cellvalue[i][1])
          + "<a href=\"" + url_prefix + "/detail/forecast/forecast/" + admin_escape(cellvalue[i][1]).substring(0, admin_escape(cellvalue[i][1]).length - 13) + "/"
          + "\" onclick='event.stopPropagation()' objectid='" + $.jgrid.htmlEncode(cellvalue[i][1]).substring(0, $.jgrid.htmlEncode(cellvalue[i][1]).length - 13) + "'>"
          + "<span class='ps-2 fa fa-caret-right' role='forecast/forecast'></span></a>";
      }
      else
        result += cellvalue[i][0] + " : " + $.jgrid.htmlEncode(cellvalue[i][1])
          + "<a href=\"" + url_prefix + "/detail/input/demand/" + admin_escape(cellvalue[i][1])
          + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right' role='input/demand'></span></a>";
    }
    return result;
  },

  forecastdetail: function (cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue === '' || cellvalue === null)
      return '';
    if (options['colModel']['popup'] || rowdata.showdrilldown === '0')
      return $.jgrid.htmlEncode(cellvalue);

    if (rowdata.hasOwnProperty('hasForecastRecord')
      && (rowdata.hasForecastRecord === 'True'))
      return $.jgrid.htmlEncode(cellvalue)
        + "<a href=\"" + url_prefix + "/detail/" + options.colModel.role + "/" + admin_escape(cellvalue)
        + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a>";
    else
      return $.jgrid.htmlEncode(cellvalue);
  },

  listdetail: function (cellvalue, options, rowdata) {
    if (cellvalue === undefined || cellvalue === '')
      return '';
    if (options['colModel']['popup'])
      return cellvalue;
    var result = '';
    var count = cellvalue.length;
    for (var i = 0; i < count; i++) {
      if (result != '')
        result += ', ';
      result += '<span><span class="listdetailkey"';
      if (cellvalue[i].length > 2)
        result += ' data-extra="' + $.jgrid.htmlEncode(cellvalue[i][2]) + '"';
      result += '>' + $.jgrid.htmlEncode(cellvalue[i][0])
        + "</span><a href=\"" + url_prefix + "/detail/" + options.colModel.role
        + "/" + admin_escape(cellvalue[i][0])
        + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right' role='"
        + options.colModel.role + "'></span></a></span>&nbsp;<span>" + cellvalue[i][1] + "</span>";
    }
    return result;
  },

  graph: function (cellvalue, options, rowdata) {
    return '<div class="graph" style="height:80px"></div>';
  },

  longstring: function (cellvalue, options, rowdata) {
    if (typeof cellvalue !== 'string') return "";
    var tipcontent = $.jgrid.htmlEncode(cellvalue);
    if (tipcontent)
      return '<span data-bs-toggle="tooltip" data-bs-placement="left" data-bs-title="' + tipcontent + '">' + tipcontent + '</span>';
    else
      return tipcontentreturn;
  },

  selectbutton: function (cellvalue, options, rowdata) {
    if (cellvalue)
      return '<button onClick="opener.dismissRelatedLookupPopup(window, grid.selected)" class="btn btn-primary btn-sm">'
        + gettext('select')
        + '</button>';
    else
      return "";
  },

  color: function (cellvalue, options, rowdata) {

    if (rowdata.color === undefined || rowdata.color === '' || cellvalue === null)
      return '';

    // Ignores color field and read the delay field
    var thedelay = Math.round(parseInt(rowdata.delay) / 86400);
    if (parseInt(rowdata.criticality) === 999 || parseInt(rowdata.operationplan__criticality) === 999) {
      return '';
    } else if (thedelay < 0) {
      return '<div class="invStatus" style="background-color: #008000; color: #151515;">' + (-thedelay) + ' ' + gettext("days early") + '</div>';
    } else if (thedelay === 0) {
      return '<div class="invStatus" style="background-color: #008000; color: #151515;">' + gettext("on time") + '</div>';
    } else if (thedelay > 0) {
      return '<div class="invStatus" style="background-color: #f00; color: #151515;">' + thedelay + ' ' + gettext("days late") + '</div>';
    }
    return '';
  },

  number: function (nData, opts) {
    if (window.SKIP_FORMATER) return nData;
    return grid.formatNumber(nData);
  }
});

jQuery.extend($.fn.fmatter.percentage, {
  unformat: function (cellvalue, options, cell) {
    return cellvalue.replace("%", "");
  }
});

jQuery.extend($.fn.fmatter.listdetail, {
  unformat: function (cellvalue, options, cell) {
    var o = [];
    $('.listdetailkey', $(cell)).each(function (idx, val) {
      o.push([$(val).text(), $(val).parent().next("span").text(), $(val).attr("data-extra")]);
    });
    return o;
  }
});

jQuery.extend($.fn.fmatter.currencyWithBlanks, {
  unformat: function (cellval, options, cell) {
    // Copied from the jqgrid source code
    var prefix = options.colModel.formatoptions.prefix;
    var suffix = options.colModel.formatoptions.suffix;
    var thegrid = $(cell).closest("table").first();
    var thousandsSeparator = thegrid.jqGrid("getGridRes", "formatter.currency.thousandsSeparator")
      .replace(/([\.\*\_\'\(\)\{\}\+\?\\])/g, "\\$1");
    var decimalSeparator = thegrid.jqGrid("getGridRes", "formatter.currency.decimalSeparator");
    if (prefix && prefix.length)
      cellval = cellval.substr(prefix.length);
    if (suffix && suffix.length)
      cellval = cellval.substr(0, cellval.length - suffix.length);
    cellval = cellval.replace(new RegExp(thousandsSeparator, "g"), "");
    if (decimalSeparator != ".")
      cellval = cellval.replace(decimalSeparator, ".");
    return cellval;
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

  formatNumber: function (nData, maxdecimals = 6) {
    // Number formatting function copied from free-jqgrid.
    // Adapted to show a max number of decimal places.
    if (typeof (nData) === 'undefined' || nData === '')
      return '';
    var isNumber = $.fmatter.isNumber;
    if (!isNumber(nData))
      nData *= 1;
    if (isNumber(nData)) {
      var bNegative = (nData < 0);
      var absData = Math.abs(nData);
      var sOutput;
      if (absData > 100000 || maxdecimals <= 0)
        sOutput = String(parseFloat(nData.toFixed()));
      else if (absData > 10000 || maxdecimals <= 1)
        sOutput = String(parseFloat(nData.toFixed(1)));
      else if (absData > 1000 || maxdecimals <= 2)
        sOutput = String(parseFloat(nData.toFixed(2)));
      else if (absData > 100 || maxdecimals <= 3)
        sOutput = String(parseFloat(nData.toFixed(3)));
      else if (absData > 10 || maxdecimals <= 4)
        sOutput = String(parseFloat(nData.toFixed(4)));
      else if (absData > 1 || maxdecimals <= 5)
        sOutput = String(parseFloat(nData.toFixed(5)));
      else
        sOutput = String(parseFloat(nData.toFixed(maxdecimals)));
      var sDecimalSeparator = jQuery("#grid").jqGrid("getGridRes", "formatter.number.decimalSeparator") || ".";
      if (sDecimalSeparator !== ".")
        // Replace the "."
        sOutput = sOutput.replace(".", sDecimalSeparator);
      var sThousandsSeparator = jQuery("#grid").jqGrid("getGridRes", "formatter.number.thousandsSeparator") || ",";
      if (sThousandsSeparator) {
        var nDotIndex = sOutput.lastIndexOf(sDecimalSeparator);
        nDotIndex = (nDotIndex > -1) ? nDotIndex : sOutput.length;
        // we cut the part after the point for integer numbers
        // it will prevent storing/restoring of wrong numbers during inline editing
        var sNewOutput = sDecimalSeparator === undefined ? "" : sOutput.substring(nDotIndex);
        var nCount = -1, i;
        for (i = nDotIndex; i > 0; i--) {
          nCount++;
          if ((nCount % 3 === 0) && (i !== nDotIndex) && (!bNegative || (i > 1))) {
            sNewOutput = sThousandsSeparator + sNewOutput;
          }
          sNewOutput = sOutput.charAt(i - 1) + sNewOutput;
        }
        sOutput = sNewOutput;
      }
      return sOutput;
    }
    return nData;
  },

  // Function used to summarize by returning the last value
  summary_last: function (val, name, record) {
    return record[name];
  },

  // Function used to summarize by returning the first value
  summary_first: function (val, name, record) {
    return val || record[name];
  },

  setSelectedRow: function (id) {
    if (grid.selected != undefined)
      $(this).jqGrid('setCell', grid.selected, 'select', null);
    grid.selected = id;
    $(this).jqGrid('setCell', id, 'select', true);
  },

  runAction: function (next_action) {
    if (!["no_action", "actions1"].includes($("#actions").val()))
      actions[$("#actions").val()]();
  },

  setStatus: function (newstatus, field_prefix) {
    var sel = jQuery("#grid").jqGrid('getGridParam', 'selarrrow');
    for (var i in sel) {
      jQuery("#grid").jqGrid("setCell", sel[i], field_prefix ? field_prefix + 'status' : 'status', newstatus, "dirty-cell");
      jQuery("#grid").jqGrid("setRowData", sel[i], false, "edited");
    };
    $("#actions1").html(gettext("Select action"));
    $('#save').removeClass("btn-primary").addClass("btn-danger").prop("disabled", false);
    $('#undo').removeClass("btn-primary").addClass("btn-danger").prop("disabled", false);
  },

  // Renders the cross list in a pivot grid
  _cached_cross: null,
  pivotcolumns: function (cellvalue, options, rowdata) {
    // Compute once for all rows in the report, and then cache the result
    if (grid._cached_cross) return grid._cached_cross;
    var result = '';
    for (var i of cross_idx) {
      if (cross[i].hidden) continue;
      var icon = "fa-plus-square-o";
      for (var p of cross_idx) {
        if (i != p && cross[p]["expand"]) {
          if (cross[p]["expand"].includes(cross[i]["key"]))
            result += "&nbsp;&nbsp;&nbsp;";
          else {
            for (var q in cross) {
              if (cross[p]["expand"].includes(cross[q]["key"])
                && cross[q]["expand"]
                && cross[q]["expand"].includes(cross[i]["key"]))
                result += "&nbsp;&nbsp;&nbsp;";
            }
          }
        }
        if (cross[i]["expand"] && cross[i]["expand"].includes(cross[p]["key"]))
          icon = "fa-minus-square-o";
      }
      if (cross[i]['editable'])
        result += cross[i]['name'] + '<input style="width:0px" class="invisible"/><br>';
      else if (cross[i]["expand"])
        result += cross[i]['name'] + '&nbsp;<i style="cursor: pointer" class="fa ' + icon + '" onclick="grid.expandCross(this, ' + i + ')"></i><br>';
      else
        result += cross[i]['name'] + '<br>';
    }
    grid._cached_cross = result;
    return result;
  },

  toggleCollapseSubOptions: function (optionString, elemId) {
    let isExpanded = $('#'+elemId+' i').hasClass( "fa-chevron-down" ) ? true : false;

    if (isExpanded) {
      $('#popup #'+elemId+' i').removeClass( "fa-chevron-down" ).addClass("fa-chevron-right");
      $('#popup #DroppointRows li[type="'+optionString+'"]').addClass("d-none");
    } else {
      $('#popup #'+elemId+' i').removeClass( "fa-chevron-right" ).addClass("fa-chevron-down");
      $('#popup #DroppointRows li[type="'+optionString+'"]').removeClass("d-none");
    }

  },

  // Render the customization popup window
  showCustomize: function (pivot, gridid, cross_arg, cross_idx_arg, cross_only_arg, ok_callback, reset_callback) {
    hideModal('timebuckets');
    $.jgrid.hideModal("#searchmodfbox_grid");
    var thegrid = $((typeof gridid !== 'undefined') ? gridid : "#grid");
    var colModel = thegrid.jqGrid('getGridParam', 'colModel');
    var maxfrozen = 0;
    var skipped = 0;
    var graph = false;
    var cross_only = pivot && typeof cross_only_arg !== 'undefined' && cross_only_arg;

    var row0 = cross_only ?
      '' :
      '<div class="row mb-3">' +
      '<div class="col">' +
      '<div class="card"><div class="card-header">' + gettext("Available options") + '</div>' +
      '<div class="card-body">' +
      '<ul class="list-group" id="DroppointRows" style="height: 160px; overflow-y: scroll;">placeholder1</ul>' +
      '</div>' +
      '</div>' +
      '</div>' +
      '<div class="col">' +
      '<div class="card"><div class="card-header">' + gettext("Selected options") + '</div>' +
      '<div class="card-body">' +
      '<ul class="list-group" id="Rows" style="height: 160px; overflow-y: scroll;">placeholder0</ul>' +
      '</div>' +
      '</div>' +
      '</div>' +
      '</div>';

    var row1 = "";
    var row2 = "";

    var val0s = ""; //selected columns
    var val0a = {}; //available columns
    var val1s = ""; //selected crosses
    var val1a = ""; //available crosses
    const collapsibleSet = new Set();

    for (var i in colModel) {
      if (colModel[i].name == 'graph')
        graph = true;
      else if (colModel[i].name != "rn" && colModel[i].name != "cb" && colModel[i].counter != null && colModel[i].label != '' && !('alwayshidden' in colModel[i])) {
        if (colModel[i].frozen) maxfrozen = parseInt(i, 10) + 1 - skipped;
        if (!colModel[i].hidden)
          val0s += '<li id="' + (i) + '"  class="list-group-item" style="cursor: move;">' + colModel[i].label + '</li>';
        else
          val0a[colModel[i].label] = i;
      }
      else
        skipped++;
    }

    if (pivot) {
      var my_cross = (typeof cross_arg !== 'undefined') ? cross_arg : cross;
      var my_cross_idx = (typeof cross_idx_arg !== 'undefined') ? cross_idx_arg : cross_idx;
      // Add list of crosses
      var row1 = '<div class="row">' +
        '<div class="col">' +
        '<div class="card">' +
        '<div class="card-header">' +
        gettext('Available Cross') +
        '</div>' +
        '<div class="card-body">' +
        '<ul class="list-group" id="DroppointCrosses" style="height: 160px; overflow-y: scroll;">placeholder1</ul>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '<div class="col">' +
        '<div class="card">' +
        '<div class="card-header">' +
        gettext('Selected Cross') +
        '</div>' +
        '<div class="card-body">' +
        '<ul class="list-group" id="Crosses" style="height: 160px; overflow-y: scroll;">placeholder0</ul>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '</div>';
      for (var j in my_cross_idx) {
        val1s += '<li class="list-group-item" id="' + (1000 + parseInt(my_cross_idx[j], 10)) + '" style="cursor: move;">' + my_cross[my_cross_idx[j]]['name'] + '</li>';
      }
      var fieldlist = {};
      for (var j in my_cross) {
        if (my_cross_idx.indexOf(parseInt(j, 10)) > -1 || my_cross[j]['name'] == "") continue;
        fieldlist[my_cross[j]['name']] = parseInt(j, 10);
      }
      for (var j of Object.keys(fieldlist).sort())
        val1a += '<li class="list-group-item" id="' + (1000 + fieldlist[j]) + '" style="cursor: move;">' + j + '</li>';
    }
    else {
      // Add selection of number of frozen columns
      row2 = '<div class="row mt-3"><div class="col">' +
        gettext("Frozen columns") +
        '&nbsp;&nbsp;<select id="frozen" class="form-select w-auto d-inline">';
      var maxfreeze = Math.min(colModel.length, 5);
      for (var i = 0; i <= maxfreeze; i++) {
        if (i == maxfrozen)
          row2 += '<option selected value="' + i + '">' + i + '</option>';
        else
          row2 += '<option value="' + i + '">' + i + '</option>';
      }
      row2 += '</select></div></div>';
    }

    row0 = row0.replace('placeholder0', val0s);
    var availableoptions = "";
    for (var o of Object.keys(val0a).sort()) {
      if (o.indexOf(' - ') > 1) {
        collapsibleOption = o.split(' - ')[0];
        if (!collapsibleSet.has(collapsibleOption)) {
          collapsibleSet.add(collapsibleOption);
          let collapseIcon = '<i class="fa fa-chevron-right pt-1 float-end" style="cursor: pointer; z-index: 3000; position: relative"></i>';
          availableoptions += '<li id="' + collapsibleSet.size*1000 + '" class="list-group-item do-not-drag" style="cursor: pointer" onclick="grid.toggleCollapseSubOptions(\'' + collapsibleOption + '\',' + collapsibleSet.size*1000 + ')">' + collapsibleOption + ' attributes' + collapseIcon + '</li>';
        }
        availableoptions += '<li id="' + val0a[o] + '" type="' + collapsibleOption + '" class="list-group-item ps-4 d-none" style="cursor: move">' + o + '</li>';
      } else {
        availableoptions += '<li id="' + val0a[o] + '" class="list-group-item" style="cursor: move">' + o + '</li>';
      }
    }
    row0 = row0.replace('placeholder1', availableoptions);
    if (pivot) {
      row1 = row1.replace('placeholder0', val1s);
      row1 = row1.replace('placeholder1', val1a);
    }

    $('#popup').html('' +
      '<div class="modal-dialog modal-lg">' +
      '<div class="modal-content">' +
      '<div class="modal-header">' +
      '<h5 class="modal-title">' + gettext("Customize") + '</h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label=' + gettext("Close") + '></button>' +
      '</div>' +
      '<div class="modal-body">' +
      row0 +
      row1 +
      row2 +
      (typeof extra_customize_html !== 'undefined' ? extra_customize_html : '') +  // Not very clean to use a global variable here
      '</div>' +
      '<div class="modal-footer justify-content-between">' +
      '<input type="submit" id="cancelCustbutton" role="button" class="btn btn-gray" data-bs-dismiss="modal" value="' + gettext('Cancel') + '">' +
      '<input type="submit" id="resetCustbutton" role="button" class="btn btn-gray" value="' + gettext('Reset') + '">' +
      '<input type="submit" id="okCustbutton" role="button" class="btn btn-primary" value="' + gettext("OK") + '">' +
      '</div>' +
      '</div>' +
      '</div>');
    showModal('popup');

    if (!cross_only) {
      var Rows = document.getElementById("Rows");
      var DroppointRows = document.getElementById("DroppointRows");
      Sortable.create(Rows, {
        group: {
          name: 'Rows',
          put: ['DroppointRows']
        },
        animation: 100
      });
      Sortable.create(DroppointRows, {
        group: {
          name: 'DroppointRows',
          put: ['Rows']
        },
        animation: 100,
        filter: ".do-not-drag"
      });
    }

    if (pivot) {
      var Crosses = document.getElementById("Crosses");
      var DroppointCrosses = document.getElementById("DroppointCrosses");
      Sortable.create(Crosses, {
        group: {
          name: 'Crosses',
          put: ['DroppointCrosses']
        },
        animation: 100
      });
      Sortable.create(DroppointCrosses, {
        group: {
          name: 'DroppointCrosses',
          put: ['Crosses']
        },
        animation: 100
      });
    }

    $('#resetCustbutton').on(
      'click',
      typeof reset_callback !== 'undefined' ? reset_callback : function () {
        var result = {};
        result[reportkey] = { "favorites": favorites };
        if (typeof url_prefix != 'undefined')
          var url = url_prefix + '/settings/';
        else
          var url = '/settings/';
        $.ajax({
          url: url,
          type: 'POST',
          contentType: 'application/json; charset=utf-8',
          data: JSON.stringify(result),
          success: function () { window.location.href = window.location.href; },
          error: ajaxerror
        });
      });

    $('#okCustbutton').on(
      'click',
      typeof ok_callback !== 'undefined' ? ok_callback : function () {
        var colModel = $("#grid")[0].p.colModel;
        var perm = [];
        var hiddenrows = [];
        if (colModel[0].name == "cb") perm.push(0);
        cross_idx = [];
        try {
          if (!graph) $("#grid").jqGrid('destroyFrozenColumns');
        }
        catch (e) {
          console.log("Error destroying frozen columns:", e);
        };

        $('#Rows li').each(function () {
          var val = parseInt(this.id, 10);
          if (val < 1000) {
            $("#grid").jqGrid("showCol", colModel[val].name);
            perm.push(val);
          }
        });

        $('#DroppointRows li').each(function () {
          var val = parseInt(this.id, 10);
          if (val < 1000) {
            hiddenrows.push(val);
            if (pivot)
              $("#grid").jqGrid('setColProp', colModel[val].name, { frozen: false });
            $("#grid").jqGrid("hideCol", colModel[val].name);
          }
        });

        $('#Crosses li').each(function () {
          var val = parseInt(this.id, 10);
          if (val >= 1000)
            cross_idx.push(val - 1000);
        });

        var numfrozen = 0;
        if (pivot) {
          for (var i in colModel)
            if ("counter" in colModel[i])
              numfrozen = parseInt(i) + 1;
            else
              perm.push(parseInt(i));
        }
        else
          numfrozen = parseInt($("#frozen").val());
        for (var i in hiddenrows)
          perm.push(hiddenrows[i]);
        for (var i in colModel)
          if ("alwayshidden" in colModel[i])
            perm.push(parseInt(i));
        $("#grid").jqGrid("remapColumns", perm, true);
        var skipped = 0;
        for (var i in colModel)
          if (colModel[i].name != "rn" && colModel[i].name != "cb" && colModel[i].counter != null)
            $("#grid").jqGrid('setColProp', colModel[i].name, { frozen: i - skipped < numfrozen });
          else
            skipped++;
        if (!graph)
          $("#grid").jqGrid('setFrozenColumns');
        $("#grid").trigger('reloadGrid');
        var reload = typeof extraCustomize !== 'undefined' ? extraCustomize() : false;
        grid.saveColumnConfiguration(function () {
          if (reload) window.location.href = window.location.href;
        });
        hideModal('popup');

      });
  },

  getGridConfig: function () {
    // Returns the current settings of the grid:
    // 1) Filter
    // 2) Sorting
    // 3) Column configuration
    var colArray = new Array();
    var colModel = $("#grid").jqGrid('getGridParam', 'colModel');
    var pivot = false;
    var skipped = 0;
    var maxfrozen = 0;
    for (var i in colModel) {
      if (colModel[i].name != "rn" && colModel[i].name != "cb" && "counter" in colModel[i] && !('alwayshidden' in colModel[i])) {
        colArray.push([colModel[i].name, colModel[i].hidden, colModel[i].width]);
        if (colModel[i].frozen) maxfrozen = parseInt(i) + 1 - skipped;
      }
      else if (colModel[i].name == 'columns' || colModel[i].name == 'graph')
        pivot = true;
      else
        skipped++;
    }
    var result = { "rows": colArray };
    var filter = $('#grid').getGridParam("postData").filters;
    if (typeof filter !== 'undefined' && filter.rules != [])
      result["filter"] = filter;
    var sidx = $('#grid').getGridParam('sortname');
    if (sidx !== '') {
      // Report is sorted
      result['sidx'] = sidx;
      result['sord'] = $('#grid').getGridParam('sortorder');
    }
    if (pivot) {
      result['crosses'] = [];
      for (var i in cross_idx)
        result['crosses'].push(cross[cross_idx[i]].key);
    }
    else
      result['frozen'] = maxfrozen;
    return result;
  },

  // Save the customized column configuration
  saveColumnConfiguration: function (pgButton, indx) {
    // This function can be called with different arguments:
    //   - no arguments, when called from our code
    //   - paging button string, when called from jqgrid paging event
    //   - number argument, when called from jqgrid resizeStop event
    //   - function argument, when you want to run a callback function after the save
    var colArray = new Array();
    var colModel = $("#grid").jqGrid('getGridParam', 'colModel');
    var maxfrozen = 0;
    var pivot = false;
    var skipped = 0;
    var label_width;
    var page = $('#grid').jqGrid('getGridParam', 'page');
    if (typeof pgButton === 'string') {
      // JQgrid paging gives only the current page
      if (pgButton.indexOf("next") >= 0)
        ++page;
      else if (pgButton.indexOf("prev") >= 0)
        --page;
      else if (pgButton.indexOf("last") >= 0)
        page = $("#grid").jqGrid('getGridParam', 'lastpage');
      else if (pgButton.indexOf("first") >= 0)
        page = 1;
      else if (pgButton.indexOf("user") >= 0)
        page = $('input.ui-pg-input').val();
      $('#save, #undo').addClass("btn-primary").removeClass("btn-danger").prop('disabled', true);
    }
    else if (typeof indx != 'undefined' && colModel[indx].name == "operationplans")
      // We're resizing a Gantt chart column. Not too clean to trigger the redraw here, but so be it...
      gantt.redraw();
    for (var i in colModel) {
      if (colModel[i].name != "rn" && colModel[i].name != "cb" && "counter" in colModel[i] && !('alwayshidden' in colModel[i])) {
        colArray.push([colModel[i].name, colModel[i].hidden, colModel[i].width]);
        if (colModel[i].frozen) maxfrozen = parseInt(i) + 1 - skipped;
      }
      else if (colModel[i].name == 'columns') {
        pivot = true;
        label_width = colModel[i].width;
      }
      else if (colModel[i].name == 'graph')
        pivot = true;
      else
        skipped++;
    }
    var result = {
      [reportkey]: {
        "rows": colArray,
        "page": page,
        "favorites": favorites
      }
    };
    var tmp = $('#grid').getGridParam("postData");
    var filter = tmp ? tmp.filters : initialfilter;
    if (typeof filter !== 'undefined' && filter.rules != [])
      result[reportkey]["filter"] = filter;
    var sidx = $('#grid').getGridParam('sortname');
    if (sidx !== '') {
      // Report is sorted
      result[reportkey]['sidx'] = sidx;
      result[reportkey]['sord'] = $('#grid').getGridParam('sortorder');
    }
    if (pivot) {
      result[reportkey]['crosses'] = [];
      for (var i in cross_idx)
        result[reportkey]['crosses'].push(cross[cross_idx[i]].key);
      if (label_width)
        result[reportkey]['label_width'] = label_width;
    }
    else
      result[reportkey]['frozen'] = maxfrozen;
    if (typeof extraPreference == 'function') {
      var extra = extraPreference();
      for (var idx in extra)
        result[reportkey][idx] = extra[idx];
    }
    if (typeof url_prefix != 'undefined')
      var url = url_prefix + '/settings/';
    else
      var url = '/settings/';
    grid._cached_cross = null;
    $.ajax({
      url: url,
      type: 'POST',
      contentType: 'application/json; charset=utf-8',
      data: JSON.stringify(result),
      success: function () {
        preferences = result[reportkey];
        if (typeof pgButton === 'function')
          pgButton();
      },
      error: ajaxerror
    });
  },

  // This function is called when a cell is just being selected in an editable
  // grid. It is used to either a) select the content of the cell (to make
  // editing it easier) or b) display a date picker it the field is of type
  // date.
  afterEditCell: function (rowid, cellname, value, iRow, iCol) {
    $(document.getElementById(iRow + '_' + cellname)).trigger("select");
  },

  showExport: function (only_list, scenario_permissions) {
    hideModal('timebuckets');
    $.jgrid.hideModal("#searchmodfbox_grid");

    // The only_list argument is true when we show a "list" report.
    // It is false for "table" reports.
    var showit = true;
    var content = '<div class="modal-dialog modal-lg">' +
      '<div class="modal-content">' +
      '<div class="modal-header">' +
      '<h5 class="modal-title text-capitalize-first">' + gettext("Export CSV or Excel file") + '</h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="' + gettext("Close") + '"></button>' +
      '</div>' +
      '<div class="modal-body">';
    if (only_list)
      content += '<div class="row" id="csvformat">' +
        '<div class="col">' +
        '<p class="fw-bold">' + gettext("Export format") + '</p>' +
        '<div class="form-check">' +
        '<input class="form-check-input" id="spreadsheetlist" type="radio" name="csvformat" value="spreadsheetlist" checked="">' +
        '<label class="form-check-label" for="spreadsheetlist">' + gettext("Spreadsheet list") + '</label>' +
        '</div>' +
        '<div class="form-check">' +
        '<input class="form-check-input" id="csvlist" type="radio" name="csvformat" value="csvlist">' +
        '<label class="form-check-label" for="csvlist">' + gettext("CSV list") + '</label>' +
        '</div>' +
        '<p class="fw-bold mt-3">' + gettext("Data source URL") + '&nbsp;&nbsp;' +
        '<a href="' + documentation + 'user-interface/getting-around/exporting-data.html" target="_blank" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="' +
        gettext("Using this link external applications can pull data from frePPLe") + '">' +
        '<span class="fa fa-question-circle"></span>' +
        '</a><p>' +
        '<div class="input-group">' +
        '<input type="text" readonly id="urladdress" class="input-group-text" style="background: white">' +
        '<span class="input-group-text fa fa-clipboard" id="copybutton" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="' +
        gettext("Copy to clipboard") + '"</span>' +
        '</div>' +
        '</div>';
    else if (!only_list)
      content += '<div class="row" id="csvformat">' +
        '<div class="col">' +
        '<p class="fw-bold">' + gettext("Export format") + '</p>' +
        '<div class="form-check">' +
        '<input class="form-check-input" id="spreadsheettable" type="radio" name="csvformat" value="spreadsheettable" checked="">' +
        '<label class="form-check-label" for="spreadsheettable">' + gettext("Spreadsheet table") + '</label>' +
        '</div>' +
        '<div class="form-check">' +
        '<input class="form-check-input" id="spreadsheetlist" type="radio" name="csvformat" value="spreadsheetlist">' +
        '<label class="form-check-label" for="spreadsheetlist">' + gettext("Spreadsheet list") + '</label>' +
        '</div>' +
        '<div class="form-check">' +
        '<input class="form-check-input" id="csvtable" type="radio" name="csvformat" value="csvlist">' +
        '<label class="form-check-label" for="csvtable">' + gettext("CSV table") + '</label>' +
        '</div>' +
        '<div class="form-check">' +
        '<input class="form-check-input" id="csvlist" type="radio" name="csvformat" value="csvlist">' +
        '<label class="form-check-label" for="csvlist">' + gettext("CSV list") + '</label>' +
        '</div>' +
        '<p class="fw-bold mt-3">' + gettext("Data source URL") + '&nbsp;&nbsp;' +
        '<a href="' + documentation + 'user-interface/getting-around/exporting-data.html" target="_blank" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="' +
        gettext("Using this link external applications can pull data from frePPLe") + '">' +
        '<span class="fa fa-question-circle"></span>' +
        '</a><p>' +
        '<div class="input-group">' +
        '<input type="text" readonly id="urladdress" class="input-group-text" style="background: white">' +
        '<span class="input-group-text fa fa-clipboard" id="copybutton" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="' +
        gettext("Copy to clipboard") + '"</span>' +
        '</div>' +
        '</div>';
    else
      showit = false;

    if (showit) {
      // Prepare upfront the html for the scenarios to export
      // We limit the list of scenarios to 6
      if (scenario_permissions.length > 0) {
        content += '<div class="col">' +
          '<p class="fw-bold">' + gettext("Scenarios to export") + '</p>' +
          '<div class="check" name="scenarios" id="scenarios" value="default">';
        for (var i = 0; i < scenario_permissions.length; i++) {
          if (scenario_permissions[i][2] == 1)
            content +=
              '<div class="form-check" style="white-space: nowrap">' +
              '<input class="form-check-input" type="checkbox" value="" id="' + scenario_permissions[i][0] + '" checked disabled>' +
              '&nbsp;&nbsp;&nbsp;<label class="form-check-label" for="' + scenario_permissions[i][0] + '">' +
              escapeAttribute(scenario_permissions[i][1]) +
              '</label>' +
              '</div>';
        }
        for (var i = 0; i < scenario_permissions.length && i < 6; i++) {
          if (scenario_permissions[i][2] != 1)
            content +=
              '<div class="form-check" style="white-space: nowrap">' +
              '<input class="form-check-input" type="checkbox" value="" id="' + scenario_permissions[i][0] + '">' +
              '&nbsp;&nbsp;&nbsp;<label class="form-check-label" for="' + scenario_permissions[i][0] + '">' +
              escapeAttribute(scenario_permissions[i][1]) +
              '</label>' +
              '</div>';
        }
        content += '</div></div>';
      }
      content += '</div></div>' +  // closing modal-body and modal-content
        '<div class="modal-footer justify-content-between">' +
        '<input type="submit" id="cancelbutton" role="button" class="btn btn-gray" data-bs-dismiss="modal" value="' + gettext('Cancel') + '">' +
        '<input type="submit" id="exportbutton" role="button" class="btn btn-primary" value="' + gettext('Export') + '">' +
        '</div>' +
        '</div>' +
        '</div>';
      $('#popup').html(content);
      showModal('popup');
    }

    // initialize the data source url
    update_datasource_url();

    // Update url when the scenario selection changes
    for (var i = 0; i < scenario_permissions.length && i < 6; i++) {
      if (scenario_permissions[i][2] != 1)
        $('#' + scenario_permissions[i][0]).on('click', function () {
          update_datasource_url();
        });
    }

    $('#copybutton').on('click', function () {
      // should be up to date but let's recompute it.
      update_datasource_url();
      navigator.clipboard.writeText($('#urladdress').val());
    });

    //Compute the power query url to display
    function update_datasource_url() {

      var url = (location.href.indexOf("#") != -1 ?
        location.href.substr(0, location.href.indexOf("#")) : location.href);


      if (location.search.length > 0)
        // URL already has arguments
        url += "&";
      else if (url.charAt(url.length - 1) != '?')
        // This is the first argument for the URL
        url += "?";

      // csvtable and spreadsheet table are converted into csvlist
      // Maintaining a table view with buckets as columns won't work with Excel after a bucket shift
      url += "format=spreadsheetlist";

      // retrieve visible columns from the view
      url += "&selected_rows=";
      var colModel = $("#grid").jqGrid('getGridParam', 'colModel');
      var firstLoop = true;
      var pivot = false;
      for (var i in colModel) {
        if (colModel[i].name == 'columns' || colModel[i].name == 'graph')
          pivot = true;
        if (colModel[i].name != "rn"
          && colModel[i].name != "cb"
          && "counter" in colModel[i]
          && !('alwayshidden' in colModel[i])
          && !colModel[i].hidden) {
          if (firstLoop)
            firstLoop = false;
          else
            url += ",";
          url += colModel[i].name;
        }
      }

      var tmp = $('#grid').getGridParam("postData");
      var filter = tmp ? tmp.filters : initialfilter;
      if (typeof filter !== 'undefined' && filter.rules != [])
        url += "&filters=" + filter;

      url += "&language=" + document.documentElement.lang;

      var sidx = $('#grid').getGridParam('sortname');
      if (sidx !== '') {
        // Report is sorted
        url += "&sidx=" + sidx;
        url += "&sord=" + $('#grid').getGridParam('sortorder');
      }

      if (pivot) {
        var firstLoop = true;
        for (var i in cross_idx) {
          if (firstLoop) {
            url += "&selected_crosses=";
            firstLoop = false;
          }
          else
            url += ",";
          url += cross[cross_idx[i]].key;
        }
      }

      if (scenario_permissions.length > 1) {
        var firstTime = true;
        var scenarios = "";
        for (var i = 0; i < scenario_permissions.length; i++) {
          if ($('#' + scenario_permissions[i][0]).is(":checked")) {
            if (firstTime)
              firstTime = false;
            else
              scenarios += ",";

            scenarios += scenario_permissions[i][0];
          }
        }
        url += "&scenarios=" + scenarios;
      }
      $('#urladdress').val(url);
    }

    $('#exportbutton').on('click', function () {
      // Fetch the report data
      var url = (location.href.indexOf("#") != -1 ? location.href.substr(0, location.href.indexOf("#")) : location.href);
      var scenarios = "";
      if (scenario_permissions.length > 1) {
        var firstTime = true;
        for (var i = 0; i < scenario_permissions.length; i++) {
          if ($('#' + scenario_permissions[i][0]).is(":checked")) {
            if (firstTime)
              firstTime = false;
            else
              scenarios += ",";

            scenarios += scenario_permissions[i][0];
          }
        }
      }

      if (location.search.length > 0)
        // URL already has arguments
        url += "&format=" + $('#csvformat input:radio:checked').val();
      else if (url.charAt(url.length - 1) == '?')
        // This is the first argument for the URL, but we already have a question mark at the end
        url += "format=" + $('#csvformat input:radio:checked').val();
      else
        // This is the first argument for the URL
        url += "?format=" + $('#csvformat input:radio:checked').val();

      // Append scenarios if needed
      if (scenario_permissions.length > 1)
        url += "&scenarios=" + scenarios;

      // Append current filter and sort settings to the URL
      var postdata = $("#grid").jqGrid('getGridParam', 'postData');
      url += "&" + jQuery.param(postdata);
      // Open the window
      window.open(url, '_blank');
      hideModal('popup');
    });
  },


  // Display time bucket selection dialog
  showBucket: function () {
    // Show popup
    hideModal('popup');
    $.jgrid.hideModal("#searchmodfbox_grid");
    $("#okbutton").on('click', function () {
      // Compare old and new parameters
      var params = $('#horizonbuckets').val() + '|' +
        $('#horizonstart').val() + '|' +
        $('#horizonend').val() + '|' +
        ($('#horizontype').is(':checked') ? "True" : "False") + '|' +
        $('#horizonbefore').val() + '|' +
        $('#horizonlength').val() + '|' +
        $('#horizonunit').val();

      if (params == $('#horizonoriginal').val())
        // No changes to the settings. Close the popup.
        hideModal('timebuckets');
      else {
        // Ajax request to update the horizon preferences
        $.ajax({
          type: 'POST',
          url: url_prefix + '/horizon/',
          data: {
            horizonbuckets: $('#horizonbuckets').val() ?
              $('#horizonbuckets').val() :
              $("#horizonbucketsul li a").first().text(),
            horizonstart: $('#horizonstart').val(),
            horizonend: $('#horizonend').val(),
            horizontype: ($('#horizontype').is(':checked') ? '1' : '0'),
            horizonlength: $('#horizonlength').val(),
            horizonbefore: $('#horizonbefore').val(),
            horizonunit: $('#horizonunit').val()
          },
          dataType: 'text/html',
          async: false  // Need to wait for the update to be processed!
        });
        // Reload the report
        window.location.href = window.location.href;
      }
    });
    showModal('timebuckets', false);
  },

  //Display dialog for copying or deleting records
  showDelete: function (url) {
    if ($('#delete_selected').is(":disabled")) return;
    var sel = jQuery("#grid").jqGrid('getGridParam', 'selarrrow');
    if (sel.length == 1 && typeof dont_show_related_objects_for_deletion == 'undefined')
      // Redirect to a page for deleting a single entity
      location.href = url + admin_escape(sel[0]) + '/delete/';
    else if (sel.length > 0) {
      hideModal('timebuckets');
      $.jgrid.hideModal("#searchmodfbox_grid");
      $('#popup').html('<div class="modal-dialog">' +
        '<div class="modal-content">' +
        '<div class="modal-header">' +
        '<h5 class="modal-title text-capitalize-first">' + gettext('Delete data') + '</h5>' +
        '<button type="button" class="btn-close" data-bs-dismiss="modal"></span></button>' +
        '</div>' +
        '<div class="modal-body">' +
        '<p>' + interpolate(gettext('You are about to delete %s objects AND ALL RELATED RECORDS!'), [sel.length], false) + '</p>' +
        '</div>' +
        '<div class="modal-footer justify-content-between">' +
        '<input type="submit" id="cancelbutton" role="button" class="btn btn-gray pull-left" data-bs-dismiss="modal" value="' + gettext('Cancel') + '">' +
        '<input type="submit" id="delbutton" role="button" class="btn btn-primary pull-right" value="' + gettext('Confirm') + '">' +
        '</div>' +
        '</div>' +
        '</div>');
      showModal('popup');
      $('#delbutton').on('click', function () {
        $.ajax({
          url: url,
          data: JSON.stringify([{ 'delete': sel }]),
          type: "POST",
          contentType: "application/json",
          success: function () {
            $("#delete_selected, #copy_selected, #edit_selected").prop("disabled", true);
            $('.cbox, #cb_grid.cbox').prop("checked", false);
            $("#grid").trigger("reloadGrid");
            hideModal('popup');
          },
          error: function (result, stat, errorThrown) {
            if (result.status == 401) {
              location.reload();
              return;
            }
            $('#popup .modal-body p').html(result.responseText);
            $('#popup .modal-title').html(gettext("Error"));
            $('#popup .modal-header').addClass('bg-danger');
            $('#delbutton').prop("disabled", true).hide();
          }
        })
      })
    }
  },

  showCopy: function () {
    if ($('#copy_selected').is(":disabled")) return;
    var sel = jQuery("#grid").jqGrid('getGridParam', 'selarrrow');
    if (sel.length > 0) {
      hideModal('timebuckets');
      $.jgrid.hideModal("#searchmodfbox_grid");
      $('#popup').html('<div class="modal-dialog">' +
        '<div class="modal-content">' +
        '<div class="modal-header">' +
        '<h5 class="modal-title text-capitalize-first">' + gettext("Copy data") + '</h5>' +
        '<button type="button" class="btn-close" data-bs-dismiss="modal"></button>' +
        '</div>' +
        '<div class="modal-body">' +
        '<p>' + interpolate(gettext('You are about to duplicate %s objects'), [sel.length], false) + '</p>' +
        '</div>' +
        '<div class="modal-footer justify-content-between">' +
        '<input type="submit" id="cancelbutton" role="button" class="btn btn-gray" data-bs-dismiss="modal" value="' + gettext('Cancel') + '">' +
        '<input type="submit" id="copybutton" role="button" class="btn btn-primary" value="' + gettext('Confirm') + '">' +
        '</div>' +
        '</div>' +
        '</div>');
      showModal('popup');
      $('#copybutton').on('click', function () {
        $.ajax({
          url: location.pathname,
          data: JSON.stringify([{ 'copy': sel }]),
          type: "POST",
          contentType: "application/json",
          success: function () {
            $("#delete_selected, #copy_selected, #edit_selected").prop("disabled", true);
            $('.cbox, #cb_grid.cbox').prop("checked", false);
            $("#grid").trigger("reloadGrid");
            hideModal('popup');
          },
          error: function (result, stat, errorThrown) {
            if (result.status == 401) {
              location.reload();
              return;
            }
            $('#popup .modal-body p').html(result.responseText);
            $('#popup .modal-title').html(gettext("Error"));
            $('#popup .modal-header').addClass('bg-danger');
            $('#copybutton').prop("disabled", true).hide();
          }
        })
      })
    }
  },

  // Display filter dialog
  showFilter: function (gridid, curfilterid, filterid) {
    $("#addsearch").val("");
    $("#filteroperand, #filterfield, #andordropdown").remove();
    grid.handlerinstalled = false;
    hideModal('popup');
    hideModal('timebuckets');
    var thegridid = (typeof gridid !== 'undefined') ? gridid : "grid";
    var thegrid = $("#" + thegridid);
    var curfilter = $((typeof curfilterid !== 'undefined') ? curfilterid : "#curfilter");
    hideModal('timebuckets');
    hideModal('popup');
    thegrid.jqGrid('searchGrid', {
      closeOnEscape: true,
      multipleSearch: true,
      multipleGroup: true,
      overlay: 0,
      resize: false,
      sopt: ['eq', 'ne', 'lt', 'le', 'gt', 'ge', 'bw', 'bn', 'in', 'ni', 'ew', 'en', 'cn', 'nc', 'ico'],
      onSearch: function () {
        var c = $("#fbox_" + thegridid).jqFilter('filterData');
        grid.saveColumnConfiguration();
        grid.getFilterGroup(thegrid, c, true, curfilter);
        if (typeof extraSearchUpdate == 'function')
          extraSearchUpdate(c);
      },
      onReset: function () {
        if (typeof initialfilter !== 'undefined') {
          thegrid.jqGrid('getGridParam', 'postData').filters = JSON.stringify(initialfilter);
          grid.getFilterGroup(thegrid, initialfilter, true, curfilter);
        }
        else
          curfilter.html("");
        grid.saveColumnConfiguration();
        return true;
      }
    });
    $("#searchmodfbox_grid").detach().appendTo("#content-main");
  },

  resetFilter: function () {
    var curfilter = $((typeof curfilterid !== 'undefined') ? curfilterid : "#curfilter");
    curfilter.html("");
    $("#grid").setGridParam({
      postData: { filters: '' },
      search: true
    }).trigger('reloadGrid');
    grid.saveColumnConfiguration();
  },

  countFilters: 0,

  handlerinstalled: false,

  addFilter: function (event) {
    if (event) {
      event.stopPropagation();
      event.preventDefault();
      var field = $(event.target).attr("data-filterfield");
    }
    else
      var field = $("#filterfield [data-filterfield]").first().attr("data-filterfield");
    var n = {
      "field": field,
      "op": "cn",
      "data": $("#addsearch").val(),
      "filtercount": ++grid.filtercount
    };
    var c = $('#grid').getGridParam("postData");
    c = (c !== undefined) ? c.filters : initialfilter;
    if (c && c !== "") {
      c = JSON.parse(c);
      if ((c["rules"] !== undefined && c["rules"].length > 0) || (c["groups"] !== undefined && c["groups"].length > 0))
        // Add condition to existing filter
        c["rules"].push(n);
      else
        // Wrap existing filter in a new and-filter
        c = {
          "groupOp": "AND",
          "rules": [n],
          "groups": [c]
        };
    }
    else {
      // First filter
      c = {
        "groupOp": "AND",
        "rules": [n],
        "groups": []
      };
    }
    $("#grid").setGridParam({
      postData: { filters: JSON.stringify(c) },
      search: true
    }).trigger('reloadGrid');
    grid.saveColumnConfiguration();
    if (typeof extraSearchUpdate == 'function')
      extraSearchUpdate(c);
    grid.getFilterGroup($("#grid"), c, true, $("#curfilter"));
    $(document).off("click", grid.clickFilter);
    grid.handlerinstalled = false;
    $("#addsearch").val("");
    $("#filteroperand, #filterfield, #andordropdown").remove();
    $("#tooltip").css("display", "none");
  },

  clickFilter: function (event) {
    if ($(event.target).attr('id') != "addsearch") {
      $(document).off("click", grid.clickFilter);
      grid.handlerinstalled = false;
      $("#addsearch").val("");
      $("#filteroperand, #filterfield, #andordropdown").remove();
    }
  },

  setFilterField: function (event, rule, thefilter, fullfilter) {
    const el = $(event.target);
    const el_badge = el.closest(".badge");
    const colname = $(event.target).attr("data-filterfield");
    const collabel = $(event.target).attr("data-filterlabel");
    let oper = el_badge.find("span[data-operandname]").attr("data-operandname");
    let operandlabel = grid.findOperandLabel(oper);

    const col = $("#grid").jqGrid('getGridParam', 'colModel').filter((col) => (col.name == colname))[0];
    const searchoptions = col.searchoptions;

    if (rule.field == colname) return;

    // Set field name and label
    el_badge.find("span[data-colname]")
      .attr("data-colname", colname)
      .attr("data-collabel", collabel)
      .text(collabel);
    rule.field = colname;

    // Set operand label
    if (searchoptions.sopt.indexOf(oper) == -1) {
      oper = searchoptions.sopt[0];
      operandlabel = grid.findOperandLabel(oper);
      el_badge.find("span[data-operandname]").attr("data-operandname", oper).text(operandlabel);
      rule.op = oper;
    }

    // Close the dropdown
    $("#filteroperand, #filterfield, #andordropdown").remove();

    // Refilter the grid
    $("#grid").setGridParam({
      postData: { filters: JSON.stringify(fullfilter) },
      search: true
    }).trigger('reloadGrid');
    grid.saveColumnConfiguration();
  },

  setFilterOperand: function (event, rule, thefilter, fullfilter) {
    const el = $(event.target);
    const el_badge = el.closest(".badge");
    let oper = $(event.target).attr("data-operandname");
    let operandlabel = grid.findOperandLabel(oper);
    if (oper == rule.oper) return;

    // Set new operand label
    el_badge.find("span[data-operandname]").attr("data-operandname", oper).text(operandlabel);
    rule.op = oper;

    // Close the dropdown
    $("#filteroperand, #filterfield, #andordropdown").remove();

    // Refilter the grid
    $("#grid").setGridParam({
      postData: { filters: JSON.stringify(fullfilter) },
      search: true
    }).trigger('reloadGrid');
    grid.saveColumnConfiguration();
  },

  setFilterAndOr: function (event, rule, thefilter, fullfilter) {
    const el = $(event.target);
    event.stopPropagation();
    $("#filteroperand, #filterfield, #andordropdown").remove();
    andordropdown = $('<span id="andordropdown" class="mt-1 list-group dropdown-menu" style="min-width: 1em">'
      + '<a class="dropdown-item" data-oper="and">' + gettext("and") + '</a>'
      + '<a class="dropdown-item" data-oper="or">' + gettext("or") + '</a>'
      + '</span>');
    andordropdown.on("click", (event) => {
      const andor = $(event.target).attr("data-oper");
      if (andor == "and") {
        rule.groupOp = "AND";
      } else if (andor == "or") {
        rule.groupOp = "OR";
      } else {
        return;
      }
      $("#filteroperand, #filterfield, #andordropdown").remove();
      $("#grid").setGridParam({
        postData: { filters: JSON.stringify(fullfilter) },
        search: true
      }).trigger('reloadGrid');
      grid.saveColumnConfiguration();
      grid.getFilterGroup($("#grid"), fullfilter, true, thefilter, fullfilter);
    });

    el.append(andordropdown);
  },

  showFieldList: function (el, rule, thefilter, fullfilter) {
    $.jgrid.hideModal("#searchmodfbox_grid");
    $("#filteroperand, #filterfield, #andordropdown").remove();
    event.stopPropagation();
    $(document).on("click", grid.clickFilter);
    let l = $('<span id="filterfield" class="list-group dropdown-menu">');
    let cnt = 15;  // Limits the number fields to choose from
    for (var col of $("#grid").jqGrid('getGridParam', 'colModel')) {
      var searchoptions = col.searchoptions;
      if (searchoptions && searchoptions.sopt) {
        if (el.id == "addsearch")
          var n = $('<a class="dropdown-item" onclick="grid.addFilter(event)" />');
        else {
          var n = $('<a class="dropdown-item" />');
          n.on("click", (event) => grid.setFilterField(event, rule, thefilter, fullfilter));
        };
        n.attr("data-filterfield", col.name);
        n.attr("data-filterlabel", col.label);
        n.html(col.label);
        l.append(n);
        if (--cnt <= 0) break;
      }
    }
    $(el).before(l);
  },

  showOperandsList: function (el, rule, thefilter, fullfilter) {
    $.jgrid.hideModal("#searchmodfbox_grid");
    $("#filteroperand, #filterfield, #andordropdown").remove();
    event.stopPropagation();
    $(document).on("click", grid.clickFilter);
    let colname = $(el).closest(".badge").find("span[data-colname]").attr("data-colname");
    let col = $("#grid").jqGrid('getGridParam', 'colModel').filter((col) => (col.name == colname))[0];

    let l = $('<span id="filteroperand" class="list-group dropdown-menu">');
    let searchoptions = col.searchoptions;
    if (searchoptions && searchoptions.sopt) {
      for (let sopt of searchoptions.sopt) {
        let n = $('<a class="dropdown-item"/>');
        n.on("click", (event) => grid.setFilterOperand(event, rule, thefilter, fullfilter));
        n.attr("data-operandname", sopt);
        n.html(grid.findOperandLabel(sopt));
        l.append(n);
      }
      $(el).before(l);
    }
  },

  findOperandLabel(operand) {
    for (const i of $.jgrid.locales[$.jgrid.defaults.locale].search.odata)
      if (i.oper == operand) return i.text;
    return operand;
  },

  keyDownSearch: function () {
    var keycode = (event.keyCode ? event.keyCode : event.which);
    if (keycode == 13)
      grid.addFilter();
  },

  updateFilter: function (obj, idx, newvalue) {
    if (obj instanceof Array)
      for (var i in obj)
        grid.updateFilter(obj[i], idx, newvalue);
    else if (typeof obj == "object") {
      for (var i in obj) {
        if (i == "filtercount" && obj[i] == idx)
          obj.data = newvalue;
        else if (obj.hasOwnProperty(i))
          grid.updateFilter(obj[i], idx, newvalue);
      }
    }
  },

  removeFilter: function (obj, idx) {
    if (obj instanceof Array)
      for (var i in obj) {
        if (obj[i]["filtercount"] == idx)
          obj.splice(i, 1);
        else if (obj[i]["filtercount"] > idx)
          --obj[i]["filtercount"];
        else
          grid.removeFilter(obj[i], idx);
      }
    else if (typeof obj == "object") {
      for (var i in obj) {
        if (obj.hasOwnProperty(i))
          grid.removeFilter(obj[i], idx);
      }
    }
  },

  getFilterRule: function (thegrid, rule, thefilter, fullfilter) {
    // Find the column
    var i, col;
    var columns = thegrid.jqGrid('getGridParam', 'colModel');
    for (i = 0; i < columns.length; i++) {
      if (columns[i].name === rule.field || columns[i].field_name === rule.field) {
        col = columns[i];
        break;
      }
    }
    if (col == undefined)
      return;

    // Final result
    var fieldspan = $('<span data-colname=' + col.name + ' data-collabel=' + col.label + ' style="cursor: pointer">' + col.label + '</span>');
    fieldspan.on('click', (event) => grid.showFieldList(event.target, rule, thefilter, fullfilter));
    var operatorspan = $('<span data-operandname=' + rule.op + ' style="cursor: pointer;">' + grid.findOperandLabel(rule.op) + '</span>');
    operatorspan.on('click', (event) => grid.showOperandsList(event.target, rule, thefilter, fullfilter));
    var newexpression = $('<span class="badge dropdown"></span>');
    newexpression.append(fieldspan);
    newexpression.append('&nbsp;');
    newexpression.append(operatorspan);
    newexpression.append('&nbsp;');
    var newelement = $('<input class="form-control" style="width: 2.4em">');
    rule["filtercount"] = grid.countFilters++;  // Mark position in the expression
    newelement.val(rule.data);
    newelement.attr("style", "width: " + Math.min((rule.data.length + 4) * 0.5, 20) + "em");
    newelement.on({
      input: function (event) {
        this.style.width = Math.min(($(event.target).val().length + 4) * 0.5, 20) + "em";
      },
      change: function (event) {
        grid.updateFilter(fullfilter, rule["filtercount"], $(event.target).val());
        thegrid.setGridParam({
          postData: { filters: JSON.stringify(fullfilter) },
          search: true
        }).trigger('reloadGrid');
        if (typeof extraSearchUpdate == 'function')
          extraSearchUpdate(fullfilter);
        grid.saveColumnConfiguration();
      }
    });
    newexpression.append(newelement);
    newexpression.append('&nbsp;');
    var deleteelement = $('<span class="fa fa-times"/>');
    deleteelement.on('click', function (event) {
      grid.removeFilter(fullfilter, rule["filtercount"]);
      grid.getFilterGroup(thegrid, fullfilter, true, thefilter, fullfilter);
      thegrid.setGridParam({
        postData: { filters: JSON.stringify(fullfilter) },
        search: true
      }).trigger('reloadGrid');
      if (typeof extraSearchUpdate == 'function')
        extraSearchUpdate(fullfilter);
      grid.saveColumnConfiguration();
    });
    newexpression.append(deleteelement);
    thefilter.append(newexpression);
  },

  getFilterGroup: function (thegrid, group, first, thefilter, fullfilter) {
    if (!first)
      thefilter.append("( ");
    else {
      thefilter.html("");
      fullfilter = group;
      grid.countFilters = 0;
    }

    if (group !== null && group !== undefined && group.groups !== undefined) {
      for (var index = 0; index < group.groups.length; index++) {
        if (thefilter.html().length > 2) {
          var newel = $('<span class= "d-inline-block dropdown p-1" style="cursor: pointer">' +
            '<span class="dropdown-toggle">' +
            gettext(group.groupOp === "OR" ? "or" : "and ") +
            '</span></span>');
          newel.on('click', (event) => grid.setFilterAndOr(event, group, thefilter, fullfilter));
          thefilter.append(newel);
        }
        grid.getFilterGroup(thegrid, group.groups[index], false, thefilter, fullfilter);
      }
    }

    if (group !== null && group !== undefined && group.rules !== undefined) {
      for (var index = 0; index < group.rules.length; index++) {
        if (thefilter.html().length > 2) {
          var newel = $(
            '<span class="d-inline-block dropdown p-1" style="cursor: pointer"><span>' +
            gettext((group.groupOp === "OR") ? "or" : "and") +
            '</span></span>');
          newel.on('click', (event) => grid.setFilterAndOr(event, group, thefilter, fullfilter));
          thefilter.append(newel);
        }
        grid.getFilterRule(thegrid, group.rules[index], thefilter, fullfilter);
      }
    }

    if (!first) thefilter.append("&nbsp;)");
  },

  markSelectedRow: function (sel) {
    if (typeof sel !== 'undefined' && sel > 0) {
      $("#delete_selected, #copy_selected, #edit_selected").prop('disabled', false);
      if ($("#actions").length) $("#actions1").prop('disabled', false);
    }
    else {
      $("#delete_selected, #copy_selected, #edit_selected").prop('disabled', true);
      if ($("#actions").length) $("#actions1").prop('disabled', true);
    }
  },

  markAllRows: function () {
    if ($(this).is(':checked')) {
      $("#copy_selected, #delete_selected, #edit_selected").prop('disabled', false);
      $("#gridactions").prop('disabled', false);
      $('.cbox').prop("checked", true);
    }
    else {
      $("#copy_selected, #delete_selected, #edit_selected").prop('disabled', true);
      $("#gridactions").prop('disabled', true);
      $('.cbox').prop("checked", false);
    }
  },

  displayMode: function (m) {
    var url = (location.href.indexOf("#") != -1 ? location.href.substr(0, location.href.indexOf("#")) : location.href);
    if (location.search.length > 0)
      // URL already has arguments
      url = url.replace("&mode=table", "").replace("&mode=graph", "").replace("mode=table", "").replace("mode=graph", "") + "&mode=" + m;
    else if (url.charAt(url.length - 1) == '?')
      // This is the first argument for the URL, but we already have a question mark at the end
      url += "mode=" + m;
    else
      // This is the first argument for the URL
      url += "?mode=" + m;
    window.location.href = url;
  },

  findCrossByName: function (name) {
    for (var i in cross)
      if (cross[i]["key"] == name) {
        return parseInt(i);
      }
    return -1;
  },

  expandCross: function (el, index) {
    var newlist = [];
    if ($(el).hasClass("fa-plus-square-o")) {
      // Expand a level
      var expanded = [index];
      for (var child of cross[index]["expand"]) {
        var i = grid.findCrossByName(child);
        if (i > 0) expanded.push(i);
      }
      for (var i of cross_idx) {
        if (i == index)
          newlist = newlist.concat(expanded);
        else if (!expanded.includes(i))
          newlist.push(i);
      };
    }
    else {
      // Collapse a level
      for (var i of cross_idx) {
        if (!cross[index]["expand"] || cross[index]["expand"].includes(cross[i]["key"])) continue;
        var not_a_child = true;
        for (var child of cross[index]["expand"]) {
          var j = grid.findCrossByName(child);
          if (cross[j]["expand"] && cross[j]["expand"].includes(cross[i]["key"]))
            not_a_child = false;
        }
        if (not_a_child) newlist.push(i);
      }
    }
    $(el).toggleClass("fa-plus-square-o").toggleClass("fa-minus-square-o");
    cross_idx = newlist;

    // Refresh the data
    var thegrid = $("#grid");
    thegrid.jqGrid('setFrozenColumns');
    thegrid.trigger('reloadGrid');
    thegrid.setGridWidth($('#content-main').width());
    grid.saveColumnConfiguration();
  },

  showUpdate: function (url) {
    hideModal('timebuckets');
    $.jgrid.hideModal("#searchmodfbox_grid");
    var thegrid = $("#grid");
    var colModel = thegrid.jqGrid('getGridParam', 'colModel').sort((a, b) => (a.label || "").localeCompare(b.label || ""));

    var selectedrows = thegrid.jqGrid('getGridParam', 'selarrrow')
    var recordcount = selectedrows.length;
    var msg = { "update": { "fields": {} } }
    if (!recordcount || recordcount == thegrid.jqGrid('getGridParam', "reccount")) {
      recordcount = thegrid.jqGrid('getGridParam', "records");
      var tmp = $('#grid').getGridParam("postData");
      if (tmp)
        msg["update"]["filter"] =
          (typeof tmp.filters !== 'undefined' && tmp.filters.rules != []) ?
            JSON.parse(tmp.filters) : {};
      else
        msg["update"]["filter"] = initialfilter;
    }
    else
      msg["update"]["pk"] = selectedrows;

    var form = '<div class="modal-dialog modal-lg">' +
      '<div class="modal-content">';

    form += '<div class="modal-header">' +
      '<h5 class="modal-title">' + interpolate(gettext("Update %s records"), [recordcount]) + '</h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label=' + gettext("Close") + '></button>' +
      '</div>' +
      '<div class="modal-body">';

    form += '<div class="row mb-3"><div class="col">' +
      gettext("This form allows you update fields for many records.") +
      '</div></div>';

    form += '<div class="row d-none mb-3" id="updatefieldtemplate">' +
      '<div class="col">' +
      '<select class="form-select">';
    for (var field of colModel) {
      if (!field.editable) continue;
      form += '<option value="' + field.name + '">' + field.label + '</option>'
    }
    form += '</select></div>' +
      '<div class="col"><input class="form-control" type="text" placeholder="' + gettext("update to") + '"></div>' +
      '<div class="col-auto">' +
      '<button class="btn btn-sm btn-primary" onclick="grid.deleteUpdateField(event)">' +
      '<span class="fa fa-trash-o" data-bs-toggle="tooltip" data-bs-placement="top"' +
      'data-bs-title="' + gettext("Delete") + '"></span>' +
      '</button>' +
      '</div></div>';

    form += '<div class="row mb-3 updatefield">' +
      '<div class="col">' +
      '<select class="form-select">';
    for (var field of colModel) {
      if (!field.editable) continue;
      form += '<option value="' + field.name + '">' + field.label + '</option>'
    }
    form += '</select></div>' +
      '<div class="col"><input class="form-control" type="text" placeholder="' + gettext("update to") + '"></div>' +
      '<div class="col-auto">' +
      '<button class="btn btn-sm btn-primary" onclick="grid.deleteUpdateField(event)">' +
      '<span class="fa fa-trash-o" data-bs-toggle="tooltip" data-bs-placement="top"' +
      'data-bs-title="' + gettext("Delete") + '"></span>' +
      '</button>' +
      '</div></div>';

    form += '<div class="row">' +
      '<div class="col-auto ms-auto">' +
      '<button class="btn btn-sm btn-primary" id="addCustbutton" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Add">' +
      '<span class="fa fa-plus"></span>' +
      '</button>' +
      '</div>' +
      '</div>';

    form += '</div>' +
      '<div class="modal-footer justify-content-between">' +
      '<input type="submit" id="cancelCustbutton" role="button" class="btn btn-gray" data-bs-dismiss="modal" value="' + gettext('Cancel') + '">' +
      '<input type="submit" id="updateCustbutton" role="button" class="btn btn-primary" value="' + gettext("Update") + '">' +
      '</div>' +
      '</div>' +
      '</div>';

    $('#popup').html(form);
    showModal('popup');

    $('#addCustbutton').on(
      'click',
      function addTask(event) {
        var newrow = $("#updatefieldtemplate").clone();
        newrow.removeAttr("id");
        newrow.insertBefore($(event.target).closest(".row"));
        newrow.toggleClass("d-none updatefield");
        bootstrap.Tooltip.getOrCreateInstance(newrow.find('[data-bs-toggle="tooltip"]')[0]);
        event.preventDefault();
      });

    $('#updateCustbutton').on(
      'click',
      function () {
        for (var i of $("div.modal-body .updatefield")) {
          var fld = $(i).find("select :selected").val();
          var val = $(i).find("input.form-control").val();
          msg["update"]["fields"][fld] = (val == "") ? null : val;
        }
        $.ajax({
          url: url,
          data: JSON.stringify(msg),
          type: "POST",
          contentType: "application/json",
          success: function () {
            window.location.href = window.location.href;
          },
          error: ajaxerror
        });
      });
  },

  deleteUpdateField: function (event) {
    $(event.target).closest(".row").remove();
    event.preventDefault();
  }
}

//
// Functions to manage favorites
//

var favorite = {

  check: function () {
    var fav = $("#favoritename").val();
    if (fav.length > 0 && (
      (typeof favorites !== 'undefined' && !(fav in favorites))
      || (typeof preferences !== 'undefined' && !("favorites" in preferences))
      || (typeof preferences !== 'undefined' && "favorites" in preferences && !(fav in preferences.favorites))
    )) {
      $("#favoritesave").prop("disabled", false);
      return true;
    }
    else {
      $("#favoritesave").prop("disabled", true);
      return false;
    }
  },

  save: function () {
    var fav = $("#favoritename").val();
    if (!favorite.check()) return;
    favorites[fav] = grid.getGridConfig();
    grid.saveColumnConfiguration();
    var divider = $("#favoritelist li.divider");
    if (divider.length == 0) {
      $("#favoritelist").prepend('<li role="separator" class="divider"></li>');
      divider = $("#favoritelist li.divider");
    }
    var newfav_li = $('<li></li>');
    var newfav_a = $('<a class="dropdown-item" href="#" onclick="favorite.open(event)"></a>');
    newfav_a.text(fav);
    newfav_a.append(
      '<div style="float:right"><span class="fa fa-trash-o" onclick="favorite.remove(event)"></span></div>'
    );
    newfav_li.append(newfav_a);
    divider.before(newfav_li);
    favorite.check();
  },

  remove: function (event) {
    var fav = $(event.target).closest("a").text();
    if (fav in favorites) {
      if (confirm(gettext("Click ok to confirm deleting the favorite"))) {
        delete favorites[fav];
        grid.saveColumnConfiguration();
        $(event.target).closest("li").remove();
        $("#favoritename").val(fav);
        favorite.check();
      }
    }
    event.stopImmediatePropagation();
  },

  open: function (event) {
    var fav = $(event.target).parent().text();
    if (!(fav in favorites)) return;

    var thegrid = $("#grid");
    var graph = false;
    var pivot = false;
    var skipped = 0;
    var colModel = thegrid.jqGrid('getGridParam', 'colModel');
    var numfrozen = favorites[fav]["frozen"];
    for (var i in colModel) {
      if (colModel[i].name == 'graph') graph = true;
      else if (colModel[i].name == 'columns') {
        pivot = true;
        numfrozen = parseInt(i);
      }
      else if (colModel[i].name == 'cb') skipped += 1;
    }
    if (!graph) thegrid.jqGrid('destroyFrozenColumns');

    // Restore visibility and column width
    for (var r of favorites[fav]["rows"]) {
      if (r[1])
        thegrid.jqGrid("hideCol", r[0]);
      else
        thegrid.jqGrid("showCol", r[0]);
      thegrid.jqGrid('setColWidth', r[0], r[2]);
    }

    // Restore crosses
    if ("crosses" in favorites[fav]) {
      cross_idx = [];
      for (var i of favorites[fav]["crosses"]) {
        for (var j in cross)
          if (cross[j]["key"] == i)
            cross_idx.push(parseInt(j));
      }
    }

    // Reorder columns
    var perm = [];
    for (var f of favorites[fav]["rows"]) {
      if (!f[1]) {
        perm.push(f[0]);
        thegrid.jqGrid('setColProp', f[0], { frozen: perm.length < numfrozen + skipped });
      }
    }
    if (pivot) {
      for (var j of colModel) {
        if (!("counter" in j)) {
          perm.push(j["name"]);
          j.frozen = (j.name == 'columns');
        }
        else
          j.frozen = true;
      }
    }
    for (var k of colModel) {
      if (!perm.includes(k["name"]) && k["name"] != "cb")
        perm.push(k["name"]);
    }
    thegrid.jqGrid("remapColumnsByName", perm, true, false);

    // Restore the filter
    if ("filter" in favorites[fav] && favorites[fav]["filter"] != "") {
      thegrid.setGridParam({
        postData: { filters: favorites[fav]["filter"] },
        search: true
      });
      grid.getFilterGroup($('#grid'), JSON.parse(favorites[fav]["filter"]), true, $("#curfilter"));
    }
    else {
      thegrid.setGridParam({
        postData: { filters: "" },
        search: true
      });
      $("#curfilter").html("");
    }

    // Restore the sort for the backend
    var sortstring;
    if ("sord" in favorites[fav] && "sidx" in favorites[fav]) {
      thegrid.setGridParam({
        sortname: favorites[fav]["sidx"],
        sortorder: favorites[fav]["sord"]
      });
      sortstring = (favorites[fav]["sidx"] + " " + favorites[fav]["sord"]).split(",");
    }
    else {
      thegrid.setGridParam({
        sortname: "",
        sortorder: "asc"
      });
      sortstring = default_sort.split(",");
    }

    // Reset the sort icons
    var p = thegrid.jqGrid('getGridParam');
    for (var k of p.colModel) {
      var headercell = $("#" + p.id + "_" + k["name"]);
      headercell.find("span.s-ico").css("display", "none");
      headercell.find("span.ui-grid-ico-sort").addClass("disabled");
      headercell.find("span.ui-jqgrid-sort-order").html("&nbsp;");
      k.lso = "";
    }

    // Update the sort icons
    for (var k in sortstring) {
      var s = sortstring[k].trim().split(" ");
      var colname = s[0].trim();
      var headercell = $("#" + p.id + "_" + colname);
      headercell.find("span.s-ico").css("display", "");
      if (s[1].trim() == "asc") {
        headercell.find("span.ui-icon-asc").removeClass("disabled");
        p.colModel[p.iColByName[colname]].lso = "asc-desc";
      }
      else {
        headercell.find("span.ui-icon-desc").removeClass("disabled");
        p.colModel[p.iColByName[colname]].lso = "desc-asc";
      }
      headercell.find("span.ui-jqgrid-sort-order").html(parseInt(k) + 1);
    }

    // Refresh the data
    if (!graph) thegrid.jqGrid('setFrozenColumns');
    thegrid.trigger('reloadGrid');
    thegrid.setGridWidth($('#content-main').width());
    grid.saveColumnConfiguration();
  }
};

//----------------------------------------------------------------------------
// Code for ERP integration
//----------------------------------------------------------------------------

var ERPconnection = {
  IncrementalExport: function (grid, transactiontype) {
    // Collect all selected rows in the status 'proposed'
    var sel = grid.jqGrid('getGridParam', 'selarrrow');
    if (sel === null || sel.length == 0)
      return;
    var data = [];

    for (var i in sel) {
      var r = grid.jqGrid('getRowData', sel[i]);
      if (r.type === undefined)
        r.type = transactiontype;
      if (['proposed', 'approved', 'confirmed'].includes(r.status || r.operationplan__status))
        data.push(r);
    }
    if (data == [])
      return;

    // Send to the server for upload to the ERP
    hideModal('timebuckets');
    $.jgrid.hideModal("#searchmodfbox_grid");
    $('#popup').html('<div class="modal-dialog">' +
      '<div class="modal-content">' +
      '<div class="modal-header">' +
      '<h5 class="modal-title text-capitalize">' + gettext("Export") + '</h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal"></button>' +
      '</div>' +
      '<div class="modal-body pb-0">' +
      '<p>' + gettext("Export selected records?") + '</p>' +
      '</div>' +
      '<div class="modal-footer justify-content-between">' +
      '<input type="submit" id="cancelbutton" role="button" class="btn btn-gray text-capitalize" data-bs-dismiss="modal" value="' + gettext('Cancel') + '">' +
      '<input type="submit" id="button_export" role="button" class="btn btn-primary text-capitalize" value="' + gettext('Confirm') + '">' +
      '</div>' +
      '</div>' +
      '</div>');
    showModal('popup');
    document.getElementById('popup').addEventListener('hidden.bs.modal', event => {
      $("#noactionselected").prop("selected", true);
    }, { once: true });

    $('#button_export').on('click', function () {
      if ($('#button_export').val() === gettext('Close')) {
        hideModal('popup');
        return;
      }
      var tmp = gettext('connecting');
      $('#popup .modal-body p').html(String(tmp).charAt(0).toUpperCase() + String(tmp).slice(1) + '...');
      $.ajax({
        url: url_prefix + "/erp/upload/",
        data: JSON.stringify(data),
        type: "POST",
        contentType: "application/json",
        success: function (data, stat, result) {
          $('#cancelbutton').addClass("invisible");
          $('#button_export').val(gettext('Close'));
          if (result.status == 204) {
            $('#popup .modal-title').html(gettext("Error"));
            $('#popup .modal-header').addClass('bg-danger');
            $('#popup .modal-body p').html(gettext("No valid records selected"));
            return;
          }
          var rowdata = [];
          // Mark selected rows as "approved" if the original status was "proposed".
          $('#popup .modal-body p').html(gettext("Export successful"));

          // update both cell value and grid data
          for (var i in sel) {
            var tp = grid.jqGrid('getCell', sel[i], 'operationplan__type');
            if (!tp) tp = grid.jqGrid('getCell', sel[i], 'type');
            var cur = grid.jqGrid('getCell', sel[i], 'operationplan__status');
            if (cur === 'proposed' && !['STCK', 'DLVR'].includes(tp)) {
              grid.jqGrid('setCell', sel[i], 'operationplan__status', 'approved');
              rowdata = grid.jqGrid('getRowData', sel[i]);
              rowdata.operationplan__status = 'approved';
            }
            else if (!cur) {
              cur = grid.jqGrid('getCell', sel[i], 'operationplan__status');
              if (cur === 'proposed' && !['STCK', 'DLVR'].includes(tp)) {
                grid.jqGrid('setCell', sel[i], 'status', 'approved');
                rowdata = grid.jqGrid('getRowData', sel[i]);
                rowdata.status = 'approved';
              }
            }
          };
          grid.jqGrid('setRowData', rowdata);

          if (typeof checkrows === 'function') {
            checkrows(grid, sel);
          }

        },
        error: function (result) {
          if (result.status == 401) {
            location.reload();
            return;
          }
          $('#popup .modal-title').html(gettext("Error"));
          $('#popup .modal-header').addClass('bg-danger');
          $('#popup .modal-body p').html(result.responseText);
          $('#button_export').val(gettext('retry'));
        }
      });
    });
    if ($("#actions").length)
      $("#actions1 span").text($("#actionsul").children().first().text());
  },


  //  ----------------------------------------------------------------------------
  //  Sales Orders dependencies export
  //  ----------------------------------------------------------------------------
  SODepExport: function (grid, transactiontype) {
    // Collect all selected rows in the status 'proposed'
    const sel = grid.jqGrid('getGridParam', 'selarrrow');
    if (sel === null || sel.length == 0)
      return;
    const data = [];
    for (let i in sel) {
      let r = grid.jqGrid('getRowData', sel[i]);
      if (r.type === undefined)
        r.type = transactiontype;
      data.push(r);
    }
    const formatNumber = window.grid.formatNumber;

    hideModal('timebuckets');
    $.jgrid.hideModal("#searchmodfbox_grid");
    $('#popup').html('<div class="modal-dialog modal-xl">' +
      '<div class="modal-content">' +
      '<div class="modal-header">' +
      '<h5 class="modal-title text-capitalize">' + gettext("Export") + '</h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal"></button>' +
      '</div>' +
      '<div class="modal-body">' +
      '<p>' + gettext("Export selected records?") + '</p>' +
      '</div>' +
      '<div class="modal-footer justify-content-between">' +
      '<input type="submit" id="cancelbutton" role="button" class="btn btn-gray" data-bs-dismiss="modal" value="' + gettext('Cancel') + '">' +
      '<input type="submit" id="button_export" role="button" class="btn btn-primary" value="' + gettext('Confirm') + '">' +
      '</div>' +
      '</div>' +
      '</div>');
    showModal('popup');
    document.getElementById('popup').addEventListener('hidden.bs.modal', event => {
      $("#noactionselected").prop("selected", true);
    }, { once: true });

    // compose url
    let components = '?demand=';
    for (let i = 0; i < sel.length; i++) {
      const r = grid.jqGrid('getRowData', sel[i]);
      if (r.type === undefined)
        r.type = transactiontype;
      if (r.status == 'open' || r.status == 'proposed') {
        if (i == 0) components += encodeURIComponent(sel[i]);
        else components += '&demand=' + encodeURIComponent(sel[i]);
      };
    };

    function formatValue(originalValue) {
      if (originalValue[3] === 'number') {
        return formatNumber(originalValue[1]);
      } else if (originalValue[3] === 'text') {
        return originalValue[1];
      } else if (originalValue[3] === 'date') {
        return moment(originalValue[1]).format(dateformat);
      } else {
        return originalValue[1];
      }
    }

    //get demandplans
    $.ajax({
      url: url_prefix + "/demand/operationplans/" + components,
      type: "GET",
      contentType: "application/json",
      success: function (data) {
        // expected data format:
        // data = {PO: [row0, row1, ...], MO: [row0, ...], DO: [row0, ...]};
        // row = [[label0, value0, hidden], [label1, value1, hidden], ...];

        if (data.PO.length === 0 && data.MO.length === 0 && data.DO.length === 0) {
          $('#popup .modal-body').css({ 'overflow-y': 'auto' }).html('<div style="overflow-y:auto; height: 300px; resize: vertical">' +
            gettext('There are no purchase, distribution or manufacturing orders for export that are linked to this sales order') +
            '</div>');
          $('#button_export').addClass("d-none");
          return;
        }
        $('#popup .modal-body').html(
          '<div id="PO-title"><h5 class="text-capitalize">' + gettext("purchase orders") + '</h5></div>' +
          '<div id="PO-data" class="table-responsive">' +
          '<table class="table table-hover text-center" id="exporttable_PO">' +
          '<thead class="thead-default">' +
          '</thead>' +
          '</table>' +
          '</div>' +
          '<div id="MO-title"><h5 class="text-capitalize">' + gettext("manufacturing orders") + '</h5></div>' +
          '<div id="MO-data" class="table-responsive">' +
          '<table class="table table-hover text-center" id="exporttable_MO">' +
          '<thead class="thead-default">' +
          '</thead>' +
          '</table>' +
          '</div>' +
          '<div id="DO-title"><h5 class="text-capitalize">' + gettext("distribution orders") + '</h5></div>' +
          '<div id="DO-data" class="table-responsive">' +
          '<table class="table table-hover text-center" id="exporttable_DO">' +
          '<thead class="thead-default">' +
          '</thead>' +
          '</table>' +
          '</div>'
        );

        let labels = [];
        let modal_table_row_index = 0;

        for (const dataType of ['PO', 'DO', 'MO']) {
          if (data[dataType].length === 0) {
            $('#' + dataType + '-title, #' + dataType + '-data').addClass('d-none');
            continue;
          }
          labels.length = 0;

          let tableheadercontent = $('<tr/>');

          tableheadercontent.append($('<th/>').html(
            '<input id="cb_modaltableall_' + dataType + '" class="cbox" type="checkbox" aria-checked="true" checked>'
          ));

          labels.push(...data[dataType][0].map(x => x[0]));

          for (const labelIndex in labels) {
            // if not hidden
            if (!data[dataType][0][labelIndex][2])
              tableheadercontent.append($('<th/>').addClass('text-capitalize').text(labels[labelIndex]));
          }
          const tablebodycontent = $('<tbody/>');
          for (let i = 0; i < data[dataType].length; i++) {
            const row = $('<tr/>').attr('orderreference', data[dataType][i][0][1]).attr('ordertype', dataType);
            const td = $('<td/>');

            td.append($('<input/>').attr({
              'id': "cb_modaltable_" + dataType + "-" + i,
              'class': "cbox align-middle",
              'type': "checkbox",
              'aria-checked': "true",
              'checked': "true"
            }));
            row.append(td);

            for (let j = 0; j < labels.length; j++) {
              if (!data[dataType][i][j][2]) {
                if (data[dataType][i][j][0] == 'quantity') {
                  row.append($('<td class="align-middle"/><input type="number" value="' + parseFloat(data[dataType][i][j][1]) + '" id="quantity' + modal_table_row_index + '"/>'));
                } else if (data[dataType][i][j][0] === 'receipt date' || data[dataType][i][j][0] === 'end date') {
                  row.append($('<td class="align-middle"/><input type="datetime-local" value="' + data[dataType][i][j][1] + '" title="due date" required="" id="due' + modal_table_row_index + '"></modal_table_row_indexnput>'));
                } else if (data[dataType][i][j][0] == 'supplier') {
                  row.append($('<td class="align-middle"/><input type="text" value="' + data[dataType][i][j][1] + '" title="supplier" required="" id="supplier' + modal_table_row_index + '"></input>'));
                } else {
                  row.append($('<td class="align-middle"/>').text(formatValue(data[dataType][i][j])));
                }
              }
            };
            tablebodycontent.append(row);
            modal_table_row_index++;
          }

          $('#popup #exporttable_' + dataType).append(tablebodycontent);
          $('#popup #exporttable_' + dataType + ' thead').append(tableheadercontent);

          $("#cb_modaltableall_" + dataType).click(function () {
            if ($("#cb_modaltableall_" + dataType).prop("checked")) {
              $("#exporttable_" + dataType + " input[type=checkbox]").prop("checked", $(this).prop("checked"));
            } else {
              $("#exporttable_" + dataType + " tbody tr input:not(:checked)").prop("checked", true);
              $("#exporttable_" + dataType + " tbody tr input:not(:checked)").parent().parent().removeClass("active").addClass("active")
            }
            $("#exporttable_" + dataType + " input[type=checkbox]").prop("checked", $(this).prop("checked"));
            if ($("#popup .modal-body tbody input[type=checkbox]:checked").length > 0) {
              $('#button_export').prop('disabled', false);;
            } else {
              $('#button_export').prop('disabled', true);
            };
          });
          $("#exporttable_" + dataType + " tbody input[type=checkbox]").click(function () {
            $(this).parent().parent().toggleClass('selected');
            $("#cb_modaltableall_" + dataType).prop("checked", $("#exporttable_" + dataType + " tbody input[type=checkbox]:not(:checked)").length == 0);
            if ($("#popup .modal-body tbody input[type=checkbox]:checked").length > 0) {
              $('#button_export').prop('disabled', false);;
            } else {
              $('#button_export').prop('disabled', true);
            };
          });
        }

        $('#button_export').on('click', function () {
          //get selected row data
          const exportData = [];
          let cells = [];
          const cellsData = {};
          const rows = $('#popup .modal-body tbody input[type=checkbox]:checked').parent().parent();

          index = 0;
          for (const row of rows) {
            let date = '.modal-body #due' + index;
            let quantity = '.modal-body #quantity' + index;
            let supplier = '.modal-body #supplier' + index;

            // Always send seconds even if they are 0
            newDate = ($(date).val().length === 16) ? $(date).val() + ":00" : $(date).val();

            exportData.push({
              'reference': row.attributes.orderreference.value,
              'type': row.getAttribute('ordertype'),
              'quantity': Number($(quantity).val()),
              'enddate': newDate,
              'supplier': $(supplier).val()
            });
            index++;
          }

          $('#popup .modal-body').html(gettext('connecting') + '...');
          $.ajax({
            url: url_prefix + "/erp/upload/",
            data: JSON.stringify(exportData),
            type: "POST",
            contentType: "application/json",
            success: function () {
              $('#popup .modal-body').html(gettext("Export successful"));
              $('#cancelbutton').val(gettext('Close'));
              $('#button_export').prop('disabled', true);
              // Mark selected rows as "approved" if the original status was "proposed".
              for (var i in sel) {
                const cur = grid.jqGrid('getCell', sel[i], 'status');
                if (cur == 'proposed')
                  grid.jqGrid('setCell', sel[i], 'status', 'approved');
              };
            },
            error: function (result, stat, errorThrown) {
              if (result.status == 401) {
                location.reload();
                return;
              }
              $('#popup .modal-title').html(gettext("Error during export"));
              $('#popup .modal-header').addClass('bg-danger');
              $('#popup .modal-body').css({ 'overflow-y': 'auto' }).html('<div style="overflow-y:auto; height: 300px; resize: vertical">' + result.responseText + '</div>');
              $('#button_export').val(gettext('Retry'));
              $('#popup .modal-dialog').css({ 'visibility': 'visible' })
              $('#popup').modal('show');
            }
          });
        });


        if ($("#actions").length)
          $("#actions1 span").text($("#actionsul").children().first().text());
        if ($("#DRPactions").length)
          $("#DRPactions1 span").text($("#DRPactionsul").children().first().text());
      },
      error: function (result, stat, errorThrown) {
        if (result.status == 401) {
          location.reload();
          return;
        }
        $('#popup .modal-title').html(gettext("Error"));
        $('#popup .modal-header').addClass('bg-danger');
        $('#popup .modal-body').css({ 'overflow-y': 'auto' }).html('<div style="overflow-y:auto; height: 300px; resize: vertical">' + result.responseText + '</div>');
        $('#button_export').val(gettext('Retry'));
        $('#popup .modal-dialog').css({ 'visibility': 'visible' })
        $('#popup').modal('show');
      }
    });

  }
} //end Code for ERP integration


//----------------------------------------------------------------------------
// Code for reorderable widgets.
//----------------------------------------------------------------------------

var widget = {
  init: function (callback) {
    $(".widget-list").each(function () {
      Sortable.create($(this)[0], {
        group: "widgets",
        handle: ".widget-handle",
        animation: 100,
        onEnd: callback
      });
    });
  },

  getConfig: function () {
    var rows = [];
    $(".widget-list").each(function () {
      var row = {
        "name": $(this).attr("data-widget") || "",
        "cols": [{ "width": $(this).attr("data-widget-width") || 12, "widgets": [] }]
      };

      $(this).find(".widget").each(function () {
        row["cols"][0]["widgets"].push([
          $(this).attr("data-widget") || "",
          {
            "collapsed": $(this).find(".collapse.show").length == 0
          }
        ]);
      });
      rows.push(row);
    });
    return rows;
  }
};

//----------------------------------------------------------------------------
// Code for sending dashboard configuration to the server.
//----------------------------------------------------------------------------

var dashboard = {
  dragAndDrop: function () {

    $(".cockpitcolumn").each(function () {
      Sortable.create($(this)[0], {
        group: "widgets",
        handle: ".card-header",
        animation: 100,
        onEnd: function (e) { dashboard.save(); },
        delay: 1000
      });
    });

    $("#dashboard").each(function () {
      Sortable.create($(this)[0], {
        group: "cockpit",
        handle: "h1",
        animation: 100,
        onEnd: function (e) { dashboard.save(); },
        delay: 1000
      });
    });

    $(".panel-toggle").click(function () {
      var icon = $(this);
      icon.toggleClass("fa-minus fa-plus");
      icon.closest(".card").find(".card-body").toggle();
    });
    $(".panel-close").click(function () {
      $(this).closest(".card").remove();
      dashboard.save();
    });
  },

  save: function (reload) {
    // Loop over all rows
    var results = [];
    $("[data-cockpit-row]").each(function () {
      var rowname = $(this).attr("data-cockpit-row");
      var cols = [];
      // Loop over all columns in the row
      $(".cockpitcolumn", this).each(function () {
        var width = 12;
        if ($(this).hasClass("col-md-12"))
          width = 12;
        else if ($(this).hasClass("col-md-11"))
          width = 11;
        else if ($(this).hasClass("col-md-10"))
          width = 10;
        else if ($(this).hasClass("col-md-9"))
          width = 9;
        else if ($(this).hasClass("col-md-8"))
          width = 8;
        else if ($(this).hasClass("col-md-7"))
          width = 7;
        else if ($(this).hasClass("col-md-6"))
          width = 6;
        else if ($(this).hasClass("col-md-5"))
          width = 5;
        else if ($(this).hasClass("col-md-4"))
          width = 4;
        else if ($(this).hasClass("col-md-3"))
          width = 3;
        else if ($(this).hasClass("col-md-2"))
          width = 2;
        // Loop over all widgets in the column
        var widgets = [];
        $("[data-cockpit-widget]", this).each(function () {
          widgets.push([$(this).attr("data-cockpit-widget"), {}]);
        });
        cols.push({ 'width': width, 'widgets': widgets });
      });
      if (cols.length > 0)
        results.push({ 'rowname': rowname, 'cols': cols });
    });

    // Send to the server
    if (typeof url_prefix != 'undefined')
      var url = url_prefix + '/settings/';
    else
      var url = '/settings/';
    $.ajax({
      url: url,
      type: 'POST',
      contentType: 'application/json; charset=utf-8',
      data: JSON.stringify({ "freppledb.common.cockpit": results }),
      success: function () {
        if ($.type(reload) === "string")
          window.location.href = window.location.href;
      },
      error: ajaxerror
    });
  },

  customize: function (rowname) {
    // Detect the current layout of this row
    var layout = "";
    $("[data-cockpit-row='" + rowname + "'] .cockpitcolumn").each(function () {
      if (layout != "")
        layout += " - ";
      if ($(this).hasClass("col-md-12"))
        layout += "100%";
      else if ($(this).hasClass("col-md-11"))
        layout += "92%";
      else if ($(this).hasClass("col-md-10"))
        layout += "83%";
      else if ($(this).hasClass("col-md-9"))
        layout += "75%";
      else if ($(this).hasClass("col-md-8"))
        layout += "67%";
      else if ($(this).hasClass("col-md-7"))
        layout += "58%";
      else if ($(this).hasClass("col-md-6"))
        layout += "50%";
      else if ($(this).hasClass("col-md-5"))
        layout += "42%";
      else if ($(this).hasClass("col-md-4"))
        layout += "33%";
      else if ($(this).hasClass("col-md-3"))
        layout += "25%";
      else if ($(this).hasClass("col-md-2"))
        layout += "17%";
    });

    var txt = '<div class="modal-dialog">' +
      '<div class="modal-content">' +
      '<div class="modal-header">' +
      '<h5 class="modal-title">' + gettext("Customize a dashboard row") + '</h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>' +
      '</div>' +
      '<div class="modal-body">' +
      '<form class="form-horizontal">' +

      '<div class="row mb-3">' +
      '<label class="col-3 col-form-label" for="id_name" class="col-form-label">' + gettext("Name") + ':</label>' +
      '<div class="col-9">' +
      '<input id="id_name" class="form-control" type="text" value="' + rowname + '">' +
      '</div></div>' +

      '<div class="row mb-3">' +
      '<label class="col-3 col-form-label" for="id_layout2" class="col-form-label">' + gettext("Layout") + ':</label>' +
      '<div class="col-9 dropdown">' +
      '<button class="form-control dropdown-toggle w-100" id="id_layout2" name="layout" type="button" data-bs-toggle="dropdown" aria-haspopup="true">' +
      '<span id="id_layout">' + layout + '</span>&nbsp;<span class="caret"></span>' +
      '</button>' +
      '<ul class="dropdown-menu" aria-labelledby="id_layout" id="id_layoutul">' +
      '<li class="dropdown-header">' + gettext("Single column") + '</li>' +
      '<li><a class="dropdown-item" onclick="dashboard.setlayout(this)">100%</a></li>' +
      '<li class="divider"></li>' +
      '<li class="dropdown-header">' + gettext("Two columns") + '</li>' +
      '<li><a class="dropdown-item" onclick="dashboard.setlayout(this)">75% - 25%</a></li>' +
      '<li><a class="dropdown-item" onclick="dashboard.setlayout(this)">67% - 33%</a></li>' +
      '<li><a class="dropdown-item" onclick="dashboard.setlayout(this)">50% - 50%</a></li>' +
      '<li><a class="dropdown-item" onclick="dashboard.setlayout(this)">33% - 67%</a></li>' +
      '<li><a class="dropdown-item" onclick="dashboard.setlayout(this)">25% - 75%</a></li>' +
      '<li class="divider"></li>' +
      '<li class="dropdown-header">' + gettext("Three columns") + '</li>' +
      '<li><a class="dropdown-item" onclick="dashboard.setlayout(this)">50% - 25% - 25%</a></li>' +
      '<li><a class="dropdown-item" onclick="dashboard.setlayout(this)">33% - 33% - 33%</a></li>' +
      '<li class="divider"></li>' +
      '<li class="dropdown-header">' + gettext("Four columns") + '</li>' +
      '<li><a class="dropdown-item" onclick="dashboard.setlayout(this)">25% - 25% - 25% - 25%</a></li>' +
      '</ul></div>' +
      '</div>' +

      '<div class="row mb-3">' +
      '<label class="col-3 col-form-label" for="id_widget2" class="col-form-label">' + gettext("Add widget") + ':</label>' +
      '<div class="col-9 dropdown">' +
      '<button class="form-control dropdown-toggle w-100" id="id_widget2" type="button" data-bs-toggle="dropdown">' +
      '<span id="id_widget">-</span>&nbsp;<span class="caret"></span>' +
      '</button>' +
      '<ul class="dropdown-menu col-9" aria-labelledby="id_widget2" id="id_widgetul">';

    var numwidgets = hiddenwidgets.length;
    for (var i = 0; i < numwidgets; i++)
      txt += '<li><a class="dropdown-item" onclick="dashboard.setwidget(' + i + ')">' + hiddenwidgets[i][1] + '</a></li>';

    txt +=
      '</ul></div><span id="newwidgetname" style="display:none"></span>' +
      '</div>' +

      '</form></div>' +
      '<div class="modal-footer">' +
      '<input type="submit" role="button" onclick=\'hideModal("popup")\' class="btn btn-gray pull-left" data-bs-dismiss="modal" value="' + gettext('Cancel') + '">' +
      '<input type="submit" role="button" onclick=\'dashboard.saveCustomization("' + rowname + '")\' class="btn btn-primary pull-right" value="' + gettext('Save') + '">' +
      '<input type="submit" role="button" onclick=\'dashboard.addRow("' + rowname + '", false)\' class="btn btn-primary pull-right" value="' + gettext('Add new below') + '">' +
      '<input type="submit" role="button" onclick=\'dashboard.addRow("' + rowname + '", true)\' class="btn btn-primary pull-right" value="' + gettext('Add new above') + '">' +
      '<input type="submit" role="button" onclick=\'dashboard.deleteRow("' + rowname + '")\' class="btn btn-danger pull-right" value="' + gettext('Delete') + '">' +
      '</div>' +

      '</div></div></div>';

    $('#popup').html(txt);
    showModal('popup');
  },

  setlayout: function (elem) {
    $("#id_layout").text($(elem).text());
  },

  setwidget: function (idx) {
    $("#id_widget").text(hiddenwidgets[idx][1]);
    $("#newwidgetname").text(hiddenwidgets[idx][0]);
  },

  saveCustomization: function (rowname) {
    // Update the name
    var newname = $("#id_name").val();
    if (rowname != newname) {
      // Make sure name is unique
      var cnt = 2;
      while ($("[data-cockpit-row='" + newname + "']").length > 1)
        newname = $("#id_name").val() + ' - ' + (cnt++);

      // Update
      $("[data-cockpit-row='" + rowname + "'] .col-md-11 h1").text(newname);
      $("[data-cockpit-row='" + rowname + "'] h1 button").attr("onclick", "dashboard.customize('" + newname + "')");
      $("[data-cockpit-row='" + rowname + "'] .horizontal-form").attr("id", newname);
      $("[data-cockpit-row='" + rowname + "']").attr("data-cockpit-row", newname);
    }

    // Update the layout
    var newlayout = $("#id_layout").text().split("-");
    var colindex = 0;
    var lastcol = null;
    // Loop over existing columns
    $("[id='" + rowname + "'] .cockpitcolumn").each(function () {
      if (colindex < newlayout.length) {
        // Resize existing column
        lastcol = this;
        $(this).removeClass("col-md-1 col-md-2 col-md-3 col-md-4 col-md-5 col-md-6 col-md-7 col-md-8 col-md-9 col-md-10 col-md-11 col-md-12");
        $(this).addClass("col-md-" + Math.round(0.12 * parseInt(newlayout[colindex])));
      }
      else {
        // Remove this column, after moving all widgets to the previous column
        $("[data-cockpit-widget]", this).appendTo(lastcol);
        $(this).remove();
      }
      colindex++;
    });
    while (colindex < newlayout.length) {
      // Adding extra columns
      lastcol = $('<div class="cockpitcolumn col-md-' + Math.round(0.12 * parseInt(newlayout[colindex])) + ' col-sm-12"></div>').insertAfter(lastcol);
      colindex++;
    }

    // Adding new widget
    var newwidget = $("#newwidgetname").text();
    if (newwidget != '') {
      $('<div class="card"></div>').attr("data-cockpit-widget", newwidget).appendTo(lastcol);
      dashboard.save("true"); // Force reload of the page
    }
    else
      dashboard.save();

    // Almost done
    dashboard.dragAndDrop();
    hideModal('popup');
  },

  deleteRow: function (rowname) {
    $("[data-cockpit-row='" + rowname + "']").remove();
    dashboard.save();
    hideModal('popup');
  },

  addRow: function (rowname, position_above) {
    // Make sure name is unique
    var newname = $("#id_name").val();
    var cnt = 2;
    while ($("[data-cockpit-row='" + $.escapeSelector(newname) + "']").length >= 1)
      newname = $("#id_name").val() + ' - ' + (cnt++);

    // Build new content
    var newelements = '<div class="row" data-cockpit-row="' + newname + '">' +
      '<div class="col-md-11"><h1 style="float: left">' + newname + '</h1></div>' +
      '<div class="col-md-1"><h1 class="pull-right">' +
      '<button class="btn btn-sm btn-primary" onclick="dashboard.customize(\'' + newname + '\')" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="' + gettext("Customize") + '"><span class="fa fa-wrench"></span></button>' +
      '</h1></div>' +

      '<div class="horizontal-form" id="' + newname + '">';
    var newlayout = $("#id_layout").text().split("-");
    var newwidget = $("#newwidgetname").text();
    for (var i = 0; i < newlayout.length; i++) {
      newelements += '<div class="cockpitcolumn col-md-' + Math.round(0.12 * parseInt(newlayout[i])) + ' col-sm-12">';
      if (i == 0 && newwidget != '')
        newelements += '<div class="card" data-cockpit-widget="' + newwidget + '"></div>';
      newelements += '</div>';
    }
    newelements += '</div></div></div>';

    // Insert in page
    if (position_above)
      $("[data-cockpit-row='" + $.escapeSelector(rowname) + "']").first().before($(newelements));
    else
      $("[data-cockpit-row='" + $.escapeSelector(rowname) + "']").last().after($(newelements));

    // Almost done
    if (newwidget != '')
      // Force reload of the page when adding a widget
      dashboard.save("true");
    else
      dashboard.save();
    dashboard.dragAndDrop();
    hideModal('popup');
  }

}


function savePreference(setting, value, callback) {
  if (typeof url_prefix != 'undefined')
    var url = url_prefix + '/settings/';
  else
    var url = '/settings/';
  var data = {};
  data[setting] = value;
  $.ajax({
    url: url,
    type: 'POST',
    contentType: 'application/json; charset=utf-8',
    data: JSON.stringify(data),
    success: function () {
      if (typeof callback === 'function')
        callback();
    }
  });
}

function getUnreadMessages() {
  var msg = $("#messages");
  if (!msg.length) return;
  $.ajax({
    url: url_prefix + "/inbox/",
    type: "GET",
    contentType: "application/json",
    success: function (json) {
      var tt_el = msg.parent().parent();
      if (json.unread) {
        msg.removeClass("fa-envelope-open-o").addClass("fa-envelope-o");
        msg.next().text(json.unread);
        tt_el.attr("data-bs-title", interpolate(gettext("%s unread messages"), [json.unread]));
      }
      else {
        msg.removeClass("fa-envelope-o").addClass("fa-envelope-open-o");
        msg.next().text("");
        tt_el.attr("data-bs-title", gettext("No unread messages"));
      }
      var tt = bootstrap.Tooltip.getInstance(tt_el);
      if (tt) tt.dispose();
      bootstrap.Tooltip.getOrCreateInstance(tt_el);
    }
  });
}

$(function () {

  // Send django's CRSF token with every POST request to the same site
  $(document).ajaxSend(function (event, xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type) && sameOrigin(settings.url))
      xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
  });

  // Never cache ajax results
  $.ajaxSetup({ cache: false });

  getUnreadMessages();

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
  $('.search-input').typeahead({ minLength: 2 }, {
    limit: 1000,
    highlight: true,
    name: 'search',
    display: 'value',
    source: searchsource,
    templates: {
      suggestion: function (data) {
        if (data.value === null)
          return '<span><p style="margin-top: 5px; margin-bottom: 1px;">'
            + $.jgrid.htmlEncode(data.label)
            + '</p><li  role="separator" class="divider"></li></span>';
        var href = url_prefix + data.url;
        if (!data.removeTrailingSlash)
          href += admin_escape(data.value) + "/?noautofilter";
        else
          href += encodeURIComponent(data.value);
        return '<li><a href="' + href + '" >'
          + $.jgrid.htmlEncode(data.display)
          + '</a><div class="tt-external"><a target="_blank" href="' + href + '">'
          + '<i class="fa fa-external-link" aria-hidden="true"></i>'
          + '</a></div></li>';
      },
    }
  });

});


//----------------------------------------------------------------------------
// Cookie manipulation functions
//----------------------------------------------------------------------------

function getCookie(name) {
  var allcookies = document.cookie.split(';');
  var search = name + '=';
  for (var i = allcookies.length; i >= 0; i--)
    if (jQuery.trim(allcookies[i]).indexOf(search) == 0)
      return jQuery.trim(allcookies[i]).substr(search.length);
  return null;
}

function setCookie(name, value, days) {
  // When the expiry is unspecified, you get a cookie valid for the browser session
  var expires = "";
  if (days) {
    var date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + (value || "") + expires + "; path=/";
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

function about_show() {
  $.ajax({
    url: "/about/",
    type: "GET",
    contentType: "application/json",
    success: function (data) {
      hideModal('timebuckets');
      $.jgrid.hideModal("#searchmodfbox_grid");
      content = '<div class="modal-dialog">' +
        '<div class="modal-content">' +
        '<div class="modal-header">' +
        '<h5 class="modal-title">About frePPLe</h5>' +
        '<button type="button" class="btn-close" data-bs-dismiss="modal"></button>' +
        '</div>' +
        '<div class="modal-body">' +
        '<div class="row mb-3"><div class="col-6 fw-bold">Version</div>' +
        '<div class="col-6">' + data.version + ' ' + data.edition + '</div></div>' +
        '<div class="row mb-3"><div class="col-6 fw-bold">Storage</div>' +
        '<div class="col-6' + (data.storage_exceeded ? " text-danger" : "") + '">' + data.storage_used + ' used';
      if (data.storage_allocation)
        content += ' of ' + data.storage_allocation + ' allocated';
      content += '</div ></div > ' +
        '<div class="row"><div class="col-6 fw-bold">Active item locations</div><div class="col-6"><table class="table table-sm table-borderless">';
      for (const [db, sz] of Object.entries(data.itemlocations))
        content += "<tr><td>" + db + "</td><td>" + sz + '</td></tr>';
      content += '</table></div></div> ' +
        '<div class="row mb-3"><div class="col-6 fw-bold">Installed apps</div><div class="col-6">';
      for (var i of data.apps)
        content += i + '<br>';
      content += '</div></div></div></div></div>';
      $('#popup').html(content);
      showModal('popup');
    },
    error: ajaxerror
  });
}

function containsObject(obj, list) {
  var i;
  for (i = 0; i < list.length; i++) {
    if (list[i] === obj) {
      return true;
    }
  }

  return false;
}

function showModal(id, dispose = true, options = null) {
  var el = document.getElementById(id);
  if (dispose) {
    var p = bootstrap.Modal.getInstance(el);
    if (p) p.dispose();
  }
  var p = options ?
    bootstrap.Modal.getOrCreateInstance(el, options) :
    bootstrap.Modal.getOrCreateInstance(el);
  p.show();
}

function hideModal(id) {
  var el = document.getElementById(id);
  var p = bootstrap.Modal.getInstance(el);
  if (p) p.hide();
}

//----------------------------------------------------------------------------
// Display import dialog for CSV-files
//----------------------------------------------------------------------------

function import_show(title, paragraph, multiple, fxhr, initialDropped, buttonlabel) {
  var xhr = { abort: function () { } };

  hideModal('timebuckets');
  $.jgrid.hideModal("#searchmodfbox_grid");
  var modalcontent = '<div class="modal-dialog modal-lg">' +
    '<div class="modal-content">' +
    '<div class="modal-header">' +
    '<h5 class="modal-title">' +
    '<span id="modal_title">' + gettext("Import CSV or Excel file") + '</span>' + '&nbsp;' +
    '<span id="animatedcog" class="fa fa-cog fa-spin fa-2x fa-fw" style="visibility: hidden;"></span>' +
    '</h5>' +
    '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>' +
    '</div>' +
    '<div class="modal-body">' +
    '<form id="uploadform">' +
    '<p id="extra_text">' + gettext('Load an Excel file or a CSV-formatted text file.') + '<br>' +
    gettext('The first row should contain the field names.') + '<br><br>' +
    '<input class="form-check-input" type="checkbox" autocomplete="off" name="erase" value="yes" id="eraseBeforeImport"/><label for="eraseBeforeImport">&nbsp;&nbsp;' +
    gettext('First delete all existing records AND ALL RELATED TABLES') + '</label><br>' +
    '</p>';
  if (isDragnDropUploadCapable()) {
    modalcontent += '' +
      '<div class="box" style="outline: 2px dashed black; outline-offset: -1em">' +
      '<div class=text-center box__input" style="text-align: center; padding: 20px;">' +
      '<input class="box__file d-none" type="file" id="csv_file" name="csv_file" data-multiple-caption="{count} ' + gettext("files selected") + '" multiple/>' +
      '<label class="d-block p-3" id="uploadlabel" for="csv_file">' +
      '<a class="btn btn-primary">' + gettext("Select files to upload") +
      '</a>&nbsp;' + gettext("or drop them here") +
      '<i class="fa fa-sign-in fa-2x fa-rotate-90"></i>' +
      '</label>' +
      '</div>' +
      '<div class="d-none box__uploading" style="display: none;">Uploading&hellip;</div>' +
      '<div class="d-none box__success" style="display: none;">Done!</div>' +
      '<div class="box__error" style="display: none;">Error!<span></span>.</div>' +
      '</div>';
  } else {
    modalcontent += gettext('Data file') + ':<input type="file" id="csv_file" name="csv_file"/>';
  }
  modalcontent += '' +
    '<br></form>' +
    '<div style="margin: 5px 0">' +
    '<div id="uploadResponse" style="height: 50vh; resize: vertical; display: none; background-color: inherit; border: none; overflow: auto;"></div>' +
    '</div>' +
    '</div>' +
    '<div class="modal-footer justify-content-between">' +
    '<input type="submit" id="cancelbutton" role="button" class="btn btn-gray pull-left" data-bs-dismiss="modal" value="' + gettext('Close') + '">' +
    '<input type="submit" id="copytoclipboard" role="button" class="btn btn-gray pull-left" value="' + gettext('Copy to clipboard') + '" style="display: none;">' +
    '<input type="submit" id="importbutton" role="button" class="btn btn-primary pull-right" value="' + gettext('Import') + '">' +
    '<input type="submit" id="cancelimportbutton" role="button" class="btn btn-primary pull-left" value="' + gettext('Cancel Import') + '" style="display: none;">' +
    '</div>' +
    '</div>' +
    '</div>';
  $('#popup').html(modalcontent);
  showModal('popup');

  if (title !== '') {
    $("#modal_title").text(title);
  }
  if (typeof buttonlabel !== 'undefined') {
    $("#importbutton").val(buttonlabel);
  }
  if (paragraph === null) {
    $("#extra_text").remove();
  } else if (paragraph !== '') {
    $("#extra_text").text(paragraph);
  }

  var filesdropped = false;
  var filesselected = false;
  if (isDragnDropUploadCapable()) {
    $('.box').on('drag dragstart dragend dragover dragenter dragleave drop', function (e) {
      e.preventDefault();
      e.stopPropagation();
    })
      .on('dragover dragenter', function () {
        $('.box').removeClass('bg-warning').addClass('bg-warning');
      })
      .on('dragleave dragend drop', function () {
        $('.box').removeClass('bg-warning');
      })
      .on('drop', function (e) {
        if (multiple)
          filesdropped = e.originalEvent.dataTransfer.files;
        else
          filesdropped = [e.originalEvent.dataTransfer.files[0]];
        $("#uploadlabel").text(filesdropped.length > 1 ? ($("#csv_file").attr('data-multiple-caption') || '').replace('{count}', filesdropped.length) : filesdropped[0].name);
      });
  }
  $("#csv_file").on('change', function (e) {
    if (multiple)
      filesselected = e.target.files;
    else
      filesselected = [e.target.files[0]];
    $("#uploadlabel").text(filesselected.length > 1 ? ($("#csv_file").attr('data-multiple-caption') || '').replace('{count}', filesselected.length) : filesselected[0].name);
  });
  if (initialDropped !== null && typeof initialDropped !== 'undefined') {
    if (multiple)
      filesdropped = initialDropped;
    else
      filesdropped = [initialDropped[0]];
    $("#uploadlabel").text(
      filesdropped.length > 1 ?
        ($("#csv_file").attr('data-multiple-caption') || '').replace('{count}', filesdropped.length) :
        filesdropped[0].name
    );
  };
  $('#importbutton').on('click', function () {
    if ($("#csv_file").val() === "" && !filesdropped) {
      return;
    }
    var filesdata = '';

    $('#uploadResponse').css('display', 'block');
    $('#uploadResponse').html(gettext('Importing...'));
    $('#uploadResponse').on('scroll', function () {
      if (parseInt($('#uploadResponse').attr('data-scrolled')) !== $('#uploadResponse').scrollTop()) {
        $('#uploadResponse').attr('data-scrolled', true);
        $('#uploadResponse').off('scroll');
      }
    });
    $('#importbutton').hide();
    $("#animatedcog").css('visibility', 'visible');
    $('#uploadform').css('display', 'none');
    $('#copytoclipboard').on('click', function () {
      $("#uploadResponse").find("tr.hidden").remove();
      navigator.clipboard.writeText($("#uploadResponse").prop("innerText"));
    });
    $('#cancelimportbutton').show().on('click', function () {
      $("#uploadResponse").append('<div><strong>' + gettext('Canceled') + '</strong></div>');
      xhr.abort();
      $("#animatedcog").css('visibility', 'hidden');
      $("#uploadResponse").append(theclone.contents());
      $("#uploadResponse").scrollTop($("#uploadResponse")[0].scrollHeight);
      $('#cancelimportbutton').hide();
      $('#copytoclipboard').show();
    });

    // Prepare formdata
    filesdata = new FormData($("#uploadform")[0]);
    if (filesdropped) {
      $.each(filesdropped, function (i, fdropped) {
        filesdata.append(fdropped.name, fdropped);
      });
    }
    if (filesselected) {
      filesdata.delete('csv_file');
      $.each(filesselected, function (i, fdropped) {
        filesdata.append(fdropped.name, fdropped);
      });
    }

    // Upload the files
    xhr = $.ajax(
      Object.assign({
        type: 'post',
        url: typeof (url) != 'undefined' ? url : '',
        cache: false,
        data: filesdata,
        success: function (data) {
          var el = $('#uploadResponse');
          el.html(data);
          if (el.attr('data-scrolled') !== "true") {
            el.scrollTop(el[0].scrollHeight - el.height());
          }
          $('#cancelbutton').html(gettext('Close'));
          $('#importbutton').hide();
          $("#animatedcog").css('visibility', 'hidden');
          $('#cancelimportbutton').hide();
          if (document.queryCommandSupported('copy')) {
            $('#copytoclipboard').show();
          }
          $("#grid").trigger("reloadGrid");
        },
        xhrFields: {
          onprogress: function (e) {
            var el = $('#uploadResponse');
            el.html(e.currentTarget.response);
            var progress = el.find(".recordcount").last();
            var records = el.find("[data-cnt]").last().attr("data-cnt");
            progress.text(interpolate(gettext("%s records processed"), [records]));
            if (el.attr('data-scrolled') !== "true") {
              el.attr('data-scrolled', el[0].scrollHeight - el.height());
              el.scrollTop(el[0].scrollHeight - el.height());
            }
          }
        },
        error: function (result, stat, errorThrown) {
          if (result.status == 401) {
            location.reload();
            return;
          }
          $('#cancelimportbutton').hide();
          $('#copytoclipboard').show();
          $("#animatedcog").css('visibility', 'hidden');
          $("#uploadResponse").scrollTop($("#uploadResponse")[0].scrollHeight);
        },
        processData: false,
        contentType: false
      }, fxhr)
    );
  }
  );
}


//----------------------------------------------------------------------------
// This function returns all arguments in the current URL as a dictionary.
//----------------------------------------------------------------------------

function getURLparameters() {

  if (window.location.search.length == 0) return {};
  var params = {};
  jQuery.each(window.location.search.match(/^\??(.*)$/)[1].split('&'), function (i, p) {
    p = p.split('=');
    p[1] = unescape(p[1]).replace(/\+/g, ' ');
    params[p[0]] = params[p[0]] ? ((params[p[0]] instanceof Array) ? (params[p[0]].push(p[1]), params[p[0]]) : [params[p[0]], p[1]]) : p[1];
  });
  return params;
};


//----------------------------------------------------------------------------
// Dropdown list to select the model.
//----------------------------------------------------------------------------

function selectDatabase(el) {
  // Find new database and current database
  var db = el.getAttribute("data-database");

  // Change the location
  if (database == db)
    return;
  else if (database == 'default') {
    if (window.location.pathname == '/')
      window.location.href = "/" + db + "/";
    else
      window.location.href = window.location.href.replace(window.location.pathname, "/" + db + window.location.pathname);
  }
  else if (db == 'default')
    window.location.href = window.location.href.replace("/" + database + "/", "/");
  else
    window.location.href = window.location.href.replace("/" + database + "/", "/" + db + "/");
};


//----------------------------------------------------------------------------
// Jquery utility function to bind an event such that it fires first.
//----------------------------------------------------------------------------

$.fn.bindFirst = function (name, fn) {
  // bind as you normally would
  // don't want to miss out on any jQuery magic
  this.on(name, fn);

  // Thanks to a comment by @Martin, adding support for
  // namespaced events too.
  this.each(function () {
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

  header: function (margin, scale) {
    var el = $("#grid_graph");
    el.html("");
    var scale_stops = scale.range();
    var scale_width = scale.rangeBand();
    var svg = d3.select(el.get(0)).append("svg");
    svg.attr('height', '15px');
    svg.attr('width', Math.max(el.width(), 0));
    var wt = 0;
    for (var i in timebuckets) {
      var w = margin + scale_stops[i] + scale_width / 2;
      if (wt <= w) {
        var t = svg.append('text')
          .attr('class', timebuckets[i]['history'] ? 'svgheaderhistory' : 'svgheadertext')
          .attr('x', w)
          .attr('y', '12')
          .attr('data-bucket', i)
          .text(timebuckets[i]['name'])
          .on("mouseenter", function (d) {
            var bucket = parseInt($(this).attr("data-bucket"));
            var tiptext = "&nbsp;" + timebuckets[bucket]["startdate"] + ' - ' + timebuckets[bucket]["enddate"] + "&nbsp;";
            graph.showTooltip(tiptext.replaceAll(" 00:00:00", ""));
          })
          .on("mouseleave", graph.hideTooltip)
          .on("mousemove", graph.moveTooltip);
        wt = w + t.node().getComputedTextLength() + 12;
      }
    }
  },

  showTooltip: function (txt) {
    // Find or create the tooltip div
    var tt = d3.select("#tooltip");
    if (tt.empty())
      tt = d3.select("body")
        .append("div")
        .attr("id", "tooltip")
        .attr("role", "tooltip")
        .attr("class", "card p-2")
        .style("position", "absolute");

    // Update content and display
    tt.html('' + txt)
      .style('display', 'block');
    graph.moveTooltip();
  },

  hideTooltip: function () {
    d3.select("#tooltip").style('display', 'none');
    d3.event.stopPropagation();
  },

  moveTooltip: function () {
    var xpos = d3.event.pageX + 5;
    var ypos = d3.event.pageY - 28;
    var xlimit = $(window).width() - $("#tooltip").width() - 20;
    var ylimit = $(window).height() - $("#tooltip").height() - 20;
    if (xpos > xlimit) {
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

  miniAxis: function (s) {
    var sc = this.scale().range();
    var dm = this.scale().domain();
    // Draw the scale line
    s.append("path")
      .attr("class", "domain")
      .attr("d", "M-10 0 H0 V" + (sc[0] - 2) + " H-10");
    // Draw the maximum value
    s.append("text")
      .attr("x", -2)
      .attr("y", 13) // Depends on font size...
      .attr("text-anchor", "end")
      .text(grid.formatNumber(Math.round(dm[1])));
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

  // Height of the blocks
  rowsize: 25,

  header: function (el = "#jqgh_grid_operationplans") {
    // "scaling" stores the number of pixels available to show a day.
    var d = (viewend.getTime() - viewstart.getTime());
    var scaling = 86400000 / d * $(el).width();
    var total = (horizonend.getTime() - horizonstart.getTime()) / d * $(el).width();
    var result = [
      '<svg width="' + total + 'px" height="34px">',
      '<line class="time" x1="0" y1="17" x2="' + total + '" y2="17"/>'
    ];
    var x = 0;
    if (scaling < 5) {
      // Quarterly + monthly buckets
      var bucketstart = new Date(horizonstart.getFullYear(), horizonstart.getMonth(), 1);
      while (bucketstart < horizonend) {
        var x1 = (bucketstart.getTime() - viewstart.getTime()) / 86400000 * scaling;
        var bucketend = new Date(bucketstart.getFullYear(), bucketstart.getMonth() + 1, 1);
        var x2 = (bucketend.getTime() - viewstart.getTime()) / 86400000 * scaling;
        result.push('<text class="svgheadertext" x="' + Math.floor((x1 + x2) / 2) + '" y="31">' + moment(bucketstart).format("MMM") + '</text>');
        if (bucketstart.getMonth() % 3 == 0) {
          var quarterend = new Date(bucketstart.getFullYear(), bucketstart.getMonth() + 3, 1);
          x2 = (quarterend.getTime() - viewstart.getTime()) / 86400000 * scaling;
          var quarter = Math.floor((bucketstart.getMonth() + 3) / 3);
          result.push('<line class="time" x1="' + Math.floor(x1) + '" y1="0" x2="' + Math.floor(x1) + '" y2="34"/>');
          result.push('<text class="svgheadertext" x="' + Math.floor((x1 + x2) / 2) + '" y="13">' + bucketstart.getFullYear() + " Q" + quarter + '</text>');
        }
        else
          result.push('<line class="time" x1="' + Math.floor(x1) + '" y1="17" x2="' + Math.floor(x1) + '" y2="34"/>');
        bucketstart = bucketend;
      }
    }
    else if (scaling < 10) {
      // Monthly + weekly buckets, short style
      x -= horizonstart.getDay() * scaling;
      var bucketstart = new Date(horizonstart.getTime() - 86400000 * viewstart.getDay());
      while (bucketstart < horizonend) {
        result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling * 3.5) + '" y="31">' + moment(bucketstart).format("MM-DD") + '</text>');
        x = x + scaling * 7;
        bucketstart.setTime(bucketstart.getTime() + 86400000 * 7);
      }
      bucketstart = new Date(horizonstart.getFullYear(), horizonstart.getMonth(), 1);
      while (bucketstart < horizonend) {
        x1 = (bucketstart.getTime() - viewstart.getTime()) / 86400000 * scaling;
        bucketend = new Date(bucketstart.getFullYear(), bucketstart.getMonth() + 1, 1);
        x2 = (bucketend.getTime() - viewstart.getTime()) / 86400000 * scaling;
        result.push('<line class="time" x1="' + Math.floor(x1) + '" y1="0" x2="' + Math.floor(x1) + '" y2="17"/>');
        result.push('<text class="svgheadertext" x="' + Math.floor((x1 + x2) / 2) + '" y="13">' + moment(bucketstart).format("MMM YY") + '</text>');
        bucketstart = bucketend;
      }
    }
    else if (scaling < 20) {
      // Monthly + weekly buckets, long style
      x -= horizonstart.getDay() * scaling;
      var bucketstart = new Date(horizonstart.getTime() - 86400000 * horizonstart.getDay());
      while (bucketstart < horizonend) {
        result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        result.push('<text class="svgheadertext" x="' + (x + scaling * 7.0 / 2.0) + '" y="31">' + moment(bucketstart).format("YY-MM-DD") + '</text>');
        x = x + scaling * 7.0;
        bucketstart.setTime(bucketstart.getTime() + 86400000 * 7);
      }
      bucketstart = new Date(horizonstart.getFullYear(), horizonstart.getMonth(), 1);
      while (bucketstart < horizonend) {
        x1 = (bucketstart.getTime() - viewstart.getTime()) / 86400000 * scaling;
        bucketend = new Date(bucketstart.getFullYear(), bucketstart.getMonth() + 1, 1);
        x2 = (bucketend.getTime() - viewstart.getTime()) / 86400000 * scaling;
        result.push('<line class="time" x1="' + Math.floor(x1) + '" y1="0" x2="' + Math.floor(x1) + '" y2="17"/>');
        result.push('<text class="svgheadertext" x="' + Math.floor((x1 + x2) / 2) + '" y="13">' + moment(bucketstart).format("MMM YY") + '</text>');
        bucketstart = bucketend;
      }
    }
    else if (scaling <= 40) {
      // Weekly + daily buckets, short style
      var bucketstart = new Date(horizonstart.getTime());
      while (bucketstart < horizonend) {
        if (bucketstart.getDay() == 0) {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="0" x2="' + Math.floor(x) + '" y2="34"/>');
          result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling * 7 / 2) + '" y="13">' + moment(bucketstart).format("YY-MM-DD") + '</text>');
        }
        else {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        }
        result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling / 2) + '" y="31">' + moment(bucketstart).format("DD") + '</text>');
        x = x + scaling;
        bucketstart.setDate(bucketstart.getDate() + 1);
      }
    }
    else if (scaling <= 75) {
      // Weekly + daily buckets, long style
      var bucketstart = new Date(horizonstart.getTime());
      while (bucketstart < horizonend) {
        if (bucketstart.getDay() == 0) {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="0" x2="' + Math.floor(x) + '" y2="34"/>');
          result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling * 7 / 2) + '" y="13">' + moment(bucketstart).format("YY-MM-DD") + '</text>');
        }
        else {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        }
        result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling / 2) + '" y="31">' + moment(bucketstart).format("DD MM") + '</text>');
        x = x + scaling;
        bucketstart.setDate(bucketstart.getDate() + 1);
      }
    }
    else if (scaling < 350) {
      // Weekly + daily buckets, very long style
      var bucketstart = new Date(horizonstart.getTime());
      while (bucketstart < horizonend) {
        if (bucketstart.getDay() == 0) {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="0" x2="' + Math.floor(x) + '" y2="34"/>');
          result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling * 3.5) + '" y="13">' + moment(bucketstart).format("YY-MM-DD") + '</text>');
        }
        else
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling / 2) + '" y="31">' + moment(bucketstart).format("ddd DD MMM") + '</text>');
        x = x + scaling;
        bucketstart.setDate(bucketstart.getDate() + 1);
      }
    }
    else {
      // Daily + hourly buckets
      var bucketstart = new Date(horizonstart.getTime());
      while (bucketstart < horizonend) {
        if (bucketstart.getHours() == 0) {
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="0" x2="' + Math.floor(x) + '" y2="34"/>');
          result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling / 2) + '" y="13">' + moment(bucketstart).format("ddd YY-MM-DD") + '</text>');
        }
        else
          result.push('<line class="time" x1="' + Math.floor(x) + '" y1="17" x2="' + Math.floor(x) + '" y2="34"/>');
        result.push('<text class="svgheadertext" x="' + Math.floor(x + scaling / 48) + '" y="31">' + bucketstart.getHours() + '</text>');
        x = x + scaling / 24;
        bucketstart.setTime(bucketstart.getTime() + 3600000);
      }
    }
    result.push('</svg>');
    $(el).html(result.join(''));
  },

  redraw: function () {
    // Determine the conversion between svg units and the screen
    var scale = (horizonend.getTime() - horizonstart.getTime())
      / (viewend.getTime() - viewstart.getTime())
      * $("#jqgh_grid_operationplans").width() / 10000;
    $('.transformer').each(function () {
      var layers = $(this).attr("title");
      $(this).attr("transform", "scale(" + scale + ",1) translate(0," + ((layers - 1) * gantt.rowsize + 3) + ")");
    });
    gantt.header("#jqgh_grid_operationplans");
  },

  scroll: function (event) {
    var zone = viewend.getTime() - viewstart.getTime();
    viewstart.setTime(
      horizonstart.getTime()
      + $(event.target).scrollLeft() / event.target.scrollWidth * (horizonend.getTime() - horizonstart.getTime())
    );
    viewend.setTime(viewstart.getTime() + zone);
    // Determine the conversion between svg units and the screen
    var scale = (horizonend.getTime() - horizonstart.getTime()) / zone * $(event.target).width() / 10000;
    var offset = (horizonstart.getTime() - viewstart.getTime()) / (horizonend.getTime() - horizonstart.getTime()) * 10000;
    // Transform all svg elements
    $('.transformer').each(function () {
      var layers = $(this).attr("title");
      $(this).attr("transform", "scale(" + scale + ",1) translate(" + offset + "," + ((layers - 1) * gantt.rowsize + 3) + ")");
    });
  },

  zoom: function (zoom_in_or_out, el = "#jqgh_grid_operationplans") {
    // Determine the window to be shown. Min = 1 day. Max = 3 years.
    var zone = (viewend.getTime() - viewstart.getTime()) * zoom_in_or_out;
    if (zone >= horizonend.getTime() - horizonstart.getTime()) {
      viewstart.setTime(horizonstart.getTime());
      viewend.setTime(horizonend.getTime());
      zone = viewend.getTime() - viewstart.getTime();
    }
    else {
      viewend.setTime(viewstart.getTime() + zone);
      if (viewend.getTime() > horizonend.getTime()) {
        viewend.setTime(horizonend.getTime());
        viewstart.setTime(viewend.getTime() - zone);
      }
    }
    // Determine the conversion between svg units and the screen
    var scale = (horizonend.getTime() - horizonstart.getTime()) / zone * $(el).width() / 10000;
    var offset = (horizonstart.getTime() - viewstart.getTime()) / (horizonend.getTime() - horizonstart.getTime()) * 10000;
    // Transform all svg elements
    $('.transformer').each(function () {
      var layers = $(this).attr("title");
      $(this).attr("transform", "scale(" + scale + ",1) translate(" + offset + "," + ((layers - 1) * gantt.rowsize + 3) + ")");
    });
    // Redraw the header
    gantt.header(el);
  }
}

// Gauge for widgets on dashboard
// Copied from https://gist.github.com/tomerd/1499279

function Gauge(placeholderName, configuration) {
  this.placeholderName = placeholderName;

  var self = this; // for internal d3 functions

  this.configure = function (configuration) {
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

    this.config.greenColor = configuration.greenColor || "#109618";
    this.config.yellowColor = configuration.yellowColor || "#FF9900";
    this.config.redColor = configuration.redColor || "#DC3912";

    this.config.transitionDuration = configuration.transitionDuration || 500;
  }

  this.render = function () {
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

    for (var index in this.config.greenZones) {
      this.drawBand(this.config.greenZones[index].from, this.config.greenZones[index].to, self.config.greenColor);
    }

    for (var index in this.config.yellowZones) {
      this.drawBand(this.config.yellowZones[index].from, this.config.yellowZones[index].to, self.config.yellowColor);
    }

    for (var index in this.config.redZones) {
      this.drawBand(this.config.redZones[index].from, this.config.redZones[index].to, self.config.redColor);
    }

    if (undefined != this.config.label) {
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
    for (var major = this.config.min; major <= this.config.max; major += majorDelta) {
      var minorDelta = majorDelta / this.config.minorTicks;
      for (var minor = major + minorDelta; minor < Math.min(major + majorDelta, this.config.max); minor += minorDelta) {
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

      if (major == this.config.min || major == this.config.max) {
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
      .x(function (d) { return d.x })
      .y(function (d) { return d.y })
      .interpolate("basis");

    pointerContainer.selectAll("path")
      .data([pointerPath])
      .enter()
      .append("svg:path")
      .attr("d", pointerLine)
      .style("fill", "#dc3912")
      .style("stroke", "#c63310")
      .style("fill-opacity", 0.7);

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

  this.buildPointerPath = function (value) {
    var delta = this.config.range / 13;

    var head = valueToPoint(value, 0.85);
    var head1 = valueToPoint(value - delta, 0.12);
    var head2 = valueToPoint(value + delta, 0.12);

    var tailValue = value - (this.config.range * (1 / (270 / 360)) / 2);
    var tail = valueToPoint(tailValue, 0.28);
    var tail1 = valueToPoint(tailValue - delta, 0.12);
    var tail2 = valueToPoint(tailValue + delta, 0.12);

    return [head, head1, tail2, tail, tail1, head2, head];

    function valueToPoint(value, factor) {
      var point = self.valueToPoint(value, factor);
      point.x -= self.config.cx;
      point.y -= self.config.cy;
      return point;
    }
  }

  this.drawBand = function (start, end, color) {
    if (0 >= end - start) return;

    this.body.append("svg:path")
      .style("fill", color)
      .attr("d", d3.svg.arc()
        .startAngle(this.valueToRadians(start))
        .endAngle(this.valueToRadians(end))
        .innerRadius(0.65 * this.config.raduis)
        .outerRadius(0.85 * this.config.raduis))
      .attr("transform", function () { return "translate(" + self.config.cx + ", " + self.config.cy + ") rotate(270)" });
  }

  this.redraw = function (value, transitionDuration) {
    var pointerContainer = this.body.select(".pointerContainer");

    pointerContainer.selectAll("text").text(Math.round(value));

    var pointer = pointerContainer.selectAll("path");
    pointer.transition()
      .duration(undefined != transitionDuration ? transitionDuration : this.config.transitionDuration)
      //.delay(0)
      //.ease("linear")
      //.attr("transform", function(d)
      .attrTween("transform", function () {
        var pointerValue = value;
        if (value > self.config.max) pointerValue = self.config.max + 0.02 * self.config.range;
        else if (value < self.config.min) pointerValue = self.config.min - 0.02 * self.config.range;
        var targetRotation = (self.valueToDegrees(pointerValue) - 90);
        var currentRotation = self._currentRotation || targetRotation;
        self._currentRotation = targetRotation;

        return function (step) {
          var rotation = currentRotation + (targetRotation - currentRotation) * step;
          return "translate(" + self.config.cx + ", " + self.config.cy + ") rotate(" + rotation + ")";
        }
      });
  }

  this.valueToDegrees = function (value) {
    // thanks @closealert
    //return value / this.config.range * 270 - 45;
    return value / this.config.range * 270 - (this.config.min / this.config.range * 270 + 45);
  }

  this.valueToRadians = function (value) {
    return this.valueToDegrees(value) * Math.PI / 180;
  }

  this.valueToPoint = function (value, factor) {
    return {
      x: this.config.cx - this.config.raduis * factor * Math.cos(this.valueToRadians(value)),
      y: this.config.cy - this.config.raduis * factor * Math.sin(this.valueToRadians(value))
    };
  }

  // initialization
  this.configure(configuration);
}


function showModalImage(event, title) {
  var popup = $('#popup');
  popup.html(
    '<div class="modal-dialog modal-xl" style="margin-top: 20px; width:90%; margin-left: auto; margin-right: auto">'
    + '<div class="modal-content">'
    + '<div class="modal-header" style="border-top-left-radius: inherit; border-top-right-radius: inherit">'
    + '<button type="button" class="btn-close" data-bs-dismiss="modal"></button>'
    + '<h5 class="modal-title"></h5>'
    + '</div>'
    + '<div class="modal-body">'
    + '<img src="" style="width:100%">'
    + '</div>'
    + '</div>'
    + '</div>');
  popup.find("h4").text(title);
  popup.find("img").attr("src", $(event.target).attr("src"));
  showModal('popup');
  event.preventDefault();
}

/* Jquery extension to make an element draggable.
 * Copied from http://cssdeck.com/labs/wsse5ous
 */
$.fn.drags = function (opt) {

  opt = $.extend({ handle: "", cursor: "move" }, opt);

  if (opt.handle === "") {
    var $el = this;
  } else {
    var $el = this.find(opt.handle);
  }

  return $el
    .css('cursor', opt.cursor)
    .on("mousedown", function (e) {
      if (opt.handle === "")
        var $drag = $(this).addClass('draggable');
      else
        var $drag = $(this).addClass('active-handle').parent().addClass('draggable');
      var z_idx = $drag.css('z-index'),
        drg_h = $drag.outerHeight(),
        drg_w = $drag.outerWidth(),
        pos_y = $drag.offset().top + drg_h - e.pageY,
        pos_x = $drag.offset().left + drg_w - e.pageX;
      $drag.css('z-index', 1000).parents().on("mousemove", function (e) {
        $('.draggable').offset({
          top: e.pageY + pos_y - drg_h,
          left: e.pageX + pos_x - drg_w
        }).on("mouseup", function () {
          $(this).removeClass('draggable').css('z-index', z_idx);
        });
      });
      e.preventDefault(); // disable selection
    }).on("mouseup", function () {
      if (opt.handle === "") {
        $(this).removeClass('draggable');
      } else {
        $(this).removeClass('active-handle').parent().removeClass('draggable');
      }
    });
}

//  Follower functions

var follow = {
  setMethod: function (el) {
    var me = $(el);
    me.closest(".dropdown").find(".followerspan").text(me.text());
  },

  get: function (event, el) {
    var t = $(el);
    event.preventDefault();
    $.ajax({
      url: url_prefix + "/follow/",
      data: {
        "object_pk": t.attr("data-pk"),
        "model": t.attr("data-model"),
      },
      type: "GET",
      contentType: "application/json; charset=utf-8",
      success: function (data) {
        // Show dialog with detailed follower info
        hideModal('timebuckets');
        $.jgrid.hideModal("#searchmodfbox_grid");
        var dlg = $(
          '<div class="modal-dialog"><div class="modal-content">' +
          '<div class="modal-header">' +
          '<h5 class="modal-title"></h5>' +
          '<button type="button" class="btn-close" data-bs-dismiss="modal"></button>' +
          '</div>' +
          '<div class="modal-body">' +
          '<table id="follower_key" style="width:100%">' +
          '<tr><th>' + gettext("Follow") + '&nbsp;&nbsp;' +
          '<span class="dropdown">' +
          '<button class="form-control w-auto d-inline dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="true">' +
          '<span class="followerspan"></span>&nbsp;<span class="caret">' +
          '</button>' +
          '<ul class="dropdown-menu">' +
          '<li><a class="dropdown-item" href="#" onclick="follow.setMethod(this)">online</a></li>' +
          '<li><a class="dropdown-item" href="#" onclick="follow.setMethod(this)">email</a></li>' +
          '</ul></span>' +
          '</th></tr><tr><td id="follower_models" style="vertical-align:top"></td></tr>' +
          '</table>' +
          '</div>' +
          '<div class="modal-footer justify-content-between">' +
          '<input type="submit" role="button" class="btn btn-primary" data-bs-dismiss="modal" value="' + gettext('Close') + '">' +
          '<input type="submit" role="button" class="btn btn-primary" onclick="follow.post(event, this)" value="' + gettext('Update') + '">' +
          '</div>' +
          '</div></div>'
        );
        dlg.find(".modal-title")
          .text(interpolate(gettext("Manage notifications of %s"), [data.label + " " + data.object_pk], false));
        dlg.find(".followerspan").text(data.type);
        dlg.find("#follower_key")
          .attr("data-model", data.model)
          .attr("data-object_pk", data["object_pk"]);
        if (data.parents) {
          // You're already following it through another object
          for (var p of data.parents) {
            var e = $("<div style='margin-top:10px; margin-bottom:10px'>" + gettext("Following") + " " + p.model + " <a class='text-decoration-underline' target='_blank'></a></div>");
            e.find("a").attr("href", p.url).text(p.object_pk);
            e.find("a").append($("<i style='text-indent:0.5em' class='fa fa-external-link'></i>"));
            dlg.find("td").first().append(e);
          }
        }
        else if (data.models) {
          // You're directly following this object or not following it yet.
          for (var p of data.models) {
            var e = $("<div class='form-check'><label>"
              + "<input class='form-check-input' type='checkbox'/><span class='text-capitalize'></span>"
              + "</label></div>"
            );
            e.find("span").text(p.label);
            e.find("input").attr("data-model", p.model);
            if (p.checked) e.find("input").attr("checked", "true");
            dlg.find("td").first().append(e);
          }
        }
        if (data.users) {
          var e = $("<th></th>");
          e.text(gettext("Add followers"));
          dlg.find("th").after(e);
          e = $("<td id='follower_users' style='vertical-align:top'></td>");
          for (var u of data.users) {
            var e2 = $("<div class='form-check'><label>"
              + "<input  class='form-check-input' type='checkbox'/><span class='followername'></span>"
              + "</label>&nbsp;&nbsp;"
              + '<span class="dropdown">'
              + '<button class="form-control w-auto d-inline dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="true">'
              + '<span class="followerspan"></span>&nbsp;<span class="caret">'
              + '</button>'
              + '<ul class="dropdown-menu">'
              + '<li><a class="dropdown-item" href="#" onclick="follow.setMethod(this)">online</a></li>'
              + '<li><a class="dropdown-item" href="#" onclick="follow.setMethod(this)">email</a></li>'
              + '</ul></span>'
              + "</div>"
            );
            e2.find("input").attr("data-username", u.username);
            if (u.following != "no") e2.find("input").attr("checked", "true");
            e2.find(".followerspan").text(u.following == "email" ? "email" : "online");
            if (u.following == "indirect") {
              e2.find("input").attr("disabled", "disabled");
              e2.find(".dropdown").addClass("disabled");
            }
            e2.find("span.followername").text(u.username);
            e.append(e2);
          }
          dlg.find("td").after(e);
        }
        $('#popup').html(dlg);
        showModal('popup');
      },
      error: ajaxerror
    });
  },

  post: function () {
    var dlg = $("#popup");
    var key = dlg.find("#follower_key");
    var data = {
      "object_pk": key.attr("data-object_pk"),
      "model": key.attr("data-model"),
      "type": dlg.find("#follower_key .followerspan").text(),
      "users": {},
      "models": []
    };
    dlg.find("#follower_users input:checked").each(function () {
      if ($(this).attr("disabled") != "disabled")
        data["users"][$(this).attr("data-username")] = $(this).closest(".checkbox").find(".followerspan").text();
    });
    dlg.find("#follower_models input:checked").each(function () {
      data["models"].push($(this).attr("data-model"));
    });
    $.ajax({
      url: url_prefix + "/follow/",
      data: JSON.stringify([data]),
      type: "POST",
      contentType: "application/json",
      success: function () {
        hideModal('popup');
      },
      error: ajaxerror
    });
  }
}
