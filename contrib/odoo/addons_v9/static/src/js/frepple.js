openerp.frepple = function(instance, local) {
  var _t = instance.web._t,
      _lt = instance.web._lt;
  var QWeb = instance.web.qweb;

  local.HomePage = instance.Widget.extend({
    start: function() {
      var el = this.$el;
      el.height("calc(100% - 34px)");
      var model = new instance.web.Model("res.company");
      model.call("getWebToken", [], {context: new instance.web.CompoundContext({})})
        .then(function(result) {
          el.append('<iframe src="http://localhost:8000?webtoken=' + result 
            + ' " width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" '
            + ' scrolling="yes" style="border-width:0px;"/>');
          });
    }
  });

  instance.web.client_actions.add('frepple.homepage', 'instance.frepple.HomePage');
}
