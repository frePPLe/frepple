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

angular.module('frepple.common').factory('WebSvc',  webfactory);

webfactory.$inject = ['$rootScope', '$websocket', '$interval'];

/*
 * This service connects to the frePPLe web service using a web socket.
 * The URL of the web socket is retrieved from the global variable "service_url".
 */
function webfactory($rootScope, $websocket, $interval) {
  'use strict';
  var debug = true;
  var webservice = $websocket(service_url, {
    reconnectIfNotNormalClose: true
  });

  $interval(function() { //every 20min websocket keepalive
    webservice.send("/alive/");
  }, 600000);

  webservice.onMessage(function(message) {
    var jsondoc = angular.fromJson(message.data);
    if (debug)
      console.log(jsondoc);
    $rootScope.$broadcast("websocket-" + jsondoc.category, jsondoc);
  });

  webservice.onError(function(message) {
    message = '<p>Websocket connection is not working.</p><p>Please check that <strong>plan.webservice</strong> parameter is set to <strong>true</strong>,<br>and <strong>execute the plan</strong>.</p>';
    angular.element("#controller").scope().databaseerrormodal = true;
    angular.element("#controller").scope().$apply();
    angular.element(document)
      .find('#popup2 .modal-title span').html('Websocket connection problem');
    angular.element(document)
      .find('.modal-body').html('<div style="width: 100%; overflow: auto;">'+ message + '</div>');
    angular.element(document).find('#popup2').modal('show');
        angular.element("#controller").scope().$apply();
  });

  function subscribe(msg, callback) {
    var destroyHandler = $rootScope.$on("websocket-" + msg, function(events, data) {
      callback(data);
    });
    $rootScope.$on('$destroy', destroyHandler);
  }

  function send(data) {
    if (webservice.readyState > 1) {
      webservice = $websocket(service_url);
    }
    if (debug)
      console.log("send:" + data);
    webservice.send(data);
  }

  var methods = {
    send: send,
    subscribe: subscribe
  };
  return methods;
}
