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

angular.module('frepple.input').service('Model', ModelService);

ModelService.$inject = ['Buffer', 'Demand', 'Item', 'Location', 'Operation', 'Resource'];

function ModelService (Buffer, Demand, Item, Location, Operation, Resource) {

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
