/*
 * Copyright (C) 2020 by frePPLe bv
 *
 * This file is a heavily modified version of the code published under
 * MIT license on https://github.com/twinssbc/AngularJS-ResponsiveCalendar.
 *
 * Copyright (c) 2014 twinssbc
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

angular.module('calendar', [])
  .constant('calendarConfig', {
    formatDay: 'd',
    formatDayHeader: 'EEE',
    formatDayTitle: 'MMMM dd, yyyy',
    formatWeekTitle: 'MMMM yyyy, Week w',
    formatMonthTitle: 'MMMM yyyy',
    formatWeekViewDayHeader: 'EEE d',
    formatHourColumn: 'ha',
    showWeeks: true
  })
  .controller('calendarController',
    ['$scope', '$attrs', '$parse', '$interpolate', '$log', 'dateFilter', 'gettextCatalog', 'calendarConfig', 'PreferenceSvc',
      function calendarController($scope, $attrs, $parse, $interpolate, $log, dateFilter, gettextCatalog, calendarConfig, PreferenceSvc) {
        'use strict';
        var self = this,
          ngModelCtrl = { $setViewValue: angular.noop };

        // Configuration attributes
        angular.forEach(['formatDay', 'formatDayHeader', 'formatDayTitle', 'formatWeekTitle', 'formatMonthTitle',
          'formatWeekViewDayHeader', 'formatHourColumn'], function (key, index) {
            self[key] = angular.isDefined($attrs[key]) ? $interpolate($attrs[key])($scope.$parent) : calendarConfig[key];
          });

        angular.forEach(['showWeeks'], function (key, index) {
          self[key] = angular.isDefined($attrs[key]) ? ($scope.$parent.$eval($attrs[key])) : calendarConfig[key];
        });

        self.hourParts = 3600;

        var unregisterFn = $scope.$parent.$watch($attrs.eventSource, function (value) {
          self.onEventSourceChanged(value);
        });

        $scope.$on('$destroy', unregisterFn);

        $scope.admin_escape = admin_escape;
        $scope.url_prefix = url_prefix;
        $scope.scrollBarWidth = getScrollBarWidth();
        $scope.calendarmode = calendarmode;
        $scope.grouping = grouping;
        $scope.groupingdir = groupingdir;
        $scope.grid = grid;
        $scope.groupingcfg = groupingcfg;

        $scope.calendarmodes = {
          'start': gettextCatalog.getString("View start events"),
          'end': gettextCatalog.getString("View end events"),
          'start_end': gettextCatalog.getString("View start and end events"),
          'duration': gettextCatalog.getString("View full duration")
        };

        function setCalendarMode(m) {
          $scope.calendarmode = m;
          PreferenceSvc.save("calendarmode", m);
        }
        $scope.setCalendarMode = setCalendarMode;

        function setGrouping(g) {
          $scope.grouping = g;
          PreferenceSvc.save("grouping", g);
          self._onDataLoaded();
        }
        $scope.setGrouping = setGrouping;

        function setGroupingDir(g) {
          $scope.groupingdir = g;
          PreferenceSvc.save("groupingdir", g);
          self._onDataLoaded();
        }
        $scope.setGroupingDir = setGroupingDir;

        if (angular.isDefined($attrs.initDate)) {
          self.currentCalendarDate = $scope.$parent.$eval($attrs.initDate);
        }
        if (!self.currentCalendarDate) {
          self.currentCalendarDate = currentdate;
          if ($attrs.ngModel && !$scope.$parent.$eval($attrs.ngModel)) {
            $parse($attrs.ngModel).assign($scope.$parent, self.currentCalendarDate);
          }
        }

        $scope.getHeight = function (headerheight) {
          if (preferences && preferences.details && preferences.details != "bottom") {
            var el = angular.element(document).find("#content-main");
            return Math.max(150, $(window).height() - el.offset().top - headerheight - 40);
          }
          else if (preferences && preferences['height'])
            return preferences['height'] - headerheight;
          else
            return 220 - headerheight;
        }

        $scope.displayEvent = function (opplan, dt) {
          switch ($scope.calendarmode) {
            case "duration":
              return true;
            case "start_end":
              return moment(
                opplan.operationplan__startdate || opplan.startdate
                || opplan.operationplan__enddate || opplan.enddate
              ).isSame(dt.date, "day")
                || moment(
                  opplan.operationplan__enddate || opplan.enddate
                  || opplan.operationplan__startdate || opplan.startdate
                ).isSame(dt.date, "day");
            case "start":
              return moment(
                opplan.operationplan__startdate || opplan.startdate
                || opplan.operationplan__enddate || opplan.enddate
              ).isSame(dt.date, "day");
            case "end":
              return moment(
                opplan.operationplan__enddate || opplan.enddate
                || opplan.operationplan__startdate || opplan.startdate
              ).isSame(dt.date, "day");
          }
        }

        $scope.isStart = function (opplan, dt) {
          var d = opplan.startdate || opplan.operationplan__startdate;
          if (!d)
            return false;
          else if (dt instanceof Date)
            return d.getFullYear() === dt.getFullYear() && d.getMonth() === dt.getMonth() && d.getDate() === dt.getDate();
          else
            return moment(d).isSame(dt.date, "day");
        }

        $scope.isEnd = function (opplan, dt) {
          var d = opplan.enddate || opplan.operationplan__enddate;
          if (!d)
            return false;
          // Subtract 1 microsecond to assure that an end date of 00:00:00 is seen
          // as ending on the previous day.
          if (d > (opplan.startdate || opplan.operationplan__startdate))
            d = new Date(d - 1);
          if (dt instanceof Date)
            return d.getFullYear() === dt.getFullYear() && d.getMonth() === dt.getMonth() && d.getDate() === dt.getDate();
          else
            return moment(d).isSame(dt.date, "day");
        }

        $scope.displayEvent = function (opplan, dt) {
          switch ($scope.calendarmode) {
            case "duration":
              return true;
            case "start_end":
              // Subtract 1 microsecond to assure that an end date of 00:00:00 is seen
              // as ending on the previous day.
              return (opplan.startdate ? moment(opplan.startdate).isSame(dt.date, "day") : false)
                || (opplan.enddate ? moment(opplan.enddate > opplan.startdate ? opplan.enddate - 1 : opplan.enddate).isSame(dt.date, "day") : false);
            case "start":
              return opplan.startdate ? moment(opplan.startdate).isSame(dt.date, "day") : false;
            case "end":
              // Subtract 1 microsecond to assure that an end date of 00:00:00 is seen
              // as ending on the previous day.
              return opplan.enddate ? moment(opplan.enddate > opplan.startdate ? opplan.enddate - 1 : opplan.enddate).isSame(dt.date, "day") : false;
          }
        }

        self.init = function (ngModelCtrl_) {
          ngModelCtrl = ngModelCtrl_;

          ngModelCtrl.$render = function () {
            self.render();
          };
        };

        self.render = function () {
          if (ngModelCtrl.$modelValue) {
            var date = new Date(ngModelCtrl.$modelValue),
              isValid = !isNaN(date);

            if (isValid) {
              this.currentCalendarDate = date;
            } else {
              $log.error('"ng-model" value must be a Date object, a number of milliseconds since 01.01.1970 or a string representing an RFC2822 or ISO 8601 date.');
            }
            ngModelCtrl.$setValidity('date', isValid);
          }
          this.refreshView();
        };

        self.refreshView = function () {
          if (this.mode) {
            this.range = this._getRange(this.currentCalendarDate);
            this._refreshView();
            this.rangeChanged();
          }
        };

        // Split array into smaller arrays
        self.split = function (arr, size) {
          var arrays = [];
          while (arr.length > 0) {
            arrays.push(arr.splice(0, size));
          }
          return arrays;
        };

        self.onEventSourceChanged = function (value) {
          self.eventSource = value;
          if (self._onDataLoaded) {
            self._onDataLoaded();
          }
        };

        $scope.move = function (direction) {
          var step = self.mode.step,
            currentCalendarDate = self.currentCalendarDate,
            year = currentCalendarDate.getFullYear() + direction * (step.years || 0),
            month = currentCalendarDate.getMonth() + direction * (step.months || 0),
            date = currentCalendarDate.getDate() + direction * (step.days || 0),
            firstDayInNextMonth;

          currentCalendarDate.setFullYear(year, month, date);
          if ($scope.mode === 'calendarmonth') {
            firstDayInNextMonth = new Date(year, month + 1, 1);
            if (firstDayInNextMonth.getTime() <= currentCalendarDate.getTime()) {
              self.currentCalendarDate = new Date(firstDayInNextMonth - 24 * 60 * 60 * 1000);
            }
          }
          ngModelCtrl.$setViewValue(self.currentCalendarDate);
          self.refreshView();
        };

        self.move = function (direction) {
          $scope.move(direction);
        };

        self.changeMode = function (m) {
          $scope.mode = m;
        };

        self.rangeChanged = function () {
          if ($scope.rangeChanged) {
            $scope.rangeChanged({
              startdate: this.range.startdate,
              enddate: this.range.enddate
            });
          }
          else
            console.error("No rangeChanged callback is registered");
        };
      }])
  .directive('calendar', function calendarDirective() {
    'use strict';
    return {
      restrict: 'EA',
      replace: true,
      templateUrl: '/static/operationplandetail/calendar.html',
      scope: {
        mode: '=',
        editable: '=',
        rangeChanged: '&',
        eventSelected: '&',
        timeSelected: '&'
      },
      require: ['calendar', '?^ngModel'],
      controller: 'calendarController',
      link: function (scope, element, attrs, ctrls) {
        var calendarCtrl = ctrls[0], ngModelCtrl = ctrls[1];
        var dropcallback;
        scope.curselected = null;

        if (ngModelCtrl)
          calendarCtrl.init(ngModelCtrl);

        scope.$on('selectedEdited', function (event, field, oldvalue, newvalue) {
          if (scope.curselected === null) return;
          if (scope.mode && !scope.mode.startsWith("calendar")) return;
          if (field == "loadplans") {
            // Special logic to convert from detail-opplan to card change
            var res = [];
            angular.forEach(newvalue, function (theloadplan) {
              res.push([theloadplan.resource.name, theloadplan.quantity]);
            });
            scope.changeCard(scope.curselected, "resource", scope.curselected.resource, res);
            scope.curselected["resource"] = res;
          }
          else {
            scope.changeCard(scope.curselected, field, oldvalue);
            scope.curselected[field] = newvalue;
          }
        });

        scope.$on('changeDate', function (event, direction) {
          calendarCtrl.move(direction);
        });

        scope.$on('eventSourceChanged', function (event, value) {
          calendarCtrl.onEventSourceChanged(value);
        });

        scope.selectCard = function (opplan) {
          if (scope.curselected) {
            if (scope.curselected.reference && scope.curselected.reference == opplan.reference && opplan.selected)
              return;
            if (scope.curselected.operationplan__reference && scope.curselected.operationplan__reference == opplan.reference && opplan.selected)
              return;
            delete scope.curselected.selected;
          }
          opplan.selected = true;
          scope.curselected = opplan;
          scope.eventSelected({ event: opplan });
          angular.element(document).find("#delete_selected, #gridactions").prop("disabled", false);
        };

        scope.changeCard = function (opplan, field, oldvalue, newvalue) {
          if (!opplan.hasOwnProperty(field + "Original"))
            opplan[field + "Original"] = oldvalue;
          opplan.dirty = true;
          angular.element(document).find("#save, #undo")
            .removeClass("btn-primary btn-danger")
            .addClass("btn-danger")
            .prop("disabled", false);
          $(window).off('beforeunload', upload.warnUnsavedChanges);
          $(window).on('beforeunload', upload.warnUnsavedChanges);
          if (newvalue !== undefined)
            scope.$parent.$broadcast("cardChanged", field, oldvalue, newvalue);
        };

        function HandlerDrop(event) {
          var dragstart = new Date(event.originalEvent.dataTransfer.getData("dragstart"));
          var dragend = new Date($(event.target).closest(".datecell").attr("data-date"));
          var dragreference = event.originalEvent.dataTransfer.getData("dragreference");
          var row_dragstart = event.originalEvent.dataTransfer.getData("dragrow");
          var row_dragend = $(event.target).closest("[data-row]").attr("data-row");

          // Validate the move
          if (scope.grouping === "resource" && row_dragstart == row_dragend && dragstart.getTime() === dragend.getTime()) {
            // No change of row or date, when grouping by resource
            event.preventDefault();
            return;
          } else if (scope.grouping !== "resource" && dragstart.getTime() === dragend.getTime()) {
            // No change of date
            event.preventDefault();
            row_dragend = row_dragstart; // Changing rows is only allowed when grouping by resource
            return;
          }

          scope.$apply(function () {
            for (var dragcard of scope.$parent.calendarevents) {
              if ((dragcard["id"] || dragcard["reference"]) == dragreference) {
                // Identified the card that is being dropped
                var changed = false;
                if (scope.isStart(dragcard, dragstart)) {
                  // Dragging the start date card
                  if (dragcard.hasOwnProperty("operationplan__startdate")) {
                    scope.changeCard(dragcard, "operationplan__startdate", dragcard.operationplan__startdate, dragend);
                    dragcard.operationplan__startdate = dragend;
                    dragcard.startdate = dragend;
                    if (dragcard.operationplan__enddate < dragend)
                      dragcard.operationplan__enddate = dragend;
                    changed = true;
                  }
                  else if (dragcard.hasOwnProperty("startdate")) {
                    scope.changeCard(dragcard, "startdate", dragcard.startdate, dragend);
                    dragcard.startdate = dragend;
                    if (dragcard.enddate < dragend)
                      dragcard.enddate = dragend;
                    changed = true;
                  }
                }
                else if (scope.isEnd(dragcard, dragstart)) {
                  // Dragging the end date card
                  if (dragcard.hasOwnProperty("operationplan__enddate")) {
                    scope.changeCard(dragcard, "operationplan__enddate", dragcard.operationplan__enddate, dragend);
                    dragcard.operationplan__enddate = dragend;
                    dragcard.enddate = dragend;
                    if (dragcard.operationplan__startdate > dragend)
                      dragcard.operationplan__startdate = dragend;
                    changed = true;
                  }
                  else if (dragcard.hasOwnProperty("enddate")) {
                    scope.changeCard(dragcard, "enddate", dragcard.enddate, dragend);
                    dragcard.enddate = dragend;
                    if (dragcard.startdate > dragend)
                      dragcard.startdate = dragend;
                    changed = true;
                  }
                }
                else {
                  // Dragging a card on an intermediate day
                  var delta = (dragend - dragstart) / 86400000.0;
                  if (dragcard.hasOwnProperty("operationplan__startdate")) {
                    var newstart = new Date(dragcard["operationplan__startdate"]);
                    newstart.setDate(dragcard["operationplan__startdate"].getDate() + delta);
                    scope.changeCard(dragcard, "operationplan__startdate", dragcard.operationplan__startdate, newstart);
                    dragcard.operationplan__startdate = newstart;
                    dragcard.startdate = newstart;
                    if (dragcard.operationplan__enddate < newstart)
                      dragcard.operationplan__enddate = dragend;
                    changed = true;
                  }
                  else if (dragcard.hasOwnProperty("startdate")) {
                    var newstart = new Date(dragcard["startdate"]);
                    newstart.setDate(dragcard["startdate"].getDate() + delta);
                    scope.changeCard(dragcard, "startdate", dragcard.startdate, newstart);
                    dragcard.startdate = newstart;
                    if (dragcard.enddate < newstart)
                      dragcard.enddate = newstart;
                    changed = true;
                  }
                }
                if (row_dragstart != row_dragend && dragcard.resource == row_dragstart) {
                  scope.changeCard(dragcard, "resource", dragcard.row_dragstart, row_dragend);
                  dragcard.resource = row_dragend;
                  changed = true;
                }
                if (changed && dropcallback) dropcallback(dragcard, true);
                break;
              }
            }
          });
          event.preventDefault();
        }

        function HandlerDragStart(event) {
          event.originalEvent.dataTransfer.setData(
            "dragstart",
            $(event.target).closest(".datecell").attr("data-date")
          );
          event.originalEvent.dataTransfer.setData(
            "dragreference",
            $(event.target).closest(".card").attr("data-reference")
          );
          event.originalEvent.dataTransfer.setData(
            "dragrow",
            $(event.target).closest("[data-row]").attr("data-row")
          );
          event.stopPropagation();
        };

        function HandlerDragOver(event) {
          event.preventDefault();
        };

        function enableDragDrop(callback) {
          disableDragDrop();
          element.on('dragover', 'td.datecell', HandlerDragOver);
          element.on('drop', 'td.datecell', HandlerDrop);
          element.on('dragstart', '.card', HandlerDragStart);
          dropcallback = callback;
        };
        scope.enableDragDrop = enableDragDrop;

        function disableDragDrop() {
          element.off('dragover', 'td.datecell', HandlerDragOver);
          element.off('drop', 'td.datecell', HandlerDrop);
          element.off('dragstart', '.card', HandlerDragStart);
          dropcallback = null;
        }
        scope.disableDragDrop = disableDragDrop;
      }
    };
  })
  .directive('monthview', ['dateFilter', function monthDirective(dateFilter) {
    'use strict';
    return {
      restrict: 'EA',
      replace: true,
      templateUrl: '/static/operationplandetail/month.html',
      require: ['^calendar', '?^ngModel'],
      link: function (scope, element, attrs, ctrls) {
        var ctrl = ctrls[0], ngModelCtrl = ctrls[1];
        scope.showWeeks = ctrl.showWeeks;

        ctrl.mode = {
          step: { months: 1 }
        };

        function getDates(startDate, n) {
          var dates = new Array(n), current = new Date(startDate), i = 0;
          current.setHours(12); // Prevent repeated dates because of timezone bug
          while (i < n) {
            dates[i++] = new Date(current);
            current.setDate(current.getDate() + 1);
          }
          return dates;
        }

        scope.select = function (viewDate) {
          var rows = scope.rows;
          var selectedDate = viewDate.date;
          var events = viewDate.events;
          if (rows) {
            var currentCalendarDate = ctrl.currentCalendarDate;
            var currentMonth = currentCalendarDate.getMonth();
            var currentYear = currentCalendarDate.getFullYear();
            var selectedMonth = selectedDate.getMonth();
            var selectedYear = selectedDate.getFullYear();
            var direction = 0;
            if (currentYear === selectedYear) {
              if (currentMonth !== selectedMonth) {
                direction = currentMonth < selectedMonth ? 1 : -1;
              }
            } else {
              direction = currentYear < selectedYear ? 1 : -1;
            }

            ctrl.currentCalendarDate = selectedDate;
            if (ngModelCtrl) {
              ngModelCtrl.$setViewValue(selectedDate);
            }
            if (direction === 0) {
              for (var row = 0; row < 6; row += 1) {
                for (var date = 0; date < 7; date += 1) {
                  var selected = ctrl.compare(selectedDate, rows[row][date].date) === 0;
                  rows[row][date].selected = selected;
                  if (selected) {
                    scope.selectedDate = rows[row][date];
                  }
                }
              }
            } else {
              ctrl.refreshView();
            }

            if (scope.timeSelected) {
              scope.timeSelected({
                selectedTime: selectedDate,
                events: events
              });
            }
          }
        };

        ctrl._refreshView = function () {
          var startDate = ctrl.range.startdate,
            date = startDate.getDate(),
            month = (startDate.getMonth() + (date !== 1 ? 1 : 0)) % 12,
            year = startDate.getFullYear() + (date !== 1 && month === 0 ? 1 : 0);

          var days = getDates(startDate, 42);
          for (var i = 0; i < 42; i++) {
            days[i] = angular.extend(createDateObject(days[i], ctrl.formatDay), {
              secondary: days[i].getMonth() !== month
            });
          }

          scope.labels = new Array(7);
          for (var j = 0; j < 7; j++) {
            scope.labels[j] = dateFilter(days[j].date, ctrl.formatDayHeader);
          }

          var headerDate = new Date(year, month, 1);
          scope.$parent.title = dateFilter(headerDate, ctrl.formatMonthTitle);
          scope.rows = ctrl.split(days, 7);

          if (scope.showWeeks) {
            scope.weekNumbers = [];
            var thursdayIndex = (4 + 7 - 1) % 7,
              numWeeks = scope.rows.length;
            for (var curWeek = 0; curWeek < numWeeks; curWeek++) {
              scope.weekNumbers.push(
                getISO8601WeekNumber(scope.rows[curWeek][thursdayIndex].date));
            }
          }
        };

        function createDateObject(date, format) {
          return {
            date: date,
            label: dateFilter(date, format),
            selected: ctrl.compare(date, ctrl.currentCalendarDate) === 0,
            current: ctrl.compare(date, currentdate) === 0
          };
        }

        function compareEvent(event1, event2) {
          return (event1.startdate ? event1.startdate : event1.enddate).getTime() -
            (event2.startdate ? event2.startdate : event2.enddate);
        }

        ctrl._onDataLoaded = function () {
          var eventSource = ctrl.eventSource,
            rows = scope.rows,
            row,
            date,
            keys = [];

          for (row = 0; row < 6; row += 1)
            for (date = 0; date < 7; date += 1)
              rows[row][date].events = null;

          for (var event of eventSource) {
            if (processCard(event, false) && scope.grouping && !keys.includes(event[scope.grouping]))
              keys.push(event[scope.grouping]);
          }

          for (row = 0; row < 6; row += 1)
            for (date = 0; date < 7; date += 1)
              if (rows[row][date].events)
                rows[row][date].events.sort(compareEvent);

          var findSelected = false;
          for (row = 0; row < 6; row += 1) {
            for (date = 0; date < 7; date += 1) {
              if (rows[row][date].selected) {
                scope.selectedDate = rows[row][date];
                findSelected = true;
                break;
              }
            }
            if (findSelected) break;
          }

          if (scope.grouping) {
            if (scope.groupingdir && scope.groupingdir == "desc")
              scope.categories = keys.sort().reverse();
            else
              scope.categories = keys.sort();
          }
          else
            scope.categories = ["dummy"];
        };

        function processCard(event, incremental) {
          var oneDay = 86400000;
          var eventStartTime = event.startdate ? new Date(event.startdate) : null;
          var eventEndTime = event.enddate ? new Date(event.enddate) : null;
          var st;
          var et;

          if ((eventEndTime ? eventEndTime : eventStartTime) <= ctrl.range.startdate ||
            (eventStartTime ? eventStartTime : eventEndTime) >= ctrl.range.enddate)
            return false;
          st = ctrl.range.startdate;
          et = ctrl.range.enddate;
          if (!eventEndTime) eventEndTime = eventStartTime;
          if (!eventStartTime) eventStartTime = eventEndTime;

          var timeDiff;
          var timeDifferenceStart;
          if (eventStartTime <= st)
            timeDifferenceStart = 0;
          else {
            timeDiff = eventStartTime - st - (eventStartTime.getTimezoneOffset() - st.getTimezoneOffset()) * 60000;
            timeDifferenceStart = timeDiff / oneDay;
          }

          var timeDifferenceEnd;
          if (eventEndTime >= et) {
            timeDiff = et - st - (et.getTimezoneOffset() - st.getTimezoneOffset()) * 60000;
            timeDifferenceEnd = timeDiff / oneDay;
          } else {
            timeDiff = eventEndTime - st - (eventEndTime.getTimezoneOffset() - st.getTimezoneOffset()) * 60000;
            timeDifferenceEnd = timeDiff / oneDay;
          }

          var index = Math.floor(timeDifferenceStart);
          var index2 = index - 1;
          var eventSet;

          // Delete before the start
          while (incremental && index2 >= 0) {
            var rowIndex = Math.floor(index2 / 7);
            var dayIndex = Math.floor(index2 % 7);
            var exists = false;
            eventSet = scope.rows[rowIndex][dayIndex].events;
            if (eventSet) {
              for (var r = eventSet.length - 1; r >= 0; r--) {
                if ((event.id || event.reference) == (eventSet[r].id || eventSet[r].reference)) {
                  eventSet.splice(r, 1);
                  exists = true;
                  break;
                }
              }
            }
            if (!exists) break;
            index2 -= 1;
          }

          // Insert during duration
          var first = true;
          while (first || index < timeDifferenceEnd) {
            first = false;
            var rowIndex = Math.floor(index / 7);
            var dayIndex = Math.floor(index % 7);
            eventSet = scope.rows[rowIndex][dayIndex].events;
            if (eventSet) {
              var exists = false;
              if (incremental) {
                for (var r of eventSet) {
                  if ((event.id || event.reference) == (r.id || r.reference)) {
                    exists = true;
                    break;
                  }
                }
              }
              if (!exists) eventSet.push(event);
            } else {
              eventSet = [];
              eventSet.push(event);
              scope.rows[rowIndex][dayIndex].events = eventSet;
            }
            index += 1;
          }

          // Delete after end
          while (incremental) {
            var rowIndex = Math.floor(index / 7);
            var dayIndex = Math.floor(index % 7);
            if (rowIndex >= scope.rows.length || dayIndex >= scope.rows[rowIndex].length)
              break;
            var exists = false;
            eventSet = scope.rows[rowIndex][dayIndex].events;
            if (eventSet) {
              for (var r = eventSet.length - 1; r >= 0; r--) {
                if ((event.id || event.reference) == (eventSet[r].id || eventSet[r].reference)) {
                  eventSet.splice(r, 1);
                  exists = true;
                  break;
                }
              }
            }
            if (!exists) break;
            index += 1;
          };
          return true;
        };

        scope.$on('duplicateOperationplan', function (event, card, clone) {
          for (var row = 0; row < 6; row += 1)
            for (var date = 0; date < 7; date += 1)
              if (scope.rows[row][date].events) {
                var newevents = [];
                for (var event of scope.rows[row][date].events) {
                  newevents.push(event);
                  if (event.reference == card.reference)
                    newevents.push(clone);
                }
                scope.rows[row][date].events = newevents;
              }
          scope.selectCard(clone);
        });

        scope.$on('changeMode', function (event, mode) {
          ctrl.changeMode(mode);
          if (scope.editable && mode == "calendarmonth")
            scope.enableDragDrop(processCard);
          else
            scope.disableDragDrop();
        });

        ctrl.compare = function (date1, date2) {
          return (new Date(date1.getFullYear(), date1.getMonth(), date1.getDate()) - new Date(date2.getFullYear(), date2.getMonth(), date2.getDate()));
        };

        ctrl._getRange = function getRange(currentDate) {
          var year = currentDate.getFullYear(),
            month = currentDate.getMonth(),
            firstDayOfMonth = new Date(year, month, 1),
            difference = 1 - firstDayOfMonth.getDay(),
            numDisplayedFromPreviousMonth = (difference > 0) ? 7 - difference : -difference,
            startDate = new Date(firstDayOfMonth),
            endDate;

          if (numDisplayedFromPreviousMonth > 0) {
            startDate.setDate(-numDisplayedFromPreviousMonth + 1);
          }

          endDate = new Date(startDate);
          endDate.setDate(endDate.getDate() + 42);

          return {
            startdate: startDate,
            enddate: endDate
          };
        };

        function getISO8601WeekNumber(date) {
          var dayOfWeekOnFirst = (new Date(date.getFullYear(), 0, 1)).getDay();
          var firstThurs = new Date(date.getFullYear(), 0, ((dayOfWeekOnFirst <= 4) ? 5 : 12) - dayOfWeekOnFirst);
          var thisThurs = new Date(date.getFullYear(), date.getMonth(), date.getDate() + (4 - date.getDay()));
          var diff = thisThurs - firstThurs;
          return (1 + Math.round(diff / 6.048e8)); // 6.048e8 ms per week
        }

        ctrl.refreshView();
        if (scope.editable && scope.mode == "calendarmonth")
          scope.enableDragDrop(processCard);
      }
    };
  }])
  .directive('weekview', ['dateFilter', function weekDirective(dateFilter) {
    'use strict';
    return {
      restrict: 'EA',
      replace: true,
      templateUrl: '/static/operationplandetail/week.html',
      require: '^calendar',
      link: function (scope, element, attrs, ctrl) {
        scope.formatWeekViewDayHeader = ctrl.formatWeekViewDayHeader;
        scope.formatHourColumn = ctrl.formatHourColumn;

        ctrl.mode = {
          step: { days: 7 }
        };

        scope.hourParts = ctrl.hourParts;

        function getDates(startdate, n) {
          var dates = new Array(n),
            current = new Date(startdate),
            i = 0;
          current.setHours(12); // Prevent repeated dates because of timezone bug
          while (i < n) {
            dates[i++] = {
              date: new Date(current)
            };
            current.setDate(current.getDate() + 1);
          }
          return dates;
        }

        scope.select = function (selectedTime, events) {
          if (scope.timeSelected) {
            scope.timeSelected({
              selectedTime: selectedTime,
              events: events
            });
          }
        };

        ctrl._onDataLoaded = function () {
          var eventSource = ctrl.eventSource;
          var keys = [];

          for (var day = 0; day < 7; day += 1) {
            if (scope.dates[day].events) scope.dates[day].events = null;
          }

          for (var event of eventSource) {
            if (processCard(event, false) && scope.grouping && !keys.includes(event[scope.grouping]))
              keys.push(event[scope.grouping]);
          }

          if (scope.grouping) {
            if (scope.groupingdir && scope.groupingdir == "desc")
              scope.categories = keys.sort().reverse();
            else
              scope.categories = keys.sort();
          }
          else
            scope.categories = ["dummy"];
        };

        function processCard(event, incremental) {
          var oneHour = 3600000,
            eps = 0.016;
          var eventStartTime = event.startdate ? new Date(event.startdate) : null;
          var eventEndTime = event.enddate ? new Date(event.enddate) : null;

          if ((eventEndTime ? eventEndTime : eventStartTime) <= ctrl.range.startdate ||
            (eventStartTime ? eventStartTime : eventEndTime) >= ctrl.range.enddate)
            return false;

          if (!eventEndTime) eventEndTime = eventStartTime;
          if (!eventStartTime) eventStartTime = eventEndTime;

          var timeDiff;
          var timeDifferenceStart;
          if (eventStartTime <= ctrl.range.startdate) {
            timeDifferenceStart = 0;
          } else {
            timeDiff = eventStartTime - ctrl.range.startdate - (eventStartTime.getTimezoneOffset() - ctrl.range.startdate.getTimezoneOffset()) * 60000;
            timeDifferenceStart = timeDiff / oneHour;
          }

          var timeDifferenceEnd;
          if (eventEndTime >= ctrl.range.enddate) {
            timeDiff = ctrl.range.enddate - ctrl.range.startdate - (ctrl.range.enddate.getTimezoneOffset() - ctrl.range.startdate.getTimezoneOffset()) * 60000;
            timeDifferenceEnd = timeDiff / oneHour;
          } else {
            timeDiff = eventEndTime - ctrl.range.startdate - (eventEndTime.getTimezoneOffset() - ctrl.range.startdate.getTimezoneOffset()) * 60000;
            timeDifferenceEnd = timeDiff / oneHour;
          }

          var startIndex = Math.floor(timeDifferenceStart);
          var endIndex = Math.ceil((timeDifferenceEnd - eps) / 24);
          var dayIndex = Math.floor(startIndex / 24);

          // Delete before the start
          var index2 = dayIndex - 1;
          while (incremental && index2 >= 0) {
            var exists = false;
            var eventSet = scope.dates[index2].events;
            if (eventSet) {
              for (var r = eventSet.length - 1; r >= 0; r--) {
                if ((event.id || event.reference) == (eventSet[r].id || eventSet[r].reference)) {
                  eventSet.splice(r, 1);
                  exists = true;
                  break;
                }
              }
            }
            if (!exists) break;
            index2 -= 1;
          }

          // Insert during duration
          do {
            if (scope.dates[dayIndex].events) {
              var exists = false;
              if (incremental) {
                for (var r of scope.dates[dayIndex].events) {
                  if ((event.id || event.reference) == (r.id || r.reference)) {
                    exists = true;
                    break;
                  }
                }
              }
              if (!exists) scope.dates[dayIndex].events.push(event);
            }
            else
              scope.dates[dayIndex].events = [event];
            dayIndex += 1;
          }
          while (dayIndex < endIndex);

          // Delete after the end
          while (incremental && dayIndex < 7) {
            var exists = false;
            eventSet = scope.dates[dayIndex].events;
            if (eventSet) {
              for (var r = eventSet.length - 1; r >= 0; r--) {
                if ((event.id || event.reference) == (eventSet[r].id || eventSet[r].reference)) {
                  eventSet.splice(r, 1);
                  exists = true;
                  break;
                }
              }
            }
            if (!exists) break;
            dayIndex += 1;
          };
          return true;
        };

        scope.$on('duplicateOperationplan', function (event, card, clone) {
          for (var day = 0; day < 7; day += 1) {
            if (!scope.dates[day].events) continue;
            var newevents = [];
            for (var event of scope.dates[day].events) {
              newevents.push(event);
              if (event.reference == card.reference)
                newevents.push(clone);
            }
            scope.dates[day].events = newevents;
          }
          scope.selectCard(clone);
        });

        scope.$on('changeMode', function (event, mode) {
          ctrl.changeMode(mode);
          if (scope.editable && mode == "calendarweek")
            scope.enableDragDrop(processCard);
          else
            scope.disableDragDrop();
        });

        ctrl._refreshView = function () {
          var weekNumberIndex,
            weekFormatPattern = 'w',
            title;
          scope.dates = getDates(ctrl.range.startdate, 7);
          weekNumberIndex = ctrl.formatWeekTitle.indexOf(weekFormatPattern);
          title = dateFilter(ctrl.range.startdate, ctrl.formatWeekTitle);
          if (weekNumberIndex !== -1)
            title = title.replace(weekFormatPattern, getISO8601WeekNumber(ctrl.range.startdate));
          scope.$parent.title = title;
        };

        ctrl._getRange = function getRange(currentDate) {
          var year = currentDate.getFullYear(),
            month = currentDate.getMonth(),
            date = currentDate.getDate(),
            day = currentDate.getDay(),
            firstDayOfWeek = new Date(year, month, date - day),
            enddate = new Date(year, month, date - day + 7);

          return {
            startdate: firstDayOfWeek,
            enddate: enddate
          };
        };

        //This can be decomissioned when upgrade to Angular 1.3
        function getISO8601WeekNumber(date) {
          var checkDate = new Date(date);
          checkDate.setDate(checkDate.getDate() + 4 - (checkDate.getDay() || 7)); // Thursday
          var time = checkDate.getTime();
          checkDate.setMonth(0); // Compare with Jan 1
          checkDate.setDate(1);
          return Math.floor(Math.round((time - checkDate) / 86400000) / 7) + 1;
        }

        ctrl.refreshView();
        if (scope.editable && scope.mode == "calendarweek")
          scope.enableDragDrop(processCard);
      }
    };
  }])
  .directive('dayview', ['dateFilter', function dayDirective(dateFilter) {
    'use strict';
    return {
      restrict: 'EA',
      replace: true,
      templateUrl: '/static/operationplandetail/day.html',
      require: '^calendar',
      link: function (scope, element, attrs, ctrl) {
        scope.formatHourColumn = ctrl.formatHourColumn;

        ctrl.mode = {
          step: { days: 1 }
        };

        scope.hourParts = ctrl.hourParts;
        scope.events = [];

        function createDateObjects(startdate) {
          var rows = [],
            time,
            currentHour = startdate.getHours(),
            currentDate = startdate.getDate();

          for (var hour = 0; hour < 24; hour += 1) {
            time = new Date(startdate.getTime());
            time.setHours(currentHour + hour);
            time.setDate(currentDate);
            rows.push({
              date: time
            });
          }
          scope.dt = { date: startdate };
          return rows;
        }

        scope.select = function (selectedTime, events) {
          if (scope.timeSelected) {
            scope.timeSelected({
              selectedTime: selectedTime,
              events: events
            });
          }
        };

        function processCard(card, incremental) {
          // No drag and drop in the daily calendar view
        };

        scope.$on('duplicateOperationplan', function (event, card, clone) {
          var newevents = [];
          for (var event of scope.events) {
            newevents.push(event);
            if (event.reference == card.reference)
              newevents.push(clone);
          }
          scope.events = newevents;
          scope.selectCard(clone);
        });

        scope.$on('changeMode', function (event, mode) {
          ctrl.changeMode(mode);
          if (scope.editable && mode == "calendarday")
            scope.enableDragDrop(processCard);
          else
            scope.disableDragDrop();
        });

        ctrl._onDataLoaded = function () {
          var eventSource = ctrl.eventSource,
            startdate = ctrl.range.startdate,
            enddate = ctrl.range.enddate,
            keys = [];

          scope.events = null;

          for (var event of eventSource) {
            var eventStartTime = event.startdate ? new Date(event.startdate) : null;
            var eventEndTime = event.enddate ? new Date(event.enddate) : null;
            if ((eventEndTime ? eventEndTime : eventStartTime) <= startdate ||
              (eventStartTime ? eventStartTime : eventEndTime) >= enddate)
              continue;
            if (scope.events)
              scope.events.push(event);
            else
              scope.events = [event];
            if (scope.grouping && !keys.includes(event[scope.grouping]))
              keys.push(event[scope.grouping]);
          }

          if (scope.grouping) {
            if (scope.groupingdir && scope.groupingdir == "desc")
              scope.categories = keys.sort().reverse();
            else
              scope.categories = keys.sort();
          }
          else
            scope.categories = ["dummy"];
        };

        ctrl._refreshView = function () {
          var startingDate = ctrl.range.startdate;

          scope.rows = createDateObjects(startingDate);
          scope.dates = [startingDate];
          scope.$parent.title = dateFilter(startingDate, ctrl.formatDayTitle);
        };

        ctrl._getRange = function getRange(currentDate) {
          var year = currentDate.getFullYear(),
            month = currentDate.getMonth(),
            date = currentDate.getDate(),
            startdate = new Date(year, month, date),
            enddate = new Date(year, month, date + 1);

          return {
            startdate: startdate,
            enddate: enddate
          };
        };

        ctrl.refreshView();
        if (scope.editable && scope.mode == "calendarday")
          scope.enableDragDrop(processCard);
      }
    };
  }]);
/*
 * Copyright (C) 2024 by frePPLe bv
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

var operationplandetailapp = angular.module('operationplandetailapp',
  ['ngCookies', 'gettext', 'ngWebSocket', 'frepple.input', 'frepple.common', 'calendar', 'd3'],
  ['$locationProvider', function ($locationProvider) {
    $locationProvider.html5Mode({ enabled: true, requireBase: false });
  }]);

operationplandetailapp.config(['$httpProvider', function ($httpProvider) {
  $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
  $httpProvider.defaults.xsrfCookieName = 'csrftoken';
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
}]);

operationplandetailapp.run(['gettextCatalog', function (gettextCatalog) {
  gettextCatalog.setCurrentLanguage(language);
  //gettextCatalog.debug = true; //show missing label on untranslated strings
}]);

operationplandetailapp.filter('formatdate', function () {
  return function (datestr) {
    if (moment.isMoment(datestr))
      return datestr.format(dateformat);
    else if (datestr && typeof (datestr) !== "undefined")
      return moment(datestr, datetimeformat).format(dateformat);
  };
});

operationplandetailapp.filter('formatdatetime', function () {
  return function (datestr) {
    if (moment.isMoment(datestr))
      return datestr.year() > 1971 ? datestr.format(datetimeformat) : "";
    else if (datestr && typeof (datestr) !== "undefined") {
      var tmp = moment(datestr, datetimeformat);
      return tmp.year() > 1971 ? tmp.format(datetimeformat) : "";
    }
  };
});


operationplandetailapp.filter('formatnumber', function () {
  return function (nData, maxdecimals = 6) {
  // Number formatting function copied from free-jqgrid.
  // Adapted to show a max number of decimal places.
  if (typeof (nData) === 'undefined' || nData === '')
    return '';

  const isNumber = nData !== '' && nData !== null && !isNaN(nData) && isFinite(nData);

  if (isNumber) {
    nData *= 1;
    const bNegative = (nData < 0);
    const absData = Math.abs(nData);
    let sOutput = 0.0;

    if (absData > 100000 || maxdecimals <= 0)
      sOutput = String(parseFloat(absData.toFixed()));
    else if (absData > 10000 || maxdecimals <= 1)
      sOutput = String(parseFloat(absData.toFixed(1)));
    else if (absData > 1000 || maxdecimals <= 2)
      sOutput = String(parseFloat(absData.toFixed(2)));
    else if (absData > 100 || maxdecimals <= 3)
      sOutput = String(parseFloat(absData.toFixed(3)));
    else if (absData > 10 || maxdecimals <= 4)
      sOutput = String(parseFloat(absData.toFixed(4)));
    else if (absData > 1 || maxdecimals <= 5)
      sOutput = String(parseFloat(absData.toFixed(5)));
    else
      sOutput = String(parseFloat(absData.toFixed(maxdecimals)));

    sOutput = (bNegative ? "-" : "") + sOutput;

    const sDecimalSeparator = jQuery("#grid").jqGrid("getGridRes", "formatter.number.decimalSeparator") || ".";
    if (sDecimalSeparator !== ".")
      // Replace the "."
      sOutput = sOutput.replace(".", sDecimalSeparator);
    const sThousandsSeparator = jQuery("#grid").jqGrid("getGridRes", "formatter.number.thousandsSeparator") || ",";
    if (sThousandsSeparator && absData >= 1000) {
      let nDotIndex = sOutput.lastIndexOf(sDecimalSeparator);
      nDotIndex = (nDotIndex > -1) ? nDotIndex : sOutput.length;
      // we cut the part after the point for integer numbers
      // it will prevent storing/restoring of wrong numbers during inline editing
      let sNewOutput = sDecimalSeparator === undefined ? "" : sOutput.substring(nDotIndex);
      let nCount = -1, i;
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
  return (nData ? nData.toLocaleString() : null) || '0';
 };
});

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
    if (value !== 'no_action' && value !== 'erp_incr_export') {
      $scope.$apply(function () {
        $scope.operationplan.status = value;
      });
    }
  }
  $scope.refreshstatus = refreshstatus;

  function setMode(m) {
    function innerFunction() {
      PreferenceSvc.save("mode", m, function () {
        window.location.reload();
      });
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

angular.module('operationplandetailapp').directive('showproblemspanelDrv', showproblemspanelDrv);

showproblemspanelDrv.$inject = ['$window', 'gettextCatalog'];

function showproblemspanelDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: { operationplan: '=data' },
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    scope.$watchGroup(['operationplan.id', 'operationplan.problems.length', , 'operationplan.info'], function (newValue, oldValue) {
      angular.element(document).find('#attributes-operationproblems').empty().append(
        '<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_problems" aria-expanded="false" aria-controls="widget_problems">' +
        '<h5 class="card-title text-capitalize fs-5 me-auto">' +
        gettextCatalog.getString("problems") +
        '</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>' +
        '<div class="card-body collapse' +
        (scope.$parent.widget[1]["collapsed"] ? '' : ' show') +
        '" id="widget_problems">' +
        '<table class="table table-sm table-hover table-borderless"><thead><tr><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("name") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("start") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("end") + '</b>' +
        '</td></tr></thead>' +
        '<tbody></tbody>' +
        '</table></div>'
      );
      var rows = (
        scope.operationplan.hasOwnProperty('problems')
        || scope.operationplan.hasOwnProperty('info')
      ) ? "" : ('<tr><td colspan="3">' + gettextCatalog.getString('no problems') + '</td></tr>');
      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('problems')) {
          angular.forEach(scope.operationplan.problems, function (theproblem) {
            rows += '<tr><td>' +
              theproblem.description + '</td><td>' +
              theproblem.start + '</td><td>' +
              theproblem.end + '</td></tr>';
          });
        }
        if (scope.operationplan.hasOwnProperty('info')) {
          angular.forEach(scope.operationplan.info.split('\n'), function (info) {
            rows += '<tr><td colspan="3">' + info + '</td><tr>';
          });
        }
      }
      angular.element(document).find('#attributes-operationproblems tbody').append(rows);
      angular.element(elem).find('.collapse')
        .on("shown.bs.collapse", grid.saveColumnConfiguration)
        .on("hidden.bs.collapse", grid.saveColumnConfiguration);
    }); //watch end

  } //link end
} //directive end

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

angular.module('operationplandetailapp').directive('showresourcespanelDrv', showresourcespanelDrv);

showresourcespanelDrv.$inject = ['$window', 'gettextCatalog'];

function showresourcespanelDrv($window, gettextCatalog) {

	var directive = {
		restrict: 'EA',
		scope: { operationplan: '=data', mode: "=mode" },
		link: linkfunc
	};
	return directive;

	function linkfunc(scope, elem, attrs) {
		function redraw() {
			angular.element(document).find('#attributes-operationresources').empty().append(
				'<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_resources" aria-expanded="false" aria-controls="widget_resources">' + 
				'<h5 class="card-title text-capitalize fs-5 me-auto">' +
				gettextCatalog.getString("resource") +
				'</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>' +
				'<div class="card-body collapse' + 
				(scope.$parent.widget[1]["collapsed"] ? '' : ' show') +
				'" id="widget_resources">' +
				'<table class="table table-sm table-hover table-borderless"><thead><tr><td>' +
				'<b class="text-capitalize">' + gettextCatalog.getString("name") + '</b>' +
				'</td><td>' +
				'<b class="text-capitalize">' + gettextCatalog.getString("quantity") + '</b>' +
				'</td>' +
				'<tbody></tbody>' +
				'</table></div>'
			);
			var rows = '<tr><td colspan="2">' + gettextCatalog.getString('no resources') + '</td></tr>';
			if (typeof scope.operationplan !== 'undefined') {
				if (scope.operationplan.hasOwnProperty('loadplans')) {
					rows = '';
					angular.forEach(scope.operationplan.loadplans, function (theresource) {
						if (!theresource.hasOwnProperty('alternates'))
							rows += '<tr><td>' + $.jgrid.htmlEncode(theresource.resource.name)
								+ "<a href=\"" + url_prefix + "/detail/input/resource/" + admin_escape(theresource.resource.name)
								+ "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a></td>"
								+ '<td>' + grid.formatNumber(theresource.quantity) + '</td></tr>';
						else {
							rows += '<tr><td style="white-space: nowrap;"><div class="dropdown">'
								+ '<button class="form-control w-auto dropdown-toggle" data-bs-toggle="dropdown" type="button" style="min-width: 150px">'
								+ $.jgrid.htmlEncode(theresource.resource.name)
								+ '</button>'
								+ '<ul class="dropdown-menu">'
								+ '<li><a role="menuitem" class="dropdown-item alternateresource text-capitalize">'
								+ $.jgrid.htmlEncode(theresource.resource.name)
								+ '</a></li>';
							angular.forEach(theresource.alternates, function (thealternate) {
								rows += '<li><a role="menuitem" class="dropdown-item alternateresource text-capitalize">'
									+ $.jgrid.htmlEncode(thealternate.name)
									+ '</a></li>';
							});
							rows += '</ul></td><td>' + grid.formatNumber(theresource.quantity) + '</td></tr>';
						}
					});
				}
			};
			angular.element(document).find('#attributes-operationresources tbody').append(rows);
			angular.element(document).find('#attributes-operationresources a.alternateresource').bind('click', function () {
				var newresource = $(this).html();
				var curresource = $(this).parent().parent().prev().html();
				if (newresource != curresource) {
					var first = true;
					angular.forEach(scope.operationplan.loadplans, function (theresource) {
						if (theresource.resource.name == curresource && first) {
							first = false;
							// Update the assigned resource
							theresource.resource.name = newresource;
							// Update the alternate list
							angular.forEach(theresource.alternates, function (thealternate) {
								if (thealternate.name === newresource)
									thealternate.name = curresource;
							});
							// Redraw the directive
							redraw();

							if (scope.mode && (scope.mode.startsWith("calendar") || scope.mode == "kanban")) {
								// Update a calendar or kanban card
								scope.$emit("updateCard", "loadplans", scope.operationplan.loadplansOriginal, scope.operationplan.loadplans);
							}
							else {
								// Update the grid
								// TODO this code shouldn't live here...
								var grid = angular.element(document).find("#grid");
								var selrow = grid.jqGrid('getGridParam', 'selarrrow');
								var colmodel = grid.jqGrid('getGridParam', 'colModel').find(function (i) { return i.name == "resources" });
								if (!colmodel)
									colmodel = grid.jqGrid('getGridParam', 'colModel').find(function (i) { return i.name == "resource" });
								var cell = grid.jqGrid('getCell', selrow, colmodel.name);
								if (colmodel.formatter == 'detail' && cell == curresource) {
									grid.jqGrid("setCell", selrow, colmodel.name, newresource, "dirty-cell");
									grid.jqGrid("setRowData", selrow, false, "edited");
									angular.element(document).find("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
									angular.element(document).find("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
									$(window).off('beforeunload', upload.warnUnsavedChanges);
									$(window).on('beforeunload', upload.warnUnsavedChanges);
								}
								else if (colmodel.formatter == 'listdetail') {
									var res = [];
									angular.forEach(scope.operationplan.loadplans, function (theloadplan) {
										res.push([theloadplan.resource.name, theloadplan.quantity, theloadplan.reference]);
									});
									grid.jqGrid("setCell", selrow, colmodel.name, res, "dirty-cell");
									grid.jqGrid("setRowData", selrow, false, "edited");
									angular.element(document).find("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
									angular.element(document).find("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
									$(window).off('beforeunload', upload.warnUnsavedChanges);
									$(window).on('beforeunload', upload.warnUnsavedChanges);
								}
							}
							return false;
						}
					});
				}
			});
            angular.element(elem).find('.collapse')
             .on("shown.bs.collapse", grid.saveColumnConfiguration)
             .on("hidden.bs.collapse", grid.saveColumnConfiguration);
		};

		scope.$watchGroup(['operationplan.id', 'operationplan.loadplans.length'], redraw);
	} //link end
} //directive end

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

angular.module('operationplandetailapp').directive('showbufferspanelDrv', showbufferspanelDrv);

showbufferspanelDrv.$inject = ['$window', 'gettextCatalog', '$filter'];

function showbufferspanelDrv($window, gettextCatalog, $filter) {

  var directive = {
    restrict: 'EA',
    scope: { operationplan: '=data' },
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    function redraw() {
      angular.element(document).find('#attributes-operationflowplans').empty().append(
        '<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_bufferspanel" aria-expanded="false" aria-controls="widget_bufferspanel">' + 
        '<h5 class="card-title text-capitalize fs-5 me-auto">' +
        gettextCatalog.getString("items") +
        '</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>' +
        '<div class="card-body collapse' + 
        (scope.$parent.widget[1]["collapsed"] ? '' : ' show') + 
        '" id="widget_bufferspanel">' +
        '<table class="table table-sm table-hover table-borderless"><thead><tr><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("item") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("location") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("quantity") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("onhand") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("date") + '</b>' +
        '</td></tr></thead>' +
        '<tbody></tbody>' +
        '</table></div>'
      );
      var rows = '<tr><td colspan="3">' + gettextCatalog.getString('no movements') + '<td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('flowplans')) {
          rows = '';
          var firstproducer = true;
          angular.forEach(scope.operationplan.flowplans, function (theflow) {
            if (theflow.quantity > 0 && firstproducer) {
              rows += '<tr class="border-top">';
              firstproducer = false;
            }
            else
              rows += '<tr>';
            if (!theflow.hasOwnProperty('alternates')) {
              rows += '<td><span ';
              if (theflow.buffer.description)
                rows += ' onmouseenter="$(this).tooltip(\'show\')" title="' + $.jgrid.htmlEncode(theflow.buffer.description) + '"';
              rows += '>' + $.jgrid.htmlEncode(theflow.buffer.item)
                + "<a href=\"" + url_prefix + "/detail/input/item/" + admin_escape(theflow.buffer.item)
                + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a>"
                + '</span></td>'
            }
            else {
              rows += '<td style="white-space: nowrap"><div class="dropdown">'
                + '<button class="btn btn-primary text-capitalize" data-bs-toggle="dropdown" type="button" style="min-width: 150px">'
                + $.jgrid.htmlEncode(theflow.buffer.item)
                + '</button>'
                + '<ul class="dropdown-menu">'
                + '<li><a role="menuitem" class="dropdown-item alternateitem text-capitalize">'
                + $.jgrid.htmlEncode(theflow.buffer.item)
                + '</a></li>';
              angular.forEach(theflow.alternates, function (thealternate) {
                rows += '<li><a role="menuitem" class="dropdown-item alternateitem text-capitalize">'
                  + $.jgrid.htmlEncode(thealternate)
                  + '</a></li>';
              });
              rows += '</ul></td>';
            }
            rows += '<td>' + $.jgrid.htmlEncode(theflow.buffer.location)
              + '</td><td>' + grid.formatNumber(theflow.quantity)
              + '</td><td>' + grid.formatNumber(theflow.onhand)
              + '</td><td style="white-space: nowrap">' + $filter('formatdatetime')(theflow.date)
              + '</td></tr>';
          });
          angular.element(document).find('#attributes-operationflowplans thead').css('display', 'table-header-group');
        }
      }
      angular.element(document).find('#attributes-operationflowplans tbody').append(rows);
      angular.element(document).find('#attributes-operationflowplans a.alternateitem').bind('click', function () {
        var newitem = $(this).html();
        var curitem = $(this).parent().parent().prev().html();
        if (newitem != curitem) {
          angular.forEach(scope.operationplan.flowplans, function (theflow) {
            if (theflow.buffer.item == curitem) {
              // Update the assigned item
              theflow.buffer.item = newitem;
              // Redraw the directive
              redraw();
              // Update the grid
              var grid = angular.element(document).find("#grid");
              var selrow = grid.jqGrid('getGridParam', 'selarrrow');
              var colmodel = grid.jqGrid('getGridParam', 'colModel').find(function (i) { return i.name == "material" });
              var cell = grid.jqGrid('getCell', selrow, 'material');
              if (colmodel.formatter == 'detail' && cell == curitem) {
                grid.jqGrid("setCell", selrow, "material", newitem, "dirty-cell");
                grid.jqGrid("setRowData", selrow, false, "edited");
                angular.element(document).find("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
                angular.element(document).find("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
              }
              else if (colmodel.formatter == 'listdetail') {
                var items = [];
                angular.forEach(scope.operationplan.flowplans, function (theflowplan) {
                  items.push([theflowplan.buffer.item, theflowplan.quantity]);
                });
                grid.jqGrid("setCell", selrow, "material", items, "dirty-cell");
                grid.jqGrid("setRowData", selrow, false, "edited");
                angular.element(document).find("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
                angular.element(document).find("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
              }
              return false;
            }
          });
        }
      });
      angular.element(elem).find('.collapse')
        .on("shown.bs.collapse", grid.saveColumnConfiguration)
        .on("hidden.bs.collapse", grid.saveColumnConfiguration);
    };
    scope.$watchGroup(['operationplan.id', 'operationplan.flowplans.length'], redraw);
  } //link end
} //directive end

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
 */

