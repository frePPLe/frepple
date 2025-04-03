========================
Creating an custom theme
========================

The user interface is styled using bootstrap v5. All variables documented at
https://getbootstrap.com/docs/5.2/customize/overview/ are available to you to
design your look and feel.

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

      npm install grunt-cli pnpm -g

#. | **Install the javascript dependencies**:
   | Compiling the frePPLe and bootstrap styles requires a number of
     javascript libraries. Install these with the following command:

   ::

      pnpm install

#. | **Design the SASS files**:
   | The styles are defined in the following files. Check out
     https://getbootstrap.com/docs/5.2/customize/overview/ to learn more about 
     customizing the bootstrap CSS styles.

       - | *freppledb/common/static/css/frepple.scss*:
         | Defines the frePPLe specific CSS styles.

       - | *freppledb/common/static/css/THEME/theme.scss*:
         | Optionally, you can create files with theme-specific styles that can't
           be expressed as variable values.

#. | **Compile the SASS files**:
   | The less files need to be compiled into a CSS stylesheet for each theme.
     Edit the gruntfile.js file to include your theme in the list of themes, and
     then run the following command:

   ::

       grunt sass

   In each of the theme folders the file bootstrap.min.css and bootstrap.min.css.map
   will be generated.

#. | **Update djangosettings.py file**:
   | New themes are only shown in the user interface when the theme is configured
     in the setting *THEMES*.
   | You can also edit the setting *DEFAULT_THEME* to make your theme the default
     one.
