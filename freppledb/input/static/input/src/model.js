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

'use strict';

angular.module('frepple.input').service('Model', ModelService);

ModelService.$inject = ['Buffer', 'Demand', 'Item', 'Location', 'Operation', 'Resource'];

function ModelService(Buffer, Demand, Item, Location, Operation, Resource) {

  var masterdata = {
    demands: {},
    operations: {},
    items: {},
    locations: {},
    buffers: {},
    resources: {}
  };

  // Populate all master data from a json document
  function load(jsondoc) {
    for (var i in jsondoc.items)
      masterdata.items[jsondoc.items[i].name] = new Item(jsondoc.items[i]);
    for (var i in jsondoc.operations)
      masterdata.operations[jsondoc.operations[i].name] = new Operation(jsondoc.operations[i]);
    for (var i in jsondoc.demands)
      masterdata.demands[jsondoc.demands[i].name] = new Demand(jsondoc.demands[i]);
    for (var i in jsondoc.locations)
      masterdata.locations[jsondoc.locations[i].name] = new Location(jsondoc.locations[i]);
    for (var i in jsondoc.buffers)
      masterdata.buffers[jsondoc.buffers[i].name] = new Buffer(jsondoc.buffers[i]);
    for (var i in jsondoc.resources)
      masterdata.resources[jsondoc.resources[i].name] = new Resource(jsondoc.resources[i]);
  }

  var service = {
    masterdata: masterdata,
    load: load,
  };
  return service;
};