'use strict';

angular.module('operationplandetailapp').directive('showoperationpeggingpanelDrv', showoperationpeggingpanelDrv);

showoperationpeggingpanelDrv.$inject = ['$window', 'gettextCatalog', '$filter'];

function showoperationpeggingpanelDrv($window, gettextCatalog, $filter) {

  var directive = {
    restrict: 'EA',
    scope: { operationplan: '=data' },
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs, transclude) {
    scope.$watchGroup(['operationplan.id', 'operationplan.pegging_demand.length'], function (newValue, oldValue) {
      angular.element(document).find('#attributes-operationdemandpegging').empty().append(
        '<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_demandpegging" aria-expanded="false" aria-controls="widget_demandpegging">' + 
        '<h5 class="card-title text-capitalize fs-5 me-auto">' +
        gettextCatalog.getString("demand") +
        '</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>' +
        '<div class="card-body table-responsive collapse' + 
        (scope.$parent.widget[1]["collapsed"] ? '' : ' show') + 
        '" id="widget_demandpegging" style="max-height:15em; overflow:auto">' +        
        '</div>'
      );
      var rows = '';
      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('pegging_demand')) {          
          angular.forEach(scope.operationplan.pegging_demand, function (thedemand) {
            rows += '<tr><td>' + $.jgrid.htmlEncode(thedemand.demand.name)
              + "<a href=\"" + url_prefix
              + (thedemand.demand.forecast ? "/detail/forecast/forecast/" : "/detail/input/demand/")
              + admin_escape(thedemand.demand.name)
              + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a>"
              + '</td><td>';
            if (thedemand.demand.item.description)
              rows += '<span onmouseenter="$(this).tooltip(\'show\')" title="'
                + $.jgrid.htmlEncode(thedemand.demand.item.description) + '">'
                + $.jgrid.htmlEncode(thedemand.demand.item.name)
                + "</span>";
            else
              rows += $.jgrid.htmlEncode(thedemand.demand.item.name);
            rows += "<a href=\"" + url_prefix + "/detail/input/item/" + admin_escape(thedemand.demand.item.name)
              + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a>"
              + '</td><td>' + $filter('formatdate')(thedemand.demand.due)
              + '</td><td>' + grid.formatNumber(thedemand.quantity) + '</td></tr>';
          });
        }
      }

      if (rows == '')
        angular.element(document).find('#widget_demandpegging').append(
          '<div>' + gettextCatalog.getString('There is no demand requiring this supply.') + '</div>'
        );
      else 
        angular.element(document).find('#widget_demandpegging').append(
          '<table class="table table-sm table-hover table-borderless"><thead><tr><td>' +
          '<b class="text-capitalize">' + gettextCatalog.getString("name") + '</b>' +
          '</td><td>' +
          '<b class="text-capitalize">' + gettextCatalog.getString("item") + '</b>' +
          '</td><td>' +
          '<b class="text-capitalize">' + gettextCatalog.getString("due") + '</b>' +
          '</td><td>' +
          '<b class="text-capitalize">' + gettextCatalog.getString("quantity") + '</b>' +
          '</td></thead>' +
          '<tbody>' + rows + '</tbody></table>'
          );
      angular.element(elem).find('.collapse')
        .on("shown.bs.collapse", grid.saveColumnConfiguration)
        .on("hidden.bs.collapse", grid.saveColumnConfiguration);     
    }); //watch end

  } //link end
} //directive end

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

