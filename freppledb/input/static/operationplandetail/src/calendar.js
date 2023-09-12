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