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

forecastapp.directive("customerstable", customerstable);

customerstable.$inject = ['$filter'];

function customerstable($filter) {
  return {
    transclude: false,
    //scope: { customers: '=', selectCustomer: '&' },
    link: function ($scope, $elem, attrs) {

      $elem.on('click', '.evtcustrow', function (evt) {
        $(this).css('background-color', '');
        angular.element(document).find('#customerstable .evtcustrow').removeClass('bg-light');
        angular.element(evt.target).closest('.evtcustrow').addClass('bg-light');
        var value = parseInt(angular.element(evt.target).closest('.evtcustrow').attr('index'));
        $scope.$apply(function () {
          $scope.selectCustomer(value);
        });
      });
      $elem.on('mouseenter', '.evtcustrow', function () {
        if (!$(this).hasClass('bg-light')) {
          $(this).css('background-color', '#f5f5f5');
        }
      });
      $elem.on('mouseleave', '.evtcustrow', function () {
        if (!$(this).hasClass('bg-light')) {
          $(this).css('background-color', '');
        }
      });

      $scope.$watchGroup(['customers', 'customerstrigger'], function (oldValue, newValue, scope) {
        drawtable();
      });

      function drawtable() {
        var tableRow = '';
        if ($scope.changedcustomerrows[0] === -1 && $scope.changedcustomerrows[1] === -1) { //draw everything
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
          angular.forEach($scope.customers, function (customer, index) {
            newlevel = customer.lvl;

            // if new level is the same as the old level this is not a child of the old

            if (newlevel > oldlevel)
              tableRow += '<div level="' + newlevel + '">';
            else if (newlevel < oldlevel)
              tableRow += '</div>';
            oldlevel = newlevel;

            if (customer.visible === true && !customer.hide) {
              tableRow += '<div index=' + index + ' class="d-flex flex-wrap evtcustrow';
              if (customer.customer === $scope.selectedcustomer)
                tableRow += ' bg-light';
              tableRow += '"><div style="overflow:hidden; padding-left: ' + customer.lvl * 13 + 'px;">&nbsp;';

              if (customer.children === true && customer.expanded <= 0)
                tableRow += '<span class="fa fa-caret-right"></span>';
              if (customer.children === true && customer.expanded > 0)
                tableRow += '<span class="fa fa-caret-down"></span>';
              if (customer.children === false)
                tableRow += '<span>&nbsp;</span>';

              var tmp = angular.element('<span style="white-space:nowrap"></span>');
              tmp.text(customer.customer);
              if (customer.description) tmp.attr("title", customer.description);
              tableRow += tmp[0].outerHTML + '</div><div class="ms-auto text-right">';
              var first = true;
              if (customer.values) {
                // Display values
                customer.values.reverse();
                for (var i = 0; i < customer.values.length; i++) {
                  if (first) {
                    // $scope.buckets is reversed so the first bucket is the last one
                    tableRow += '<span class="numbervalueslast">';
                    first = false;
                  }
                  else
                    tableRow += '<span class="numbervalues">';
                  tableRow += $filter('number')(customer.values[i].value, 0) + '</span>';
                }
              }
              if ($scope.showdescription) {
                // Display description
                var tmp2 = first ?
                  angular.element('<span class="numbervalueslast"></span>') :
                  angular.element('<span class="numbervalues"></span>');
                if (customer.description) tmp2.text(customer.description);
                tableRow += tmp2[0].outerHTML;
              }
              tableRow += '</div></div>';
            }
          }); //end forEach
          $elem.append(tableRow);

        } else if ($scope.changedcustomerrows[0] >= 0 && $scope.changedcustomerrows[1] < 0) { //just showing or hiding
          rowindex = $scope.changedcustomerrows[0];

          //the parent row must change the carret
          $elem[0].querySelector('.evtcustrow[index="' + rowindex + '"]').classList.add('bg-light');
          if ($scope.customers[rowindex].children === true && $scope.customers[rowindex].expanded <= 0)
            $elem[0].querySelector(".evtcustrow[index='" + rowindex + "'] .fa").classList = 'fa fa-caret-right';
          if ($scope.customers[rowindex].children === true && $scope.customers[rowindex].expanded > 0)
            $elem[0].querySelector(".evtcustrow[index='" + rowindex + "'] .fa").classList = 'fa fa-caret-down';
          if ($scope.customers[rowindex].children === true && $scope.customers[rowindex].expanded > 0)
            $elem[0].querySelector('.evtcustrow[index="' + rowindex + '"]').nextSibling.style.display = 'block';
          else if ($scope.customers[rowindex].children === true && $scope.customers[rowindex].expanded <= 0)
            $elem[0].querySelector('.evtcustrow[index="' + rowindex + '"]').nextSibling.style.display = 'none';
        } else if ($scope.changedcustomerrows[0] >= 0 && $scope.changedcustomerrows[1] > 0) { //needs to add rows
          rowindex = $scope.changedcustomerrows[0];
          var newindex = 0;
          numchanged = $scope.changedcustomerrows[1] - $scope.changedcustomerrows[0];
          //update all row indexes that are after the insert
          const domslice = Array.apply(null, $elem[0].querySelectorAll(".evtcustrow")).slice($scope.changedcustomerrows[0] + 1);

          angular.forEach(domslice, function (domslicerow) {
            newindex = parseInt(domslicerow.getAttribute('index')) + numchanged;
            domslicerow.setAttribute('index', '' + newindex);
          });

          $elem[0].querySelector(".evtcustrow[index='" + $scope.changedcustomerrows[0] + "'] .fa").classList = 'fa fa-caret-down';

          tableRow = '<div level="' + $scope.customers[$scope.changedcustomerrows[0] + 1].lvl + '">';
          angular.forEach($scope.customers.slice($scope.changedcustomerrows[0] + 1, $scope.changedcustomerrows[1] + 1), function (customer, sliceindex) {

            rowindex = $scope.changedcustomerrows[0] + sliceindex + 1;
            if (customer.visible === true && !customer.hide) {
              tableRow += '<div index=' + rowindex + ' class="d-flex flex-wrap evtcustrow';
              if (customer.customer === $scope.selectedcustomer)
                tableRow += ' bg-light';
              tableRow += '"><div style="overflow:hidden; text-align: left; padding-left: ' + customer.lvl * 13 + 'px">&nbsp;';

              if (customer.children === true && customer.expanded <= 0)
                tableRow += '<span class="fa fa-caret-right"></span>';
              if (customer.children === true && customer.expanded > 0)
                tableRow += '<span class="fa fa-caret-down"></span>';
              if (customer.children === false)
                tableRow += '<span>&nbsp;</span>';
              var tmp = angular.element('<span style="white-space:nowrap"></span>');
              tmp.text(customer.customer);
              if (customer.description) tmp.attr("title", customer.description);
              tableRow += tmp[0].outerHTML + '</div><div class="ms-auto text-right">';
              if (customer.values)
                tableRow +=
                  '<span class="numbervalueslast">' + $filter('number')(customer.values[2].value, 0) + '</span>' +
                  '<span class="numbervalues">' + $filter('number')(customer.values[1].value, 0) + '</span>' +
                  '<span class="numbervalues">' + $filter('number')(customer.values[0].value, 0) + '</span>';
              if ($scope.showdescription) {
                var tmp2 = customer.values ?
                  angular.element('<span class="numbervalues"></span>') :
                  angular.element('<span class="numbervalueslast"></span>');
                if (customer.description) tmp2.text(customer.description);
                tableRow += tmp2[0].outerHTML;
              }
              tableRow += '</div></div>';
            }
          }); // end for each
          tableRow += '</div>';
          $elem.find(".evtcustrow[index='" + $scope.changedcustomerrows[0] + "']").after(tableRow);
        } //end adding new rows
      } //end drawtable
    }
  };
}
