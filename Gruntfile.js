/* Copyright (C) 2015 by frePPLe bv
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

const sass = require('sass');

function themeconfig(themefolder, themename) {
  // Auxilary function to generate the task configuration for a single theme.
  var cfg = {
    options: {
      implementation: sass,
      includePaths: [
        themefolder + '/static/css/' + themename, // frePPLe theme folder
        'freppledb/common/static/css'//, // frePPLe folder
      ],
      outputStyle: 'compressed'
    },
    files: {}
  }
  cfg.files[themefolder + '/static/css/' + themename + '/bootstrap.min.css'] = [
    'freppledb/common/static/css/frepple.scss', // Generic frePPLe styles
    themefolder + '/static/css/' + themename + '/frepple.scss' // Theme specific styles
  ]
  return cfg;
}

// Grunt configuration
module.exports = function (grunt) {

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    // SASS compilation
    sass: {
      odoo: themeconfig('freppledb/common', 'odoo'),
      grass: themeconfig('freppledb/common', 'grass'),
      earth: themeconfig('freppledb/common', 'earth'),
      lemon: themeconfig('freppledb/common', 'lemon'),
      snow: themeconfig('freppledb/common', 'snow'),
      strawberry: themeconfig('freppledb/common', 'strawberry'),
      water: themeconfig('freppledb/common', 'water'),
      orange: themeconfig('freppledb/common', 'orange'),
      openbravo: themeconfig('freppledb/common', 'openbravo'),
    },
    // When any .scss file changes we automatically run the "sass"-task.
    watch: {
      files: ["**/*.scss"],
      tasks: ["sass"]
    },

    // Extract translations
    nggettext_extract: {
      pot: {
        options: {
          msgmerge: true
        },
        files: {
          'freppledb/common/static/common/po/template.pot': [
            'freppledb/input/static/operationplandetail/*.html',
            'freppledb/input/static/operationplandetail/src/*.js',
            'freppledb/forecast/static/forecast/*.html',
            'freppledb/forecast/static/forecast/src/*.js'
          ]
        }
      },
    },

    // Compile translations
    nggettext_compile: {
      all: {
        files: {
          'freppledb/common/static/js/i18n/angular-freppletranslations.js': [
            'freppledb/common/static/common/po/*.po'
          ]
        }
      },
    },

    // Concatenate javascript files
    concat: {
      common: {
        src: [
          'freppledb/common/static/common/src/module.js',
          'freppledb/common/static/common/src/webfactory.js',
          'freppledb/common/static/common/src/preferences.js'
        ],
        dest: 'freppledb/common/static/js/frepple-common.js'
      },
      input: {
        src: [
          'freppledb/input/static/input/src/module.js',
          'freppledb/input/static/input/src/buffer.js',
          'freppledb/input/static/input/src/demand.js',
          'freppledb/input/static/input/src/customer.js',
          'freppledb/input/static/input/src/item.js',
          'freppledb/input/static/input/src/location.js',
          'freppledb/input/static/input/src/operation.js',
          'freppledb/input/static/input/src/operationplan.js',
          'freppledb/input/static/input/src/resource.js',
          'freppledb/input/static/input/src/model.js',
        ],
        dest: 'freppledb/input/static/js/frepple-input.js'
      },
      operationplandetail: {
        src: [
          'freppledb/input/static/operationplandetail/src/calendar.js',
          'freppledb/input/static/operationplandetail/src/module.js',
          'freppledb/input/static/operationplandetail/src/operationplandetailCtrl.js',
          'freppledb/input/static/operationplandetail/src/problemspanelDrv.js',
          'freppledb/input/static/operationplandetail/src/resourcespanelDrv.js',
          'freppledb/input/static/operationplandetail/src/bufferspanelDrv.js',
          'freppledb/input/static/operationplandetail/src/demandpeggingpanelDrv.js',
          'freppledb/input/static/operationplandetail/src/operationplanpanelDrv.js',
          'freppledb/input/static/operationplandetail/src/supplyinformationDrv.js',
          'freppledb/input/static/operationplandetail/src/downstreamoperationplansDrv.js',
          'freppledb/input/static/operationplandetail/src/upstreamoperationplansDrv.js',
          'freppledb/input/static/operationplandetail/src/inventorydataDrv.js',
          'freppledb/input/static/operationplandetail/src/inventorygraphDrv.js',
          'freppledb/input/static/operationplandetail/src/kanbanDrv.js',
          'freppledb/input/static/operationplandetail/src/ganttDrv.js',
        ],
        dest: 'freppledb/input/static/js/frepple-operationplandetail.js'
      },
      forecast: {
        src: [
            'freppledb/forecast/static/forecast/src/module.js',
            'freppledb/forecast/static/forecast/src/customerstable.js',
            'freppledb/forecast/static/forecast/src/itemstable.js',
            'freppledb/forecast/static/forecast/src/locationstable.js',
            'freppledb/forecast/static/forecast/src/forecastgridDrv.js',
            'freppledb/forecast/static/forecast/src/displayForecastGraph.js',
            'freppledb/forecast/static/forecast/src/forecast.js'
            ],
          dest: 'freppledb/forecast/static/js/frepple-forecast.js'
      }
    },

    // Uglify the javascript files
    uglify: {
      options: {
        sourceMap: true,
        banner: '/* frePPLe <%= pkg.version %>\n' +
          'Copyright (C) 2010-2019 by frePPLe bv\n\n' +
          'Permission is hereby granted, free of charge, to any person obtaining\n' +
          'a copy of this software and associated documentation files(the\n' +
          '"Software"), to deal in the Software without restriction, including\n' +
          'without limitation the rights to use, copy, modify, merge, publish,\n' +
          'distribute, sublicense, and/ or sell copies of the Software, and to\n' +
          'permit persons to whom the Software is furnished to do so, subject to\n' +
          'the following conditions:\n' +
          '\n' +
          'The above copyright notice and this permission notice shall be\n' +
          'included in all copies or substantial portions of the Software.\n' +
          '\n' +
          'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,\n' +
          'EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF\n' +
          'MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND\n' +
          'NONINFRINGEMENT.IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE\n' +
          'LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION\n' +
          'OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION\n' +
          'WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n' +
          '*/\n'
      },
      js: {
        src: ['freppledb/common/static/js/frepple.js'],
        dest: 'freppledb/common/static/js/frepple.min.js'
      },
      common: {
        src: ['freppledb/common/static/js/frepple-common.js'],
        dest: 'freppledb/common/static/js/frepple-common.min.js'
      },
      input: {
        src: ['freppledb/input/static/js/frepple-input.js'],
        dest: 'freppledb/input/static/js/frepple-input.min.js'
      },
      operationplandetail: {
        src: ['freppledb/input/static/js/frepple-operationplandetail.js'],
        dest: 'freppledb/input/static/js/frepple-operationplandetail.min.js'
      },
      forecast: {
        src: ['freppledb/forecast/static/js/frepple-forecast.js'],
        dest: 'freppledb/forecast/static/js/frepple-forecast.min.js'
      }
    },

    // Clean intermediate files
    clean: [
      'freppledb/common/static/js/frepple-common.js',
      'freppledb/input/static/js/frepple-input.js',
      'freppledb/input/static/js/frepple-operationplandetail.js',
      'freppledb/forecast/static/js/frepple-forecast.js'
    ]
  });

  // Load tasks
  grunt.loadNpmTasks('grunt-sass');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-angular-gettext');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify-es');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-exec');

  // Register our tasks
  grunt.registerTask('minify', ['concat', 'uglify', 'clean']);
  grunt.registerTask('default', ['sass', 'concat', 'uglify', 'clean']);

};
