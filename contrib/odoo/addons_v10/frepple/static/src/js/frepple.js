openerp.frepple = function(instance, local) {
  var _t = instance.web._t,
      _lt = instance.web._lt;
  var QWeb = instance.web.qweb;

  /* Forecast editor widget. */
  local.ForecastEditor = instance.Widget.extend({
    start: function() {
      var el = this.$el;
      el.height("calc(100% - 34px)");
      var model = new instance.web.Model("res.company");
      model.call("getFreppleURL", [], {context: new instance.web.CompoundContext({'navbar': false, 'url': '/forecast/editor/'})})
        .then(function(result) {
          el.append('<iframe src="' + result
            + '" width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" '
            + ' scrolling="yes" style="border-width:0px;"/>');
          });
    }
  });
  instance.web.client_actions.add('frepple.forecasteditor', 'instance.frepple.ForecastEditor');

  /* Inventory planning widget. */
  local.InventoryPlanning = instance.Widget.extend({
    start: function() {
      var el = this.$el;
      el.height("calc(100% - 34px)");
      var model = new instance.web.Model("res.company");
      model.call("getFreppleURL", [], {context: new instance.web.CompoundContext({'navbar': false, 'url': '/inventoryplanning/drp/'})})
        .then(function(result) {
          el.append('<iframe src="' + result
            + '" width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" '
            + ' scrolling="yes" style="border-width:0px;"/>');
          });
    }
  });
  instance.web.client_actions.add('frepple.inventoryplanning', 'instance.frepple.InventoryPlanning');

  /* Plan editor widget. */
  local.PlanEditor = instance.Widget.extend({
    start: function() {
      var el = this.$el;
      el.height("calc(100% - 34px)");
      var model = new instance.web.Model("res.company");
      model.call("getFreppleURL", [], {context: new instance.web.CompoundContext({'navbar': false, 'url': '/planningboard/'})})
        .then(function(result) {
          el.append('<iframe src="' + result
            + '" width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" '
            + ' scrolling="yes" style="border-width:0px;"/>');
          });
    }
  });
  instance.web.client_actions.add('frepple.planeditor', 'instance.frepple.PlanEditor');

  /* Full user interface widget. */
  local.HomePage = instance.Widget.extend({
    start: function() {
      var el = this.$el;
      el.height("calc(100% - 34px)");
      var model = new instance.web.Model("res.company");
      model.call("getFreppleURL", [], {context: new instance.web.CompoundContext({'navbar': true, 'url': '/'})})
        .then(function(result) {
          el.append('<iframe src="' + result
            + '" width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" '
            + ' scrolling="yes" style="border-width:0px;"/>');
          });
    }
  });
  instance.web.client_actions.add('frepple.homepage', 'instance.frepple.HomePage');

}
