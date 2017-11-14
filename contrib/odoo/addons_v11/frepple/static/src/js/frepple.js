odoo.define('frepple', function (require) {
  'use strict';

  var core = require('web.core');
  var Widget = require('web.Widget');

  /* Forecast editor widget. */
  var ForecastEditor = Widget.extend({
    start: function() {
      var el = this.$el;
      el.height("calc(100% - 34px)");
      this._rpc({
        model: 'res.company',
        method: 'getFreppleURL',
        args: [false, '/forecast/editor/'],
        })
        .then(function(result) {
          el.append('<iframe src="' + result
            + '" width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" '
            + ' scrolling="yes" style="border-width:0px;"/>');
          });
    }
  });
  core.action_registry.add('frepple.forecasteditor', ForecastEditor);

  /* Inventory planning widget. */
  var InventoryPlanning = Widget.extend({
    start: function() {
      var el = this.$el;
      el.height("calc(100% - 34px)");
      this._rpc({
        model: 'res.company',
        method: 'getFreppleURL',
        args: [false, '/inventoryplanning/drp/'],
        })
        .then(function(result) {
          el.append('<iframe src="' + result
            + '" width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" '
            + ' scrolling="yes" style="border-width:0px;"/>');
          });
    }
  });
  core.action_registry.add('frepple.inventoryplanning', InventoryPlanning);

  /* Plan editor widget. */
  var PlanEditor = Widget.extend({
    start: function() {
      var el = this.$el;
      el.height("calc(100% - 34px)");
      this._rpc({
        model: 'res.company',
        method: 'getFreppleURL',
        args: [false, '/planningboard/'],
        })
        .then(function(result) {
          el.append('<iframe src="' + result
            + '" width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" '
            + ' scrolling="yes" style="border-width:0px;"/>');
          });
    }
  });
  core.action_registry.add('frepple.planeditor', PlanEditor);

  /* Full user interface widget. */
  var HomePage = Widget.extend({
    start: function() {
      var el = this.$el;
      el.height("calc(100% - 34px)");
      this._rpc({
        model: 'res.company',
        method: 'getFreppleURL',
        args: [true, '/'],
        })      
        .then(function(result) {
          el.append('<iframe src="' + result
            + '" width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" '
            + ' scrolling="yes" style="border-width:0px;"/>');
          });
    }
  });
  core.action_registry.add('frepple.homepage', HomePage);

});