angular.module('operationplandetailapp').directive('showoperationplanDrv', showoperationplanDrv);

showoperationplanDrv.$inject = ['$window', 'gettextCatalog'];

function showoperationplanDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    templateUrl: '/static/operationplandetail/operationplanpanel.html',
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    scope.actions = actions;
    scope.editable = editable;
    scope.opptype = { //just a translation
      'MO': gettextCatalog.getString('manufacturing order'),
      'PO': gettextCatalog.getString('purchase order'),
      'DO': gettextCatalog.getString('distribution order'),
      'STCK': gettextCatalog.getString('stock'),
      'DLVR': gettextCatalog.getString('delivery'),
    }

    scope.$on("cardChanged", function (event, field, oldvalue, newvalue) {
      if (typeof scope.operationplan == undefined)
        return;
      else if (field === "startdate")
        scope.operationplan["start"] = newvalue;
      else if (field === "enddate")
        scope.operationplan["end"] = newvalue;
      else
        scope.operationplan[field] = newvalue;
    });

    //need to watch all of these because a webservice may change them on the fly
    scope.$watchGroup([
      'operationplan.id', 'operationplan.start', 'operationplan.end', 'operationplan.quantity',
      'operationplan.completed_quantity', 'operationplan.criticality', 'operationplan.delay',
      'operationplan.status', 'operationplan.remark'
    ], function (newValue, oldValue) {
      if (scope.operationplan === undefined || scope.operationplan === null)
        return;
      if (scope.operationplan.id == -1 || scope.operationplan.type === 'STCK') {
        // Multiple operationplans selected
        angular.element(elem).find('input').attr('disabled', 'disabled');
      }
      else if (typeof scope.operationplan.id !== 'undefined') {
        // Single operationplan selected
        angular.element(elem).find('input[disabled]').attr('disabled', false);
        if (scope.operationplan.hasOwnProperty('start'))
          angular.element(elem).find("#setStart").val(moment.utc(scope.operationplan.start, datetimeformat).format(datetimeformat));
        if (scope.operationplan.hasOwnProperty('end'))
          angular.element(elem).find("#setEnd").val(moment.utc(scope.operationplan.end, datetimeformat).format(datetimeformat));
      }
      else {
        // No operationplan selected
        angular.element(elem).find("#setStart").val('');
        angular.element(elem).find("#setEnd").val('');
      }
      angular.element(elem).find("#statusrow").css(
        "display", (scope.operationplan.status && scope.operationplan.type !== 'STCK') ? "table-row" : "none"
      );
      angular.element(elem).find('.collapse')
        .on("shown.bs.collapse", grid.saveColumnConfiguration)
        .on("hidden.bs.collapse", grid.saveColumnConfiguration);
    }); //watch end

  } //link end
} //directive end

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

