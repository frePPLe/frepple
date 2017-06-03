========================
Creating an custom theme
========================

The user interface is styled using bootstrap. All variables documented at
http://getbootstrap.com/customize/ are available to you to design your
look and feel.

Proceed with the following steps to compile a custom theme:

#. | **Install node.js**:
   | Download and install the node.js javascript runtime environment from
     https://nodejs.org/en/.
   | The installation also makes the npm command available which we'll use
     in the following steps.

#. | **Install grunt command line tools**:
   | Grunt is a javascript task running utility.
   | Install it with the command:

   ::

      npm install grunt-cli -g

#. | **Install the javascript dependencies**:
   | Compiling the frePPLe and bootstrap styles requires a number of
     javascript libraries. Install these with the following command:

   ::

      npm install

#. | **Design the LESS files**:
   | The styles are defined in the following files. Check out http://lesscss.org/
     to learn more about the Less syntax used in these files.

       - | *freppledb/common/static/css/frepple.less*:
         | Defines the frePPLe specific CSS styles.

       - | *freppledb/common/static/css/THEME/variables.less*:
         | Defines the configuration of bootstrap for each of the themes.
           The value of the variables is what a theme unique.

       - | *freppledb/common/static/css/THEME/frepple.less*:
         | Optionally, you can create files with theme-specific styles that can't
           be expressed as variable values.

#. | **Compile the LESS files**:
   | The less files need to be compiled into a CSS stylesheet for each theme.
     This is done by the following command:

   ::

       grunt less

   In each of the theme folders the file bootstrap.min.css and bootstrap.min.css.map
   are generated.

#. | **Update djangosettings.py file**:
   | New themes are only shown in the user interface when the theme is configured
     in the setting *THEMES*.
