
This directory contains a sample web application for frePPLe.
It is built using the incredible Django web application framework.

The basic steps to set up a development environment:

- Install python 2.5
  Lower versions may work, but are not tested...

- Install django
  FREPPLE NEEDS THE DEVELOPMENT VERSION OF DJANGO. AT THE TIME FREPPLE 0.5.1 IS
  RELEASED DJANGO WAS AT REVISION 7538.
  To get this version of django use the following command:
    svn co --revision 7538 http://code.djangoproject.com/svn/django/trunk/ django_src
  Later versions of django may or may not work with frePPLe...

- Some patches are required to django.
  These are included at the bottom of this file. Copy these into a patch file to
  apply, or merge the updates manually.

- Install your database: postgresql / mysql / oracle
  Alternatively, you can use the sqlite3 database bundled with Python.

- Install the python database access library for the database (see the django
  documentation for details)

- Create a database schema for frePPle.
  For the django tests, the user should have sufficient privileges to create a
  new database.

- Edit the file settings.py to point to your database schema

- Initialize the database schema:
      manage.py syncdb
  When the command prompts you to create a django superuser you can choose
  'no', since the inital dataset that is installed will include the users
  "admin", "frepple" and "guest".
  When the command finishes, verify the database tables are created correctly.

- Test your installation by starting the development server:
      manage.py runserver
  and then pointing your browser to http://127.0.0.1:8000/admin
  A login page should come up.

- The "execute" screen in the user interface allows you to erase the data,
  to load a dataset, to generate a random test model and run frePPLe.

For more detailed information please look at the django documentation
on http://www.djangoproject.com
The tutorial is very good, and doesn't take too much time.

To install a production environment django is deployed in an apache
web server using the mod_python module.
Below are some instructions / notes I took during configuration on my
Fedora Linux machine. I used Fedora 8 with mysql database.
It doesn't serve as a complete reference but only as a brief guideline.
- Make sure mysql runs a transactional storage engine as default.
      vi /etc/my.cnf
      >> [mysqld]
      >> ...
      >> default_storage_engine=InnoDB
      >> ...
  Restart mysql after this step.
  (This setting is also included now in the settings.py file)
- Create the mysql user and database
      mysql -u root -p
      >> drop user frepple;
      >> drop database frepple;
      >> create database frepple;
      >> create user frepple identified by 'frepple';
      >> grant all privileges on frepple.* to 'frepple'@'%' identified by 'frepple';
  In case you'll have non-ascii characters in the data (and who doesnt't?) it
  is recommended to use utf-8 for encoding the database character data.
- Update apache by adding a file /etc/httpd/conf.d/z_frepple.conf with the settings
  shown in the provided httpd.conf file. You will need to carefully review and update
  the settings!
- Update the apache configuration file /etc/httpd/conf/httpd.conf:
     - Run the web server as the same user used for the django development project
     - Switch keepalive on
     - Comment out some redundant modules
     - Choose the appropriate logging level and format
     - etc...
Your mileage with the above may vary...

Documentation of the code can be generated with the epydoc package:
- Install epydoc (version >3.0 recommended)
- Run the 'doc' make target:
    make doc
- Point your browser to the file doc/index.html

Enjoy!