angular.module('operationplandetailapp').directive('showsupplyinformationDrv', showsupplyinformationDrv);

showsupplyinformationDrv.$inject = ['$window', 'gettextCatalog'];

function showsupplyinformationDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: { operationplan: '=data' },
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    scope.$watchGroup(['operationplan.id', 'operationplan.attributes.supply.length'], function (newValue, oldValue) {
      angular.element(document).find('#attributes-supplyinformation').empty().append(
        '<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_supply" aria-expanded="false" aria-controls="widget_supply">' + 
        '<h5 class="card-title text-capitalize fs-5 me-auto">' +
        gettextCatalog.getString("supply information") +
        '</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>' +
        '<div class="card-body collapse' + 
				(scope.$parent.widget[1]["collapsed"] ? '' : ' show') +
				'" id="widget_supply">' +
        '<div class="table-responsive"><table class="table table-hover table-sm"><thead><tr><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("priority") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("types") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("origin") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("lead time") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("cost") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("size minimum") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("size multiple") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("effective start") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("effective end") + '</b>' +
        '</td></tr></thead>' +
        '<tbody></tbody>' +
        '</table></div></div>'
      );
      var rows = '<tr><td colspan="9">' + gettextCatalog.getString('no supply information') + '</td></tr>';

      if (typeof scope.operationplan !== 'undefined' && scope.operationplan.hasOwnProperty('attributes')) {
        if (scope.operationplan.attributes.hasOwnProperty('supply')) {
          rows = '';
          angular.forEach(scope.operationplan.attributes.supply, function (thesupply) {
            rows += '<tr>'
            for (var i in thesupply) {
              rows += '<td>';

              rows += thesupply[i];

              rows += '</td>';
            }
            rows += '</tr>'
          });
        }
      }
      angular.element(document).find('#attributes-supplyinformation tbody').append(rows);
      angular.element(elem).find('.collapse')
        .on("shown.bs.collapse", grid.saveColumnConfiguration)
        .on("hidden.bs.collapse", grid.saveColumnConfiguration);
    }); //watch end

  } //link end
} //directive end

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

