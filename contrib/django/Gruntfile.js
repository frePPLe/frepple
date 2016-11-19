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

function themeconfig(themename)
{
  // Auxilary function to generate the task configuration for a single theme.
  var cfg = {
    options: {
      paths: [
        'freppledb/common/static/css/' + themename,  // frePPLe theme folder
        'freppledb/common/static/css',               // frePPLe folder
        'node_modules/bootstrap/less'                // bootstrap folder
        ],
      strictMath: true,
      sourceMap: true,
      compress: true,
      relativeUrls: true,
      plugins: [
        new (require('less-plugin-autoprefix'))({ browsers: ["last 2 versions"] })
      ]
    },
    files: {}
  }
  cfg.files['freppledb/common/static/css/' + themename + '/bootstrap.min.css'] = [
    'freppledb/common/static/css/frepple.less',                  // Generic frePPLe styles
    'freppledb/common/static/css/' + themename + '/frepple.less' // Theme specific styles
    ]
  return cfg;
}


// Grunt configuration
module.exports = function (grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    // Less compilation
    less: {
      odoo: themeconfig('odoo'),
      grass: themeconfig('grass'),
      earth: themeconfig('earth'),
      lemon: themeconfig('lemon'),
      snow: themeconfig('snow'),
      strawberry: themeconfig('strawberry'),
      water: themeconfig('water'),
      orange: themeconfig('orange'),
      openbravo: themeconfig('openbravo')
    },
    // When any .less file changes we automatically run the "less"-task.
    watch: {
      files: ["**/*.less"],
      tasks: ["less"]
    },
    // Minify the javascript files
    uglify: {
      options: {
        sourceMap: true,
        banner: '/* frePPLe <%= pkg.version %> <%= grunt.template.today("yyyy-mm-dd") %>\n' +
          'Copyright (C) 2010-2016 by frePPLe bvba\n\n' +
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
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-uglify');

  grunt.registerTask('default', ['less']);
};
