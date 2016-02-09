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
      grass2: themeconfig('grass2'),
      grass3: themeconfig('grass3'),
      earth2: themeconfig('earth2'),
      lemon2: themeconfig('lemon2'),
      snow2: themeconfig('snow2'),
      strawberry2: themeconfig('strawberry2'),
      water2: themeconfig('water2'),
      orange2: themeconfig('orange2')
    },
    // When any .less file changes we automatically run the "less"-task.
    watch: {
      files: ["**/*.less"],
      tasks: ["less"]
    }
  });

  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-watch');

  grunt.registerTask('default', ['less']);
};