angular.module('operationplandetailapp').directive('showdownstreamoperationplansDrv', showdownstreamoperationplansDrv);

showdownstreamoperationplansDrv.$inject = ['$window', 'gettextCatalog'];

function showdownstreamoperationplansDrv($window, gettextCatalog) {

	var directive = {
		restrict: 'EA',
		scope: { operationplan: '=data' },
		templateUrl: '/static/operationplandetail/downstreamoperationplans.html',
		link: linkfunc
	};
	return directive;

	function linkfunc(scope, elem, attrs) {

		function expandOrCollapse(i) {
			// 0: collapsed, 1: expanded, 2: hidden, 3: leaf node
			var j = i + 1;
			var mylevel = scope.operationplan.downstreamoperationplans[i][0];
			if (scope.operationplan.downstreamoperationplans[i][11] == 0)
				scope.operationplan.downstreamoperationplans[i][11] = 1;
			else
				scope.operationplan.downstreamoperationplans[i][11] = 0;
			while (j < scope.operationplan.downstreamoperationplans.length) {
				if (scope.operationplan.downstreamoperationplans[j][0] <= mylevel)
					break;
				else if (scope.operationplan.downstreamoperationplans[j][0] > mylevel + 1
					|| scope.operationplan.downstreamoperationplans[i][11] == 0)
					scope.operationplan.downstreamoperationplans[j][11] = 2;
				else if (j == scope.operationplan.downstreamoperationplans.length - 1 ||
					scope.operationplan.downstreamoperationplans[j][0] >= scope.operationplan.downstreamoperationplans[j + 1][0]) {
					if (scope.operationplan.downstreamoperationplans[j][12] != null
						&& scope.operationplan.downstreamoperationplans[j][12] == scope.operationplan.downstreamoperationplans[j + 1][12])
						scope.operationplan.downstreamoperationplans[j][11] = 1;
					else
						scope.operationplan.downstreamoperationplans[j][11] = 3;
				}
				else if (scope.operationplan.downstreamoperationplans[j][0] == mylevel + 1
					&& scope.operationplan.downstreamoperationplans[i][11] == 1)
					scope.operationplan.downstreamoperationplans[j][11] = 0;
				++j;
			}
		}
		scope.expandOrCollapse = expandOrCollapse;

		scope.url_prefix = url_prefix;

		angular.element(document).find('#widget_downstream')
         .on("shown.bs.collapse", grid.saveColumnConfiguration)
         .on("hidden.bs.collapse", grid.saveColumnConfiguration);
	} //link end
} //directive end

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

angular.module('operationplandetailapp').directive('showupstreamoperationplansDrv', showupstreamoperationplansDrv);

showupstreamoperationplansDrv.$inject = ['$window', 'gettextCatalog'];

function showupstreamoperationplansDrv($window, gettextCatalog) {

	var directive = {
		restrict: 'EA',
		scope: { operationplan: '=data' },
		templateUrl: '/static/operationplandetail/upstreamoperationplans.html',
		link: linkfunc
	};
	return directive;

	function linkfunc(scope, elem, attrs) {

		function expandOrCollapse(i) {
			// 0: collapsed, 1: expanded, 2: hidden, 3: leaf
			var j = i + 1;
			var mylevel = scope.operationplan.upstreamoperationplans[i][0];
			if (scope.operationplan.upstreamoperationplans[i][11] == 0)
				scope.operationplan.upstreamoperationplans[i][11] = 1;
			else
				scope.operationplan.upstreamoperationplans[i][11] = 0;
			while (j < scope.operationplan.upstreamoperationplans.length) {
				if (scope.operationplan.upstreamoperationplans[j][0] <= mylevel)
					break;
				else if (scope.operationplan.upstreamoperationplans[j][0] > mylevel + 1
					|| scope.operationplan.upstreamoperationplans[i][11] == 0)
					scope.operationplan.upstreamoperationplans[j][11] = 2;
				else if (j == scope.operationplan.upstreamoperationplans.length - 1 ||
					scope.operationplan.upstreamoperationplans[j][0] >= scope.operationplan.upstreamoperationplans[j + 1][0]) {
					if (scope.operationplan.upstreamoperationplans[j][12] != null
						&& scope.operationplan.upstreamoperationplans[j][12] == scope.operationplan.upstreamoperationplans[j + 1][12])
						scope.operationplan.upstreamoperationplans[j][11] = 1;
					else
						scope.operationplan.upstreamoperationplans[j][11] = 3;
				}
				else if (scope.operationplan.upstreamoperationplans[j][0] == mylevel + 1
					&& scope.operationplan.upstreamoperationplans[i][11] == 1)
					scope.operationplan.upstreamoperationplans[j][11] = 0;
				++j;
			}
		}
		scope.expandOrCollapse = expandOrCollapse;

		scope.url_prefix = url_prefix;

        angular.element(elem).find('#widget_upstream')
         .on("shown.bs.collapse", grid.saveColumnConfiguration)
         .on("hidden.bs.collapse", grid.saveColumnConfiguration);
	} //link end
} //directive end

