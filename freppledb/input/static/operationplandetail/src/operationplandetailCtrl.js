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
  $scope.detailposition = detailposition;
  $scope.operationplans = [];
  $scope.kanbanoperationplans = {};
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

  if (typeof $scope.displayongrid === 'function') {
    //watch is only needed if we can update the grid
    $scope.$watchGroup(
      ['operationplan.id', 'operationplan.start', 'operationplan.end', 'operationplan.quantity', 'operationplan.status', 'operationplan.quantity_completed', "operationplan.remark", "operationplan.loadplans", "operationplan.resource"],
      function (newValue, oldValue) {
        if (oldValue[0] === newValue[0] && newValue[0] !== -1 && typeof oldValue[0] !== 'undefined') {
          //is a change to the current operationplan
          if (typeof oldValue[1] !== 'undefined' && typeof newValue[1] !== 'undefined' && oldValue[1] !== newValue[1]) {
            if ($scope.mode == "kanban" || $scope.mode.startsWith("calendar"))
              $scope.$broadcast("selectedEdited", "startdate", oldValue[1], new Date($scope.operationplan.start));
            else
              $scope.displayongrid($scope.operationplan.id, "startdate", $scope.operationplan.start);
          }
          if (typeof oldValue[2] !== 'undefined' && typeof newValue[2] !== 'undefined' && oldValue[2] !== newValue[2]) {
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
          if (!isNaN(parseFloat(opplan[field[1]]))) {
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
    $scope.operationplan = new OperationPlan();
    aggregatedopplan.start = aggregatedopplan.startdate;
    aggregatedopplan.end = aggregatedopplan.enddate;
    aggregatedopplan.id = -1;
    aggregatedopplan.count = selectionData.length;
    aggregatedopplan.type = (selectionData.length > 0) ? selectionData[0].type : "";
    $scope.$apply(function () { $scope.operationplan.extend(aggregatedopplan); });
  }
  $scope.processAggregatedInfo = processAggregatedInfo;

  $scope.$on('updateCard', function (event, field, oldvalue, newvalue) {
    $scope.$apply(function () {
      $scope.$broadcast('selectedEdited', field, oldvalue, newvalue);
    });
  });

  function displayInfo(row) {
    if ($scope.mode == "kanban" && row === undefined) {
      $scope.loadKanbanData();
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
    $scope.operationplan = new OperationPlan();
    $scope.operationplan.id = rowid;

    function callback(opplan) {
      if (row === undefined)
        return opplan;

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

    if (typeof $scope.operationplan.id === 'undefined')
      $scope.$apply(function () { $scope.operationplan = new OperationPlan(); });
    else
      $scope.operationplan.get(callback);
  }
  $scope.displayInfo = displayInfo;

  function refreshstatus(value) {
    if (value !== 'no_action') {
      $scope.$apply(function () { $scope.operationplan.status = value; });
    }
  }
  $scope.refreshstatus = refreshstatus;

  function setMode(m) {
    function innerFunction() {
      PreferenceSvc.save("mode", m);
      $scope.$apply(function () {
        $scope.operationplan = null;
        $scope.mode = m;
      });
      angular.element('#controller').scope().$broadcast('changeMode', m);
      if (m == 'kanban') {
        $("#gridmode, #calendarmode").removeClass("active");
        $("#kanbanmode").addClass("active");
        mode = "kanban";
        $scope.loadKanbanData();
      }
      else if (m.startsWith('calendar')) {
        $("#kanbanmode, #gridmode").removeClass("active");
        $("#calendarmode").addClass("active");
        mode = m;
        // No need to call loadCalendarData since it's triggered automatically with the above $apply
      }
      else {
        $("#kanbanmode, #calendarmode").removeClass("active");
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
        '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary" value="' + gettext('Return to page') + '">' +
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

  function getDirtyCards() {
    var dirty = [];
    if ($scope.mode && $scope.mode.startsWith("calendar")) {
      angular.forEach($scope.calendarevents, function (card) {
        var dirtycard = { id: card.id || card.reference };
        var dirtyfields = false;
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
    }
    else if ($scope.mode == "kanban") {
      angular.forEach($scope.kanbanoperationplans, function (value, key) {
        angular.forEach(value.rows, function (card) {
          var dirtycard = { id: card.id || card.reference };
          var dirtyfields = false;
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

  // Initial display
  if (preferences && preferences.mode == "kanban") {
    $scope.loadKanbanData();
  }
}