<<< START DJANGO PATCH <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
Index: django/contrib/admin/media/js/admin/DateTimeShortcuts.js
===================================================================
--- django/contrib/admin/media/js/admin/DateTimeShortcuts.js	(revision 6980)
+++ django/contrib/admin/media/js/admin/DateTimeShortcuts.js	(working copy)
@@ -92,7 +92,7 @@
     openClock: function(num) {
         var clock_box = document.getElementById(DateTimeShortcuts.clockDivName+num)
         var clock_link = document.getElementById(DateTimeShortcuts.clockLinkName+num)
-
+
         // Recalculate the clockbox position
         // is it left-to-right or right-to-left layout ?
         if (getStyle(document.body,'direction')!='rtl') {
@@ -106,7 +106,7 @@
             clock_box.style.left = findPosX(clock_link) - 110 + 'px';
         }
         clock_box.style.top = findPosY(clock_link) - 30 + 'px';
-
+
         // Show the clock box
         clock_box.style.display = 'block';
         addEvent(window, 'click', function() { DateTimeShortcuts.dismissClock(num); return true; });
@@ -128,16 +128,19 @@
         // Shortcut links (calendar icon and "Today" link)
         var shortcuts_span = document.createElement('span');
         inp.parentNode.insertBefore(shortcuts_span, inp.nextSibling);
-        var today_link = document.createElement('a');
-        today_link.setAttribute('href', 'javascript:DateTimeShortcuts.handleCalendarQuickLink(' + num + ', 0);');
-        today_link.appendChild(document.createTextNode(gettext('Today')));
+        //
+        // I don't like this today link...
+        //
+        //var today_link = document.createElement('a');
+        //today_link.setAttribute('href', 'javascript:DateTimeShortcuts.handleCalendarQuickLink(' + num + ', 0);');
+        //today_link.appendChild(document.createTextNode(gettext('Today')));
         var cal_link = document.createElement('a');
         cal_link.setAttribute('href', 'javascript:DateTimeShortcuts.openCalendar(' + num + ');');
         cal_link.id = DateTimeShortcuts.calendarLinkName + num;
         quickElement('img', cal_link, '', 'src', DateTimeShortcuts.admin_media_prefix + 'img/admin/icon_calendar.gif', 'alt', gettext('Calendar'));
         shortcuts_span.appendChild(document.createTextNode('\240'));
-        shortcuts_span.appendChild(today_link);
-        shortcuts_span.appendChild(document.createTextNode('\240|\240'));
+        //shortcuts_span.appendChild(today_link);
+        //shortcuts_span.appendChild(document.createTextNode('\240|\240'));
         shortcuts_span.appendChild(cal_link);

         // Create calendarbox div.
@@ -208,7 +211,7 @@
 	    }
 	}

-
+
         // Recalculate the clockbox position
         // is it left-to-right or right-to-left layout ?
         if (getStyle(document.body,'direction')!='rtl') {
@@ -222,7 +225,7 @@
             cal_box.style.left = findPosX(cal_link) - 180 + 'px';
         }
         cal_box.style.top = findPosY(cal_link) - 75 + 'px';
-
+
         cal_box.style.display = 'block';
         addEvent(window, 'click', function() { DateTimeShortcuts.dismissCalendar(num); return true; });
     },
Index: django/contrib/admin/templates/widget/foreign.html
===================================================================
--- django/contrib/admin/templates/widget/foreign.html	(revision 6980)
+++ django/contrib/admin/templates/widget/foreign.html	(working copy)
@@ -2,9 +2,9 @@
 {% output_all bound_field.form_fields %}
 {% if bound_field.raw_id_admin %}
     {% if bound_field.field.rel.limit_choices_to %}
-        <a href="{{ bound_field.related_url }}?{% for limit_choice in bound_field.field.rel.limit_choices_to.items %}{% if not forloop.first %}&amp;{% endif %}{{ limit_choice|join:"=" }}{% endfor %}" class="related-lookup" id="lookup_{{ bound_field.element_id }}" onclick="return showRelatedObjectLookupPopup(this);"> <img src="{% admin_media_prefix %}img/admin/selector-search.gif" width="16" height="16" alt="Lookup"></a>
+        <a href="{{ bound_field.related_url }}?{% for limit_choice in bound_field.field.rel.limit_choices_to.items %}{% if not forloop.first %}&amp;{% endif %}{{ limit_choice|join:"=" }}{% endfor %}" class="related-lookup" id="lookup_{{ bound_field.element_id }}" onclick="return showRelatedObjectLookupPopup(this);"> <img src="{% admin_media_prefix %}img/admin/selector-search.gif" width="16" height="16" alt="Lookup"/></a>
     {% else %}