/*
 * Copyright (C) 2020 by frePPLe bv
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
 */

angular.module('operationplandetailapp').directive('showKanbanDrv', showKanbanDrv);

showKanbanDrv.$inject = ['$window', 'gettextCatalog', 'OperationPlan', 'PreferenceSvc'];

function showKanbanDrv($window, gettextCatalog, OperationPlan, PreferenceSvc) {
  'use strict';

  var directive = {
    restrict: 'EA',
    scope: {
      operationplan: '=',
      kanbanoperationplans: '=',
      kanbancolumns: '=',
      editable: '='
    },
    templateUrl: '/static/operationplandetail/kanban.html',
    link: linkfunc
  };
  return directive;

  function linkfunc($scope, $elem, attrs) {

    $scope.curselected = null;
    $scope.colstyle = 'col-md-1';
    $scope.type = 'PO';
    $scope.admin_escape = admin_escape;
    $scope.url_prefix = url_prefix;
    $scope.mode = mode;

    $scope.opptype = {
      'MO': gettextCatalog.getString('Manufacturing Order'),
      'PO': gettextCatalog.getString('Purchase Order'),
      'DO': gettextCatalog.getString('Distribution Order'),
      'STCK': gettextCatalog.getString('Stock'),
      'DLVR': gettextCatalog.getString('Delivery'),
    };

    function getHeight(gutter) {
      if (preferences && preferences['height'])
        return preferences['height'] - (gutter || 25);
      else
        return 220;
    }
    $scope.getHeight = getHeight;

    function hideColumn(col) {
      var idx = $scope.$parent.kanbancolumns.indexOf(col);
      $scope.$parent.kanbancolumns.splice(idx, 1);
      PreferenceSvc.save("columns", $scope.$parent.kanbancolumns);
    };
    $scope.hideColumn = hideColumn;
    $scope.grid = grid;

    // Handler for selecting a card
    function selectCard(opplan) {
      if ($scope.curselected) {
        if ($scope.curselected.reference && $scope.curselected.reference == opplan.reference && opplan.selected)
          return;
        if ($scope.curselected.operationplan__reference && $scope.curselected.operationplan__reference == opplan.reference && opplan.selected)
          return;
        delete $scope.curselected.selected;
      }
      opplan.selected = true;
      $scope.curselected = opplan;
      $scope.$parent.displayInfo(opplan);
      angular.element(document).find("#delete_selected, #gridactions").prop("disabled", false);
    };
    $scope.selectCard = selectCard;

    $scope.$on('selectedEdited', function (event, field, oldvalue, newvalue) {
      if ($scope.curselected === null) return;
      if (field == "loadplans") {
        // Special logic to convert from detail-opplan to card change
        var res = [];
        angular.forEach(newvalue, function (theloadplan) {
          res.push([theloadplan.resource.name, theloadplan.quantity]);
        });
        $scope.changeCard($scope.curselected, "resource", $scope.curselected.resource, res);
        $scope.curselected["resource"] = res;
      }
      else
        $scope.changeCard($scope.curselected, field, oldvalue, newvalue);
      if (field === "status") {
        var idx = $scope.kanbanoperationplans[oldvalue].rows.indexOf($scope.curselected);
        if (idx != -1) {
          $scope.kanbanoperationplans[oldvalue].rows.splice(idx, 1);
          $scope.kanbanoperationplans[newvalue].rows.unshift($scope.curselected);
          $scope.kanbanoperationplans[oldvalue].records--;
          $scope.kanbanoperationplans[newvalue].records++;
        }
      }
      if (field != "loadplans") {
        if ($scope.curselected.hasOwnProperty("operationplan__" + field))
          $scope.curselected["operationplan__" + field] = newvalue;
        else
          $scope.curselected[field] = newvalue;
      }
    });

    function changeCard(opplan, field, oldvalue, newvalue) {
      if (!opplan.hasOwnProperty(field + "Original"))
        opplan[field + "Original"] = oldvalue;
      opplan.dirty = true;
      angular.element(document).find("#save, #undo")
        .removeClass("btn-primary btn-danger")
        .addClass("btn-danger")
        .prop("disabled", false);
      $(window).off('beforeunload', upload.warnUnsavedChanges);
      $(window).on('beforeunload', upload.warnUnsavedChanges);
      if (newvalue !== undefined)
        $scope.$parent.$broadcast("cardChanged", field, oldvalue, newvalue);
    };
    $scope.changeCard = changeCard;

    // Handlers for dragging cards and columns
    function HandlerDragOver(event) {
      event.preventDefault();
    }

    function HandlerDrop(event) {
      var endvalue = $(event.target).closest("div[data-column]").attr("data-column");
      if (endvalue) {
        var startvalue = event.originalEvent.dataTransfer.getData("startcolumn");
        var startindex = event.originalEvent.dataTransfer.getData("startindex");
        if (startindex !== "undefined") {
          // Dragging a card
          var endindex = $(event.target).closest(".card");
          if (endindex) endindex = endindex.attr("data-index");
          $scope.$apply(function () {
            var o = $scope.kanbanoperationplans[startvalue].rows[startindex];
            $scope.kanbanoperationplans[startvalue].rows.splice(startindex, 1);
            if (endindex) {
              // Insert in the middle
              $scope.kanbanoperationplans[endvalue].rows.splice(
                endindex > startindex && endvalue == startvalue ? endindex - 1 : endindex, 0, o
              );
            }
            else
              // Insert at the top
              $scope.kanbanoperationplans[endvalue].rows.unshift(o);
            $scope.kanbanoperationplans[startvalue].records--;
            $scope.kanbanoperationplans[endvalue].records++;

            angular.element(document).find("#save, #undo")
              .removeClass("btn-primary btn-danger")
              .addClass("btn-danger")
              .prop("disabled", false);
            $(window).off('beforeunload', upload.warnUnsavedChanges);
            $(window).on('beforeunload', upload.warnUnsavedChanges);

            // Detect card changes (including reverting to the original situation)
            if (o.hasOwnProperty("operationplan__status")) {
              if (!o.hasOwnProperty("operationplan__statusOriginal")) {
                if (o.operationplan__status != endvalue) {
                  o.operationplan__statusOriginal = o.operationplan__status;
                  o.operationplan__status = endvalue;
                  o.status = endvalue;
                  o.dirty = true;
                }
              }
              else {
                if (o.operationplan__statusOriginal == endvalue) {
                  o.dirty = false;
                  delete o.operationplan__statusOriginal;
                } else {
                  o.dirty = true;
                }
                o.operationplan__status = endvalue;
                o.status = envalue;
              }
            }
            else {
              if (!o.hasOwnProperty("statusOriginal")) {
                if (o.status != endvalue) {
                  o.statusOriginal = o.status;
                  o.status = endvalue;
                  o.dirty = true;
                }
              }
              else {
                if (o.statusOriginal == endvalue) {
                  o.dirty = false;
                  delete o.statusOriginal;
                } else {
                  o.dirty = true;
                }
                o.status = endvalue;
              }
            }
            $scope.$parent.$broadcast("cardChanged", "status", o.statusOriginal, o.status);
          });
        }
        else {
          // Dragging a column
          $scope.$apply(function () {
            var startindex = $scope.kanbancolumns.indexOf(startvalue);
            var endindex = $scope.kanbancolumns.indexOf(endvalue);
            var tmp = $scope.kanbancolumns[startindex];
            $scope.kanbancolumns[startindex] = $scope.kanbancolumns[endindex];
            $scope.kanbancolumns[endindex] = tmp;
            PreferenceSvc.save("columns", $scope.$parent.kanbancolumns);
          });
        }
      }
      event.preventDefault();
    }

    function HandlerDragStart(event) {
      event.originalEvent.dataTransfer.setData(
        "startindex",
        $(event.target).attr("data-index")
      );
      event.originalEvent.dataTransfer.setData(
        "startcolumn",
        $(event.target).closest("div[data-column]").attr("data-column")
      );
      event.stopPropagation();
    };

    function enableDragDrop() {
      $elem.on('dragover', 'div[data-column], .card', HandlerDragOver);
      $elem.on('drop', 'div[data-column]', HandlerDrop);
      $elem.on('dragstart', 'div[data-column] .panel .card-header, .card', HandlerDragStart);
    }
    $scope.enableDragDrop = enableDragDrop;

    function disableDragDrop() {
      $elem.off('dragover', 'div[data-column], .card', HandlerDragOver);
      $elem.off('drop', 'div[data-column]', HandlerDrop);
      $elem.off('dragstart', 'div[data-column] .panel .card-header, .card', HandlerDragStart);
    }
    $scope.disableDragDrop = disableDragDrop;

    $scope.$on('duplicateOperationplan', function (event, card, clone) {
      $scope.selectCard(clone);
    });

    $scope.$on('changeMode', function (event, mode) {
      $scope.mode = mode;
      if ($scope.editable && mode == "kanban")
        enableDragDrop();
      else
        disableDragDrop();
    });

    if ($scope.editable && mode == "kanban")
      enableDragDrop();
  }
}

/*
 * Copyright (C) 2023 by frePPLe bv
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
 */

angular.module('operationplandetailapp').directive('showGanttDrv', showGanttDrv);

showGanttDrv.$inject = ['$window', 'gettextCatalog', 'OperationPlan', 'PreferenceSvc'];

