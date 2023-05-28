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

angular.module('frepple.common').factory('WebSvc', webfactory);

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
  var message = '';
  var themodal = angular.element(document);

  function showerrormodal(msg) {
    angular.element("#controller").scope().databaseerrormodal = false;

    if (typeof msg === 'string') {
      message = '<p>' + msg + '</p>';
    } else if (typeof msg === 'object') {
      message = '<div style="width: 100%; overflow: auto;" class="webservicerror">' + msg.description + '</div>';
    } else {
      message = "<p>The web service isn't running.</p><p>Use the <a class='underline' target='_blank' href='" + url_prefix
      + "/execute/#runwebservice'>web service</a> task in the admin/execute screen to restart it.</p>";
    }

    angular.element("#controller").scope().$applyAsync(function () {
      if (typeof msg === 'object') {
        if (msg.hasOwnProperty('category') && msg.hasOwnProperty('description')) {
          themodal.find('.modal-title').html('Webservice error');
          themodal.find('.modal-body').css({ 'width': 500, 'height': 350, 'overflow': 'auto' });
          themodal.find('#savechangesparagraph').hide();
          themodal.find('#saveAbutton').hide();
          themodal.find('.modal-body').append(message);
        }
      } else {
        themodal.find('.modal-title').html('Websocket connection problem');
        themodal.find('.modal-body').html('<div style="width: 100%; overflow: auto;">' + message + '</div>');
      }
    });
    var p = angular.element(document).find('#popup2');
    p.find(".modal-footer").hide();
    showModal('popup2');
  }

  var webservice = $websocket(service_url, {
    reconnectIfNotNormalClose: true
  });

  $interval(function () { //every 20min websocket keepalive
    webservice.send("/alive/");
  }, 600000);

  webservice.onMessage(function (message) {
    var jsondoc = angular.fromJson(message.data);
    if (debug) console.log(jsondoc);
    if (jsondoc.hasOwnProperty('category') && jsondoc.category === 'error') {
      showerrormodal(jsondoc);
    } else {
      $rootScope.$broadcast("websocket-" + jsondoc.category, jsondoc);
    }
  });

  var alreadyprocessing = false;
  webservice.onError(function (message) {

    if (!alreadyprocessing) {
      alreadyprocessing = true;
      $http({
        method: 'POST',
        url: url_prefix + '/execute/api/frepple_start_web_service/'
      }).then(function successCallback(response) {
        if (response.data.message !== "Successfully launched task") {
          showerrormodal();
        } else {
          const taskid = response.data.taskid;
          var answer = {};
          const idUrl = url_prefix + '/execute/api/status/?id=' + taskid;
          var testsuccess = $interval(function (counter) {
            $http({
              method: 'POST',
              url: idUrl
            }).then(function (response) {
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
    var destroyHandler = $rootScope.$on("websocket-" + msg, function (events, data) {
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
