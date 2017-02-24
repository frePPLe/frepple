/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
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
