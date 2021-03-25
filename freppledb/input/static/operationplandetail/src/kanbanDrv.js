/*
 * Copyright (C) 2020 by frePPLe bv
 *
 * This library is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation; either version 3 of the License, or
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
 * General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
    $scope.colsum = 12;
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
    }
    
    getColStyle();
    
    function getColStyle() {    
      // Column styles
      switch ($scope.kanbancolumns.length) {
        case 1:
          $scope.colstyle = 'col-md-12';
          $scope.colsum = 12;
          break;
        case 2:
          $scope.colstyle = 'col-md-6';
          $scope.colsum = 12;
          break;
        case 3:
          $scope.colstyle = 'col-md-4';
          $scope.colsum = 12;
          break;
        case 4:
          $scope.colstyle = 'col-md-3';
          $scope.colsum = 12;
          break;        
        case 5:
          $scope.colstyle = 'col-md-3';
          $scope.colsum = 15;
          break;
        case 6:
          $scope.colstyle = 'col-md-2';
          $scope.colsum = 12;
          break;        
        case 7:
          $scope.colstyle = 'col-md-2';
          $scope.colsum = 14;
          break;        
        case 8:
          $scope.colstyle = 'col-md-2';
          $scope.colsum = 16;
          break;
        default:
          $scope.colstyle = 'col-md-1';
          $scope.colsum = $scope.kanbancolumns.length;
      }
      $scope.$parent.colsum = $scope.colsum;
    }   

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
      getColStyle();
      PreferenceSvc.save("columns", $scope.$parent.kanbancolumns);
    };
    $scope.hideColumn = hideColumn;
    $scope.grid = grid;
    
    // Handler for selecting a card
    function selectCard(opplan) {
      if ($scope.curselected) {
        if ($scope.curselected.reference == opplan.reference && opplan.selected)
          return;
        delete $scope.curselected.selected;
      }
      opplan.selected = true;
      $scope.curselected = opplan;
      $scope.$parent.displayInfo(opplan);
    };
    $scope.selectCard = selectCard;

    $scope.$on('selectedEdited', function(event, field, oldvalue, newvalue) {
      if ($scope.curselected === null) return;      
      $scope.changeCard($scope.curselected, field, oldvalue);
      if (field === "status") {
        var idx = $scope.kanbanoperationplans[oldvalue].rows.indexOf($scope.curselected);
        if (idx != -1) {
          $scope.kanbanoperationplans[oldvalue].rows.splice(idx, 1);
          $scope.kanbanoperationplans[newvalue].rows.unshift($scope.curselected);
          $scope.kanbanoperationplans[oldvalue].records--;
          $scope.kanbanoperationplans[newvalue].records++;
        }
      }
      $scope.curselected[field] = newvalue;                  
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
      var endvalue = $(event.target).closest(".column").attr("data-column");
      if (endvalue) {
        var startvalue = event.originalEvent.dataTransfer.getData("startcolumn");
        var startindex = event.originalEvent.dataTransfer.getData("startindex");
        if (startindex !== "undefined") {
          // Dragging a card
          var endindex = $(event.target).closest(".card");
          if (endindex) endindex = endindex.attr("data-index");
          $scope.$apply(function() {
            var o = $scope.kanbanoperationplans[startvalue].rows[startindex];
            $scope.kanbanoperationplans[startvalue].rows.splice(startindex, 1);
            if (endindex) {
              // Insert in the middle
              $scope.kanbanoperationplans[endvalue].rows.splice(
                  endindex > startindex && endvalue == startvalue ? endindex -1 : endindex, 0, o
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
            if (!o.hasOwnProperty("statusOriginal")) {
               if (o.status != endvalue) {
                 o.statusOriginal = o.status;
                 o.status = endvalue;
                 o.dirty = true;
               }
            }
            else {
              if (o.statusOriginal == endvalue){
                o.dirty = false;
                delete o.statusOriginal;
              } else {
                o.dirty = true;
              }
              o.status = endvalue;
            }
            $scope.$parent.$broadcast("cardChanged", "status", o.statusOriginal, o.status);
          });
        }
        else {
          // Dragging a column
          $scope.$apply(function() {
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
          $(event.target).closest(".column").attr("data-column")
          );
    };
    
    function enableDragDrop() {      
      $elem.on('dragover', '.column, .card', HandlerDragOver );
      $elem.on('drop', '.column', HandlerDrop);
      $elem.on('dragstart', '.column .panel .panel-heading, .card', HandlerDragStart);
    }
    $scope.enableDragDrop = enableDragDrop;
    
    function disableDragDrop() {      
      $elem.off('dragover', '.column, .card', HandlerDragOver );
      $elem.off('drop', '.column', HandlerDrop);
      $elem.off('dragstart', '.column .panel .panel-heading, .card', HandlerDragStart);
    }
    $scope.disableDragDrop = disableDragDrop;
        
    $scope.$on('changeMode', function (event, mode) {
      $scope.mode = mode;
      if (mode == "kanban")
        enableDragDrop();
      else
        disableDragDrop();
    });
    
    if (mode == "kanban")
      enableDragDrop();
  }
}
