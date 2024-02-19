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

forecastapp.directive("itemstable", itemstable);

itemstable.$inject = ['$filter'];

function itemstable($filter) {
  return {
    transclude: false,
    //scope: { items: '=', selectItem: '&' },
    link: function ($scope, $elem, attrs) {

      $elem.on('click', '.evtitemrow', function (evt) {
        $(this).css('background-color', '');
        angular.element(document).find('#itemstable .evtitemrow').removeClass('bg-light');
        angular.element(evt.target).closest('.evtitemrow').addClass('bg-light');
        var value = parseInt(angular.element(evt.target).closest('.evtitemrow').attr('index'));
        $scope.$apply(function () {
          $scope.selectItem(value);
        });
      });
      $elem.on('mouseenter', '.evtitemrow', function () {
        if (!$(this).hasClass('bg-light')) {
          $(this).css('background-color', '#f5f5f5');
        }
      });
      $elem.on('mouseleave', '.evtitemrow', function () {
        if (!$(this).hasClass('bg-light')) {
          $(this).css('background-color', '');
        }
      });

      $scope.$watchGroup(['items', 'itemstrigger'], function (oldValue, newValue, scope) {
        drawtable();
      });

      function drawtable() {
        var tableRow = '';
        if ($scope.changeditemrows[0] === -1 && $scope.changeditemrows[1] === -1) { //draw everything
          $elem.children().remove(); //delete the rows
          tableRow = '<div class="d-table w-100">' +
            '<div style="float: left; overflow:hidden;">&nbsp;</div>' +
            '<div class="ms-auto text-right">';
          var first = true;
          if ($scope.buckets) {
            // Display time buckets
            for (var i = 0; i < $scope.buckets.length; i++) {
              if (first) {
                //$scope.buckets is reversed so the first bucket is the last one
                tableRow += '<span class="numbervalueslast"><strong><small>';
                first = false;
              }
              else
                tableRow += '<span class="numbervalues"><strong><small>';
              tableRow += $scope.buckets[i] + '</small></strong></span>';
            }
          }
          if ($scope.showdescription) {
            if (first)
              tableRow += '<span class="numbervalueslast"></span>';
            else
              tableRow += '<span class="numbervalues"></span>';
          }
          tableRow += '</div></div>';

          var oldlevel = 0;
          var newlevel = 0;
          var rowindex = 0;
          var numchanged = 0;
          angular.forEach($scope.items, function (item, index) {
            newlevel = item.lvl;

            // if new level is the same as the old level this is not a child of the old

            if (newlevel > oldlevel)
              tableRow += '<div level="' + newlevel + '">';
            else if (newlevel < oldlevel)
              tableRow += '</div>';
            oldlevel = newlevel;

            if (item.visible === true && !item.hide) {
              tableRow += '<div index=' + index + ' class="d-flex flex-wrap evtitemrow';
              if (item.item === $scope.selecteditem)
                tableRow += ' bg-light';
              tableRow += '"><div style="overflow:visible; padding-left: ' + item.lvl * 13 + 'px">&nbsp;';

              if (item.children === true && item.expanded <= 0)
                tableRow += '<span class="fa fa-caret-right"></span>';
              if (item.children === true && item.expanded > 0)
                tableRow += '<span class="fa fa-caret-down"></span>';
              if (item.children === false)
                tableRow += '<span>&nbsp;</span>';

              var tmp = angular.element('<span style="white-space:nowrap"></span>');
              tmp.text(item.item);
              if (item.description) tmp.attr("title", item.description);
              tableRow += tmp[0].outerHTML + '</div><div class="ms-auto text-right">';
              var first = true;
              if (item.values) {
                // Display values
                item.values.reverse();
                for (var i = 0; i < item.values.length; i++) {
                  if (first) {
                    // $scope.buckets is reversed so the first bucket is the last one
                    tableRow += '<span class="numbervalueslast">';
                    first = false;
                  }
                  else
                    tableRow += '<span class="numbervalues">';
                  tableRow += $filter('number')(item.values[i].value, 0) + '</span>';
                }
              }
              if ($scope.showdescription) {
                // Display description
                var tmp2 = first ?
                  angular.element('<span class="numbervalueslast"></span>') :
                  angular.element('<span class="numbervalues"></span>');
                if (item.description) tmp2.text(item.description);
                tableRow += tmp2[0].outerHTML;
              }
              tableRow += '</div></div>';
            }
          }); //end forEach
          $elem.append(tableRow);

        } else if ($scope.changeditemrows[0] >= 0 && $scope.changeditemrows[1] < 0) { //just showing or hiding
          rowindex = $scope.changeditemrows[0];

          //the parent row must change the carret
          $elem[0].querySelector('.evtitemrow[index="' + rowindex + '"]').classList.add('bg-light');
          if ($scope.items[rowindex].children === true && $scope.items[rowindex].expanded <= 0)
            $elem[0].querySelector(".evtitemrow[index='" + rowindex + "'] .fa").classList = 'fa fa-caret-right';
          if ($scope.items[rowindex].children === true && $scope.items[rowindex].expanded > 0)
            $elem[0].querySelector(".evtitemrow[index='" + rowindex + "'] .fa").classList = 'fa fa-caret-down';
          if ($scope.items[rowindex].children === true && $scope.items[rowindex].expanded > 0)
            $elem[0].querySelector('.evtitemrow[index="' + rowindex + '"]').nextSibling.style.display = 'block';
          else if ($scope.items[rowindex].children === true && $scope.items[rowindex].expanded <= 0)
            $elem[0].querySelector('.evtitemrow[index="' + rowindex + '"]').nextSibling.style.display = 'none';
        } else if ($scope.changeditemrows[0] >= 0 && $scope.changeditemrows[1] > 0) { //needs to add rows
          rowindex = $scope.changeditemrows[0];
          var newindex = 0;
          numchanged = $scope.changeditemrows[1] - $scope.changeditemrows[0];
          //update all row indexes that are after the insert
          const domslice = Array.apply(null, $elem[0].querySelectorAll(".evtitemrow")).slice($scope.changeditemrows[0] + 1);

          angular.forEach(domslice, function (domslicerow) {
            newindex = parseInt(domslicerow.getAttribute('index')) + numchanged;
            domslicerow.setAttribute('index', '' + newindex);
          });

          $elem[0].querySelector(".evtitemrow[index='" + $scope.changeditemrows[0] + "'] .fa").classList = 'fa fa-caret-down';

          tableRow = '<div level="' + $scope.items[$scope.changeditemrows[0] + 1].lvl + '">';
          angular.forEach($scope.items.slice($scope.changeditemrows[0] + 1, $scope.changeditemrows[1] + 1), function (item, sliceindex) {

            rowindex = $scope.changeditemrows[0] + sliceindex + 1;
            if (item.visible === true && !item.hide) {
              tableRow += '<div index=' + rowindex + ' class="d-flex flex-wrap evtitemrow';
              if (item.item === $scope.selecteditem)
                tableRow += ' bg-light';
              tableRow += '"><div style="overflow:hidden; text-align: left; padding-left: ' + item.lvl * 13 + 'px">&nbsp;';

              if (item.children === true && item.expanded <= 0)
                tableRow += '<span class="fa fa-caret-right"></span>';
              if (item.children === true && item.expanded > 0)
                tableRow += '<span class="fa fa-caret-down"></span>';
              if (item.children === false)
                tableRow += '<span>&nbsp;</span>';
              var tmp = angular.element('<span style="white-space:nowrap"></span>');
              tmp.text(item.item);
              if (item.description) tmp.attr("title", item.description);
              tableRow += tmp[0].outerHTML + '</div><div class="ms-auto text-right">';
              if (item.values)
                tableRow +=
                  '<span class="numbervalueslast">' + $filter('number')(item.values[2].value, 0) + '</span>' +
                  '<span class="numbervalues">' + $filter('number')(item.values[1].value, 0) + '</span>' +
                  '<span class="numbervalues">' + $filter('number')(item.values[0].value, 0) + '</span>';
              if ($scope.showdescription) {
                var tmp2 = item.values ?
                  angular.element('<span class="numbervalues"></span>') :
                  angular.element('<span class="numbervalueslast"></span>');
                if (item.description) tmp2.text(item.description);
                tableRow += tmp2[0].outerHTML;
              }
              tableRow += '</div></div>';
            }
          }); // end for each
          tableRow += '</div>';
          $elem.find(".evtitemrow[index='" + $scope.changeditemrows[0] + "']").after(tableRow);
        } //end adding new rows
      } //end drawtable
    }
  };
}
