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

angular.module('frepple.common').factory('WebSvc',  webfactory);

webfactory.$inject = ['$rootScope', '$websocket', '$interval', '$http', '$window'];

/*
 * This service connects to the frePPLe web service using a web socket.
 * The URL of the web socket is retrieved from the global variable "service_url".
 * The authentication is retrieved from the global variable "service_token".
 */
function webfactory($rootScope, $websocket, $interval, $http, $window) {
  'use strict';
  var debug = false;
  var authenticated = false;
  var message='';
  var themodal = angular.element(document);

  function showerrormodal(msg) {
    angular.element("#controller").scope().databaseerrormodal = false;

    if (typeof msg === 'string') {
      message = '<p>'+msg+'</p>';
    } else if (typeof msg === 'object') {
      message = '<div style="width: 100%; overflow: auto;" class="webservicerror">'+ msg.description + '</div>';
    } else {
      message = '<p>Websocket connection is not working.</p><p>Please check that <strong>plan.webservice</strong> parameter is set to <strong>true</strong>,<br>and <strong>execute the plan</strong>.</p>';
    }

    angular.element("#controller").scope().$applyAsync(function(){
      if (typeof msg === 'object') {
        if (msg.hasOwnProperty('category') && msg.hasOwnProperty('description')) {
          themodal.find('.modal-title span').html('Webservice error');
          themodal.find('.modal-body').css({'width':500,'height':350,'overflow':'auto'});
          themodal.find('#savechangesparagraph').hide();
          themodal.find('#saveAbutton').hide();
          themodal.find('.modal-body').append(message);
        }
      } else {
        themodal.find('.modal-title span').html('Websocket connection problem');
        themodal.find('.modal-body').html('<div style="width: 100%; overflow: auto;">'+ message + '</div>');
      }
    });

    angular.element(document).find('#popup2').modal('show');
  }

  var webservice = $websocket(service_url, {
    reconnectIfNotNormalClose: true
  });

  $interval(function() { //every 20min websocket keepalive
    webservice.send("/alive/");
  }, 600000);

  webservice.onMessage(function(message) {
    var jsondoc = angular.fromJson(message.data);
    if (debug) console.log(jsondoc);
    if (jsondoc.hasOwnProperty('category') && jsondoc.category === 'error') {
      showerrormodal(jsondoc);
    } else {
      $rootScope.$broadcast("websocket-" + jsondoc.category, jsondoc);
    }
  });

  var alreadyprocessing = false;
  webservice.onError(function(message) {

    if (!alreadyprocessing) {
      alreadyprocessing = true;
      $http({
        method: 'POST',
        url: url_prefix + '/execute/api/frepple_start_web_service/'
      }).then(function successCallback(response) {
        if(response.data.message !== "Successfully launched task") {
          showerrormodal();
        } else {
          const taskid = response.data.taskid;
          var answer = {};
          const idUrl = url_prefix + '/execute/api/status/?id=' + taskid;
          var testsuccess = $interval(function(counter) {
            $http({
              method: 'POST',
              url: idUrl
            }).then(function(response) {
              showerrormodal('Starting Web Service, please wait a moment.');
              angular.element(document).find('#saveAbutton').hide();
              answer = response.data[Object.keys(response.data)];
              if (answer.message === "Web service active") {
                $interval.cancel(testsuccess);
                $window.location.reload();
              } else if (answer.finished !== "None" && answer.status !== "Web service active") {
                $interval.cancel(testsuccess);
                showerrormodal();
                alreadyprocessing = false;
              }
            });
          }, 1000, 0); //every second
        }
      }, function errorCallback(response) {
        showerrormodal(response.data);
      });
    }

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
      authenticated = false;
    }
    if (!authenticated) {
    	webservice.send("/authenticate/" + service_token);
    	authenticated = true;
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
