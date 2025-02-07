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
