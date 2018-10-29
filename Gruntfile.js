/* Copyright (C) 2015 by frePPLe bvba
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
 */

function themeconfig(themefolder, themename) {
  // Auxilary function to generate the task configuration for a single theme.
  var cfg = {
    options: {
      paths: [
        themefolder + '/static/css/' + themename, // frePPLe theme folder
        'freppledb/common/static/css', // frePPLe folder
        'node_modules/bootstrap/less' // bootstrap folder
        ],
      strictMath: true,
      sourceMap: true,
      compress: true,
      relativeUrls: true,
      plugins: [
        new(require('less-plugin-autoprefix'))({
          browsers: ["last 2 versions"]
        })
      ]
    },
    files: {}
  }
  cfg.files[themefolder + '/static/css/' + themename + '/bootstrap.min.css'] = [
    'freppledb/common/static/css/frepple.less', // Generic frePPLe styles
    themefolder + '/static/css/' + themename + '/frepple.less' // Theme specific styles
    ]
  return cfg;
}

// Grunt configuration
module.exports = function (grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    // Less compilation
    less: {
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
    // When any .less file changes we automatically run the "less"-task.
    watch: {
      files: ["**/*.less"],
      tasks: ["less"]
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
            'freppledb/input/static/operationplandetail/src/*.js'
            ]
        }
      },
    },

    exec: {
      extractDjangoStrings: {
        command: 'make international'
        },
      merge_pot_template: {
        command: 'find . -type f -name "*.po" -exec msgmerge -U template.pot {} \\;',
        cwd: 'freppledb/common/static/common/po'
        }
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
              'freppledb/common/static/common/src/preferences.js',
              'freppledb/common/static/common/src/chat.js'
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
              'freppledb/input/static/operationplandetail/src/module.js',
              'freppledb/input/static/operationplandetail/src/operationplandetailCtrl.js',
              'freppledb/input/static/operationplandetail/src/problemspanelDrv.js',
              'freppledb/input/static/operationplandetail/src/resourcespanelDrv.js',
              'freppledb/input/static/operationplandetail/src/bufferspanelDrv.js',
              'freppledb/input/static/operationplandetail/src/demandpeggingpanelDrv.js',
              'freppledb/input/static/operationplandetail/src/operationplanpanelDrv.js',
              'freppledb/input/static/operationplandetail/src/supplyinformationDrv.js',
              'freppledb/input/static/operationplandetail/src/networkstatusDrv.js'
              ],
        dest: 'freppledb/input/static/js/frepple-operationplandetail.js'
      }
    },

    // Uglify the javascript files
    uglify: {
      options: {
        sourceMap: true,
        banner: '/* frePPLe <%= pkg.version %> <%= grunt.template.today("yyyy-mm-dd") %>\n' +
          'Copyright (C) 2010-2017 by frePPLe bvba\n\n' +
          'This library is free software; you can redistribute it and/or modify it\n' +
          'under the terms of the GNU Affero General Public License as published\n' +
          'by the Free Software Foundation; either version 3 of the License, or\n' +
          '(at your option) any later version.\n\n' +
          'This library is distributed in the hope that it will be useful,\n' +
          'but WITHOUT ANY WARRANTY; without even the implied warranty of\n' +
          'MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero\n' +
          'General Public License for more details.\n\n' +
          'You should have received a copy of the GNU Affero General Public\n' +
          'License along with this program.  If not, see <http://www.gnu.org/licenses/>.\n' +
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
      }
    },

    // Clean intermediate files
    clean: [
      'freppledb/common/static/js/frepple-common.js',
      'freppledb/input/static/js/frepple-input.js',
      'freppledb/input/static/js/frepple-operationplandetail.js'
      ]
  });

  // Load tasks
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-angular-gettext');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-exec');

  // Tanslations process
  // 1) Extract django strings: make international
  // 2) Extract angular strings: grunt ngettext_extract
  // 3) Merge .pot file from the previous step into the .po files:  grunt merge_pot_template
  // 4) Translate all strings in the angular and django .po files. The real work!
  // 5) Process the angular .po files into a javascript file: grunt nggettext_compile
  grunt.registerTask('international_1', ['exec:extractDjangoStrings', 'nggettext_extract', 'exec:merge_pot_template']);
  grunt.registerTask('international_2', ['nggettext_compile']);

  // Register our tasks
  grunt.registerTask('minify', ['concat', 'uglify', 'clean']);
  grunt.registerTask('default', ['less', 'concat', 'uglify', 'clean']);

};
