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
 */

angular.module("frepple.input", ['frepple.common']);

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

angular.module('frepple.input').factory('Buffer', BufferFactory);

BufferFactory.$inject = ['$http', 'getURLprefix', 'Item', 'Location'];

function BufferFactory($http, getURLprefix, Item, Location) {

  var debug = false;

  function Buffer(data) {
    if (data)
      this.extend(data);
  };

  Buffer.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove
  };

  return Buffer;

  function extend(data) {
    angular.extend(this, data);
  };

  // REST API GET
  function get() {
    var buf = this;
    return $http
      .get(getURLprefix() + '/api/input/buffer/' + encodeURIComponent(buf.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Buffer get '" + buf.name + "': ", response.data);
          buf.extend(response.data);
          return buf;
        }
      );
  };

  // REST API PUT
  function save() {
    var buf = this;
    return $http
      .put(getURLprefix() + '/api/input/buffer/' + encodeURIComponent(buf.name) + "/", buf)
      .then(
        function (response) {
          if (debug)
            console.log("Buffer save '" + buf.name + "': ", response.data);
          buf.extend(response.data);
          return buf;
        }
      );
  };

  // REST API DELETE
  function remove() {
    var buf = this;
    return $http
      .delete(getURLprefix() + '/api/input/buffer/' + encodeURIComponent(buf.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Buffer delete '" + buf.name + "': ", response.data);
          return buf;
        }
      );
  };
};

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

angular.module('frepple.input').factory('Demand', DemandFactory);

DemandFactory.$inject = ['$http', 'getURLprefix', 'Location', 'Item', 'Customer'];