function showGanttDrv($window, gettextCatalog, OperationPlan, PreferenceSvc) {
  'use strict';

  var directive = {
    restrict: 'EA',
    scope: {
      ganttoperationplans: '=',
      editable: '='
    },
    templateUrl: '/static/operationplandetail/gantt.html',
    link: linkfunc
  };
  return directive;

  function linkfunc($scope, $elem, attrs) {
    $scope.rowheight = 25;
    $scope.curselected = null;
    $scope.colstyle = 'col-md-1';
    $scope.type = 'PO';
    $scope.admin_escape = admin_escape;
    $scope.url_prefix = url_prefix;
    $scope.mode = mode;

    $scope.$watch('ganttoperationplans', function () {
      $scope.drawGantt();
    });

    function getHeight(gutter) {
      if (preferences && preferences['height'])
        return preferences['height'] - (gutter || 25);
      else
        return 220;
    }
    $scope.getHeight = getHeight;

    function getDirtyCards() {
      console.log("getting changes");
      return 111;
    }
    $scope.getDirtyCards = getDirtyCards;

    function findOperationPlan(ref) {
      if (ref === null) return null;
      return $scope.ganttoperationplans.rows ?
        $scope.ganttoperationplans.rows.find(e => { return e.operationplan__reference == ref; }) :
        null;
    }
    $scope.findOperationPlan = findOperationPlan;

    function buildtooltip() {
      var opplan = $scope.findOperationPlan($(this).attr("data-reference"));
      var extra = '';
      var thedelay = Math.round(opplan.operationplan__delay / 8640) / 10;
      if (thedelay < 0.1)
        thedelay = "" + (-thedelay) + " " + gettext("days early");
      else if (thedelay > 0.1)
        thedelay = "" + thedelay + " " + gettext("days late");
      else
        thedelay = gettext("on time");
      if (opplan.operationplan__operation__description)
        extra += gettext('description') + ": " + opplan.operationplan__operation__description + '<br>';
      if (opplan.operationplan__batch)
        extra += gettext('batch') + ": " + opplan.operationplan__batch + '<br>';
      if (opplan.operationplan__type === 'MO') {
        return gettext('manufacturing order') + '<br>' +
          opplan.operationplan__operation__name + '<br>' +
          gettext('reference') + ": " + opplan.operationplan__reference + '<br>' +
          extra +
          gettext('start') + ": " + moment(opplan.operationplan__startdate).format(datetimeformat) + '<br>' +
          gettext('end') + ": " + moment(opplan.operationplan__enddate).format(datetimeformat) + '<br>' +
          gettext('quantity') + ": " + grid.formatNumber(opplan.operationplan__quantity) + "<br>" +
          gettext('criticality') + ": " + Math.round(opplan.operationplan__criticality) + "<br>" +
          gettext('delay') + ": " + thedelay + "<br>" +
          gettext('status') + ": " + gettext(opplan.operationplan__status) + "<br>";
      }
      else if ($(this).attr("data-type") === 'PO') {
        return gettext('purchase order') + '<br>' +
          opplan.operationplan__item__name + ' @ ' + opplan.operationplan__location__name + '<br>' +
          gettext('reference') + ": " + opplan.operationplan__reference + '<br>' +
          extra +
          gettext('start') + ": " + moment(opplan.operationplan__startdate).format(datetimeformat) + '<br>' +
          gettext('end') + ": " + moment(opplan.operationplan__enddate).format(datetimeformat) + '<br>' +
          gettext('quantity') + ": " + grid.formatNumber(opplan.operationplan__quantity) + "<br>" +
          gettext('criticality') + ": " + opplan.operationplan__criticality + "<br>" +
          gettext('delay') + ": " + thedelay + "<br>" +
          gettext('status') + ": " + gettext(opplan.operationplan__status) + "<br>";
      }
      else if ($(this).attr("data-type") === 'DO') {
        return gettext('distribution order') + '<br>' +
          opplan.operationplan__item__name + ' @ ' + opplan.operationplan__location__name + '<br>' +
          gettext('origin') + ": " + opplan.operationplan__origin__name + '<br>' +
          gettext('reference') + ": " + opplan.operationplan__reference + '<br>' +
          extra +
          gettext('start') + ": " + moment(opplan.operationplan__startdate).format(datetimeformat) + '<br>' +
          gettext('end') + ": " + moment(opplan.operationplan__enddate).format(datetimeformat) + '<br>' +
          gettext('quantity') + ": " + grid.formatNumber(opplan.operationplan__quantity) + "<br>" +
          gettext('criticality') + ": " + opplan.operationplan__criticality + "<br>" +
          gettext('delay') + ": " + thedelay + "<br>" +
          gettext('status') + ": " + gettext(opplan.operationplan__status) + "<br>";
      }
      else if ($(this).attr("data-type") === 'STCK') {
        return gettext('inventory') + '<br>' +
          opplan.operationplan__item__name + ' @ ' + opplan.operationplan__location__name + '<br>' +
          gettext('quantity') + ": " + grid.formatNumber(opplan.operationplan__quantity) + "<br>";
      }
      else if ($(this).attr("data-type") === 'DLVR') {
        return gettext('customer delivery') + '<br>' +
          extra +
          opplan.operationplan__item__name + ' @ ' + opplan.operationplan__location__name + '<br>' +
          gettext('demand') + ": " + opplan.operationplan__demand__name + '<br>' +
          gettext('start') + ": " + moment(opplan.operationplan__startdate).format(datetimeformat) + '<br>' +
          gettext('end') + ": " + moment(opplan.operationplan__enddate).format(datetimeformat) + '<br>' +
          gettext('quantity') + ": " + grid.formatNumber(opplan.operationplan__quantity) + "<br>" +
          gettext('criticality') + ": " + opplan.operationplan__criticality + "<br>" +
          gettext('delay') + ": " + thedelay + "<br>" +
          gettext('status') + ": " + gettext(opplan.operationplan__status) + "<br>";
      }
    }
    $scope.buildtooltip = buildtooltip;

    function buildcolor(rowdata) {
      if (rowdata.operationplan__reference === $scope.curselected)
        // Currently selected
        return "black";

      // The logic here needs to be in sync with the color formatter in the frepple.js file
      var thenumber = parseInt(rowdata['operationplan__color']);
      if (rowdata['operationplan__inventory_item'] || rowdata['operationplan__leadtime']) {
        if (!isNaN(thenumber)) {
          if (thenumber >= 100 && thenumber < 999999)
            return '#008000';
          else if (thenumber === 0)
            return '#f00';
          else if (thenumber === 999999)
            return 'white';
          else {
            thenumber = Math.round(thenumber / 100 * 255);
            return 'rgb(' + 255 + ',' + thenumber + ',' + 0 + ')';
          }
        }
      } else {
        var thedelay = Math.round(parseInt(rowdata['operationplan__delay']) / 8640) / 10;
        if (parseInt(rowdata['operationplan__criticality']) === 999)
          return '#f00';
        else if (thedelay < 0)
          return '#008000';
        else if (thedelay === 0)
          return '#008000';
        else if (thedelay > 0) {
          if (isNaN(thenumber))
            thenumber = Math.max(0, Math.min(100, 100 - thedelay));
          if (thenumber > 100 || thenumber < 0)
            return '#f00';
          else
            return 'rgb(' + 255 + ',' + Math.round(thenumber / 100 * 255) + ',' + 0 + ')';
        }
      }
      return 'rgb(111,111,255)';
    }
    $scope.buildcolor = buildcolor;

    function time2scale(d) {
      return Math.round(10000 * (d - viewstart) / (viewend - viewstart));
    }
    $scope.time2scale = time2scale;

    function duration2scale(d) {
      return Math.round(10000 * d / (viewend - viewstart));
    }
    $scope.duration2scale = duration2scale;

    function drawGantt() {
      var width = $("#ganttgraph").width();
      var scale = (width - 200) / 10000;
      if (!$scope.ganttoperationplans.rows) return;
      var data = '<table class="table" style="table-layout: fixed"><tr><th class="align-middle" style="width:200px">' + gettext("resource") + '</th><th style="overflow-x: scroll; width:' + width + 'px" id="ganttheader"></th></tr>';
      var curresource;
      var first = true;
      var layer = [];
      var svgdata = "";
      for (var opplan of $scope.ganttoperationplans.rows) {
        if (opplan.resource != curresource) {
          curresource = opplan.resource;
          if (!first)
            data += '<svg width="100%" height="'
              + (layer.length * $scope.rowheight)
              + 'px"><g class="ganttrow" transform="scale(' + scale + ',1) translate(0,' + ((layer.length - 1) * $scope.rowheight) + ')" title="' + layer.length + '">'
              + svgdata + "</g></svg></td></tr>";
          first = false;
          data += "<tr><td>" + opplan.resource + '</td><td style="width: ' + width + 'px">';
          layer = [];
          svgdata = "";
        }

        var row = 0;
        for (; row < layer.length; ++row) {
          if (new Date(opplan["startdate"]) >= layer[row] && (opplan["enddate"] != opplan["startdate"])) {
            layer[row] = new Date(opplan["enddate"]);
            break;
          }
        };
        if (row >= layer.length) layer.push(new Date(opplan["enddate"]));

        svgdata += '<rect class="opplan" x="' + time2scale(new Date(opplan.startdate))
          + '" y="' + (-row * $scope.rowheight)
          + '" fill="' + buildcolor(opplan)
          + '" width="' + duration2scale(opplan.enddate - opplan.startdate)
          + '" height="' + $scope.rowheight
          + '" data-reference="' + encodeURI(opplan.operationplan__reference) + '"';
        if (opplan["status"] == "proposed")
          svgdata += ' fill-opacity="0.5"/>';
        else
          svgdata += '/>';
      }
      if (!first)
        data += '<svg width = "100%" height = "'
          + (layer.length * $scope.rowheight) + ''
          + 'px"><g class="ganttrow" transform="scale(' + scale + ',1) translate(0,' + ((layer.length - 1) * $scope.rowheight) + ')" title="' + layer.length + '">'
          + svgdata + "</g></svg></td></tr>";
      data += "</table>";
      angular.element(document).find('#ganttgraph').empty().append(data);
      gantt.header("#ganttheader");

      $('svg rect').on("click", function (d) {
        var prev = $scope.findOperationPlan($scope.curselected);
        if (prev) {
          $scope.curselected = null;
          $('svg rect[data-reference="' + admin_escape(prev.operationplan__reference) + '"]')
            .attr("fill", $scope.buildcolor(prev))
            .attr("fill-opacity", prev.operationplan__status == 'proposed' ? "0.5" : "1");
        }
        var ref = $(d.target).attr("data-reference");
        var opplan = $scope.findOperationPlan(ref);
        if (opplan) {
          $(d.target).attr("fill", "black").attr("fill-opacity", "1");
          opplan.id = ref;
        }
        $scope.curselected = opplan ? opplan.operationplan__reference : null;
        $scope.$parent.displayInfo(opplan);
      }).
        each(function () {
          bootstrap.Tooltip.getOrCreateInstance($(this)[0], {
            title: $scope.buildtooltip,
            animation: false,
            html: true,
            container: 'body',
            trigger: 'hover',
            offset: '[0,10]',
            template: `<div class="tooltip opacity-100" role="tooltip">
                <div class="tooltip-arrow"></div>
                <div class="tooltip-inner bg-white text-start text-body fs-6 p-3"></div>
              </div>`
          });
        });
    }
    $scope.drawGantt = drawGantt;

    $scope.$on('zoom', function () {
      drawGantt();
    });

    $("#ganttheader").on("scroll", function (event) {
      gantt.scroll(event);
      drawGantt();
    });
  }
}

/*
 * Copyright (C) 2024 by frePPLe bv
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

angular.module('d3', [])

  // D3 Factory
  .factory('d3service', function() {
    /* this place can be used to declare locals or other D3.js
       specific configurations. */

    return d3;
  });