-        <a href="{{ bound_field.related_url }}" class="related-lookup" id="lookup_{{ bound_field.element_id }}" onclick="return showRelatedObjectLookupPopup(this);"> <img src="{% admin_media_prefix %}img/admin/selector-search.gif" width="16" height="16" alt="Lookup"></a>
+        <a href="{{ bound_field.related_url }}" class="related-lookup" id="lookup_{{ bound_field.element_id }}" onclick="return showRelatedObjectLookupPopup(this);"> <img src="{% admin_media_prefix %}img/admin/selector-search.gif" width="16" height="16" alt="Lookup"/></a>
     {% endif %}
 {% else %}
 {% if bound_field.needs_add_label %}
Index: django/contrib/admin/views/decorators.py
===================================================================
--- django/contrib/admin/views/decorators.py	(revision 6980)
+++ django/contrib/admin/views/decorators.py	(working copy)
@@ -23,7 +23,7 @@
         post_data = _encode_post_data({})
     return render_to_response('admin/login.html', {
         'title': _('Log in'),
-        'app_path': request.path,
+        'app_path': request.get_full_path(),
         'post_data': post_data,
         'error_message': error_message
     }, context_instance=template.RequestContext(request))
@@ -100,7 +100,7 @@
                         return view_func(request, *args, **kwargs)
                     else:
                         request.session.delete_test_cookie()
-                        return http.HttpResponseRedirect(request.path)
+                        return http.HttpResponseRedirect(request.get_full_path())
             else:
                 return _display_login_form(request, ERROR_MESSAGE)

Index: django/core/management/__init__.py
===================================================================
--- django/core/management/__init__.py	(revision 6980)
+++ django/core/management/__init__.py	(working copy)
@@ -13,36 +13,63 @@
 # doesn't have to reload every time it's called.
 _commands = None

-def find_commands(management_dir):
-    """
-    Given a path to a management directory, returns a list of all the command
-    names that are available.
+try:
+    from pkgutil import iter_modules

-    Returns an empty list if no commands are defined.
-    """
-    command_dir = os.path.join(management_dir, 'commands')
-    try:
-        return [f[:-3] for f in os.listdir(command_dir)
-                if not f.startswith('_') and f.endswith('.py')]
-    except OSError:
-        return []
+except:

-def find_management_module(app_name):
-    """
-    Determines the path to the management module for the given app_name,
-    without actually importing the application or the management module.
+    # Python versions earlier than 2.5 don't have the iter_modules function

-    Raises ImportError if the management module cannot be found for any reason.
-    """
-    parts = app_name.split('.')
-    parts.append('management')
-    parts.reverse()
-    path = None
-    while parts:
-        part = parts.pop()
-        f, path, descr = find_module(part, path and [path] or None)
-    return path
+    def find_commands(app_name):
+        """
+        Given an application name, returns a list of all the commands found.

+        Raises ImportError if no commands are defined.
+        """
+        management_dir = find_management_module(app_name)
+        command_dir = os.path.join(management_dir, 'commands')
+        try:
+            return [f[:-3] for f in os.listdir(command_dir)
+                    if not f.startswith('_') and f.endswith('.py')]
+        except OSError:
+            return []
+
+    def find_management_module(app_name):
+        """
+        Determines the path to the management module for the given app_name,
+        without actually importing the application or the management module.
+
+        Raises ImportError if the management module cannot be found for any reason.
+        """
+        parts = app_name.split('.')
+        parts.append('management')
+        parts.reverse()
+        path = None
+        while parts:
+            part = parts.pop()
+            f, path, descr = find_module(part, path and [path] or None)
+        return path
+
+else:
+
+    # Python 2.5
+    # The iter_modules function has the advantage to be more cleaner and more
+    # generic: also finds packages in zip files, recognizes other file
+    # extensions than .py
+
+    def find_commands(app_name):
+        """
+        Given an application name, returns a list of all the commands found.
+
+        Raises ImportError if no commands are defined.
+        """
+        packages = {}
+        mgmt_package = "%s.management.commands" % app_name
+        # The next line imports the *package*, not all modules in the package
+        __import__(mgmt_package)
+        path = getattr(sys.modules[mgmt_package], '__path__', None)
+        return [i[1] for i in iter_modules(path)]
+
 def load_command_class(app_name, name):
     """
     Given a command name and an application name, returns the Command
@@ -78,15 +105,14 @@
     """
     global _commands
     if _commands is None:
