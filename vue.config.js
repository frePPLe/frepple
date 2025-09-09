const { defineConfig } = require("@vue/cli-service");
module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: 'freppledb',
  outputDir: 'freppledb/common/static/js/vuejs',
  assetsDir: 'freppledb/common/static',
  runtimeCompiler: true
});
