/*
 * Copyright (C) 2017 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 *
 */

'use strict';

angular.module('operationplandetailapp').controller('operationplandetailCtrl', operationplanCtrl);

operationplanCtrl.$inject = ['$scope', '$http', 'OperationPlan', 'PreferenceSvc'];

function operationplanCtrl($scope, $http, OperationPlan, PreferenceSvc) {
  $scope.operationplan = new OperationPlan();
  $scope.aggregatedopplan = null;
  $scope.mode = preferences ? preferences.mode : "table";
  $scope.preferences = preferences;
  $scope.operationplans = [];
  $scope.kanbanoperationplans = {};
  $scope.ganttoperationplans = {};
  $scope.deleted = [];
  $scope.kanbancolumns = preferences ? preferences.columns : undefined;
  if (!$scope.kanbancolumns)
    $scope.kanbancolumns = ["proposed", "approved", "confirmed", "completed", "closed"];
  $scope.groupBy = preferences ? preferences.groupBy : undefined;
  if (!$scope.groupBy) {
    if (typeof groupBy !== 'undefined')
      $scope.groupBy = groupBy;
    else
      $scope.groupBy = "status";
  }
  $scope.groupOperator = preferences ? preferences.groupOperator : undefined;
  if (!$scope.groupOperator)
    $scope.groupOperator = "eq";

  // This template function will pass the values to the grid, function(id,column,value)
  // will set the row as "edited", and trigger "save undo" buttons.
  // If the function does not exist it makes no sense to watch for changes on the bottom part.
  $scope.displayongrid = displayongrid;
  $scope.currentId = null;

  if (typeof $scope.displayongrid === 'function') {
    //watch is only needed if we can update the grid
    $scope.$watchGroup(
      ['operationplan.id', 'operationplan.start', 'operationplan.end', 'operationplan.quantity', 'operationplan.status', 'operationplan.quantity_completed', "operationplan.remark", "operationplan.loadplans", "operationplan.resource"],
      function (newValue, oldValue) {
        if (typeof newValue[0] == "string") {
          $scope.currentId = newValue[0];
        } else if (typeof $scope.operationplan.id == 'undefined') {
          $scope.operationplan.id = $scope.currentId;
        }
        if (oldValue[0] === newValue[0] && newValue[0] !== -1) {
          //is a change to the current operationplan
          if (typeof oldValue[1] !== 'undefined' && typeof newValue[1] !== 'undefined' && oldValue[1].toISOString() !== newValue[1].toISOString()) {
            if ($scope.mode == "kanban" || $scope.mode.startsWith("calendar"))
              $scope.$broadcast("selectedEdited", "startdate", oldValue[1], new Date($scope.operationplan.start));
            else
              $scope.displayongrid($scope.operationplan.id, "startdate", $scope.operationplan.start);
          }
          if (typeof oldValue[2] !== 'undefined' && typeof newValue[2] !== 'undefined' && oldValue[2].toISOString() !== newValue[2].toISOString()) {
            if ($scope.mode == "kanban" || $scope.mode.startsWith("calendar"))
              $scope.$broadcast("selectedEdited", "enddate", oldValue[2], new Date($scope.operationplan.end));
            else
              $scope.displayongrid($scope.operationplan.id, "enddate", $scope.operationplan.end);
          }
          if (typeof oldValue[3] !== 'undefined' && typeof newValue[3] !== 'undefined' && oldValue[3] !== newValue[3]) {
            if ($scope.mode == "kanban" || $scope.mode.startsWith("calendar"))
              $scope.$broadcast("selectedEdited", "quantity", oldValue[3], $scope.operationplan.quantity);
            else
              $scope.displayongrid($scope.operationplan.id, "quantity", $scope.operationplan.quantity);
          }
          if (typeof oldValue[4] !== 'undefined' && typeof newValue[4] !== 'undefined' && oldValue[4] !== newValue[4]) {
            if (actions.hasOwnProperty($scope.operationplan.status)) {
              if ($scope.mode == "kanban" || $scope.mode.startsWith("calendar"))
                $scope.$broadcast("selectedEdited", "status", oldValue[4], $scope.operationplan.status);
              else
                $scope.displayongrid($scope.operationplan.id, "status", $scope.operationplan.status);
            }
            else
              actions[Object.keys(actions)[0]]();
          }
          if (typeof oldValue[5] !== 'undefined' && typeof newValue[5] !== 'undefined' && oldValue[5] !== newValue[5]) {
            if ($scope.mode == "kanban" || $scope.mode.startsWith("calendar"))
              $scope.$broadcast("selectedEdited", "quantity_completed", oldValue[5], $scope.operationplan.quantity_completed);
            else
              $scope.displayongrid($scope.operationplan.id, "quantity_completed", $scope.operationplan.quantity_completed);
          }
          if (typeof oldValue[6] !== 'undefined' && typeof newValue[6] !== 'undefined' && oldValue[6] !== newValue[6]) {
            if ($scope.mode == "kanban" || $scope.mode.startsWith("calendar"))
              $scope.$broadcast("selectedEdited", "remark", oldValue[6], $scope.operationplan.remark);
            else
              $scope.displayongrid($scope.operationplan.id, "remark", $scope.operationplan.remark);
          }
        }
        oldValue[0] = newValue[0];

        widget.init(grid.saveColumnConfiguration);
      }); //end watchGroup
  }

  function processAggregatedInfo(selectionData, colModel) {
    var aggColModel = [];
    var aggregatedopplan = {};
    aggregatedopplan.colmodel = {};
    var temp = 0;
    angular.forEach(colModel, function (value, key) {
      if (value.hasOwnProperty('summaryType')) {
        aggColModel.push([key, value.name, value.summaryType, value.formatter]);
        aggregatedopplan[value.name] = null;
        aggregatedopplan.colmodel[value.name] = {
          'type': value.summaryType,
          'label': value.label,
          'formatter': value.formatter
        };
      }
    });
    angular.forEach(selectionData, function (opplan) {
      angular.forEach(aggColModel, function (field) {
        if (field[2] === 'sum') {
          if (field[3] === 'duration') {
            temp = new moment.duration(opplan[field[1]]).asSeconds();
            if (temp._d !== 'Invalid Date') {
              if (aggregatedopplan[field[1]] === null)
                aggregatedopplan[field[1]] = temp;
              else
                aggregatedopplan[field[1]] += temp;
            }
          }
          else if (!isNaN(parseFloat(opplan[field[1]]))) {
            if (aggregatedopplan[field[1]] === null) {
              aggregatedopplan[field[1]] = parseFloat(opplan[field[1]]);
            } else {
              aggregatedopplan[field[1]] += parseFloat(opplan[field[1]]);
            }
          }
        } else if (field[2] === 'max') {

          if (['color', 'number', 'currency'].indexOf(field[3]) !== -1 && opplan[field[1]] !== "") {
            if (parseFloat(opplan[field[1]])) {
              if (aggregatedopplan[field[1]] === null) {
                aggregatedopplan[field[1]] = parseFloat(opplan[field[1]]);
              } else {
                aggregatedopplan[field[1]] = Math.max(aggregatedopplan[field[1]], parseFloat(opplan[field[1]]));
              }
            }
          } else if (field[3] === 'duration') {
            temp = new moment.duration(opplan[field[1]]).asSeconds();
            if (temp._d !== 'Invalid Date') {
              if (aggregatedopplan[field[1]] === null) {
                aggregatedopplan[field[1]] = temp;
              } else {
                aggregatedopplan[field[1]] = Math.max(aggregatedopplan[field[1]], temp);
              }
            }
          } else if (field[3] === 'date') {
            temp = new moment(opplan[field[1]], datetimeformat);
            if (temp._d !== 'Invalid Date') {
              if (aggregatedopplan[field[1]] === null || temp.isAfter(aggregatedopplan[field[1]]))
                aggregatedopplan[field[1]] = temp;
            }
          }

        } else if (field[2] === 'min') {

          if (['color', 'number'].indexOf(field[3]) !== -1 && opplan[field[1]] !== "") {
            temp = parseFloat(opplan[field[1]]);
            if (!isNaN(temp)) {
              if (aggregatedopplan[field[1]] === null) {
                aggregatedopplan[field[1]] = temp;
              } else {
                aggregatedopplan[field[1]] = Math.min(aggregatedopplan[field[1]], temp);
              }
            }
          } else if (field[3] === 'duration') {
            temp = new moment.duration(opplan[field[1]]).asSeconds();
            if (temp._d !== 'Invalid Date') {
              if (aggregatedopplan[field[1]] === null) {
                aggregatedopplan[field[1]] = temp;
              } else {
                aggregatedopplan[field[1]] = Math.min(aggregatedopplan[field[1]], temp);
              }
            }
          } else if (field[3] === 'date') {
            temp = new moment(opplan[field[1]], datetimeformat);
            if (temp._d !== 'Invalid Date') {
              if (aggregatedopplan[field[1]] === null) {
                aggregatedopplan[field[1]] = temp;
              } else {
                aggregatedopplan[field[1]] = moment.min(aggregatedopplan[field[1]], temp);
              }
            }
          }

        }
      });
    });
    angular.forEach(aggColModel, function (field) {
      if (field[3] === 'duration')
        aggregatedopplan[field[1]] = formatDuration(aggregatedopplan[field[1]]);
    });
    $scope.operationplan = new OperationPlan();
    aggregatedopplan.start = aggregatedopplan.startdate || aggregatedopplan.operationplan__startdate;
    if (moment.isMoment(aggregatedopplan.start))
      aggregatedopplan.start = aggregatedopplan.start.toDate();
    aggregatedopplan.end = aggregatedopplan.enddate || aggregatedopplan.operationplan__enddate;
    if (moment.isMoment(aggregatedopplan.end))
      aggregatedopplan.end = aggregatedopplan.end.toDate();
    aggregatedopplan.id = -1;
    aggregatedopplan.count = selectionData.length;
    aggregatedopplan.type = (selectionData.length > 0) ? selectionData[0].type : "";
    if (!aggregatedopplan.count)
      angular.element(document).find("#delete_selected, #copy_selected, #edit_selected").prop("disabled", true);
    $scope.$apply(function () { $scope.operationplan.extend(aggregatedopplan); });
  }
  $scope.processAggregatedInfo = processAggregatedInfo;

  $scope.$on('updateCard', function (event, field, oldvalue, newvalue) {
    $scope.$apply(function () {
      $scope.$broadcast('selectedEdited', field, oldvalue, newvalue);
    });
  });

  function zoom() {
    $scope.$apply(function () {
      $scope.$broadcast('zoom');
    });
  };
  $scope.zoom = zoom;

  function displayInfo(row) {
    if ($scope.mode == "kanban" && row === undefined) {
      $scope.loadKanbanData();
      return;
    }
    if ($scope.mode == "gantt" && row === undefined) {
      $scope.loadGanttData();
      return;
    }
    if ($scope.mode.startsWith("calendar") && row === undefined) {
      $scope.loadCalendarData();
      return;
    }
    var rowid = undefined;
    if (typeof row !== 'undefined') {
      if (row.hasOwnProperty('operationplan__reference'))
        rowid = row.operationplan__reference;
      else
        rowid = row.reference;
    }

    angular.element(document).find("#delete_selected, #copy_selected, #edit_selected").prop("disabled", false);

    function callback(opplan) {
      if (row === undefined)
        return opplan;
      if (opplan.hasOwnProperty("duplicated")) {
        opplan.reference = opplan.id = 'Copy of ' + opplan.duplicated;
        delete opplan.upstreamoperationplans;
        delete opplan.downstreamoperationplans;
        delete opplan.pegging_demand;
      }

      // load previous changes from grid
      if (row.operationplan__startdate !== undefined && row.operationplan__startdate !== '')
        opplan.start = row.operationplan__startdate;
      else if (row.startdate !== undefined && row.startdate !== '')
        opplan.start = row.startdate;
      if (row.operationplan__enddate !== undefined && row.operationplan__enddate !== '')
        opplan.end = row.operationplan__enddate;
      else if (row.enddate !== undefined && row.enddate !== '')
        opplan.end = row.enddate;
      if (row.operationplan__quantity !== undefined && row.operationplan__quantity !== '')
        opplan.quantity = parseFloat(row.operationplan__quantity);
      else if (row.quantity !== undefined && row.quantity !== '')
        opplan.quantity = parseFloat(row.quantity);
      if (row.operationplan__status !== undefined && row.operationplan__status !== '')
        opplan.status = row.operationplan__status;
      else if (row.status !== undefined && row.status !== '')
        opplan.status = row.status;
      if (row.operationplan__quantity_completed !== undefined && row.operationplan__quantity_completed !== '')
        opplan.quantity_completed = parseFloat(row.operationplan__quantity_completed);
      else if (row.quantity_completed !== undefined && row.quantity_completed !== '')
        opplan.quantity_completed = parseFloat(row.quantity_completed);
      if (opplan.invstatus !== undefined) opplan.invstatus.pipeline = 0;

      // Assure data type
      if ($scope.operationplan.hasOwnProperty("start") && !($scope.operationplan.start instanceof Date))
        $scope.operationplan.start = moment($scope.operationplan.start, datetimeformat).toDate();
      if ($scope.operationplan.hasOwnProperty("end") && !($scope.operationplan.end instanceof Date))
        $scope.operationplan.end = moment($scope.operationplan.end, datetimeformat).toDate();
      if ($scope.operationplan.hasOwnProperty("operationplan__startdate") && !($scope.operationplan.operationplan__startdate instanceof Date))
        $scope.operationplan.operationplan__startdate = moment($scope.operationplan.operationplan__startdate, datetimeformat).toDate();
      if ($scope.operationplan.hasOwnProperty("operationplan__enddate") && !($scope.operationplan.operationplan__enddate instanceof Date))
        $scope.operationplan.operationplan__enddate = moment($scope.operationplan.operationplan__enddate, datetimeformat).toDate();
    }

    if (row && row.hasOwnProperty("duplicated")) {
      $scope.operationplan = new OperationPlan(row);
      $scope.operationplan.id = row.duplicated;
      $scope.operationplan.get(callback);
    }
    else {
      if ($scope.operationplan === null || typeof ($scope.operationplan) !== 'object')
        $scope.operationplan = new OperationPlan();
      $scope.operationplan.id = rowid;
      if (typeof $scope.operationplan.id === 'undefined')
        $scope.$apply(function () {
          angular.element(document).find("#delete_selected, #copy_selected, #edit_selected").prop("disabled", true);
          $scope.operationplan = new OperationPlan();
        });
      else
        $scope.operationplan.get(callback);
    }
  }
  $scope.displayInfo = displayInfo;

  function refreshstatus(value) {
    if (value !== 'no_action') {
      $scope.$apply(function () { $scope.operationplan.status = value; });
    }
  }
  $scope.refreshstatus = refreshstatus;

  function toggleShowTop(v) {
    showTop = !showTop;
    PreferenceSvc.save("showTop", showTop, function () { location.reload(); });

  }
  $scope.toggleShowTop = toggleShowTop;

  function toggleShowChildren(v) {
    showChildren = !showChildren;
    PreferenceSvc.save("showChildren", showChildren, function () { location.reload(); });
  }
  $scope.toggleShowChildren = toggleShowChildren;

  function setMode(m) {
    function innerFunction() {
      PreferenceSvc.save("mode", m);
      $scope.$apply(function () {
        $scope.operationplan = null;
        $scope.mode = m;
      });
      if (m == "gantt")
        $("#zoomin, #zoomout").removeClass("d-none");
      else
        $("#zoomin, #zoomout").addClass("d-none");
      angular.element('#controller').scope().$broadcast('changeMode', m);
      if (m == 'kanban') {
        $("#gridmode, #calendarmode, #ganttmode").removeClass("active");
        $("#kanbanmode").addClass("active");
        mode = "kanban";
        $scope.loadKanbanData();
      }
      else if (m == 'gantt') {
        $("#gridmode, #calendarmode, #kanbanmode").removeClass("active");
        $("#ganttmode").addClass("active");
        mode = "gantt";
        $scope.loadGanttData();
      }
      else if (m.startsWith('calendar')) {
        $("#kanbanmode, #gridmode, #ganttmode").removeClass("active");
        $("#calendarmode").addClass("active");
        mode = m;
        // No need to call loadCalendarData since it's triggered automatically with the above $apply
      }
      else {
        $("#kanbanmode, #calendarmode, #ganttmode").removeClass("active");
        $("#gridmode").addClass("active");
        mode = "grid";
        angular.element(document).find("#grid").jqGrid("GridUnload");
        // $("#jqgrid").jqGrid('setGridParam', {datatype:'json'}).trigger('reloadGrid');

        // We could deallocate the kanban cards, but that can be slow.
        // $scope.kanbanoperationplans = {};
        initialfilter = thefilter;
        displayGrid(true);
      }
      setHeights();
    }

    var save_button = angular.element(document).find("#save");
    if ($scope.mode != m && save_button.hasClass("btn-danger")) {
      $('#popup').html('<div class="modal-dialog">' +
        '<div class="modal-content">' +
        '<div class="modal-header alert-warning" style="border-top-left-radius: inherit; border-top-right-radius: inherit">' +
        '<h5 class="modal-title">' + gettext("Save or cancel your changes first") + '</h5>' +
        '</div>' +
        '<div class="modal-body">' +
        gettext("There are unsaved changes on this page.") +
        '</div>' +
        '<div class="modal-footer justify-content-between">' +
        '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary" data-bs-dismiss="modal" value="' + gettext('Return to page') + '">' +
        '<input type="submit" id="savebutton" role="button" class="btn btn-danger" value="' + gettext('Save') + '">' +
        '</div>' +
        '</div>' +
        '</div>'
      );
      showModal('popup');
      $('#savebutton').on('click', function () {
        save_button.trigger('click');
        innerFunction();
        hideModal('popup');
      });
      $('#cancelbutton').on('click', function () {
        hideModal('popup');
      });
      return false;
    }
    else {
      innerFunction();
      return true;
    }
  }
  $scope.setMode = setMode;

  function displayonpanel(rowid, columnid, value) {
    angular.element(document.getElementById($scope.operationplan.id)).removeClass("edited").addClass("edited");
    if (typeof $scope.operationplan.id !== 'undefined' && rowid === $scope.operationplan.id.toString()) {
      if (columnid === "startdate" || columnid === "operationplan__startdate") {
        $scope.$apply(function () {
          $scope.operationplan.start = value instanceof Date ? value : new Date(value);
        });
      }
      if (columnid === "enddate" || columnid === "operationplan__enddate") {
        $scope.$apply(function () {
          $scope.operationplan.end = value instanceof Date ? value : new Date(value);
        });
      }
      if (columnid === "quantity") {
        $scope.$apply(function () { $scope.operationplan.quantity = parseFloat(value); });
      }
      if (columnid === "status") {
        $scope.refreshstatus(value);
      }
      if (columnid === "quantity_completed") {
        $scope.$apply(function () { $scope.operationplan.quantity_completed = parseFloat(value); });
      }
    }
  }
  $scope.displayonpanel = displayonpanel;

  function formatInventoryStatus(opplan) {
    if (opplan.color === undefined || opplan.color === '')
      return [undefined, ""];
    var thenumber = parseInt(opplan.color);

    if (opplan.inventory_item || opplan.leadtime) {
      if (!isNaN(thenumber)) {
        if (thenumber >= 100 && thenumber < 999999)
          return ["rgba(0,128,0,0.5)", Math.round(opplan.computed_color) + "%"];
        else if (thenumber === 0)
          return ["rgba(255,0,0,0.5)", Math.round(opplan.computed_color) + "%"];
        else if (thenumber === 999999)
          return [undefined, ""];
        else
          return ["rgba(255," + Math.round(thenumber / 100 * 255) + ",0,0.5)", Math.round(opplan.computed_color) + "%"];
      }
    } else {
      var thedelay = Math.round(parseInt(opplan.delay) / 8640) / 10;
      if (isNaN(thedelay))
        thedelay = Math.round(parseInt(opplan.operationplan__delay) / 8640) / 10;
      if (parseInt(opplan.criticality) === 999 || parseInt(opplan.operationplan__criticality) === 999)
        return [undefined, ""];
      else if (thedelay < 0)
        return ["rgba(0,128,0,0.5)", (-thedelay) + ' ' + gettext("days early")];
      else if (thedelay === 0)
        return ["rgba(0,128,0,0.5)", gettext("on time")];
      else if (thedelay > 0) {
        if (thenumber > 100 || thenumber < 0)
          return ["rgba(255,0,0,0.5)", thedelay + ' ' + gettext("days late")];
        else
          return ["rgba(255," + Math.round(thenumber / 100 * 255) + ",0,0.5)", thedelay + ' ' + gettext("days late")];
      }
    }
    return [undefined, ""];
  };

  $scope.calendarevents = [];
  $scope.calendarStart = null;
  $scope.calendarEnd = null;
  $scope.mode = preferences && preferences.mode || "table";

  function calendarRangeChanged(startdate, enddate) {
    $scope.calendarStart = startdate;
    $scope.calendarEnd = enddate;
    if ($scope.mode && $scope.mode.startsWith("calendar"))
      loadCalendarData();
  };
  $scope.calendarRangeChanged = calendarRangeChanged;

  function loadCalendarData(thefilter) {
    if (!thefilter) {
      var tmp = $('#grid').getGridParam("postData");
      if (tmp)
        thefilter = tmp.filters ? JSON.parse(tmp.filters) : initialfilter;
      else
        thefilter = initialfilter;
    }
    var sidx = $('#grid').getGridParam('sortname');
    var sortname = "";
    if (sidx !== '') {
      sortname = "&sidx=" + encodeURIComponent(sidx)
        + "&sord=" + encodeURIComponent($('#grid').getGridParam('sortorder'));
    }
    var baseurl = (location.href.indexOf("#") != -1 ? location.href.substr(0, location.href.indexOf("#")) : location.href)
      + (location.search.length > 0 ? "&format=calendar" : "?format=calendar")
      + "&calendarstart=" + moment($scope.calendarStart).format("YYYY-MM-DD%20HH:MM:SS")
      + "&calendarend=" + moment($scope.calendarEnd).format("YYYY-MM-DD%20HH:MM:SS")
      + sortname;
    $http.get(baseurl + "&filters=" + encodeURIComponent(JSON.stringify(thefilter)))
      .then(
        function success(response) {
          var tmp = angular.copy(response.data);
          for (var x of tmp.rows) {
            x.type = x.operationplan__type || x.type || default_operationplan_type;
            if (x.hasOwnProperty("enddate"))
              x.enddate = new Date(x.enddate);
            if (x.hasOwnProperty("operationplan__enddate")) {
              x.operationplan__enddate = new Date(x.operationplan__enddate);
              x.enddate = x.operationplan__enddate;
            }
            if (x.hasOwnProperty("startdate"))
              x.startdate = new Date(x.startdate);
            if (x.hasOwnProperty("operationplan__startdate")) {
              x.operationplan__startdate = new Date(x.operationplan__startdate);
              x.startdate = x.operationplan__startdate;
            }
            if (x.hasOwnProperty("quantity"))
              x.quantity = parseFloat(x.quantity);
            if (x.hasOwnProperty("operationplan__quantity"))
              x.operationplan__quantity = parseFloat(x.operationplan__quantity);
            if (x.hasOwnProperty("quantity_completed"))
              x.quantity_completed = parseFloat(x.quantity_completed);
            if (x.hasOwnProperty("operationplan__quantity_completed"))
              x.operationplan__quantity_completed = parseFloat(x.operationplan__quantity_completed);
            if (x.hasOwnProperty("operationplan__status"))
              x.status = x.operationplan__status;
            if (x.hasOwnProperty("operationplan__origin"))
              x.origin = x.operationplan__origin;
            [x.color, x.inventory_status] = formatInventoryStatus(x);
          }
          $scope.calendarevents = tmp.rows;
          $scope.totalevents = tmp.records;
        },
        function (err) {
          if (err.status == 401)
            location.reload();
        }
      );
  }
  $scope.loadCalendarData = loadCalendarData;

  function loadKanbanData(thefilter) {
    if (!thefilter) {
      var tmp = $('#grid').getGridParam("postData");
      if (tmp)
        thefilter = tmp.filters ? JSON.parse(tmp.filters) : initialfilter;
      else
        thefilter = initialfilter;
    }
    var sidx = $('#grid').getGridParam('sortname');
    var sortname = "";
    if (sidx !== '') {
      sortname = "&sidx=" + encodeURIComponent(sidx)
        + "&sord=" + encodeURIComponent($('#grid').getGridParam('sortorder'));
    }
    var baseurl = (location.href.indexOf("#") != -1 ? location.href.substr(0, location.href.indexOf("#")) : location.href)
      + (location.search.length > 0 ? "&format=kanban" : "?format=kanban");
    // TODO handle this filtering on the backend instead?
    angular.forEach($scope.kanbancolumns, function (key) {
      var colfilter = angular.copy(thefilter);
      var extrafilter = { field: $scope.groupBy, op: $scope.groupOperator, data: key };
      if (colfilter === undefined || colfilter === null) {
        // First filter
        colfilter = {
          "groupOp": "AND",
          "rules": [extrafilter],
          "groups": []
        };
      }
      else {
        if (colfilter["groupOp"] == "AND")
          // Add condition to existing and-filter
          colfilter["rules"].push(extrafilter);
        else
          // Wrap existing filter in a new and-filter
          colfilter = {
            "groupOp": "AND",
            "rules": [extrafilter],
            "groups": [colfilter]
          };
      }
      $http.get(baseurl + "&filters=" + encodeURIComponent(JSON.stringify(colfilter)) + sortname)
        .then(function (response) {
          var tmp = angular.copy(response.data);
          for (var x of tmp.rows) {
            x.type = x.operationplan__type || x.type || default_operationplan_type;
            if (x.hasOwnProperty("enddate"))
              x.enddate = new Date(x.enddate);
            if (x.hasOwnProperty("operationplan__enddate"))
              x.operationplan__enddate = new Date(x.operationplan__enddate);
            if (x.hasOwnProperty("startdate"))
              x.startdate = new Date(x.startdate);
            if (x.hasOwnProperty("operationplan__startdate"))
              x.operationplan__startdate = new Date(x.operationplan__startdate);
            if (x.hasOwnProperty("quantity"))
              x.quantity = parseFloat(x.quantity);
            if (x.hasOwnProperty("operationplan__quantity"))
              x.operationplan__quantity = parseFloat(x.operationplan__quantity);
            if (x.hasOwnProperty("quantity_completed"))
              x.quantity_completed = parseFloat(x.quantity_completed);
            if (x.hasOwnProperty("operationplan__quantity_completed"))
              x.operationplan__quantity_completed = parseFloat(x.operationplan__quantity_completed);
            if (x.hasOwnProperty("operationplan__status"))
              x.status = x.operationplan__status;
            if (x.hasOwnProperty("operationplan__origin"))
              x.origin = x.operationplan__origin;
            [x.color, x.inventory_status] = formatInventoryStatus(x);
          }
          $scope.kanbanoperationplans[key] = tmp;
        },
          function (err) {
            if (err.status == 401)
              location.reload();
          });
    });
  }
  $scope.loadKanbanData = loadKanbanData;

  function loadGanttData() {
    var tmp = $('#grid').getGridParam("postData");
    if (tmp)
      thefilter = tmp.filters ? JSON.parse(tmp.filters) : initialfilter;
    else
      thefilter = initialfilter;
    var sidx = $('#grid').getGridParam('sortname');
    var sortname = "";
    if (sidx !== '') {
      sortname = "&sidx=" + encodeURIComponent(sidx)
        + "&sord=" + encodeURIComponent($('#grid').getGridParam('sortorder'));
    }
    var baseurl = (location.href.indexOf("#") != -1 ? location.href.substr(0, location.href.indexOf("#")) : location.href)
      + (location.search.length > 0 ? "&format=gantt" : "?format=gantt")
      + sortname;
    $http.get(thefilter ?
      baseurl + "&filters=" + encodeURIComponent(JSON.stringify(thefilter)) :
      baseurl)
      .then(
        function success(response) {
          var tmp = angular.copy(response.data);
          for (var x of tmp.rows) {
            x.type = x.operationplan__type || x.type || default_operationplan_type;
            if (x.hasOwnProperty("enddate"))
              x.enddate = new Date(x.enddate);
            if (x.hasOwnProperty("operationplan__enddate")) {
              x.operationplan__enddate = new Date(x.operationplan__enddate);
              x.enddate = x.operationplan__enddate;
            }
            if (x.hasOwnProperty("startdate"))
              x.startdate = new Date(x.startdate);
            if (x.hasOwnProperty("operationplan__startdate")) {
              x.operationplan__startdate = new Date(x.operationplan__startdate);
              x.startdate = x.operationplan__startdate;
            }
            if (x.hasOwnProperty("quantity"))
              x.quantity = parseFloat(x.quantity);
            if (x.hasOwnProperty("operationplan__quantity"))
              x.operationplan__quantity = parseFloat(x.operationplan__quantity);
            if (x.hasOwnProperty("quantity_completed"))
              x.quantity_completed = parseFloat(x.quantity_completed);
            if (x.hasOwnProperty("operationplan__quantity_completed"))
              x.operationplan__quantity_completed = parseFloat(x.operationplan__quantity_completed);
            if (x.hasOwnProperty("operationplan__status"))
              x.status = x.operationplan__status;
            if (x.hasOwnProperty("operationplan__origin"))
              x.origin = x.operationplan__origin;
            [x.color, x.inventory_status] = formatInventoryStatus(x);
          }
          $scope.ganttoperationplans = tmp;
        },
        function (err) {
          if (err.status == 401)
            location.reload();
        }
      );
  }
  $scope.loadGanttData = loadGanttData;

  function getDirtyCards() {
    var dirty = [];
    if ($scope.mode && $scope.mode.startsWith("calendar")) {
      angular.forEach($scope.calendarevents, function (card) {
        var dirtycard = { id: card.id || card.reference };
        var dirtyfields = false;
        if (card.duplicated) {
          var data = {
            "quantity": card.quantity,
            "startdate": new moment(card.operationplan__startdate || card.startdate).format('YYYY-MM-DD HH:mm:ss'),
            "enddate": new moment(card.operationplan__enddate || card.enddate).format('YYYY-MM-DD HH:mm:ss'),
            "status": card.status,
            "type": card.type
          };
          if (card.type == "PO") {
            data["supplier"] = card.operationplan__supplier__name || card.supplier;
            data["location"] = card.operationplan__location__name || card.location;
            data["item"] = card.operationplan__item__name || card.item;
          }
          else if (card.type == "DO") {
            data["origin"] = card.operationplan__origin__name || card.origin;
            data["destination"] = card.operationplan__destination__name || card.destination;
            data["item"] = card.operationplan__item__name || card.item;
          }
          else if (card.type == "MO")
            data["operation"] = card.operationplan__operation__name || card.operation;
          if (card.resource)
            data["resource"] = card.resource
          dirty.push(data);
        }
        else {
          if (card.hasOwnProperty("operationplan__reference"))
            dirtycard["operationplan__reference"] = card.operationplan__reference;
          for (var field in card) {
            if (card.hasOwnProperty(field + "Original")) {
              dirtyfields = true;
              if (card[field] instanceof Date)
                dirtycard[field] = new moment(card[field]).format('YYYY-MM-DD HH:mm:ss');
              else
                dirtycard[field] = card[field];
            }
          }
          if (dirtyfields)
            dirty.push(dirtycard);
        }
      });
    }
    else if ($scope.mode == "kanban") {
      angular.forEach($scope.kanbanoperationplans, function (value, key) {
        angular.forEach(value.rows, function (card) {
          var dirtycard = { id: card.id || card.reference };
          var dirtyfields = false;
          if (card.duplicated) {
            var data = {
              "quantity": card.quantity,
              "startdate": new moment(card.operationplan__startdate || card.startdate).format('YYYY-MM-DD HH:mm:ss'),
              "enddate": new moment(card.operationplan__enddate || card.enddate).format('YYYY-MM-DD HH:mm:ss'),
              "status": card.operationplan__status || card.status,
              "type": card.type
            };
            if (card.type == "PO") {
              data["supplier"] = card.operationplan__supplier || card.supplier;
              data["location"] = card.operationplan__location || card.location;
              data["item"] = card.operationplan__item || card.item;
            }
            else if (card.type == "DO") {
              data["origin"] = card.operationplan__origin || card.origin;
              data["destination"] = card.operationplan__destination || card.destination;
              data["item"] = card.operationplan__item || card.item;
            }
            else if (card.type == "MO") {
              data["operation"] = card.operationplan__operation__name || card.operation;
            }
            dirty.push(data);
          }
          if (card.hasOwnProperty("operationplan__reference"))
            dirtycard["operationplan__reference"] = card.operationplan__reference;
          for (var field in card) {
            if (card.hasOwnProperty(field + "Original")) {
              dirtyfields = true;
              if (card[field] instanceof Date)
                dirtycard[field] = new moment(card[field]).format('YYYY-MM-DD HH:mm:ss');
              else
                dirtycard[field] = card[field];
            }
          }
          if (dirtyfields)
            dirty.push(dirtycard);
        });
      });
    }
    if ($scope.deleted && $scope.deleted.length) {
      dirty.push({ delete: $scope.deleted });
      $scope.deleted = [];
    }
    if (dirty != []) $scope.operationplan = undefined;
    return dirty;
  }
  $scope.getDirtyCards = getDirtyCards;

  function duplicateOperationPlan() {
    var duplicate = [];
    if ($scope.mode && $scope.mode.startsWith("calendar")) {
      $scope.$apply(function () {
        angular.forEach($scope.calendarevents, function (card) {
          if ($scope.operationplan.id == card.operationplan__reference ||
            $scope.operationplan.id == card.reference) {
            var clone = angular.copy(card);
            if (card.operationplan__reference) {
              if (!clone.hasOwnProperty("duplicated")) clone.duplicated = card.operationplan__reference;
              clone.operationplan__reference = (card.operationplan__reference && card.operationplan__reference.startsWith("Copy of"))
                ? card.operationplan__reference : ("Copy of " + card.operationplan__reference);
            }
            if (card.id) {
              if (!clone.hasOwnProperty("duplicated")) clone.duplicated = card.id;
              clone.id = (card.id && card.id.startsWith("Copy of"))
                ? card.id : ("Copy of " + card.id);
              clone.duplicated = card.duplicated ? card.duplicated : card.reference;
            }
            if (card.reference) {
              if (!clone.hasOwnProperty("duplicated")) clone.duplicated = card.reference;
              clone.reference = (card.reference && card.reference.startsWith("Copy of"))
                ? card.reference : ("Copy of " + card.reference);
            }
            clone.dirty = true;
            duplicate.push([card, clone]);
            $scope.totalevents += 1;
          }
        });
        for (var d of duplicate) {
          $scope.calendarevents.push(d[1]);
          $scope.$broadcast("duplicateOperationplan", d[0], d[1]);
        }
      });
      angular.element(document).find("#save, #undo")
        .removeClass("btn-primary btn-danger")
        .addClass("btn-danger")
        .prop("disabled", false);
      $(window).off('beforeunload', upload.warnUnsavedChanges);
      $(window).on('beforeunload', upload.warnUnsavedChanges);
    }
    else if ($scope.mode == "kanban") {
      $scope.$apply(function () {
        angular.forEach($scope.kanbanoperationplans, function (col) {
          duplicate = [];
          angular.forEach(col.rows, function (card) {
            if ($scope.operationplan.id == card.operationplan__reference ||
              $scope.operationplan.id == card.reference) {
              var clone = angular.copy(card);
              if (card.operationplan__reference) {
                if (!clone.hasOwnProperty("duplicated")) clone.duplicated = card.operationplan__reference;
                clone.operationplan__reference = (card.operationplan__reference && card.operationplan__reference.startsWith("Copy of"))
                  ? card.operationplan__reference : ("Copy of " + card.operationplan__reference);
              }
              if (card.id) {
                if (!clone.hasOwnProperty("duplicated")) clone.duplicated = card.id;
                clone.id = (card.id && card.id.startsWith("Copy of"))
                  ? card.id : ("Copy of " + card.id);
              }
              if (card.reference) {
                if (!clone.hasOwnProperty("duplicated")) clone.duplicated = card.reference;
                clone.reference = (card.reference && card.reference.startsWith("Copy of"))
                  ? card.reference : ("Copy of " + card.reference);
              }
              duplicate.push([card, clone]);
              clone.dirty = true;
            }
          });
          for (var d of duplicate) {
            col.rows.push(d[1]);
            $scope.$broadcast("duplicateOperationplan", d[0], d[1]);
          }
        });
        angular.element(document).find("#save, #undo")
          .removeClass("btn-primary btn-danger")
          .addClass("btn-danger")
          .prop("disabled", false);
        $(window).off('beforeunload', upload.warnUnsavedChanges);
        $(window).on('beforeunload', upload.warnUnsavedChanges);
      });
    }
  };
  $scope.duplicateOperationPlan = duplicateOperationPlan;

  function removeOperationPlan() {
    if (!$scope.operationplan || !$scope.operationplan.reference) return;
    if ($scope.mode && $scope.mode.startsWith("calendar")) {
      $scope.$apply(function () {
        $scope.calendarevents = $scope.calendarevents.filter(
          card => card.operationplan__reference != $scope.operationplan.reference
            && card.reference != $scope.operationplan.reference
        );
        $scope.deleted.push($scope.operationplan.reference);
        $scope.operationplan = new OperationPlan();
      });
      angular.element(document).find("#delete_selected, #copy_selected, #edit_selected").prop("disabled", true);
      angular.element(document).find("#save, #undo")
        .removeClass("btn-primary btn-danger")
        .addClass("btn-danger")
        .prop("disabled", false);
      $(window).off('beforeunload', upload.warnUnsavedChanges);
      $(window).on('beforeunload', upload.warnUnsavedChanges);
    }
    else if ($scope.mode && $scope.mode == "kanban") {
      $scope.$apply(function () {
        for (var col in $scope.kanbanoperationplans) {
          $scope.kanbanoperationplans[col].rows =
            $scope.kanbanoperationplans[col].rows.filter(
              card => card.operationplan__reference != $scope.operationplan.reference
                && card.reference != $scope.operationplan.reference
            );
        }
        $scope.deleted.push($scope.operationplan.reference);
        $scope.operationplan = new OperationPlan();
      });
      angular.element(document).find("#delete_selected, #copy_selected, #edit_selected").prop("disabled", true);
      angular.element(document).find("#save, #undo")
        .removeClass("btn-primary btn-danger")
        .addClass("btn-danger")
        .prop("disabled", false);
      $(window).off('beforeunload', upload.warnUnsavedChanges);
      $(window).on('beforeunload', upload.warnUnsavedChanges);
    }
  }
  $scope.removeOperationPlan = removeOperationPlan;

  // Initial display
  if (preferences) {
    if (preferences.mode == "kanban")
      $scope.loadKanbanData();
    else if (preferences.mode == "gantt")
      $scope.loadGanttData();
  }
}
