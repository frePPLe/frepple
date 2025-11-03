import { ref } from 'vue';
// TODO data to be sent should also be a ref

let webservice = new WebSocket(
  `ws://${window.location.hostname}:${window.location.port}`,
  { reconnect: true }
);
let authenticated = false;
export const wsresponse = ref([]);

setInterval(function () {
  //every 20min websocket keepalive
  webservice.send('/alive/');
}, 600000);

webservice.onmessage(function (message) {
  const jsondoc = JSON.parse(message.data);
  // eslint-disable-next-line no-undef
  if (debug) console.log(jsondoc);
  // eslint-disable-next-line no-prototype-builtins
  if (jsondoc.hasOwnProperty('category') && jsondoc.category === 'error') {
    // showerrormodal(jsondoc);
    console.log(17, jsondoc);
    wsresponse.value = ['error', jsondoc];
  } else {
    wsresponse.value = ['websocket-' + jsondoc.category, jsondoc];
  }
});

let alreadyprocessing = false;
webservice.onError(function (message) {
  if (!alreadyprocessing) {
    alreadyprocessing = true;
    fetch({
      method: 'POST',
      // eslint-disable-next-line no-undef
      url: url_prefix + '/execute/api/frepple_start_web_service/',
    }).then(
      function successCallback(response) {
        if (response.data.message !== 'Successfully launched task') {
          console.log(40, message);
          // showerrormodal();
        } else {
          const taskid = response.data.taskid;
          var answer = {};
          // eslint-disable-next-line no-undef
          const idUrl = url_prefix + '/execute/api/status/?id=' + taskid;
          const testsuccess = setInterval(
            function () {
              fetch({
                method: 'POST',
                url: idUrl,
              }).then(function (response) {
                // showerrormodal('Starting Web Service, please wait a moment.');
                console.log('Starting Web Service, please wait a moment.');
                // angular.element(document).find('#saveAbutton').hide();
                answer = response.data[Object.keys(response.data)];
                if (answer.message === 'Web service active') {
                  clearInterval(testsuccess);
                  location.reload();
                } else if (
                  answer.finished !== 'None' &&
                  answer.status !== 'Web service active'
                ) {
                  clearInterval(testsuccess);
                  // showerrormodal();
                  alreadyprocessing = false;
                }
              });
            },
            1000,
            0
          ); //every second
        }
      },
      function errorCallback(response) {
        console.log(response.data);
        // showerrormodal(response.data);
      }
    );
  }
});

// function subscribe(msg, callback) {
//   var destroyHandler = $rootScope.$on(
//     'websocket-' + msg,
//     function (events, data) {
//       callback(data);
//     }
//   );
//   $rootScope.$on('$destroy', destroyHandler);
// }

export function send(data) {
  if (webservice.readyState > 1) {
    // eslint-disable-next-line no-undef
    webservice = webservice(service_url);
    authenticated = false;
  }
  if (!authenticated) {
    // eslint-disable-next-line no-undef
    webservice.send('/authenticate/' + service_token);
    authenticated = true;
  }
  // eslint-disable-next-line no-undef
  if (debug) console.log('send:' + data);
  webservice.send(data);
}
