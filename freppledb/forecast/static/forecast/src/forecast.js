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

forecastapp.controller('forecastController', forecastController);

forecastController.$inject = ['$scope', '$http', '$q', '$location'];

function forecastController($scope, $http, $q, $location) {
  $scope.urlprefix = '/' + angular.element(document).find('#database').attr('name');
  if ($scope.urlprefix === '/default' || $scope.urlprefix === '/undefined') {
    $scope.urlprefix = '';
  }

  var item_in_url = $location.path().split('/');
  item_in_url = admin_unescape(item_in_url[item_in_url.indexOf('editor') + 1]);

  function outlierTooltip(e) {
    $(e.target).tooltip('show');
  }
  $scope.outlierTooltip = outlierTooltip;

  $scope.preferences = preferences;
  $scope.measures = measures;
  $scope.measurelist = [];
  angular.forEach(measures, function (val, key) {
    $scope.measurelist.push(val);
  });
  $scope.rows = $scope.preferences.rows;
  if (!$scope.rows) {
    $scope.rows = [];
    angular.forEach(measures, function (val, key) {
      if (val["initially_hidden"] !== true && val["mode_future"] !== 'hidden')
        $scope.rows.push(key);
    });
  }
  else {
    // Validate the list of measures. Some can have been deleted already.
    $scope.rows = $scope.rows.filter(m => m in measures);
  }
  $scope.selecteditem = item_in_url;
  $scope.selectedlocation = '';
  $scope.selectedcustomer = '';
  $scope.detaildata = '';
  $scope.changes = false;
  $scope.sequence = $scope.preferences.sequence;
  $scope.measure = $scope.preferences.measure;
  $scope.showdescription = $scope.preferences.showdescription || false;
  if (!$scope.measure) $scope.measure = 'forecasttotal';
  $scope.showtab = $scope.preferences.showtab;
  $scope.buckets = null;
  $scope.currentbucket = 0;
  $scope.forecast_currentbucket = 0;
  $scope.commenttype = null;
  $scope.initialmethod = '';
  $scope.forms = {};
  $scope.databaseerrormodal = true;
  $scope.datarowheight = $scope.preferences.height;
  $scope.smallestbucket = angular.element(document).find('#horizonbucketsul li').first().text();
  $scope.buckettype = angular.element(document).find('#horizonbuckets').val();
  $scope.prefix = '';
  $scope.suffix = '';

  $scope.years0 = 0;
  $scope.years1 = 0;
  $scope.years2 = 0;
  $scope.years3 = 0;

  $scope.ncurrent = 0;
  $scope.nfirst = 0;
  $scope.nsecond = 0;
  $scope.nthird = 0;

  $scope.date = '';
  $scope.newcomment = '';
  //these triggers are here to avoid having deep/heavy watches
  $scope.itemstrigger = 0;
  $scope.customerstrigger = 0;
  $scope.locationstrigger = 0;
  //changed rows [begin, end], -1 to -1 means that all changed
  $scope.changeditemrows = [-1, -1];
  $scope.changedcustomerrows = [-1, -1];
  $scope.changedlocationrows = [-1, -1];
  $scope.setPristine = false;

  var firsttime = true;
  var seqplace = 0;
  var detailurl = $scope.urlprefix + "/forecast/detail/";
  var selections = [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer];
  var lastitemspanel = selections;
  var lastlocationspanel = selections;
  var lastcustomerspanel = selections;
  var value = "";
  var detailbucketslist = {};
  var data = {};
  var currentYear = parseInt(new Date(Date.parse(currentdate)).getYear() + 1900);
  var previousdata = {};
  var datareloaded = false;

  // Modal popup window
  $scope.modalcallback = null;
  function showSaveChange() {
    $scope.modalcallback = $q.defer();
    $scope.databaseerrormodal = false;
    showModal('popup2');
    return $scope.modalcallback.promise;
  }
  $scope.showSaveChange = showSaveChange;

  $scope.$watch('detaildata', function (newValue, oldValue) {
    if ($scope.detaildata === '') {
      return;
    }
    if (firsttime) {
      firsttime = false;
      $scope.changes = false;
    } else {
      if (datareloaded) {
        $scope.changes = false;
        angular.element(document).find('#save').removeClass('btn-danger').prop('disabled', true);
        angular.element(document).find('#undo').removeClass('btn-danger').prop('disabled', true);
        angular.element(document).find('#recalculate').removeClass('disabled').prop('disabled', true);
      } else {
        $scope.changes = true;
        angular.element(document).find('#save').removeClass('btn-danger').addClass('btn-danger').prop('disabled', false);
        angular.element(document).find('#undo').removeClass('btn-danger').addClass('btn-danger').prop('disabled', false);
        angular.element(document).find('#recalculate').prop('disabled', false);
      }
    }
    datareloaded = false;
  }, true); // Heavy, deep watch

  $scope.$watch('changes', function (newvalue, oldvalue) {
    if (!newvalue) {
      angular.element(document).find('#save').removeClass('btn-danger').prop('disabled', true);
      angular.element(document).find('#undo').removeClass('btn-danger').prop('disabled', true);
    } else {
      angular.element(document).find('#save').removeClass('btn-danger').addClass('btn-danger').prop('disabled', false);
      angular.element(document).find('#undo').removeClass('btn-danger').addClass('btn-danger').prop('disabled', false);
    }
  });

  var sequenceflag = false; //for the first run
  $scope.$watch('[sequence,measure]', function () {
    if (sequenceflag === false) {
      sequenceflag = true;
      return;
    }
    $scope.selecteditem = item_in_url;
    $scope.selectedlocation = '';
    $scope.selectedcustomer = '';
    $scope.changeditemrows = [-1, -1];
    $scope.changedlocationrows = [-1, -1];
    $scope.changedcustrows = [-1, -1];
    $scope.itemstrigger += 1;
    $scope.locationstrigger += 1;
    $scope.customerstrigger += 1;

    $scope.refreshPanels($scope.urlprefix + "/forecast/itemtree/", 'items', [$scope.selecteditem, '', '']);
    $scope.refreshPanels($scope.urlprefix + "/forecast/locationtree/", 'locations', [$scope.selecteditem, '', '']);
    $scope.refreshPanels($scope.urlprefix + "/forecast/customertree/", 'customers', [$scope.selecteditem, '', '']);
  }, true);

  function refreshPanels(url, panel, selections) {
    if (panel == 'items' && $scope.sequence.indexOf('I') == -1)
      return;
    if (panel == 'locations' && $scope.sequence.indexOf('L') == -1)
      return;
    if (panel == 'customers' && $scope.sequence.indexOf('C') == -1)
      return;
    url += '?measure=' + admin_escape($scope.measure);
    if (selections[0] !== '' && typeof selections[0] === 'string') {
      url += '&item=' + admin_escape(selections[0]);
    }
    if (selections[1] !== '') {
      url += '&location=' + admin_escape(selections[1]);
    }
    if (selections[2] !== '') {
      url += '&customer=' + admin_escape(selections[2]);
    }
    if (panel === 'items' && selections[0]) {
      url += '&first=1';
    }
    $http.get(url).then(function (response) {
      var something = [];
      if (response.data.length === 0) {
        $scope.databaseerrormodal = true;
        angular.element(document).find('#popup2 .modal-body').html('<div style="width: 100%; overflow: auto;">' +
          'No data found for specified ' + panel + '</div>');
        showModal('popup2');
      }
      if (!$scope.buckets && response.data[0].values) {
        $scope.buckets = [];
        for (let something of response.data[0].values)
          $scope.buckets.push(something.bucketname);
        $scope.buckets.reverse();
      }

      if (panel === 'items') {
        $scope.items = response.data;
        $scope.changeditemrows = [-1, -1];

        if ($scope.selecteditem === '') {
          $scope.selecteditem = $scope.items[0].item;
          for (let something of $scope.items) {
            if (something.children && something.lvl === 0 && something.expanded === 0)
              something.expanded = 1;
          }
        } else {
          for (let something of $scope.items) {
            if (something.children && something.lvl <= $scope.selecteditemlevel && something.expanded === 0)
              something.expanded = 1;
          }

          for (let something of $scope.items) {
            if (something.item === $scope.selecteditem) {
              if (something.description && something.description.length > 0)
                $scope.selecteditemdescription = " (" + something.description + ")";
              else
                $scope.selecteditemdescription = "";
              break;
            }
          }
          return;
        }
      } else if (panel === 'locations') {
        $scope.locations = response.data;
        $scope.changedlocationrows = [-1, -1];

        if ($scope.selectedlocation === '') {
          $scope.selectedlocation = $scope.locations[0].location;
          for (let something of $scope.locations) {
            if (something.children && something.lvl === 0 && something.expanded === 0)
              something.expanded = 1;
          }
        } else {
          for (let something of $scope.locations) {
            if (something.children && something.lvl <= $scope.selectedlocationlevel && something.expanded === 0)
              something.expanded = 1;
          }
        }

        for (let something of $scope.locations) {
          if (something.location === $scope.selectedlocation) {
            if (something.description && something.description.length > 0)
              $scope.selectedlocationdescription = " (" + something.description + ")";
            else
              $scope.selectedlocationdescription = "";
            break;
          }
        }
        return;
      } else if (panel === 'customers') {
        $scope.customers = response.data;
        $scope.changedcustomerrows = [-1, -1];

        if ($scope.selectedcustomer === '') {
          $scope.selectedcustomer = $scope.customers[0].customer;
          for (let something of $scope.customers) {
            if (something.children && something.lvl === 0 && something.expanded === 0)
              something.expanded = 1;
          }
        } else {
          for (let something of $scope.customers) {
            if (something.children && something.lvl <= $scope.selectedcustomerlevel && something.expanded === 0)
              something.expanded = 1;
          }
        }

        for (const something of $scope.customers) {
          if (something.customer === $scope.selectedcustomer) {
            if (something.description && something.description.length > 0)
              $scope.selectedcustomerdescription = " (" + something.description + ")";
            else
              $scope.selectedcustomerdescription = "";
            break;
          }
        }

        if (panel === 'items')
          lastitemspanel = selections;
        else if (panel === 'locations')
          lastlocationspanel = selections;
        else if (panel === 'customers')
          lastcustomerspanel = selections;
        return;
      }
    },
      //if database error
      function (response) {
        if (response.status == 401) {
          location.reload();
          return;
        }
        $scope.databaseerrormodal = true;
        angular.element(document).find('#popup2 .modal-body').html('<div style="width: 100%; overflow: auto;">' + response.data + '</div>');
        showModal('popup2');
      }
    );
  }
  $scope.refreshPanels = refreshPanels;

  $scope.refreshPanels($scope.urlprefix + "/forecast/locationtree/", 'locations', lastlocationspanel);
  $scope.refreshPanels($scope.urlprefix + "/forecast/customertree/", 'customers', lastcustomerspanel);
  $scope.refreshPanels($scope.urlprefix + "/forecast/itemtree/", 'items', lastitemspanel);

  function processForecastData(response, recalc) {
    currentYear = parseInt(new Date(Date.parse(currentdate)).getYear() + 1900);

    //find item,location,customer names in response and compare with selected ones
    //if the response does not match the selection ignore it
    angular.forEach(response.data.attributes.item, function (someattr) {
      if (someattr[0] === 'Name') {
        if ($scope.selecteditem !== someattr[1]) return;
      }
    });
    angular.forEach(response.data.attributes.location, function (someattr) {
      if (someattr[0] === 'Name') {
        if ($scope.selectedlocation !== someattr[1]) return;
      }
    });
    angular.forEach(response.data.attributes.customer, function (someattr) {
      if (someattr[0] === 'Name') {
        if ($scope.selectedcustomer !== someattr[1]) return;
      }
    });

    $scope.commenttype = null;
    $scope.detaildata = angular.copy(response.data);
    for (var bckt of $scope.detaildata.forecast) {
      var p = bckt.startdate.split(/[ \-]/);
      bckt["startdate_date"] = new Date(p[0], p[1] - 1, p[2]);
      p = bckt.enddate.split(/[ \-]/);
      bckt["enddate_date"] = new Date(p[0], p[1] - 1, p[2]);
    }
    if ($scope.detaildata.attributes.hasOwnProperty('currency')) {
      var currency = angular.fromJson($scope.detaildata.attributes.currency);
    }

    $scope.grid = {};
    if (currency !== undefined) {
      $scope.grid.prefix = (currency[0] !== undefined) ? currency[0] : '';
      $scope.grid.suffix = (currency[1] !== undefined) ? currency[1] : '';
    } else {
      $scope.grid.prefix = '';
      $scope.grid.suffix = '';
    }

    $scope.initialmethod = response.data.attributes.forecast.forecastmethod;
    detailbucketslist = {};

    //gets the number of buckets (returned by the view) for each year
    angular.forEach(bucketsperyear, function (someyear) {
      if (someyear.year === currentYear - 3) {
        $scope.nthird = someyear.bucketcount;
        $scope.grid.nthird = $scope.nthird;
      } else if (someyear.year === currentYear - 2) {
        $scope.nsecond = someyear.bucketcount;
        $scope.grid.nsecond = $scope.nsecond;
      } else if (someyear.year === currentYear - 1) {
        $scope.nfirst = someyear.bucketcount;
        $scope.grid.nfirst = $scope.nfirst;
      } else if (someyear.year === currentYear) {
        $scope.ncurrent = someyear.bucketcount;
        $scope.grid.currentYear = currentYear;
      }
    });

    //count the number of buckets for each year in detaildata
    for (let something in $scope.detaildata.forecast) {
      detailbucketslist[$scope.detaildata.forecast[something].bucket] = something;

      if ($scope.detaildata.forecast[something].bucket === currentbucket) {
        $scope.detaildata.forecast[something].currentbucket = true;
        $scope.currentbucket = something;
        $scope.grid.currentbucket = $scope.currentbucket;
      }
      if ($scope.detaildata.forecast[something].bucket === forecast_currentbucket) {
        $scope.detaildata.forecast[something].forecast_currentbucket = true;
        $scope.forecast_currentbucket = something;
        $scope.grid.forecast_currentbucket = $scope.forecast_currentbucket;
      }
    }

    //to hide the animated icon
    $scope.changes = false;
    $scope.loading = false;
    previousdata = angular.copy($scope.detaildata);
    datareloaded = true;
    $scope.grid.setPristine = true;
    return;
  }

  function getDetail() {
    var url = detailurl;
    $scope.loading = true;
    url += '?measure=' + admin_escape($scope.measure);
    url += '&item=' + admin_escape($scope.selecteditem);
    url += '&location=' + admin_escape($scope.selectedlocation);
    url += '&customer=' + admin_escape($scope.selectedcustomer);

    $http.get(url).then(function (response) {
      processForecastData(response, false);
    });
  } //end getDetail()
  $scope.getDetail = getDetail;
  $scope.getDetail();

  function getBucket(thisbucket, nyearsago) {
    if ($scope.buckettype === "day") {
      //makes no sense to show forecast for 29Feb in the table
      return thisbucket - nyearsago * 365;
    } else if ($scope.buckettype === "week") {
      for (var something in $scope.detaildata.forecast) {
        if ($scope.detaildata.forecast[something].year === currentYear - nyearsago && $scope.detaildata.forecast[something].weeknumber === $scope.detaildata.forecast[thisbucket].weeknumber) {
          return something;
        }
      }
    } else if ($scope.buckettype === "month") {
      return thisbucket - nyearsago * 12;
    } else if ($scope.buckettype === "quarter") {
      return thisbucket - nyearsago * 4;
    } else if ($scope.buckettype === "year") {
      return thisbucket - nyearsago;
    }
  }
  $scope.getBucket = getBucket;

  function refreshScreen() {
    selections = [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer];
    $scope.refreshPanels($scope.urlprefix + "/forecast/itemtree/", 'items', lastitemspanel);
    $scope.refreshPanels($scope.urlprefix + "/forecast/locationtree/", 'locations', lastlocationspanel);
    $scope.refreshPanels($scope.urlprefix + "/forecast/customertree/", 'customers', lastcustomerspanel);
    $scope.commenttype = null;
    $scope.newcomment = '';
    $scope.getDetail();
  }
  $scope.refreshScreen = refreshScreen;

  value = 0;
  function checkbucket(value) {
    return value >= $scope.currentbucket
      && value < $scope.currentbucket + $scope.bucketsperyear;
  }
  $scope.checkbucket = checkbucket;

  function drillDown(url, panel, selections, currindex) {
    //this function will insert rows, and set the visible and hide flags.
    //the splice-insertion of records is the heaviest part of the code
    var k = 0;
    var len = 0;
    url += '?measure=' + admin_escape($scope.measure);
    if (selections[0] !== '')
      url += '&item=' + admin_escape(selections[0]);
    if (selections[1] !== '')
      url += '&location=' + admin_escape(selections[1]);
    if (selections[2] !== '')
      url += '&customer=' + admin_escape(selections[2]);

    if (panel === 'items') {
      if ($scope.items[currindex].children === false) return;

      if ($scope.items[currindex].expanded === 0) {
        //will be expanded for the first time
        $http.get(url).then(function (response) {
          if (response.data.length === 0) return;
          //get data for children
          //insert the records inside the response array into the scope object array
          $scope.items.splice.apply($scope.items, [currindex + 1, 0].concat(response.data));
          // set expanded to the number of children
          $scope.items[currindex].expanded = response.data.length;
          $scope.itemstrigger += 1;
          $scope.changeditemrows = [currindex, currindex + response.data.length];
        });
      } else {
        //if the children are already there
        $scope.changeditemrows[0] = currindex;
        k = currindex + 1;
        len = $scope.items.length;

        //if ( typeof($scope.items[k])==='undefined' ) return; //has children but no forescasts in children
        while ($scope.items[currindex].lvl !== $scope.items[k].lvl) {
          if ($scope.items[k].lvl === $scope.items[currindex].lvl + 1) {
            // toggle their visible/invisible flag
            $scope.items[k].visible = !$scope.items[k].visible;
            // the hide flag is for the case when you colapsed a top level
            // and had sublevels expanded, the hide flag will make sure that
            // expanding again the top level will also show the previously
            // expanded sublevels
            $scope.items[k].hide = false;
          }

          if ($scope.items[k].lvl > $scope.items[currindex].lvl + 1) {
            $scope.items[k].hide = !$scope.items[k].hide; //toggle their show/hide flag
          }
          k++;
          if (k > len - 1) {
            break;
          }
        }
        $scope.changeditemrows[1] = -1 * (k - currindex);
        //a negative expanded value says that they are there but not going to be shown
        $scope.items[currindex].expanded = -$scope.items[currindex].expanded;
        $scope.itemstrigger += 1;
      }
      lastitemspanel = selections;
      return;

    } else if (panel === 'locations') {
      if ($scope.locations[currindex].children === false) return;

      if ($scope.locations[currindex].expanded === 0) { //will be expanded for the first time
        $http.get(url).then(function (response) {
          if (response.data.length === 0) return;

          //insert the records inside the response array into the scope object array
          $scope.locations.splice.apply($scope.locations, [currindex + 1, 0].concat(response.data));
          // set expanded to the number of children
          $scope.locations[currindex].expanded = response.data.length;
          $scope.locationstrigger += 1;
          $scope.changedlocationrows = [currindex, currindex + response.data.length];
        });
      } else { //if the children are already there
        $scope.changedlocationrows[0] = currindex;
        k = currindex + 1;
        len = $scope.locations.length;
        if (typeof ($scope.locations[k]) === 'undefined') {
          return;
        } //has children but no forescasts in children
        while ($scope.locations[currindex].lvl !== $scope.locations[k].lvl) {
          if ($scope.locations[k].lvl === $scope.locations[currindex].lvl + 1) {
            $scope.locations[k].visible = !$scope.locations[k].visible; //toggle their visible/invisible flag
            $scope.locations[k].hide = false;
          }

          if ($scope.locations[k].lvl > $scope.locations[currindex].lvl + 1) {
            $scope.locations[k].hide = !$scope.locations[k].hide; //toggle their show/hide flag
          }
          k++;
          if (k > len - 1) {
            break;
          }
        }
        $scope.changedlocationrows[1] = -1 * (k - currindex);
        //a negative expanded value says that they are there but not going to be shown
        $scope.locations[currindex].expanded = -$scope.locations[currindex].expanded;
        $scope.locationstrigger += 1;
      }
      lastlocationspanel = selections;
      return;

    } else if (panel === 'customers') {
      if ($scope.customers[currindex].children === false) {
        return;
      }

      if ($scope.customers[currindex].expanded === 0) { //will be expanded for the first time
        $http.get(url).then(function (response) {
          if (response.data.length === 0) return;
          $scope.customers.splice.apply($scope.customers, [currindex + 1, 0].concat(response.data)); //insert the records inside the response array into the scope object array
          $scope.customers[currindex].expanded = response.data.length; // set expanded to the number of children
          $scope.customerstrigger += 1;
          $scope.changedcustomerrows = [currindex, currindex + response.data.length];
        });
      } else { //if the children are already there
        k = currindex + 1;
        $scope.changedcustomerrows[0] = currindex;
        len = $scope.customers.length;
        if (typeof ($scope.customers[k]) === 'undefined') {
          return;
        } //has children but no forescasts in children
        while ($scope.customers[currindex].lvl !== $scope.customers[k].lvl) {
          if ($scope.customers[k].lvl === $scope.customers[currindex].lvl + 1) {
            $scope.customers[k].visible = !$scope.customers[k].visible; //toggle their visible/invisible flag
            $scope.customers[k].hide = false;
          }

          if ($scope.customers[k].lvl > $scope.customers[currindex].lvl + 1)
            $scope.customers[k].hide = !$scope.customers[k].hide; //toggle their show/hide flag
          k++;
          if (k > len - 1) break;
        }
        $scope.changedcustomerrows[1] = -1 * (k - currindex);
        //a negative expanded value says that they are there but not going to be shown
        $scope.customers[currindex].expanded = -$scope.customers[currindex].expanded;
        $scope.customerstrigger += 1;
      }
      lastcustomerspanel = selections;
      return;

    }
  }
  $scope.drillDown = drillDown;

  function selectItem(currindex) {
    var newItem = $scope.items[currindex];

    if ($scope.changes) {
      // Changes were made - change only after confirmation
      $scope.showSaveChange().then(
        function (msg) {
          if (msg === 'continue') {
            $scope.changeItem.call(newItem, currindex);
            angular.element(document).find('#save').removeClass('btn-danger').prop('disabled', true);
            angular.element(document).find('#undo').removeClass('btn-danger').prop('disabled', true);
          } else if (msg === 'save') {
            $scope.save(false, function () { $scope.changeItem.call(newItem, currindex); });
          }
          hideModal('popup2');
        });
    } else {
      // No changes present on the page - go forward
      $scope.changeItem.call(newItem, currindex);
    }
  }
  $scope.selectItem = selectItem;

  function changeItem(currindex) {
    //This function sets up the links and call the drilldown or refresh functions.
    //The links change depending on the position of the panel, a bit more intelligence on the
    //view could save a lot of code here and reduce the calls from 3 to 1.

    seqplace = $scope.sequence.indexOf('I');
    $scope.selecteditem = this.item;

    if (this.description && this.description.length > 0)
      $scope.selecteditemdescription = " (" + this.description + ")";
    else
      $scope.selecteditemdescription = "";
    if ($scope.selectedlocation.description && $scope.selectedlocation.description.length > 0)
      $scope.selectedlocationdescription = " (" + $scope.selectedlocation.description + ")";
    else
      $scope.selectedlocationdescription = "";
    if ($scope.selectedcustomer.description && $scope.selectedcustomer.description.length > 0)
      $scope.selectedcustomerdescription = " (" + $scope.selectedcustomer.description + ")";
    else
      $scope.selectedcustomerdescription = "";

    if (seqplace === 0) {
      $scope.selectedlocation = '';
      $scope.selectedcustomer = '';
      if ($scope.sequence.indexOf('L') !== -1)
        $scope.refreshPanels($scope.urlprefix + "/forecast/locationtree/", 'locations', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
      if ($scope.sequence.indexOf('C') !== -1)
        $scope.refreshPanels($scope.urlprefix + "/forecast/customertree/", 'customers', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
    } else if (seqplace === 1) {
      if ($scope.sequence.indexOf('L') === 2) {
        $scope.selectedlocation = '';
        $scope.refreshPanels($scope.urlprefix + "/forecast/locationtree/", 'locations', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
      } else if ($scope.sequence.indexOf('C') === 2) {
        $scope.selectedcustomer = '';
        $scope.refreshPanels($scope.urlprefix + "/forecast/customertree/", 'customers', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
      }
    }
    if (this.children)
      $scope.drillDown($scope.urlprefix + "/forecast/itemtree/", 'items', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer], currindex);
    $scope.getDetail();
  }
  $scope.changeItem = changeItem;

  function selectLocation(currindex) {
    var newLocation = $scope.locations[currindex];

    if ($scope.changes) {
      // Changes were made - change only after confirmation
      $scope.showSaveChange().then(
        function (msg) {
          if (msg === 'continue') {
            $scope.changeLocation.call(newLocation, currindex);
            angular.element(document).find('#save').removeClass('btn-danger').prop('disabled', true);
            angular.element(document).find('#undo').removeClass('btn-danger').prop('disabled', true);
          } else if (msg === 'save') {
            $scope.save(false, function () { $scope.changeLocation.call(newLocation, currindex); });
          }
          hideModal('popup2');
        });
    } else {
      // No changes present on the page - change immediately
      $scope.changeLocation.call(newLocation, currindex);
    }
  }
  $scope.selectLocation = selectLocation;

  function changeLocation(currindex) {

    seqplace = $scope.sequence.indexOf('L');
    $scope.selectedlocation = this.location;

    if (this.description && this.description.length > 0)
      $scope.selectedlocationdescription = " (" + this.description + ")";
    else
      $scope.selectedlocationdescription = "";
    if ($scope.selecteditem.description && $scope.selecteditem.description.length > 0)
      $scope.selecteditemdescription = " (" + $scope.selecteditem.description + ")";
    else
      $scope.selecteditemdescription = "";
    if ($scope.selectedcustomer.description && $scope.selectedcustomer.description.length > 0)
      $scope.selectedcustomerdescription = " (" + $scope.selectedcustomer.description + ")";
    else
      $scope.selectedcustomerdescription = "";

    if (seqplace === 0) {
      $scope.selecteditem = item_in_url;
      $scope.selectedcustomer = '';
      if ($scope.sequence.indexOf('I') !== -1)
        $scope.refreshPanels($scope.urlprefix + "/forecast/itemtree/", 'items', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
      if ($scope.sequence.indexOf('C') !== -1)
        $scope.refreshPanels($scope.urlprefix + "/forecast/customertree/", 'customers', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
    } else if (seqplace === 1) {
      if ($scope.sequence.indexOf('I') === 2) {
        $scope.selecteditem = item_in_url;
        $scope.refreshPanels($scope.urlprefix + "/forecast/itemtree/", 'items', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
      } else if ($scope.sequence.indexOf('C') === 2) {
        $scope.selectedcustomer = '';
        $scope.refreshPanels($scope.urlprefix + "/forecast/customertree/", 'customers', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
      }
    }
    if (this.children)
      $scope.drillDown($scope.urlprefix + "/forecast/locationtree/", 'locations', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer], currindex);
    $scope.getDetail();
  }
  $scope.changeLocation = changeLocation;

  function selectCustomer(currindex) {
    var newCustomer = $scope.customers[currindex];

    if ($scope.changes) {
      // Changes were made - change only after confirmation
      $scope.showSaveChange().then(
        function (msg) {
          if (msg === 'continue') {
            $scope.changeCustomer.call(newCustomer, currindex);
            angular.element(document).find('#save').removeClass('btn-danger').prop('disabled', true);
            angular.element(document).find('#undo').removeClass('btn-danger').prop('disabled', true);
          } else if (msg === 'save') {
            $scope.save(false, function () { $scope.changeCustomer.call(newCustomer, currindex); });
          }
          hideModal('popup2');
        });
    } else {
      // No changes present on the page - change immediately
      $scope.changeCustomer.call(newCustomer, currindex);
    }
  }
  $scope.selectCustomer = selectCustomer;

  function changeCustomer(currindex) {

    seqplace = $scope.sequence.indexOf('C');
    $scope.selectedcustomer = this.customer;

    if (this.description && this.description.length > 0)
      $scope.selectedcustomerdescription = " (" + this.description + ")";
    else
      $scope.selectedcustomerdescription = "";
    if ($scope.selecteditem.description && $scope.selecteditem.description.length > 0)
      $scope.selecteditemdescription = " (" + $scope.selecteditem.description + ")";
    else
      $scope.selecteditemdescription = "";
    if ($scope.selectedlocation.description && $scope.selectedlocation.description.length > 0)
      $scope.selectedlocationdescription = " (" + $scope.selectedlocation.description + ")";
    else
      $scope.selectedlocationdescription = "";

    if (seqplace === 0) {
      $scope.selecteditem = item_in_url;
      $scope.selectedlocation = '';
      if ($scope.sequence.indexOf('I') !== -1)
        $scope.refreshPanels($scope.urlprefix + "/forecast/itemtree/", 'items', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
      if ($scope.sequence.indexOf('L') !== -1)
        $scope.refreshPanels($scope.urlprefix + "/forecast/locationtree/", 'locations', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
    } else if (seqplace === 1) {
      if ($scope.sequence.indexOf('I') === 2) {
        $scope.selecteditem = item_in_url;
        $scope.refreshPanels($scope.urlprefix + "/forecast/itemtree/", 'items', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
      } else if ($scope.sequence.indexOf('L') === 2) {
        $scope.selectedlocation = '';
        $scope.refreshPanels($scope.urlprefix + "/forecast/locationtree/", 'locations', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer]);
      }
    }
    if (this.children)
      $scope.drillDown($scope.urlprefix + "/forecast/customertree/", 'customers', [$scope.selecteditem, $scope.selectedlocation, $scope.selectedcustomer], currindex);
    $scope.getDetail();
  }
  $scope.changeCustomer = changeCustomer;

  $scope.busy_saving = false;

  function postDetail(data, callback) {
    $scope.busy_saving = true;
    $http.post(
      service_url + 'forecast/detail/?measure=' + admin_escape($scope.measure),
      angular.toJson(data),
      {
        headers: { "Authorization": "Bearer " + service_token }
      }
    ).then(function (response) {
      $scope.databaseerrormodal = false;
      callback(response);
      $scope.busy_saving = false;
      return;
    }, function (response) {
      if (response.status == 401) {
        location.reload();
        return;
      }
      $scope.databaseerrormodal = true;
      if (hasOwnProperty(response.data, "errors")) {
        var msg = "";
        for (var o of response.data.errors)
          msg += o + "<br>";
      }
      else
        var msg = response.data;
      angular.element(document).find('#popup2 .modal-body').html('<div style="width: 100%; overflow: auto;">' + msg + '</div>');
      showModal('popup2');
      $scope.busy_saving = false;
    });
  }
  $scope.postDetail = postDetail;

  function savePreferences(callback) {
    $scope.preferences['measure'] = $scope.measure;
    $scope.preferences['sequence'] = $scope.sequence;
    $scope.preferences['showtab'] = $scope.showtab;
    $scope.preferences['showdescription'] = $scope.showdescription;
    $scope.preferences['height'] = angular.element(document).find("#data-row").height();
    $scope.preferences['rows'] = $scope.rows;
    $http.post($scope.urlprefix + '/settings/', angular.toJson({
      "freppledb.forecast.planning": $scope.preferences
    })).then(function (response) {
      $scope.databaseerrormodal = false;
      if (typeof callback === 'function') {
        callback(response);
      }
      return;
    },
      function (response) {
        if (response.status == 440119) {
          location.reload();
          return;
        }
        $scope.databaseerrormodal = true;
        angular.element(document).find('#popup2 .modal-body').html('<div style="width: 100%; overflow: auto;">' + response.data + '</div>');
        showModal('popup2');
      });
  }
  $scope.savePreferences = savePreferences;

  function undo() {
    angular.element(document).find("div.tooltip").tooltip("hide");
    angular.element(document).find('#save').removeClass('btn-danger').prop('disabled', true);
    angular.element(document).find('#undo').removeClass('btn-danger').prop('disabled', true);
    $scope.commenttype = null;
    $scope.newcomment = '';

    if ($scope.changes === true) {

      //$scope.getDetail();
      $scope.detaildata = angular.copy(previousdata);
      datareloaded = true;
    }
    $scope.grid.setPristine = true;

  }
  $scope.undo = undo;

  function save(recalculate, callback) {
    if ($scope.busy_saving) return;
    data = {};
    var url = detailurl;
    url += '?measure=' + admin_escape($scope.measure);
    url += '&item=' + admin_escape($scope.selecteditem);
    url += '&location=' + admin_escape($scope.selectedlocation);
    url += '&customer=' + admin_escape($scope.selectedcustomer);

    data.recalculate = recalculate;
    data.units = $scope.measure;
    data.item = $scope.selecteditem;
    data.location = $scope.selectedlocation;
    data.customer = $scope.selectedcustomer;
    data.horizonbuckets = angular.element(document).find('#horizonbuckets').val();

    // Get a new entered comment
    if ($scope.newcomment !== '') {
      data.comment = $scope.newcomment;
      data.commenttype = $scope.commenttype;
    }

    // Add the forecast method
    data.forecastmethod = $scope.detaildata.attributes.forecast.forecastmethod;

    // Get changes from the table
    data.horizon = angular.element(document).find('#horizonbuckets').val();
    data.buckets = [];
    for (let el of angular.element(document).find('#fforecasttable .ng-dirty')) {
      var d = el.value;
      if (d == '')
        d = $scope.measures[el.getAttribute("data-measure")].defaultvalue;
      data.buckets.push({
        'bucket': $scope.detaildata.forecast[parseInt(el.getAttribute("data-index"))].bucket,
        [el.getAttribute("data-measure")]: d
      });
    }

    $scope.postDetail(
      data,
      function (response) {
        if (!recalculate) {
          if (typeof callback === 'function') {
            callback();
          }
          // Reset the form to pristine
          $scope.getDetail();
        } else { //recalculate
          if (typeof response.data !== 'undefined') {
            processForecastData(response, true);
          }
        }
      }
    );
  }
  $scope.save = save;

  function showCustomizeGrid() {
    var popup = angular.element('#popup');
    popup.html(
      '<div class="modal-dialog modal-lg">' +
      '<div class="modal-content">' +
      '<div class="modal-header">' +
      '<h5 class="modal-title">' + gettext("Customize") + '</h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>' +
      '</div>' +
      '<div class="modal-body">' +
      '<div class="row">' +
      '<div class="col-6">' +
      '<div class="card">' +
      '<div class="card-header">' + gettext('Selected Cross') + '</div>' +
      '<div class="card-body">' +
      '<ul class="list-group" id="Crosses" style="height: 160px; overflow-y: scroll;"></ul>' +
      '</div>' +
      '</div>' +
      '</div>' +
      '<div class="col-6">' +
      '<div class="card">' +
      '<div class="card-header">' + gettext('Available Cross') + '</div>' +
      '<div class="card-body">' +
      '<ul class="list-group" id="DroppointCrosses" style="height: 160px; overflow-y: scroll;"></ul>' +
      '</div>' +
      '</div>' +
      '</div>' +
      '</div>' +
      '<div class="row mt-3">' +
      '<div class="col-12"><input class="form-check-input" type="checkbox" id="showdescription"><label for="showdescription">&nbsp;&nbsp;' + gettext('Show descriptions') + '</label></div>' +
      '</div>' +
      '</div>' +
      '<div class="modal-footer justify-content-between">' +
      '<input type="submit" id="cancelCustbutton" role="button" class="btn btn-gray" data-bs-dismiss="modal" value="' + gettext('Cancel') + '">' +
      '<input type="submit" id="resetCustbutton" role="button" class="btn btn-primary" value="' + gettext('Reset') + '">' +
      '<input type="submit" id="okCustbutton" role="button" class="btn btn-primary" value="' + gettext("OK") + '">' +
      '</div>' +
      '</div>' +
      '</div>');

    // Create labels
    var Crosses = popup.find("#Crosses");
    var DroppointCrosses = popup.find("#DroppointCrosses");
    var hidden = Object.values($scope.measures);
    for (var j in $scope.rows) {
      var newli = $('<li class="list-group-item" style="cursor: move"></li>')
        .text($scope.measures[$scope.rows[j]].label)
        .attr("data-value", $scope.rows[j]);
      hidden = hidden.filter(a => a.name != $scope.rows[j]);
      Crosses.append(newli);
    }
    hidden.sort((a, b) => a.label.localeCompare(b.label));
    for (var j of hidden) {
      var newli = $('<li class="list-group-item" style="cursor: move"></li>')
        .text(j.label)
        .attr("data-value", j.name);
      DroppointCrosses.append(newli);
    }

    // Make draggable
    Sortable.create(Crosses[0], {
      group: {
        name: 'Crosses',
        put: ['DroppointCrosses']
      },
      animation: 100
    });
    Sortable.create(DroppointCrosses[0], {
      group: {
        name: 'DroppointCrosses',
        put: ['Crosses']
      },
      animation: 100
    });
    popup.modal('show');

    if ($scope.showdescription) popup.find('#showdescription').prop("checked", true);

    popup.find("#showdescription").on('change', function () {
      $scope.showdescription = popup.find("#showdescription").is(":checked");
    });

    popup.find('#resetCustbutton').on('click', function () {
      $scope.rows = [];
      angular.forEach(measures, function (val, key) {
        if (val["initially_hidden"] !== true
          && (val["mode_future"] !== 'hidden' || val["mode_past"] !== 'hidden'))
          $scope.rows.push(key);
      });
      savePreferences(function () { window.location.href = window.location.href; });
    });

    popup.find('#okCustbutton').on('click', function () {
      $scope.rows = [];
      $('#Crosses li').each(function (index, value) {
        $scope.rows.push($(value).attr('data-value'));
      });
      savePreferences(function () { window.location.href = window.location.href; });
    });
  };
  $scope.showCustomizeGrid = showCustomizeGrid;

  //
  // Editing of cells
  //
  $scope.edit_measure = "forecastoverride";
  $scope.edit_startdate = new Date();
  $scope.edit_enddate = new Date();
  $scope.edit_mode = 0;
  $scope.edit_set = '';
  $scope.edit_inc_perc = null;
  $scope.edit_inc = null;
  $scope.edit_comment = '';

  function applyEdit() {
    if (angular.element(document).find('#applyedit').hasClass("disabled"))
      return;

    // Toggle classes in the grid
    angular.element(document).find('#forecasttablebody input.edit-cell')
      .removeClass("edit-cell").addClass("ng-dirty");

    // Update grid
    $scope.edit_set = parseFloat($scope.edit_set);
    $scope.edit_inc_perc = parseFloat($scope.edit_inc_perc);
    var factor = 1 + $scope.edit_inc_perc / 100.0;
    var msr = $scope.measures[$scope.edit_measure];
    $scope.edit_inc = parseFloat($scope.edit_inc);
    for (var bckt in $scope.detaildata.forecast) {
      if ($scope.detaildata.forecast[bckt]["startdate_date"] < $scope.edit_enddate
        && $scope.detaildata.forecast[bckt]["enddate_date"] > $scope.edit_startdate) {
        if ($scope.edit_measure == "forecastoverride") {
          // Case 1: forecast override
          if ($scope.edit_mode == 0)
            $scope.detaildata.forecast[bckt][$scope.edit_measure] = $scope.edit_set;
          else if ($scope.edit_mode == 1) {
            $scope.detaildata.forecast[bckt][$scope.edit_measure] =
              $scope.detaildata.forecast[bckt]["forecasttotal"] + $scope.edit_inc;
          }
          else if ($scope.edit_mode == 2) {
            $scope.detaildata.forecast[bckt][$scope.edit_measure] =
              $scope.detaildata.forecast[bckt]["forecasttotal"] * factor;
          }
          $scope.detaildata.forecast[bckt]["forecasttotal"] =
            ($scope.detaildata.forecast[bckt]["forecastoverride"] != -1
              && $scope.detaildata.forecast[bckt]["forecastoverride"] != null) ?
              $scope.detaildata.forecast[bckt]["forecastoverride"] :
              $scope.detaildata.forecast[bckt]["forecastbaseline"];
        } else if (msr.discrete) {
          // Case 2: discrete measures
          if ($scope.edit_mode == 0)
            $scope.detaildata.forecast[bckt][$scope.edit_measure] = Math.round(
              $scope.edit_set
            );
          else if ($scope.edit_mode == 1)
            $scope.detaildata.forecast[bckt][$scope.edit_measure] = Math.round(
              $scope.detaildata.forecast[bckt][$scope.edit_measure] + $scope.edit_inc
            );
          else if ($scope.edit_mode == 2)
            $scope.detaildata.forecast[bckt][$scope.edit_measure] = Math.round(
              $scope.detaildata.forecast[bckt][$scope.edit_measure] * factor
            );
        } else {
          // Case 3: non-discrete measures
          if ($scope.edit_mode == 0)
            $scope.detaildata.forecast[bckt][$scope.edit_measure] = $scope.edit_set;
          else if ($scope.edit_mode == 1)
            $scope.detaildata.forecast[bckt][$scope.edit_measure] += $scope.edit_inc;
          else if ($scope.edit_mode == 2)
            $scope.detaildata.forecast[bckt][$scope.edit_measure] *= factor;
        }
      }
      if ($scope.detaildata.forecast[bckt]["startdate_date"] > $scope.edit_enddate)
        break;
    }
  }
  $scope.applyEdit = applyEdit;

  function changeEdit() {
    var disabled = $scope.edit_measure == ''
      || ($scope.edit_mode == 0 && ($scope.edit_set === '' || $scope.edit_set === null))
      || ($scope.edit_mode == 1 && !$scope.edit_inc)
      || ($scope.edit_mode == 2 && !$scope.edit_inc_perc);

    // Button
    if (disabled)
      angular.element(document).find('#applyedit').addClass("disabled");
    else
      angular.element(document).find('#applyedit').removeClass("disabled");

    // Mark impacted grid cells
    angular.element(document).find('#forecasttablebody input.edit-cell').removeClass("edit-cell");
    for (var bckt in $scope.detaildata.forecast) {
      if ($scope.detaildata.forecast[bckt]["startdate_date"] < $scope.edit_enddate
        && $scope.detaildata.forecast[bckt]["enddate_date"] > $scope.edit_startdate)
        angular.element(document).find(
          '#forecasttablebody input[data-index="' + bckt + '"][data-measure="' +
          $scope.edit_measure + '"]').addClass("edit-cell");
      if ($scope.detaildata.forecast[bckt]["startdate_date"] >= $scope.edit_enddate)
        break;
    }
  };
  $scope.changeEdit = changeEdit;

  function focusEdit(event) {
    var el = event.target;
    $scope.edit_measure = el.getAttribute("data-measure");
    var bckt = $scope.detaildata.forecast[parseInt(el.getAttribute("data-index"))];
    $scope.edit_startdate = bckt.startdate_date;
    $scope.edit_enddate = bckt.enddate_date;
    $scope.changeEdit();
  };
  $scope.focusEdit = focusEdit;

  function savefavorite() {
    if (!('favorites' in $scope.preferences))
      $scope.preferences['favorites'] = {};
    var favname = angular.element(document).find("#favoritename").val();
    $scope.preferences['favorites'][favname] = {
      'measure': $scope.measure,
      'sequence': $scope.sequence,
      'rows': $scope.rows
    };
    savePreferences();
    favorite.check();
  }
  $scope.savefavorite = savefavorite;

  function removefavorite(f, $event) {
    delete $scope.preferences.favorites[f];
    savePreferences();
    $event.stopPropagation();
  }
  $scope.removefavorite = removefavorite;

  function openfavorite(f, $event) {
    $scope.measure = $scope.preferences.favorites[f]['measure'];
    $scope.sequence = $scope.preferences.favorites[f]['sequence'];
    $scope.rows = $scope.preferences.favorites[f]['rows'];
    $scope.grid.setPristine = true;
  }
  $scope.openfavorite = openfavorite;
}