function DemandFactory($http, getURLprefix, Location, Item, Customer) {

  var debug = false;

  function Demand(data) {
    if (data) this.extend(data);
  };

  Demand.prototype = {
    extend: extend,
    getData: getData,
    // REST API methods
    get: get,
    save: save,
    remove: remove
  };

  return Demand;

  function extend(data) {
    // Convert new values to the correct type
    angular.forEach(data, function (value, key) {
      switch (key) {
        case "due":
          if (typeof value === "date" || value instanceof Date)
            data['due'] = value;
          else if (typeof value === "string" || value instanceof String)
            data['due'] = new Date(value);
          else if (!moment.isMoment(value))
            data['due'] = moment(value);
          break;
        case "delivery":
          if (!moment.isMoment(value))
            data['delivery'] = moment(value);
          break;
        case "pegging":
          value.forEach(function (i, indx) {
            if (!moment.isMoment(i.operationplan.start))
              i.operationplan.start = moment(i.operationplan.start);
            if (!moment.isMoment(i.operationplan.end))
              i.operationplan.end = moment(i.operationplan.end);
          });
          break;
        case "problems":
          value.forEach(function (i, indx) {
            if (!moment.isMoment(i.start))
              i.start = moment(i.start);
            if (!moment.isMoment(i.end))
              i.end = moment(i.end);
          });
          break;
        case "constraints":
          value.forEach(function (i, indx) {
            if (!moment.isMoment(i.start))
              i.start = moment(i.start);
            if (!moment.isMoment(i.end))
              i.end = moment(i.end);
          });
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
    if (this.due !== undefined) {
      if (this.due instanceof Date)
        fields.due = this.due.toISOString();
      else
        fields.due = this.due.format('YYYY-MM-DDTHH:mm:ss');
    }
    if (this.item !== undefined && this.item)
      fields.item = { name: this.item.name };
    if (this.location !== undefined && this.location)
      fields.location = { name: this.location.name };
    if (this.customer !== undefined && this.customer)
      fields.customer = { name: this.customer.name };
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

};

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

angular.module('frepple.input').factory('Customer', CustomerFactory);

CustomerFactory.$inject = ['$http', 'getURLprefix'];

function CustomerFactory($http, getURLprefix) {

  var debug = false;

  function Customer(data) {
    if (data)
      angular.extend(this, data);
  };

  Customer.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove
  };

  return Customer;

  function extend(data) {
    angular.extend(this, data);
  };

  // REST API GET
  function get() {
    var cst = this;
    return $http
      .get(getURLprefix() + '/api/input/customer/' + encodeURIComponent(cst.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Customer get '" + cst.name + "': ", response.data);
          cst.extend(response.data);
          return cst;
        }
      );
  };

  // REST API PUT
  function save() {
    var cst = this;
    return $http
      .put(getURLprefix() + '/api/input/customer/' + encodeURIComponent(cst.name) + "/", cst)
      .then(
        function (response) {
          if (debug)
            console.log("Customer save '" + cst.name + "': ", response.data);
          cst.extend(response.data);
          return cst;
        }
      );
  };

  // REST API DELETE
  function remove() {
    var cst = this;
    return $http
      .delete(getURLprefix() + '/api/input/customer/' + encodeURIComponent(cst.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Customer delete '" + itm.name + "': ", response.data);
          return cst;
        }
      );
  };
};

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

angular.module('frepple.input').factory('Item', ItemFactory);

ItemFactory.$inject = ['$http', 'getURLprefix'];

function ItemFactory($http, getURLprefix) {

  var debug = false;

  function Item(data) {
    if (data)
      this.extend(data);
  };

  Item.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove
  };

  return Item;

  function extend(data) {
    angular.extend(this, data);
  };

  // REST API GET
  function get() {
    var itm = this;
    return $http
      .get(getURLprefix() + '/api/input/item/' + encodeURIComponent(itm.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Item get '" + itm.name + "': ", response.data);
          itm.extend(response.data);
          return itm;
        }
      );
  };

  // REST API PUT
  function save() {
    var itm = this;
    return $http
      .put(getURLprefix() + '/api/input/item/' + encodeURIComponent(itm.name) + "/", itm)
      .then(
        function (response) {
          if (debug)
            console.log("Item save '" + itm.name + "': ", response.data);
          itm.extend(response.data);
          return itm;
        }
      );
  };

  // REST API DELETE
  function remove() {
    var itm = this;
    return $http
      .delete(getURLprefix() + '/api/input/item/' + encodeURIComponent(itm.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Item delete '" + itm.name + "': ", response.data);
          return itm;
        }
      );
  };
};

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

angular.module('frepple.input').factory('Location', LocationFactory);

LocationFactory.$inject = ['$http', 'getURLprefix'];

function LocationFactory($http, getURLprefix) {

  var debug = false;

  function Location(data) {
    if (data)
      this.extend(data);
  };

  Location.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove
  };

  return Location;

  function extend(data) {
    angular.extend(this, data);
  };

  //REST API GET
  function get() {
    var loc = this;
    return $http
      .get(getURLprefix() + '/api/input/location/' + encodeURIComponent(loc.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Location get '" + loc.name + "': ", response.data);
          loc.extend(response.data);
          return loc;
        }
      );
  };

  // REST API PUT
  function save() {
    var loc = this;
    return $http
      .put(getURLprefix() + '/api/input/location/' + encodeURIComponent(loc.name) + "/", loc)
      .then(
        function (response) {
          if (debug)
            console.log("Location save '" + loc.name + "': ", response.data);
          loc.extend(response.data);
          return loc;
        }
      );
  };

  // REST API DELETE
  function remove() {
    var loc = this;
    return $http
      .delete(getURLprefix() + '/api/input/location/' + encodeURIComponent(loc.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Location delete '" + loc.name + "': ", response.data);
          return loc;
        });
  };
};

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

angular.module('frepple.input').factory('Operation', OperationFactory);

OperationFactory.$inject = ['$http', 'getURLprefix', 'Location'];

function OperationFactory($http, getURLprefix, Location) {

  var debug = false;

  function Operation(data) {
    if (data)
      this.extend(data);
  };

  Operation.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove
  };

  return Operation;

  function extend(data) {
    angular.extend(this, data);
  }

  //REST API GET
  function get() {
    var oper = this;
    return $http
      .get(getURLprefix() + '/api/input/operation/' + encodeURIComponent(oper.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Operation get '" + oper.name + "': ", response.data);
          oper.extend(response.data);
          return oper;
        }
      );
  };

  // REST API PUT
  function save() {
    var oper = this;
    return $http
      .put(getURLprefix() + '/api/input/operation/' + encodeURIComponent(oper.name) + "/", oper)
      .then(
        function (response) {
          if (debug)
            console.log("Operation save '" + oper.name + "': ", response.data);
          oper.extend(response.data);
          return oper;
        }
      );
  };

  // REST API DELETE
  function remove() {
    var oper = this;
    return $http
      .delete(getURLprefix() + '/api/input/operation/' + encodeURIComponent(oper.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Operation delete '" + oper.name + "': ", response.data);
          return oper;
        }
      );
  };
};

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

