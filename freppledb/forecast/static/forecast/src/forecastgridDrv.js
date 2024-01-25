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
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

'use strict';

forecastapp.directive("displayForecastGrid", displayForecastGrid);

displayForecastGrid.$inject = ['$window', '$compile', 'gettextCatalog'];

function displayForecastGrid($window, $compile, gettextCatalog) {

	var directive = {
		restrict: 'EA',
		scope: {
			forecastdata: '=data',
			grid: '=grid',
			label: '@',
			onClick: '&',
			rows: '=rows',
			measures: '=measures'
		},
		templateUrl: '/static/forecast/forecastgrid.html',
		link: linkfunc
	};
	return directive;

	function linkfunc(scope, elem, attrs) {
		var buckettype = angular.element(document).find('#horizonbuckets').val();
		var outlierstring = gettextCatalog.getString('Demand outlier');
		var currentYear = parseInt(new Date(Date.parse(currentdate)).getYear() + 1900);

		scope.$watch('forecastdata.attributes', function (newValue, oldValue) {
			if (typeof scope.forecastdata === 'object') {
				if (scope.forecastdata.attributes.hasOwnProperty('currency')) {
					scope.prefix = scope.grid.prefix;
					scope.suffix = scope.grid.suffix;
				}
				drawtable();
			}
		}, true); //watch end

		scope.$watch('grid.setPristine', function (newValue, oldValue) {
			if (newValue === true) {
				drawtable();
			}
		}); //watch end

		function getBucket(thisbucket, nyearsago) {
			var startdate = new Date(scope.forecastdata.forecast[thisbucket].startdate)
			var enddate = new Date(scope.forecastdata.forecast[thisbucket].enddate)
			// Get the date right in the middle between start and end date and remove 365*nyearsago milliseconds
			var middledate = new Date(-365 * 24 * 3600 * 1000 * nyearsago + Math.round(startdate.getTime() + (enddate.getTime() - startdate.getTime()) / 2.0))

			for (var something in scope.forecastdata.forecast) {
				var bucketStart = new Date(scope.forecastdata.forecast[something].startdate.substring(0, 10)) // TODO performance optimization: too many conversions to string to date
				var bucketEnd = new Date(scope.forecastdata.forecast[something].enddate.substring(0, 10))   // TODO performance optimization: too many conversions to string to date
				if (middledate >= bucketStart && middledate < bucketEnd) {
					return something;
				}
			}
			return undefined;
		}

		function drawtable() {
			var thetable = angular.element(elem);
			var years3ago = 0;
			var years2ago = 0;
			var years1ago = 0;
			var nthird = scope.grid.nthird;
			var nsecond = scope.grid.nsecond;
			var nfirst = scope.grid.nfirst;
			var currentbucket = scope.grid.currentbucket;
			var forecastitem = admin_escape(scope.forecastdata.attributes.item[0][1]);
			var forecastlocation = admin_escape(scope.forecastdata.attributes.location[0][1]);
			var forecastcustomer = admin_escape(scope.forecastdata.attributes.customer[0][1]);
			var tableheader = '';

			// Build array of table rows
			var tablerows = [];
			angular.forEach(scope.rows, function (val) {
				tablerows.push('<tr>');
			});

			// Loop over all buckets/columns and append to the rows
			angular.forEach(scope.forecastdata.forecast, function (fctdata, fctindex) {
				if (fctindex >= currentbucket) {
					years3ago = getBucket(fctindex, 3);
					years2ago = getBucket(fctindex, 2);
					years1ago = getBucket(fctindex, 1);

					tableheader += '<th class="text-center text-nowrap" style="background-color: #aaa" title="'
						+ moment(fctdata.startdate, "YYYY-MM-DD hh:mm:ss").format(dateformat)
						+ ' - '
						+ moment(fctdata.enddate, "YYYY-MM-DD hh:mm:ss").format(dateformat)
						+ '">' + fctdata.bucket + '</th>';

					for (var r in scope.rows) {
						var m = scope.measures[scope.rows[r]];

						// Compute value to display. Damned these frontend measures
						var value;
						var idx;
						var msr = m.name.replace("3ago", "").replace("2ago", "").replace("1ago", "");
						switch (m.name) {
							case "orderstotal1ago":
								value = years1ago >= 0 ? scope.forecastdata.forecast[years1ago].orderstotal : null;
								idx = years1ago;
								break;
							case "orderstotalvalue1ago":
								value = years1ago >= 0 ? scope.forecastdata.forecast[years1ago].orderstotalvalue : null;
								idx = years1ago;
								break;
							case "orderstotal2ago":
								value = years2ago >= 0 ? scope.forecastdata.forecast[years2ago].orderstotal : null;
								idx = years2ago;
								break;
							case "orderstotalvalue2ago":
								value = years2ago >= 0 ? scope.forecastdata.forecast[years2ago].orderstotalvalue : null;
								idx = years2ago;
								break;
							case "orderstotal3ago":
								value = years3ago >= 0 ? scope.forecastdata.forecast[years3ago].orderstotal : null;
								idx = years3ago;
								break;
							case "orderstotalvalue3ago":
								value = years3ago >= 0 ? scope.forecastdata.forecast[years3ago].orderstotalvalue : null;
								idx = years3ago;
								break;
							case "ordersadjustment1ago":
								value = years1ago >= 0 ? scope.forecastdata.forecast[years1ago].ordersadjustment : null;
								idx = years1ago;
								break;
							case "ordersadjustmentvalue1ago":
								value = years1ago >= 0 ? scope.forecastdata.forecast[years1ago].ordersadjustmentvalue : null;
								idx = years1ago;
								break;
							case "ordersadjustment2ago":
								value = years2ago >= 0 ? scope.forecastdata.forecast[years2ago].ordersadjustment : null;
								idx = years2ago;
								break;
							case "ordersadjustmentvalue2ago":
								value = years2ago >= 0 ? scope.forecastdata.forecast[years2ago].ordersadjustmentvalue : null;
								idx = years2ago;
								break;
							case "ordersadjustment3ago":
								value = years3ago >= 0 ? scope.forecastdata.forecast[years3ago].ordersadjustment : null;
								idx = years3ago;
								break;
							case "ordersadjustmentvalue3ago":
								value = years3ago >= 0 ? scope.forecastdata.forecast[years3ago].ordersadjustmentvalue : null;
								idx = years3ago;
								break;
							default:
								value = fctdata[scope.rows[r]];
								idx = fctindex;
						};

						if (typeof idx === 'undefined') {
							tablerows[r] += '<td></td>';
						}
						else if (m.mode_future == "edit") {
							// Editable measure
							tablerows[r] += '<td>'
								+ '<input type="number" class="smallpadding" data-measure="'
								+ msr + '" data-index="' + idx + '" '
								+ (value === null ? '' : ' value="' + value + '" ')
								+ 'tabindex="' + r
								+ '" data-ng-model="forecastdata.forecast[' + idx + '].' + msr
								+ '" data-ng-focus="$parent.focusEdit($event)"><br>'
								+ '</td>';
						}
						else {
							var backlog = scope.rows[r].includes("backlog")
								&& fctdata[scope.rows[r]] !== null
								&& fctdata[scope.rows[r]] > 0.0
							tablerows[r] += '<td class="text-center text-nowrap">';
							if (backlog) tablerows[r] += "<span class='red'>";

							// Add the cell value
							if (m.formatter == "currency")
								tablerows[r] += scope.grid.prefix + grid.formatNumber(value, 2) + scope.grid.suffix;
							else
								tablerows[r] += grid.formatNumber(value);
							if (backlog) tablerows[r] += "</span>";

							// Add drilldown links for some measures
							switch (m.name) {
								case "ordersopen":
								case "ordersopenvalue":
									if (fctdata[scope.rows[r]] != 0.0)
										tablerows[r] += '<a href="' + url_prefix + '/forecast/demand/?noautofilter&item__name__ico=' + forecastitem
											+ '&location__name__ico=' + forecastlocation
											+ '&customer__name__ico=' + forecastcustomer
											+ '&due__gte=' + fctdata.startdate
											+ '&due__lt=' + fctdata.enddate
											+ '&status=open"><span class="ps-1 fa fa-caret-right" onclick="event.preventDefault();event.stopImmediatePropagation();window.location.href=$(event.target).parent().attr(\'href\')"></span></a>';
									break;
								case "orderstotal":
								case "orderstotalvalue":
									if (fctdata[scope.rows[r]] != 0.0)
										tablerows[r] += '<a href="' + url_prefix + '/forecast/demand/?noautofilter&item__name__ico=' + forecastitem
											+ '&location__name__ico=' + forecastlocation
											+ '&customer__name__ico=' + forecastcustomer
											+ '&due__gte=' + fctdata.startdate
											+ '&due__lt=' + fctdata.enddate
											+ '"><span class="ps-1 fa fa-caret-right" onclick="event.preventDefault();event.stopImmediatePropagation();window.location.href=$(event.target).parent().attr(\'href\')"></span></a>';
									break;
								case "orderstotal1ago":
								case "orderstotalvalue1ago":
									if (years1ago >= 0) {
										if (scope.forecastdata.forecast[years1ago]['outlier'] == 1)
											tablerows[r] += '<span class="fa fa-warning text-danger" data-bs-toggle="tooltip" data-bs-title="'
												+ outlierstring
												+ '" data-ng-mouseover="outlierTooltip($event)"></span>';
										if (scope.forecastdata.forecast[years1ago]['orderstotal'] != 0.0)
											tablerows[r] += '<a href="' + url_prefix + '/forecast/demand/?noautofilter&item__name__ico=' + forecastitem
												+ '&location__name__ico=' + forecastlocation
												+ '&customer__name__ico=' + forecastcustomer
												+ '&due__gte=' + scope.forecastdata.forecast[years1ago].startdate
												+ '&due__lt=' + scope.forecastdata.forecast[years1ago].enddate
												+ '"><span class="ps-1 fa fa-caret-right" onclick="event.preventDefault();event.stopImmediatePropagation();window.location.href=$(event.target).parent().attr(\'href\')"></span></a>';
									}
									break;
								case "orderstotal2ago":
								case "orderstotalvalue2ago":
									if (years2ago >= 0) {
										if (scope.forecastdata.forecast[years2ago]['outlier'] == 1)
											tablerows[r] += '<span class="fa fa-warning text-danger" data-bs-toggle="tooltip" data-bs-title="'
												+ outlierstring
												+ '" data-ng-mouseover="outlierTooltip($event)"></span>';
										if (scope.forecastdata.forecast[years2ago]['orderstotal'] != 0.0)
											tablerows[r] += '<a href="' + url_prefix + '/forecast/demand/?noautofilter&item__name__ico=' + forecastitem
												+ '&location__name__ico=' + forecastlocation
												+ '&customer__name__ico=' + forecastcustomer
												+ '&due__gte=' + scope.forecastdata.forecast[years2ago].startdate
												+ '&due__lt=' + scope.forecastdata.forecast[years2ago].enddate
												+ '"><span class="ps-1 fa fa-caret-right" onclick="event.preventDefault();event.stopImmediatePropagation();window.location.href=$(event.target).parent().attr(\'href\')"></span></a>';
									}
									break;
								case "orderstotal3ago":
								case "orderstotalvalue3ago":
									if (years3ago >= 0) {
										if (scope.forecastdata.forecast[years3ago]['outlier'] == 1)
											tablerows[r] += '<span class="fa fa-warning text-danger" data-bs-toggle="tooltip" data-bs-title="'
												+ outlierstring
												+ '" data-ng-mouseover="outlierTooltip($event)"></span>';
										if (scope.forecastdata.forecast[years3ago]['orderstotal'] != 0.0)
											tablerows[r] += '<a href="' + url_prefix + '/forecast/demand/?noautofilter&item__name__ico=' + forecastitem
												+ '&location__name__ico=' + forecastlocation
												+ '&customer__name__ico=' + forecastcustomer
												+ '&due__gte=' + scope.forecastdata.forecast[years3ago].startdate
												+ '&due__lt=' + scope.forecastdata.forecast[years3ago].enddate
												+ '"><span class="ps-1 fa fa-caret-right" onclick="event.preventDefault();event.stopImmediatePropagation();window.location.href=$(event.target).parent().attr(\'href\')"></span></a>';
									}
									break;
							}
							tablerows[r] += "</td>";
						}
					}
				}
			});

			// Combine all rows into a table
			var tabledata = '<tbody id="forecasttablebody">';
			for (var r of tablerows)
				tabledata += r + '</tr>';
			tabledata += "</tbody>";

			// Update the angular grid
			thetable.find("#row0").replaceWith('<tr id="row0">' + tableheader + '</tr>');
			thetable.find("#forecasttablebody").replaceWith($compile(tabledata)(scope));
			scope.grid.setPristine = false;
		}
	} //link end

}
