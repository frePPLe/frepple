/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

'use strict';

angular.module('frepple.common').directive('chatScreen', chatScreen);

chatScreen.$inject = ['$window', 'WebSvc'];

function chatScreen($window, WebSvc) {
    
    return {
      restrict: 'EA',
      scope: {
        label: '@',
        onClick: '&'
      },
        template: ''+
        '<div class="pannel" id="chat-panel" style="max-width: 700px;">'+
        '<div class="pannel-body">'+
        '<div  style="height: 200px; overflow-y: scroll;">'+
        '<table class="table" id="chathistory"></table>'+
        '</div>'+
        '</div>'+
        '<div class="panel-footer"><form>'+
        '<div class="input-group">'+        
        '<input id="chatmsg" type="text" class="form-control" size="80">'+
        '<span class="input-group-btn"><button class="btn btn-primary pull-right" id="chatsend" ng-click="sendChat()">send</button></span>'+
        '</div>'+
        '</div></form>'+
        '</div>'
      ,
      link: function(scope, elem, attrs) {
          var destroyHandler = scope.$on("websocket-chat", function(events, data) {
            //console.log(data);
            scope.displayChat(data);
          });
          scope.$on('$destroy', destroyHandler);

          scope.displayChat = function(jsondoc) {
            var chatdiv = angular.element(document).find("#chathistory");
            $(jsondoc.messages).each(function() {
              chatdiv.append($('<tr>')
                .append($('<td style="white-space: nowrap;">').text(this.date.replace("T", " ")))
                .append($('<td style="white-space: nowrap;">').text(this.name))
                .append($('<td style="white-space: wrap;">').text(this.value))
              );
            });
            chatdiv = chatdiv.parent();
            chatdiv.scrollTop(chatdiv.prop('scrollHeight'));
          };

          scope.sendChat = function() {
            var chatmsg = angular.element(document).find("#chatmsg");
            if (chatmsg.val() === "") {
              return;
            }
            WebSvc.send('/chat/' + chatmsg.val());
            chatmsg.val("");
          };
        } //link end
    }; //return end
  }; //function end
