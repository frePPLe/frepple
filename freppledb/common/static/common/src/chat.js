/*
 * Copyright (C) 2017 by frePPLe bvba
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