/*
 * Copyright (C) 2024 by frePPLe bv
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

angular.module('operationplandetailapp').directive('showinventorydataDrv', showinventorydataDrv);

showinventorydataDrv.$inject = ['$window', '$filter', 'gettextCatalog'];

function showinventorydataDrv($window, $filter, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: { operationplan: '=data' },
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    scope.$watchGroup(['operationplan.id', 'operationplan.inventoryreport.length'], function (newValue, oldValue) {
      angular.element(document).find('#attributes-inventorydata').empty().append(
        '<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_inventorydata" aria-expanded="false" aria-controls="widget_inventorydata">' +
        '<h5 class="card-title text-capitalize fs-5 me-auto">' +
        gettextCatalog.getString("inventory") +
        '</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>' +
        '<div class="card-body collapse' +
        (scope.$parent.widget[1]["collapsed"] ? '' : ' show') +
        '" id="widget_inventorydata"><div class="table-responsive">' +
        '<table class="table table-sm table-hover table-borderless">' + '<colgroup/>' +
        '<thead class="text-nowrap"></thead><tbody></tbody></table>' +
        '</div></div>'
      );
      var rows = ['<tr><td colspan="1">' + gettextCatalog.getString('no inventory information') + '</td></tr>'];
      var columnHeaders = ['<tr></tr>'];
      var columnGroups = ['<col>'];

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('inventoryreport')) {
          columnHeaders = ['<tr class="text-center"><td style="position: sticky; left: 0px; background:var(--bs-card-bg)"></td>'];
          columnGroups = ['<col>'];
          rows = [
            '<tr><td style="position: sticky; left: 0px; background:var(--bs-card-bg)"><span class="text-capitalize text-nowrap">' + gettextCatalog.getString("start inventory") + '</span></td>',
            '<tr><td style="position: sticky; left: 0px; background:var(--bs-card-bg)"><span class="text-capitalize text-nowrap">' + gettextCatalog.getString("safety stock") + '</span></td>',
            '<tr><td style="position: sticky; left: 0px; background:var(--bs-card-bg)"><span class="text-capitalize text-nowrap">' + gettextCatalog.getString("total consumed") + '</span></td>',
            '<tr><td style="position: sticky; left: 0px; background:var(--bs-card-bg)"><span class="px-3 text-capitalize text-nowrap">' + gettextCatalog.getString("consumed proposed") + '</span></td>',
            '<tr><td style="position: sticky; left: 0px; background:var(--bs-card-bg)"><span class="px-3 text-capitalize text-nowrap">' + gettextCatalog.getString("consumed confirmed") + '</span></td>',
            '<tr><td style="position: sticky; left: 0px; background:var(--bs-card-bg)"><span class="text-capitalize text-nowrap">' + gettextCatalog.getString("total produced") + '</span></td>',
            '<tr><td style="position: sticky; left: 0px; background:var(--bs-card-bg)"><span class="px-3 text-capitalize text-nowrap">' + gettextCatalog.getString("produced proposed") + '</span></td>',
            '<tr><td style="position: sticky; left: 0px; background:var(--bs-card-bg)"><span class="px-3 text-capitalize text-nowrap">' + gettextCatalog.getString("produced confirmed") + '</span></td>',
            '<tr><td style="position: sticky; left: 0px; background:var(--bs-card-bg)"><span class="text-capitalize text-nowrap">' + gettextCatalog.getString("end inventory") + '</span></td>',
          ];
          angular.forEach(scope.operationplan.inventoryreport, function (inventoryData, colIndex) {
            columnHeaders.push('<td id="inventorydata"' + inventoryData[0].replace(" ", "") +
              '" style="background: var(--bs-card-bg);" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-custom-class="custom-tooltip"' +
              'data-bs-title="' + $filter('formatdate')(inventoryData[1]) + ' - ' + $filter('formatdate')(inventoryData[2]) + '">' +
              (inventoryData[3] ? '<i class="text-capitalize">' : '<b class="text-capitalize">')
              + inventoryData[0] + (inventoryData[3] ? '</i></td>' : '</b></td>')
            );
            let gradient_idx = null;
            let isRed = false;
            let gradientBackground = false;
            let cellValue = 0;
            for (const i in inventoryData.slice(4)) {
              cellValue = $filter('number')(inventoryData.slice(4)[i]);
              if (i == 0) {
                isRed = inventoryData.slice(4)[0] < inventoryData.slice(4)[1] || inventoryData.slice(4)[0] < 0;
              } else if (i > 0) {
                isRed = false;
              };
              if (!(i == 0 || i == 8) && cellValue == 0) {
                cellValue = "";
              }
              rows[i] += '<td class="text-center" style="' + (isRed?'color: red; font-weight: bold;">':'">') + cellValue + '</td>';
            }

            if (isRed) {
              gradient_idx = 0;
              gradientBackground = true;
            } else if (inventoryData[4] >= inventoryData[5] || inventoryData[5] === 0) {
              gradientBackground = false;
            } else {
              gradient_idx = Math.round(inventoryData[4] / inventoryData[5] * 165);
              gradientBackground = true;
            };

            columnGroups.push('<col id="col' + colIndex + '" style="' + (gradientBackground ? 'background: linear-gradient(white 0%, rgba(255,'+gradient_idx+',0,0.2) 40%, rgba(255,'+gradient_idx+',0,0.2) 60%, white 100%);"':'background: var(--bs-card-bg);"') + '>');
          });
          columnHeaders.push('</tr>');
          rows = rows.map(x => x + '</tr>');
        }
      }

      angular.element(document).find('#attributes-inventorydata thead').append(columnHeaders.join(""));
      angular.element(document).find('#attributes-inventorydata tbody').append(rows.join(""));
      angular.element(document).find('#attributes-inventorydata colgroup').append(columnGroups.join(""));

      angular.element(elem).find('.collapse')
        .on("shown.bs.collapse", grid.saveColumnConfiguration)
        .on("hidden.bs.collapse", grid.saveColumnConfiguration);

      let widgetTooltipTriggerList = document.querySelectorAll('#attributes-inventorydata [data-bs-toggle="tooltip"]');

      let widgetTooltipList = [...widgetTooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl, { container: 'body', offset: '[0,5]' }));
    }); //watch end

  } //link end
} //directive end

/*
 * Copyright (C) 2024 by frePPLe bv
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

angular.module('operationplandetailapp')
  .directive('showinventorygraphDrv', showinventorygraphDrv);

showinventorygraphDrv.$inject = ['$window', '$filter', 'gettextCatalog', 'd3service'];

function showinventorygraphDrv($window, $filter, gettextCatalog) {
  return {
    restrict: 'EA', scope: { operationplan: '=data' }, link: linkfunc
  };

  function linkfunc(scope, elem, attrs, d3service) {
    scope.$watchGroup(['operationplan.id', 'operationplan.inventoryreport.length'], function (newValue, oldValue) {
      angular.element(document).find('#attributes-inventorygraph').empty().append(
        [
          '<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_inventorygraph" aria-expanded="false" aria-controls="widget_inventorygraph">',
          '<h5 class="card-title text-capitalize fs-5 me-auto">' + gettextCatalog.getString("inventory") +
          '</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>',
          '<div class="card-body collapse overflow-hidden' +
          (scope.$parent.widget[1]["collapsed"] ? '' : ' show') +
          '" id="widget_inventorygraph">',
          '<table class="table table-sm table-borderless">',
          '<tbody><tr><td role="gridcell" aria-describedby="grid_graph">',
          '<div class="graph" style="height:' + $("#attributes-operationplan .card-body").height() + '"></div>',
          '</td></tr></tbody>',
          '</table>',
          '</div>'
        ].join("\n"));
      let domain_x = [];

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('inventoryreport')) {
          const timebuckets = scope.operationplan.inventoryreport;

          let margin = { top: 10, right: 10, bottom: 30, left: 40 };
          let width = Math.max($("#attributes-operationplan .card-body").width() - margin.left - margin.right, 0);
          let height = $("#attributes-operationplan .card-body").height() - margin.top - margin.bottom;

          // Define X-axis
          let bucketnamelength = 0;
          for (let i of timebuckets) {
            domain_x.push(i[0]);
            bucketnamelength = Math.max(i[0].length, bucketnamelength);
          }
          let x = d3.scale.ordinal()
            .domain(domain_x)
            .rangeRoundBands([0, width], 0);
          let x_width = x.rangeBand();

          // // Build the data for d3
          let max_y = 0;
          let min_y = 0;
          let data = [];
          for (const bctk of timebuckets) {
            data.push({
              'bucket': bctk[0],
              'startinv': bctk[4],
              'safetystock': bctk[5],
              'consumed_total': bctk[6],
              'consumed_proposed': bctk[7],
              'consumed_confirmed': bctk[8],
              'produced_total': bctk[9],
              'produced_proposed': bctk[10],
              'produced_confirmed': bctk[11],
              'endinv': bctk[12],
            });

            //slice the first 4 strings from array to determine min and max
            let slicedbucket = bctk.slice(4 - bctk.length);
            var tmp = Math.min(...slicedbucket);
            if (tmp < min_y) min_y = tmp;
            tmp = Math.max(...slicedbucket);
            if (tmp > max_y) max_y = tmp;
          }

          // Define Y-axis
          var y = d3.scale.linear().rangeRound([height, 0]);

          // Create a new SVG element
          $($(".graph").get(0)).html("");
          let svg = d3.select($(".graph").get(0))
            .append("svg")
            .attr("class", "graphcell")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

          // Update the scale of the Y-axis by looking for the max value
          y.domain([min_y, max_y]);
          let y_zero = y(0);

          // Draw the bars
          let y_top, y_top_low;

          svg.selectAll("g")
            .data(data)
            .enter()
            .append("g")
            .attr("transform", function (d) {
              return "translate(" + x(d['bucket']) + ",0)";
            })
            .each(function (d) {
              let bucket = d3.select(this);
              if (d['produced_total'] > 0) {
                y_top = y(d['produced_total']);
                y_top_low = y(d['produced_confirmed']);
                if (d['produced_confirmed'] > 0) bucket.append("rect")
                  .attr("width", x_width / 2)
                  .attr("height", y_zero - y_top_low)
                  .attr("x", x_width / 2)
                  .attr("y", y_top_low)
                  .style("fill", 'var(--frepple-color-produced-confirmed, #113C5E)');
                if (d['produced_proposed'] > 0) bucket.append("rect")
                  .attr("width", x_width / 2)
                  .attr("height", y_top_low - y_top)
                  .attr("x", x_width / 2)
                  .attr("y", y_top)
                  .style("fill", 'var(--frepple-color-produced, #2B95EC)');
              }
              if (d['consumed_total'] > 0) {
                y_top = y(d['consumed_total']);
                y_top_low = y(d['consumed_confirmed']);
                if (d['consumed_confirmed'] > 0) bucket.append("rect")
                  .attr("width", x_width / 2)
                  .attr("height", y_zero - y_top_low)
                  .attr("y", y_top_low)
                  .style("fill", 'var(--frepple-color-consumed-confirmed, #7B5E08)');
                if (d['consumed_proposed'] > 0) bucket.append("rect")
                  .attr("width", x_width / 2)
                  .attr("height", y_top_low - y_top)
                  .attr("y", y_top)
                  .style("fill", 'var(--frepple-color-consumed, #F6BD0F)');
              }
              bucket.append("rect")
                .attr("height", height)
                .attr("width", x_width)
                .attr("fill-opacity", function (d) {
                  if (d["startinv"] >= 0 && (d["startinv"] >= d["safetystock"] || d["safetystock"] === 0)) return 0; else return 0.2;
                })
                .attr("fill", function (d) {
                  let gradient_idx = undefined;
                  if (d["startinv"] < 0) gradient_idx = 0; else if (d["startinv"] >= d["safetystock"] || d["safetystock"] === 0) return null; else gradient_idx = Math.round(d["startinv"] / d["safetystock"] * 165);
                  let grad = d3.selectAll("#gradient_" + gradient_idx);
                  if (grad.size() === 0) {
                    let newgrad = d3.select("#gradients")
                      .append("linearGradient")
                      .attr("id", "gradient_" + gradient_idx)
                      .attr("x1", 0)
                      .attr("x2", 0)
                      .attr("y1", 0)
                      .attr("y2", 1);
                    newgrad.append("stop")
                      .attr("offset", "0%")
                      .attr("stop-color", "white")
                      .attr("stop-opacity", 1);
                    newgrad.append("stop")
                      .attr("offset", "40%")
                      .attr("stop-color", "rgb(255," + gradient_idx + ",0)")
                      .attr("stop-opacity", 1);
                    newgrad.append("stop")
                      .attr("offset", "60%")
                      .attr("stop-color", "rgb(255," + gradient_idx + ",0)")
                      .attr("stop-opacity", 1);
                    newgrad.append("stop")
                      .attr("offset", "100%")
                      .attr("stop-color", "white")
                      .attr("stop-opacity", 0);
                  }
                  return "url(#gradient_" + gradient_idx + ")";
                })
                .on("click", function (d) {
                  if (d3.event.defaultPrevented || (d['produced_total'] === 0 && d['consumed_total'] === 0)) return;
                  d3.select("#tooltip").style('display', 'none');

                  window.location = url_prefix + "/data/input/operationplanmaterial/buffer/" + admin_escape(d['buffer']) + "/?noautofilter&flowdate__gte=" + timebuckets[d['bucket']]['startdate'] + "&flowdate__lt=" + timebuckets[d['bucket']]['enddate'];

                  d3.event.stopPropagation();
                })
                .on("mouseenter", function (d) {
                  let tiptext = [];
                  if (d['history']) {
                    tiptext = [
                      '<div style="text-align:center; font-style:italic">',
                      gettextCatalog.getString('Archived'),
                      d['bucket'],
                      '</div><table><tr><td class="text-capitalize">',
                      gettextCatalog.getString('start inventory'),
                      '</td><td style="text-align:right">',
                      $filter("number")(d['startinv']),
                      '</td></tr><tr><td class="text-capitalize">',
                      gettextCatalog.getString('safety stock'),
                      '</td><td style="text-align:right">',
                      $filter("number")(d['safetystock']),
                      '</td></tr></table>'
                    ].join("\n");
                  } else {
                    tiptext = [
                      '<div style="text-align:center; font-weight:bold">',
                      d['bucket'],
                      '</div><table><tr><td class="text-capitalize pe-3">',
                      gettextCatalog.getString('start inventory'),
                      '</td><td class="text-end">',
                      $filter('number')(d['startinv']),
                      '</td></tr><tr><td class="text-capitalize pe-3">',
                      gettextCatalog.getString('produced total'),
                      '</td><td class="text-end">+&nbsp;',
                      $filter('number')(d['produced_total']),
                      '</td></tr><tr><td class="text-capitalize pe-3 px-3">',
                      gettextCatalog.getString('produced proposed'),
                      '</td><td class="text-end">',
                      $filter('number')(d['produced_proposed']),
                      '</td></tr><tr><td class="text-capitalize pe-3 px-3">',
                      gettextCatalog.getString('produced confirmed'),
                      '</td><td class="text-end">',
                      $filter('number')(d['produced_confirmed']),
                      '</td></tr><tr><td class="text-capitalize pe-3">',
                      gettextCatalog.getString('consumed total'),
                      '</td><td class="text-end">-&nbsp;',
                      $filter('number')(d['consumed_total']),
                      '</td></tr><tr><td class="text-capitalize pe-3 px-3">',
                      gettextCatalog.getString('consumed proposed'),
                      '</td><td class="text-end">',
                      $filter('number')(d['consumed_proposed']),
                      '</td></tr><tr><td class="text-capitalize pe-3 px-3">',
                      gettextCatalog.getString('consumed confirmed'),
                      '</td><td class="text-end">',
                      $filter('number')(d['consumed_confirmed']),
                      '</td></tr><tr><td class="text-capitalize pe-3">',
                      gettextCatalog.getString('end inventory'),
                      '</td><td class="text-end">=&nbsp;',
                      $filter('number')(d['endinv']),
                      '</td></tr><tr><td class="text-capitalize pe-3">',
                      gettextCatalog.getString('safety stock'),
                      '</td><td class="text-end">',
                      $filter('number')(d['safetystock']),
                      '</td></tr></table>'
                    ].join("\n");
                  }
                  graph.showTooltip(tiptext);
                })
                .on("mouseleave", graph.hideTooltip)
                .on("mousemove", graph.moveTooltip)
            })

          // Display Y-Axis
          var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left")
            .tickFormat(d3.format("s"));
          svg.append("g")
            .attr("class", "y axis")
            .call(yAxis);

          if (min_y < 0 && max_y > 0)
            svg.append("line")
              .attr("x1", 0)
              .attr("x2", width)
              .attr("y1", y(0))
              .attr("y2", y(0))
              .attr("stroke-width", 1)
              .attr("stroke", "black")
              .attr("shape-rendering", "crispEdges");

          // Draw startoh line
          var line = d3.svg.line()
            .x(function (d) { return x(d['bucket']) + x_width / 2; })
            .y(function (d) { return y(d['startinv']); });
          svg.append("svg:path")
            .attr('class', 'graphline')
            .attr("stroke", 'var(--frepple-color-inventory, #8BBA00)')
            .attr("d", line(data));

          // Draw safety stock line
          var line = d3.svg.line()
            .x(function (d) { return x(d['bucket']) + x_width / 2; })
            .y(function (d) { return y(d['safetystock']); });
          svg.append("svg:path")
            .attr('class', 'graphline')
            .attr("stroke", 'var(--frepple-color-safetystock, #FF0000)')
            .attr("d", line(data));

          var nth = Math.ceil(timebuckets.length / width * bucketnamelength * 10);

          // Display X-axis for a single buffer
          var myticks = [];
          for (var i in timebuckets)
            if (i % nth == 0) myticks.push(timebuckets[i][0]);
          var xAxis = d3.svg.axis()
            .scale(x)
            .tickValues(myticks)
            .orient("bottom");
          svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

          angular.element(elem).find('.collapse')
            .on("shown.bs.collapse", grid.saveColumnConfiguration)
            .on("hidden.bs.collapse", grid.saveColumnConfiguration);

          let widgetTooltipTriggerList = document.querySelectorAll('#attributegraph [data-bs-toggle="tooltip"]');
          let widgetTooltipList = [...widgetTooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
      }
    })//watch end



  } //link end
} //directive end
