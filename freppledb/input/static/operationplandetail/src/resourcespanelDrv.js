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
