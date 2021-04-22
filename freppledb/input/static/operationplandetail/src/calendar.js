/*
 * Copyright (C) 2020 by frePPLe bv
 *
 * This file is a heavily modified version of the code published under
 * MIT license on https://github.com/twinssbc/AngularJS-ResponsiveCalendar.
 * The changes are redistributed under the GNU Affero General Public License.
 *
 * The MIT License (MIT)
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
      function ($scope, $attrs, $parse, $interpolate, $log, dateFilter, gettextCatalog, calendarConfig, PreferenceSvc) {
        'use strict';
        var self = this,
            ngModelCtrl = {$setViewValue: angular.noop}; // nullModelCtrl;

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
            self.currentCalendarDate = new Date();
            if ($attrs.ngModel && !$scope.$parent.$eval($attrs.ngModel)) {
                $parse($attrs.ngModel).assign($scope.$parent, self.currentCalendarDate);
            }
        }

        $scope.getHeight = function(headerheight) {
          if (preferences && preferences['height'])
            return preferences['height'] - headerheight;
          else
            return 220 - headerheight;
        }

        $scope.displayEvent = function(opplan, dt) {
          switch ($scope.calendarmode) {
            case "duration":
              return true;
            case "start_end":
              return moment(opplan.startdate || opplan.event.startdate || opplan.enddate || opplan.event.enddate).isSame(dt.date, "day")
                || moment(opplan.enddate || opplan.event.enddate || opplan.startdate || opplan.event.startdate).isSame(dt.date, "day");
            case "start":
              return moment(opplan.startdate || opplan.event.startdate || opplan.enddate || opplan.event.enddate).isSame(dt.date, "day");
            case "end":
              return moment(opplan.enddate || opplan.event.enddate || opplan.startdate || opplan.event.startdate).isSame(dt.date, "day");
          }
        }

        $scope.isStart = function(opplan, dt) {
          var d = opplan.startdate || (opplan.event && opplan.event.startdate);
          return d ? moment(d).isSame(dt.date, "day") : false;
        }

        $scope.isEnd = function(opplan, dt) {
          // Subtract 1 microsecond to assure that an end date of 00:00:00 is seen
          // as ending on the previous day.
          var d = opplan.enddate || (opplan.event && opplan.event.enddate);
          return d ? moment(d - 1).isSame(dt.date, "day") : false;
        }

        $scope.displayEvent = function(opplan, dt) {
          switch ($scope.calendarmode) {
            case "duration":
              return true;
            case "start_end":
              // Subtract 1 microsecond to assure that an end date of 00:00:00 is seen
              // as ending on the previous day.
              return ((opplan.startdate || (opplan.event && opplan.event.startdate)) ?
                moment(opplan.startdate || (opplan.event && opplan.event.startdate)).isSame(dt.date, "day") :
                false)
                ||
                ((opplan.enddate || (opplan.event && opplan.event.enddate)) ?
                moment((opplan.enddate || (opplan.event && opplan.event.enddate)) - 1).isSame(dt.date, "day") :
                false);
            case "start":
              return (opplan.startdate || (opplan.event && opplan.event.startdate)) ?
                moment(opplan.startdate || (opplan.event && opplan.event.startdate)).isSame(dt.date, "day") :
                false;
            case "end":
              // Subtract 1 microsecond to assure that an end date of 00:00:00 is seen
              // as ending on the previous day.
              return (opplan.enddate || (opplan.event && opplan.event.enddate)) ?
                moment((opplan.enddate || (opplan.event && opplan.event.enddate)) - 1).isSame(dt.date, "day") :
                false;
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

        function overlap(event1, event2) {
            var earlyEvent = event1,
                lateEvent = event2;
            if (event1.startIndex > event2.startIndex || (event1.startIndex === event2.startIndex && event1.startOffset > event2.startOffset)) {
                earlyEvent = event2;
                lateEvent = event1;
            }

            if (earlyEvent.endIndex <= lateEvent.startIndex) {
                return false;
            } else {
                return !(earlyEvent.endIndex - lateEvent.startIndex === 1 && earlyEvent.endOffset + lateEvent.startOffset >= self.hourParts);
            }
        }

        function calculatePosition(events) {
            var i,
                j,
                len = events.length,
                maxColumn = 0,
                col,
                isForbidden = new Array(len);

            for (i = 0; i < len; i += 1) {
                for (col = 0; col < maxColumn; col += 1) {
                    isForbidden[col] = false;
                }
                for (j = 0; j < i; j += 1) {
                    if (overlap(events[i], events[j])) {
                        isForbidden[events[j].position] = true;
                    }
                }
                for (col = 0; col < maxColumn; col += 1) {
                    if (!isForbidden[col]) {
                        break;
                    }
                }
                if (col < maxColumn) {
                    events[i].position = col;
                } else {
                    events[i].position = maxColumn++;
                }
            }
        }

        function calculateWidth(orderedEvents, hourParts) {
            var totalSize = 24 * hourParts,
                cells = new Array(totalSize),
                event,
                index,
                i,
                j,
                len,
                eventCountInCell,
                currentEventInCell;

            //sort by position in descending order, the right most columns should be calculated first
            orderedEvents.sort(function (eventA, eventB) {
                return eventB.position - eventA.position;
            });
            for (i = 0; i < totalSize; i += 1) {
                cells[i] = {
                    calculated: false,
                    events: []
                };
            }
            len = orderedEvents.length;
            for (i = 0; i < len; i += 1) {
                event = orderedEvents[i];
                index = event.startIndex * hourParts + event.startOffset;
                while (index < event.endIndex * hourParts - event.endOffset) {
                    cells[index].events.push(event);
                    index += 1;
                }
            }

            i = 0;
            while (i < len) {
                event = orderedEvents[i];
                if (!event.overlapNumber) {
                    var overlapNumber = event.position + 1;
                    event.overlapNumber = overlapNumber;
                    var eventQueue = [event];
                    while ((event = eventQueue.shift())) {
                        index = event.startIndex * hourParts + event.startOffset;
                        while (index < event.endIndex * hourParts - event.endOffset) {
                            if (!cells[index].calculated) {
                                cells[index].calculated = true;
                                if (cells[index].events) {
                                    eventCountInCell = cells[index].events.length;
                                    for (j = 0; j < eventCountInCell; j += 1) {
                                        currentEventInCell = cells[index].events[j];
                                        if (!currentEventInCell.overlapNumber) {
                                            currentEventInCell.overlapNumber = overlapNumber;
                                            eventQueue.push(currentEventInCell);
                                        }
                                    }
                                }
                            }
                            index += 1;
                        }
                    }
                }
                i += 1;
            }
        }

        self.placeEvents = function (orderedEvents) {
            calculatePosition(orderedEvents);
            calculateWidth(orderedEvents, self.hourParts);
        };
    }])
    .directive('calendar', function () {
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
                scope.curselected = null;

                if (ngModelCtrl)
                    calendarCtrl.init(ngModelCtrl);

                scope.$on('selectedEdited', function(event, field, oldvalue, newvalue) {
                  if (scope.curselected === null) return;
                  scope.changeCard(scope.curselected, field, oldvalue);
                  scope.curselected[field] = newvalue;
                });

                scope.$on('changeDate', function (event, direction) {
                    calendarCtrl.move(direction);
                });

                scope.$on('eventSourceChanged', function (event, value) {
                    calendarCtrl.onEventSourceChanged(value);
                });

                scope.$on('changeMode', function (event, mode) {
                    calendarCtrl.changeMode(mode);
                });

                scope.selectCard = function(opplan) {
                  if (scope.curselected) {
                     if (scope.curselected.reference == opplan.reference && opplan.selected)
                        return;
                     delete scope.curselected.selected;
                     }
                  opplan.selected = true;
                  scope.curselected = opplan;
                  scope.eventSelected({event:opplan});
                };

                scope.changeCard = function(opplan, field, oldvalue, newvalue) {
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
            }
        };
    })
    .directive('monthview', ['dateFilter', function (dateFilter) {
        'use strict';
        return {
            restrict: 'EA',
            replace: true,
            templateUrl: '/static/operationplandetail/month.html',
            require: ['^calendar', '?^ngModel'],
            link: function (scope, element, attrs, ctrls) {
                var ctrl = ctrls[0],
                    ngModelCtrl = ctrls[1];
                scope.showWeeks = ctrl.showWeeks;

                ctrl.mode = {
                    step: {months: 1}
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
                        current: ctrl.compare(date, new Date()) === 0
                    };
                }

                function compareEvent(event1, event2) {
                    return (event1.startdate ? event1.startdate : event1.enddate).getTime() -
                      (event2.startdate ? event2.startdate : event2.enddate);
                }

                ctrl._onDataLoaded = function () {
                    var eventSource = ctrl.eventSource,
                        len = eventSource ? eventSource.length : 0,
                        startdate = ctrl.range.startdate,
                        enddate = ctrl.range.enddate,
                        rows = scope.rows,
                        oneDay = 86400000,
                        eps = 0.001,
                        row,
                        date,
                        hasEvent = false,
                        keys = [];

                    if (rows.hasEvent) {
                        for (row = 0; row < 6; row += 1) {
                            for (date = 0; date < 7; date += 1) {
                                if (rows[row][date].hasEvent) {
                                    rows[row][date].events = null;
                                    rows[row][date].hasEvent = false;
                                }
                            }
                        }
                    }

                    for (var i = 0; i < len; i += 1) {
                        var event = eventSource[i];
                        var eventStartTime = event.startdate ? new Date(event.startdate) : null;
                        var eventEndTime = event.enddate ? new Date(event.enddate) : null;
                        var st;
                        var et;

                        if ((eventEndTime ? eventEndTime : eventStartTime) <= startdate ||
                          (eventStartTime ? eventStartTime : eventEndTime) >= enddate)
                            continue;
                        st = startdate;
                        et = enddate;
                        if (!eventEndTime) eventEndTime = eventStartTime;
                        if (!eventStartTime) eventStartTime = eventEndTime;

                        if (scope.grouping && event[scope.grouping] && !keys.includes(event[scope.grouping]))
                              keys.push(event[scope.grouping]);

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
                        var eventSet;
                        while (index < timeDifferenceEnd - eps) {
                            var rowIndex = Math.floor(index / 7);
                            var dayIndex = Math.floor(index % 7);
                            rows[rowIndex][dayIndex].hasEvent = true;
                            eventSet = rows[rowIndex][dayIndex].events;
                            if (eventSet) {
                                eventSet.push(event);
                            } else {
                                eventSet = [];
                                eventSet.push(event);
                                rows[rowIndex][dayIndex].events = eventSet;
                            }
                            index += 1;
                        }
                    }

                    for (row = 0; row < 6; row += 1) {
                        for (date = 0; date < 7; date += 1) {
                            if (rows[row][date].hasEvent) {
                                hasEvent = true;
                                rows[row][date].events.sort(compareEvent);
                            }
                        }
                    }
                    rows.hasEvent = hasEvent;

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

                ctrl.compare = function (date1, date2) {
                    return (new Date(date1.getFullYear(), date1.getMonth(), date1.getDate()) - new Date(date2.getFullYear(), date2.getMonth(), date2.getDate()) );
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
            }
        };
    }])
    .directive('weekview', ['dateFilter', function (dateFilter) {
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
                    step: {days: 7}
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

                function createDateObjects(startdate) {
                    var times = [],
                        row,
                        time,
                        currentHour = startdate.getHours(),
                        currentDate = startdate.getDate();

                    for (var hour = 0; hour < 24; hour += 1) {
                        row = [];
                        for (var day = 0; day < 7; day += 1) {
                            time = new Date(startdate.getTime());
                            time.setHours(currentHour + hour);
                            time.setDate(currentDate + day);
                            row.push({
                                date: time,
                                events: []
                            });
                        }
                        times.push(row);
                    }
                    return times;
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
                    var eventSource = ctrl.eventSource,
                        len = eventSource ? eventSource.length : 0,
                        startdate = ctrl.range.startdate,
                        enddate = ctrl.range.enddate,
                        rows = scope.rows,
                        dates = scope.dates,
                        oneHour = 3600000,
                        //add allday eps
                        eps = 0.016,
                        normalEventInRange = false,
                        day,
                        hour,
                        keys = [];

                    if (rows.hasEvent) {
                        for (day = 0; day < 7; day += 1) {
                            for (hour = 0; hour < 24; hour += 1) {
                                if (rows[hour][day].events) {
                                    rows[hour][day].events = null;
                                }
                            }
                        }
                        rows.hasEvent = false;
                    }

                    for (day = 0; day < 7; day += 1) {
                        if (dates[day].events) dates[day].events = null;
                    }

                    for (var i = 0; i < len; i += 1) {
                        var event = eventSource[i];
                        var eventStartTime = event.startdate ? new Date(event.startdate) : null;
                        var eventEndTime = event.enddate ? new Date(event.enddate) : null;

                        if ((eventEndTime ? eventEndTime : eventStartTime) <= startdate ||
                          (eventStartTime ? eventStartTime : eventEndTime) >= enddate)
                            continue;
                        normalEventInRange = true;
                        if (!eventEndTime) eventEndTime = eventStartTime;
                        if (!eventStartTime) eventStartTime = eventEndTime;

                        var timeDiff;
                        var timeDifferenceStart;
                        if (eventStartTime <= startdate) {
                            timeDifferenceStart = 0;
                        } else {
                            timeDiff = eventStartTime - startdate - (eventStartTime.getTimezoneOffset() - startdate.getTimezoneOffset()) * 60000;
                            timeDifferenceStart = timeDiff / oneHour;
                        }

                        var timeDifferenceEnd;
                        if (eventEndTime >= enddate) {
                            timeDiff = enddate - startdate - (enddate.getTimezoneOffset() - startdate.getTimezoneOffset()) * 60000;
                            timeDifferenceEnd = timeDiff / oneHour;
                        } else {
                            timeDiff = eventEndTime - startdate - (eventEndTime.getTimezoneOffset() - startdate.getTimezoneOffset()) * 60000;
                            timeDifferenceEnd = timeDiff / oneHour;
                        }

                        var startIndex = Math.floor(timeDifferenceStart);
                        var endIndex = Math.ceil(timeDifferenceEnd - eps);
                        var startRowIndex = startIndex % 24;
                        var dayIndex = Math.floor(startIndex / 24);
                        var endOfDay = dayIndex * 24;
                        var endRowIndex;

                        var startOffset = 0;
                        var endOffset = 0;
                        if (ctrl.hourParts !== 1) {
                            startOffset = Math.ceil((timeDifferenceStart - startIndex) * ctrl.hourParts);
                        }

                        do {
                            endOfDay += 24;
                            if (endOfDay <= endIndex) {
                                endRowIndex = 24;
                            } else {
                                endRowIndex = endIndex % 24;
                                if (ctrl.hourParts !== 1) {
                                    endOffset = Math.floor((endIndex - timeDifferenceEnd) * ctrl.hourParts);
                                }
                            }
                            var displayEvent = {
                                event: event,
                                startIndex: startRowIndex,
                                endIndex: endRowIndex,
                                startOffset: startOffset,
                                endOffset: endOffset
                            };
                            if (scope.grouping && event[scope.grouping] && !keys.includes(event[scope.grouping]))
                              keys.push(event[scope.grouping]);

                            if (rows[startRowIndex][dayIndex].events)
                                rows[startRowIndex][dayIndex].events.push(displayEvent);
                            else
                                rows[startRowIndex][dayIndex].events = [displayEvent];

                            if (dates[dayIndex].events)
                              dates[dayIndex].events.push(event);
                            else
                              dates[dayIndex].events = [event];

                            startRowIndex = 0;
                            startOffset = 0;
                            dayIndex += 1;
                        } while (endOfDay < endIndex);

                    }

                    if (scope.grouping) {
                      if (scope.groupingdir && scope.groupingdir == "desc")
                          scope.categories = keys.sort().reverse();
                      else
                          scope.categories = keys.sort();
                    }
                    else
                      scope.categories = ["dummy"];

                    if (normalEventInRange) {
                        for (day = 0; day < 7; day += 1) {
                            var orderedEvents = [];
                            for (hour = 0; hour < 24; hour += 1) {
                                if (rows[hour][day].events) {
                                    rows[hour][day].events.sort(compareEventByStartOffset);
                                    orderedEvents = orderedEvents.concat(rows[hour][day].events);
                                }
                            }
                            if (orderedEvents.length > 0) {
                                rows.hasEvent = true;
                                ctrl.placeEvents(orderedEvents);
                            }
                        }
                    }
                };

                ctrl._refreshView = function () {
                    var firstDayOfWeek = ctrl.range.startdate,
                        dates = getDates(firstDayOfWeek, 7),
                        weekNumberIndex,
                        weekFormatPattern = 'w',
                        title;

                    scope.rows = createDateObjects(firstDayOfWeek);
                    scope.dates = dates;
                    weekNumberIndex = ctrl.formatWeekTitle.indexOf(weekFormatPattern);
                    title = dateFilter(firstDayOfWeek, ctrl.formatWeekTitle);
                    if (weekNumberIndex !== -1)
                        title = title.replace(weekFormatPattern, getISO8601WeekNumber(firstDayOfWeek));
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

                function compareEventByStartOffset(eventA, eventB) {
                    return eventA.startOffset - eventB.startOffset;
                }

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
            }
        };
    }])
    .directive('dayview', ['dateFilter', function (dateFilter) {
        'use strict';
        return {
            restrict: 'EA',
            replace: true,
            templateUrl: '/static/operationplandetail/day.html',
            require: '^calendar',
            link: function (scope, element, attrs, ctrl) {
                scope.formatHourColumn = ctrl.formatHourColumn;

                ctrl.mode = {
                    step: {days: 1}
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
                    scope.dt = {date: startdate};
                    return rows;
                }

                function compareEventByStartOffset(eventA, eventB) {
                    return eventA.startOffset - eventB.startOffset;
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
                    var eventSource = ctrl.eventSource,
                        len = eventSource ? eventSource.length : 0,
                        startdate = ctrl.range.startdate,
                        enddate = ctrl.range.enddate,
                        rows = scope.rows,
                        oneHour = 3600000,
                        eps = 0.016,
                        eventSet,
                        normalEventInRange = false,
                        hour,
                        keys = [];

                    if (rows.hasEvent) {
                        for (hour = 0; hour < 24; hour += 1) {
                            if (rows[hour].events) {
                                rows[hour].events = null;
                            }
                        }
                        rows.hasEvent = false;
                    }
                    scope.events = null;

                    for (var i = 0; i < len; i += 1) {
                        var event = eventSource[i];
                        var eventStartTime = event.startdate ? new Date(event.startdate) : null;
                        var eventEndTime = event.enddate ? new Date(event.enddate) : null;

                        if ((eventEndTime ? eventEndTime : eventStartTime) <= startdate ||
                          (eventStartTime ? eventStartTime : eventEndTime) >= enddate)
                            continue;
                        normalEventInRange = true;
                        if (!eventEndTime) eventEndTime = eventStartTime;
                        if (!eventStartTime) eventStartTime = eventEndTime;


                        var timeDiff;
                        var timeDifferenceStart;
                        if (eventStartTime <= startdate) {
                            timeDifferenceStart = 0;
                        } else {
                            timeDiff = eventStartTime - startdate - (eventStartTime.getTimezoneOffset() - startdate.getTimezoneOffset()) * 60000;
                            timeDifferenceStart = timeDiff / oneHour;
                        }

                        var timeDifferenceEnd;
                        if (eventEndTime >= enddate) {
                            timeDiff = enddate - startdate - (enddate.getTimezoneOffset() - startdate.getTimezoneOffset()) * 60000;
                            timeDifferenceEnd = timeDiff / oneHour;
                        } else {
                            timeDiff = eventEndTime - startdate - (eventEndTime.getTimezoneOffset() - startdate.getTimezoneOffset()) * 60000;
                            timeDifferenceEnd = timeDiff / oneHour;
                        }

                        var startIndex = Math.floor(timeDifferenceStart);
                        var endIndex = Math.ceil(timeDifferenceEnd - eps);
                        var startOffset = 0;
                        var endOffset = 0;
                        if (ctrl.hourParts !== 1) {
                            startOffset = Math.floor((timeDifferenceStart - startIndex) * ctrl.hourParts);
                            endOffset = Math.floor((endIndex - timeDifferenceEnd) * ctrl.hourParts);
                        }

                        var displayEvent = {
                            event: event,
                            startIndex: startIndex,
                            endIndex: endIndex,
                            startOffset: startOffset,
                            endOffset: endOffset
                        };

                        eventSet = rows[startIndex].events;
                        if (eventSet) {
                            eventSet.push(displayEvent);
                        } else {
                            eventSet = [];
                            eventSet.push(displayEvent);
                            rows[startIndex].events = eventSet;
                        }

                        if (scope.grouping && event[scope.grouping] && !keys.includes(event[scope.grouping]))
                              keys.push(event[scope.grouping]);

                        if (scope.events)
                          scope.events.push(event);
                        else
                          scope.events = [event];
                    }

                    if (normalEventInRange) {
                        var orderedEvents = [];
                        for (hour = 0; hour < 24; hour += 1) {
                            if (rows[hour].events) {
                                rows[hour].events.sort(compareEventByStartOffset);
                                orderedEvents = orderedEvents.concat(rows[hour].events);
                            }
                        }
                        if (orderedEvents.length > 0) {
                            rows.hasEvent = true;
                            ctrl.placeEvents(orderedEvents);
                        }
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
            }
        };
    }]);