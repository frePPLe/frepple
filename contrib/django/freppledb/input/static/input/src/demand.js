/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

angular.module('frepple.input').factory('Demand', DemandFactory);

DemandFactory.$inject = ['$http', 'getURLprefix', 'Location', 'Item', 'Customer'];

function DemandFactory ($http, getURLprefix, Location, Item, Customer) {  
  
  var debug = true;

  function Demand(data) {
    if (data) this.extend(data);
  };
  
  Demand.prototype = {      
    extend: extend,
    getData: getData,
    // REST API methods
    get: get,
    save: save,
    remove: remove,
    // Quoting web service API
    quote: quote,
    cancel: cancel,
    inquiry: inquiry,
    confirm: confirm,
    info: info
  };
  
  return Demand;
  
  function extend(data) {   
    // Convert new values to the correct type
    angular.forEach(data, function(value, key) {
      switch (key) {
        case "due":
          if (!moment.isMoment(value))
            data['due'] = moment(value);
          break;
        case "pegging":
          value.forEach(function(i, indx) {
            if (!moment.isMoment(i.operationplan.start))
              i.operationplan.start = moment(i.operationplan.start);
            if (!moment.isMoment(i.operationplan.end))
              i.operationplan.end = moment(i.operationplan.end);
            });
          break;
        case "problems":
          value.forEach(function(i, indx) {
            if (!moment.isMoment(i.start))
              i.start = moment(i.start);
            if (!moment.isMoment(i.end))
              i.end = moment(i.end);
            });
          break;    
        case "constraints":
          value.forEach(function(i, indx) {
            if (!moment.isMoment(i.start))
              i.start = moment(i.start);
            if (!moment.isMoment(i.end))
              i.end = moment(i.end);
            });
          break;
        case "item":
          if (value && !value instanceof Item)
            data['item'] = new Item(value);
          break;
        case "location":
          if (value && !value instanceof Location)
            data['location'] = new Location(value);
          break;
        case "customer":
          if (value && !value instanceof Customer)
            data['customer'] = new Customer(value);
          break;
        case "maxlateness":
          // Convert from seconds to days
          data['maxlateness'] = value / 86400;
          break;
      }
    });
    
    // Merge update values in demand object
    angular.extend(this, data);
  };

  function getData() {
    var fields = {
      name: this.name
    };
    if (this.quantity !== undefined)
      fields.quantity = this.quantity;
    if (this.description !== undefined)
      fields.description = this.description;
    if (this.category !== undefined)
      fields.category = this.category;
    if (this.subcategory !== undefined)
      fields.subcategory = this.subcategory;
    if (this.due !== undefined)
      fields.due = this.due.format('YYYY-MM-DDTHH:mm:ss');
    if (this.item !== undefined && this.item)
      fields.item = {name: this.item.name};
    if (this.location !== undefined && this.location)
      fields.location = {name: this.location.name};
    if (this.customer !== undefined && this.customer)
      fields.customer = {name: this.customer.name};
    if (this.minshipment !== undefined)
      fields.minshipment = this.minshipment;
    if (this.maxlateness !== undefined)
      // Convert from days to seconds
      fields.maxlateness = this.maxlateness * 86400;
    if (this.priority !== undefined)
      fields.priority = this.priority;
    return fields;
  };
  
  // REST API GET
  function get() {
    var dmd = this;
    return $http
      .get(getURLprefix() + '/api/input/demand/' + encodeURIComponent(dmd.name) + "/")
      .then(function (response) {
        if (debug) 
          console.log("Demand get '" + dmd.name + "': ", response.data);
        dmd.extend(response.data);
        return dmd;
        });
  };
  
  // REST API PUT
  function save() {
    var dmd = this;
    return $http
      .put(getURLprefix() + '/api/input/demand/' + encodeURIComponent(dmd.name) + "/", dmd.getData())
      .then(function (response) {
        if (debug) 
          console.log("Demand save '" + dmd.name + "': ", response.data);
        dmd.extend(response.data);
        return dmd;
        });
  };
  
  // REST API DELETE
  function remove() {
    var dmd = this;
    return $http
      .delete(getURLprefix() + '/api/input/demand/' + encodeURIComponent(dmd.name) + "/")
      .then(function (response) {
        if (debug) 
          console.log("Demand delete '" + dmd.name + "': ", response.data);
        dmd.status = 'closed';
        return dmd;
        });
  };
    
  function info(name) {
    var dmd = this;
    return $http
      .post(getURLprefix() + '/quote/info/', [dmd.name])
      .then(function (response) {
        if (debug) 
          console.log("Demand info '" + dmd.name + "': ", response.data);
        dmd.extend(response.data.demands[0]);
        return dmd;
        });
  };
  
  function inquiry() {
    var dmd = this;
    dmd.status = "inquiry";
    return $http
      .post(getURLprefix() + '/quote/inquiry/', {demands:[dmd.getData()]})
      .then(function (response) {
        if (debug) 
          console.log("Demand inquiry '" + dmd.name + "': ", response.data);
        dmd.extend(response.data.demands[0]);
        return dmd;
        });
  };
  
  function quote() {
    var dmd = this;
    return $http
      .post(getURLprefix() + '/quote/quote/', {demands:[dmd.getData()]})
      .then(function (response) {
        if (debug) 
          console.log("Demand quote '" + dmd.name + "': ", response.data);
        dmd.extend(response.data.demands[0]);
        //return dmd;
        });
  };

  function cancel() {
    var dmd = this;
    return $http
      .post(getURLprefix() + '/quote/cancel/?name=' + encodeURIComponent(dmd.name))
      .then(function (response) {
        if (debug) 
          console.log("Demand '" + dmd.name + "' canceled");
        dmd.status = "closed";
        return dmd;
        });    
  };

  function confirm() {
    var dmd = this;
    return $http
      .post(getURLprefix() + '/quote/confirm/?name=' + encodeURIComponent(dmd.name))
      .then(function (response) {
        if (debug) 
          console.log("Demand '" + dmd.name + "' confirmed");
        dmd.status = "confirmed";
        return dmd;
        });      
  };

};