angular.module('frepple.input').factory('OperationPlan', OperationPlanFactory);

OperationPlanFactory.$inject = ['$http', 'getURLprefix', 'Operation', 'Location', 'Item'];

function OperationPlanFactory($http, getURLprefix, Operation, Location, Item) {

  var debug = false;

  function OperationPlan(data) {
    if (data)
      this.extend(data);
  }

  function extend(data) {
    angular.extend(this, data);
  }

  //REST API GET
  function get(callback) {
    var operplan = this;
    if (operplan.id === undefined)
      return operplan;
    else {
      return $http
        .get(getURLprefix() + '/operationplan/?reference=' + encodeURIComponent(operplan.id))
        .then(
          function (response) {
            if (debug) {
              console.log("Operation get '" + operplan.id + "': ");
              console.log(response.data);
            }
            Object.keys(operplan).forEach(key => { if (key !== "dirty") delete operplan[key] });
            operplan.extend(response.data[0]);
            if (typeof callback === 'function') {
              callback(operplan);
            }
            return operplan;
          },
          function (err) {
            if (err.status == 401)
              location.reload();
          }
        );
    }
  }

  // REST API PUT
  function save() {
    var operplan = this;
    return $http
      .put(getURLprefix() + '/api/input/operationplan/?reference=' + encodeURIComponent(operplan.name), operplan)
      .then(
        function (response) {
          if (debug) {
            console.log("OperationPlan save '" + operplan.name + "': ", response.data);
          }
          operplan.extend(response.data);
          return operplan;
        },
        function (err) {
          if (err.status == 401)
            location.reload();
        }
      );
  }

  // REST API DELETE
  function remove() {
    var operplan = this;
    return $http
      .delete(getURLprefix() + '/api/input/operationplan/?reference=' + encodeURIComponent(operplan.name))
      .then(
        function (response) {
          if (debug)
            console.log("OperationPlan delete '" + operplan.name + "': ", response.data);
          return operplan;
        },
        function (err) {
          if (err.status == 401)
            location.reload();
        }
      );
  }

  OperationPlan.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove
  };
  return OperationPlan;
}

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

angular.module('frepple.input').factory('Resource', ResourceFactory);

ResourceFactory.$inject = ['$http', 'getURLprefix', 'Location'];

function ResourceFactory($http, getURLprefix, Location) {

  var debug = false;

  function Resource(data) {
    if (data)
      this.extend(data);
  };

  Resource.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove
  };

  return Resource;

  function extend(data) {
    angular.extend(this, data);
  }

  // REST API GET
  function get() {
    var res = this;
    return $http
      .get(getURLprefix() + '/api/input/resource/' + encodeURIComponent(res.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Resource get '" + res.name + "': ", response.data);
          res.extend(response.data);
          return res;
        }
      );
  };

  // REST API PUT
  function save() {
    var res = this;
    return $http
      .put(getURLprefix() + '/api/input/resource/' + encodeURIComponent(red.name) + "/", res)
      .then(
        function (response) {
          if (debug)
            console.log("Resource save '" + res.name + "': ", response.data);
          res.extend(response.data);
          return res;
        }
      );
  };

  // REST API DELETE
  function remove() {
    var res = this;
    return $http
      .delete(getURLprefix() + '/api/input/resource/' + encodeURIComponent(res) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Resource delete '" + res.name + "': ", response.data);
          return res;
        }
      );
  };
};

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
