/*
 * Copyright (C) 2017 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

'use strict';

angular.module('operationplandetailapp').directive('showoperationplanDrv', showoperationplanDrv);

showoperationplanDrv.$inject = ['$window'];

function showoperationplanDrv($window) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    templateUrl: '/static/operationplandetail/operationplanpanel.html',
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    //need to watch all of these because a webservice may change them on the fly
    scope.$watchGroup(['operationplan.id','operationplan.start','operationplan.end','operationplan.quantity','operationplan.criticality','operationplan.delay','operationplan.status'], function () {
      if (typeof scope.operationplan !== 'undefined' && Object.keys(scope.operationplan).length > 0) {

        angular.element(elem).find('input[disabled]').attr('disabled',false);
        angular.element(elem).find('button[disabled]').attr('disabled',false);
        angular.element(elem).find('#statusrow .btn').removeClass('active');

        if (scope.operationplan.hasOwnProperty('start')) {
          angular.element(elem).find("#setStart").val(moment(scope.operationplan.start).format('YYYY-MM-DD HH:mm:ss'));
        }
        if (scope.operationplan.hasOwnProperty('end')) {
          angular.element(elem).find("#setEnd").val(moment(scope.operationplan.end).format('YYYY-MM-DD HH:mm:ss'));
        }

        if (scope.operationplan.hasOwnProperty('status')) {
          angular.element(elem).find('#statusrow .btn').removeClass('active');
          angular.element(elem).find('#'+scope.operationplan.status+'Btn').addClass('active');
        }
      }
    }); //watch end

    angular.element(elem).find(".vDateField").datetimepicker({
        format: 'YYYY-MM-DD HH:mm:ss',
        useCurrent: false,
        calendarWeeks: true,
        minDate: '2000-01-01',
        inline: false,
        sideBySide: true,
        icons: {
          time: 'fa fa-clock-o',
          date: 'fa fa-calendar',
          up: 'fa fa-chevron-up',
          down: 'fa fa-chevron-down',
          previous: 'fa fa-chevron-left',
          next: 'fa fa-chevron-right',
          today: 'fa fa-bullseye',
          clear: 'fa fa-trash',
          close: 'fa fa-remove'
        },
        locale: language,
        widgetPositioning: {
          horizontal: 'left',
          vertical: 'bottom'
        }
      }).on("dp.change", function(e) {
        if (!e.oldDate || e.date == e.oldDate) {
          return;
        }
        if (e.target.id === 'setStart') {
          scope.$apply(function () {scope.operationplan.start=new moment(e.date).format("YYYY-MM-DDTHH:mm:ss");});
        }
        if (e.target.id === 'setEnd') {
          scope.$apply(function () {scope.operationplan.end=new moment(e.date).format("YYYY-MM-DDTHH:mm:ss");});
        }
      }).on('$destroy', function() {
        if ($(this).data('DateTimePicker') !== undefined){
          $(this).data('DateTimePicker').destroy();
        }
      });

  } //link end
} //directive end