-        _commands = dict([(name, 'django.core') for name in find_commands(__path__[0])])
+        _commands = dict([(name, 'django.core') for name in find_commands('django.core')])

         if load_user_commands:
             # Get commands from all installed apps.
             from django.conf import settings
             for app_name in settings.INSTALLED_APPS:
                 try:
-                    path = find_management_module(app_name)
-                    _commands.update(dict([(name, app_name) for name in find_commands(path)]))
+                    _commands.update(dict([(name, app_name) for name in find_commands(app_name)]))
                 except ImportError:
                     pass # No management module -- ignore this app.

Index: django/db/backends/sqlite3/base.py
===================================================================
--- django/db/backends/sqlite3/base.py	(revision 6980)
+++ django/db/backends/sqlite3/base.py	(working copy)
@@ -67,7 +67,11 @@
         # NB: The generated SQL below is specific to SQLite
         # Note: The DELETE FROM... SQL generated below works for SQLite databases
         # because constraints don't exist
-        sql = ['%s %s %s;' % \
+        sql = ['%s %s = %s' % \
+                (style.SQL_KEYWORD('PRAGMA'),
+                 style.SQL_KEYWORD('SYNCHRONOUS'),
+                 style.SQL_KEYWORD('OFF'))] + \
+               ['%s %s %s;' % \
                 (style.SQL_KEYWORD('DELETE'),
                  style.SQL_KEYWORD('FROM'),
                  style.SQL_FIELD(self.quote_name(table))
Index: django/views/i18n.py
===================================================================
--- django/views/i18n.py	(revision 6980)
+++ django/views/i18n.py	(working copy)
@@ -178,5 +178,8 @@
     src.extend(csrc)
     src.append(LibFoot)
     src.append(InterPolate)
-    src = ''.join(src)
-    return http.HttpResponse(src, 'text/javascript')
+
+    # Create response, and set the HTTP header to allow caching for 1 day by the client browser
+    response = http.HttpResponse(''.join(src), 'text/javascript')
+    response['Cache-Control'] = 'max-age=86400'
+    return response
Index: django/db/models/sql/query.py
===================================================================
--- query.py	(revision 7512)
+++ query.py	(working copy)
@@ -405,8 +405,11 @@
             for col in self.select:
                 if isinstance(col, (list, tuple)):
                     r = '%s.%s' % (qn(col[0]), qn(col[1]))
-                    if with_aliases and col[1] in col_aliases:
-                        c_alias = 'Col%d' % len(col_aliases)
+                    if with_aliases:
+                        if col[1] in col_aliases:
+                            c_alias = 'Col%d' % len(col_aliases)
+                        else:
+                            c_alias = col[1]
                         result.append('%s AS %s' % (r, c_alias))
                         aliases.add(c_alias)
                         col_aliases.add(c_alias)
@@ -426,8 +429,11 @@
             aliases.update(new_aliases)
         for table, col in self.related_select_cols:
             r = '%s.%s' % (qn(table), qn(col))
-            if with_aliases and col in col_aliases:
-                c_alias = 'Col%d' % len(col_aliases)
+            if with_aliases:
+                if col in col_aliases:
+                    c_alias = 'Col%d' % len(col_aliases)
+                else:
+                    c_alias = col
                 result.append('%s AS %s' % (r, c_alias))
                 aliases.add(c_alias)
                 col_aliases.add(c_alias)
@@ -461,8 +467,11 @@
                 alias = self.join((table_alias, model._meta.db_table,
                         root_pk, model._meta.pk.column))
                 seen[model] = alias
-            if with_aliases and field.column in col_aliases:
-                c_alias = 'Col%d' % len(col_aliases)
+            if with_aliases:
+                if field.column in col_aliases:
+                    c_alias = 'Col%d' % len(col_aliases)
+                else:
+                    c_alias = field.column
                 result.append('%s.%s AS %s' % (qn(alias),
                     qn2(field.column), c_alias))
                 col_aliases.add(c_alias)

<<< END DJANGO PATCH <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
