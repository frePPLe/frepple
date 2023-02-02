/*
 * Copyright (C) 2017 by frePPLe bv
 *
 * This library is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
 * General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
		var template = '<div class="card-header"><h5 class="card-title" style="text-transform: capitalize">' +
			gettextCatalog.getString("resource") +
			'</h5></div>' +
			'<table class="table table-condensed table-hover"><thead><tr><td>' +
			'<b style="text-transform: capitalize;">' + gettextCatalog.getString("name") + '</b>' +
			'</td><td>' +
			'<b style="text-transform: capitalize;">' + gettextCatalog.getString("quantity") + '</b>' +
			'</td>' +
			'<tbody></tbody>' +
			'</table>';

		function redraw() {
			angular.element(document).find('#attributes-operationresources').empty().append(template);
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
								+ '<button class="btn btn-default" data-bs-toggle="dropdown" type="button" style="text-transform: capitalize; min-width: 150px">'
								+ $.jgrid.htmlEncode(theresource.resource.name)
								+ '</button>'
								+ '<ul class="dropdown-menu">'
								+ '<li><a role="menuitem" class="dropdown-item alternateresource" style="text-transform: capitalize">'
								+ $.jgrid.htmlEncode(theresource.resource.name)
								+ '</a></li>';
							angular.forEach(theresource.alternates, function (thealternate) {
								rows += '<li><a role="menuitem" class="dropdown-item alternateresource" style="text-transform: capitalize">'
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
					angular.forEach(scope.operationplan.loadplans, function (theresource) {
						if (theresource.resource.name == curresource) {
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
								var colmodel = grid.jqGrid('getGridParam', 'colModel').find(function (i) { return i.name == "resource" });
								var cell = grid.jqGrid('getCell', selrow, 'resource');
								if (colmodel.formatter == 'detail' && cell == curresource) {
									grid.jqGrid("setCell", selrow, "resource", newresource, "dirty-cell");
									grid.jqGrid("setRowData", selrow, false, "edited");
									angular.element(document).find("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
									angular.element(document).find("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
									$(window).off('beforeunload', upload.warnUnsavedChanges);
									$(window).on('beforeunload', upload.warnUnsavedChanges);
								}
								else if (colmodel.formatter == 'listdetail') {
									var res = [];
									angular.forEach(scope.operationplan.loadplans, function (theloadplan) {
										res.push([theloadplan.resource.name, theloadplan.quantity]);
									});
									grid.jqGrid("setCell", selrow, "resource", res, "dirty-cell");
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
		};

		scope.$watchGroup(['operationplan.id', 'operationplan.loadplans.length'], redraw);
	} //link end
} //directive end
