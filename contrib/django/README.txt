
This directory contains a sample web application for Frepple.
It is built using the incredible 'Django' web application framework.

The basic steps to set up a development environment:
- Install python 2.5
  Lower versions may work, but are not tested...
- Install django
  FREPPLE NEEDS THE DEVELOPMENT VERSION OF DJANGO. AT THE TIME FREPPLE 0.3.2 IS
  RELEASED DJANGO WAS AT REVISION 6603.
  To get this version of django use the following command:
    svn co --revision 6603 http://code.djangoproject.com/svn/django/trunk/ django_src
  Later versions of django may or may not work with frePPLe...
- Install your database: postgresql / mysql / ado_mssql
  Alternatively, you can use the sqlite3 database included with python.
- Install the python database access library for the database (see the django
  documentation for details)
- Create a database schema for frepple
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
  to load a dataset, to generate a random test model and run frepple.

For more detailed information please look at the django documentation
on http://www.djangoproject.com
The tutorial is very good, and doesn't take too much time.

To install a production environment django is deployed in an apache
web server using the mod_python module.
Below are some instructions / notes I took during configuration on my
Fedora Linux machine. I used fedora 7 with mysql database.
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
- Some patches are required to django.
  These are included at the bottom of this file. Copy these into a patch file to apply,
  or make the updates manually yourself.
- Optionally, you can update the django contrib/admin/media/css/base.css stylesheet
  by commenting out the import of a null css sheet.
  It results is request to the web server for a non-existent sheet, giving 404 error.
- Update apache by adding a file /etc/httpd/conf.d/z_frepple.conf with the settings
  shown in the provided httpd.conf file. You will need to carefully review and update
  the settings!
- Update the apache configuration file /etc/httpd/conf/httpd.conf:
     - Run the web server as the same user used for the django development project
     - Switch keepalive on
     - Comment out some redundant modules
     - Choose the appropriate logging level and format
- Link the static django content into your web root directory.
     cd /var/www/html
     ln -s /usr/lib/python2.5/site-packages/django/contrib/admin/media .
Your mileage with the above may vary...

Enjoy!


<<< START DJANGO PATCH <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
Index: contrib/admin/models.py
===================================================================
--- contrib/admin/models.py	(revision 6603)
+++ contrib/admin/models.py	(working copy)
@@ -49,4 +49,5 @@
         Returns the admin URL to edit the object represented by this log entry.
         This is relative to the Django admin index page.
         """
-        return u"%s/%s/%s/" % (self.content_type.app_label, self.content_type.model, self.object_id)
+        from django.contrib.admin.views.main import quote
+        return u"%s/%s/%s/" % (self.content_type.app_label, self.content_type.model, quote(self.object_id))
Index: contrib/admin/templates/widget/foreign.html
===================================================================
--- contrib/admin/templates/widget/foreign.html	(revision 6603)
+++ contrib/admin/templates/widget/foreign.html	(working copy)
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
Index: contrib/admin/views/decorators.py
===================================================================
--- contrib/admin/views/decorators.py	(revision 6603)
+++ contrib/admin/views/decorators.py	(working copy)
@@ -22,7 +22,7 @@
         post_data = _encode_post_data({})
     return render_to_response('admin/login.html', {
         'title': _('Log in'),
-        'app_path': request.path,
+        'app_path': request.get_full_path(),
         'post_data': post_data,
         'error_message': error_message
     }, context_instance=template.RequestContext(request))
@@ -99,7 +99,7 @@
                         return view_func(request, *args, **kwargs)
                     else:
                         request.session.delete_test_cookie()
-                        return http.HttpResponseRedirect(request.path)
+                        return http.HttpResponseRedirect(request.get_full_path())
             else:
                 return _display_login_form(request, ERROR_MESSAGE)

Index: contrib/admin/views/main.py
===================================================================
--- contrib/admin/views/main.py	(revision 6603)
+++ contrib/admin/views/main.py	(working copy)
@@ -56,12 +56,11 @@
     quoting is slightly different so that it doesn't get automatically
     unquoted by the Web browser.
     """
-    if type(s) != type(''):
-        return s
+    if not isinstance(s,basestring): return s
     res = list(s)
     for i in range(len(res)):
         c = res[i]
-        if c in ':/_':
+        if c in ':/_#?;@&=+$,"<>%':
             res[i] = '_%02X' % ord(c)
     return ''.join(res)

@@ -441,7 +440,7 @@
                     # Display a link to the admin page.
                     nh(deleted_objects, current_depth, [u'%s: <a href="../../../../%s/%s/%s/">%s</a>' % \
                         (force_unicode(capfirst(related.opts.verbose_name)), related.opts.app_label, related.opts.object_name.lower(),
-                        sub_obj._get_pk_val(), sub_obj), []])
+                        quote(sub_obj._get_pk_val()), escape(sub_obj)), []])
                 _get_deleted_objects(deleted_objects, perms_needed, user, sub_obj, related.opts, current_depth+2)
         else:
             has_related_objs = False
@@ -454,7 +453,7 @@
                 else:
                     # Display a link to the admin page.
                     nh(deleted_objects, current_depth, [u'%s: <a href="../../../../%s/%s/%s/">%s</a>' % \
-                        (force_unicode(capfirst(related.opts.verbose_name)), related.opts.app_label, related.opts.object_name.lower(), sub_obj._get_pk_val(), escape(sub_obj)), []])
+                        (force_unicode(capfirst(related.opts.verbose_name)), related.opts.app_label, related.opts.object_name.lower(), quote(sub_obj._get_pk_val()), escape(sub_obj)), []])
                 _get_deleted_objects(deleted_objects, perms_needed, user, sub_obj, related.opts, current_depth+2)
             # If there were related objects, and the user doesn't have
             # permission to delete them, add the missing perm to perms_needed.
@@ -487,7 +486,7 @@
                     nh(deleted_objects, current_depth, [
                         (_('One or more %(fieldname)s in %(name)s:') % {'fieldname': force_unicode(related.field.verbose_name), 'name': force_unicode(related.opts.verbose_name)}) + \
                         (u' <a href="../../../../%s/%s/%s/">%s</a>' % \
-                            (related.opts.app_label, related.opts.module_name, sub_obj._get_pk_val(), escape(sub_obj))), []])
+                            (related.opts.app_label, related.opts.module_name, quote(sub_obj._get_pk_val()), escape(sub_obj))), []])
         # If there were related objects, and the user doesn't have
         # permission to change them, add the missing perm to perms_needed.
         if related.opts.admin and has_related_objs:
@@ -507,7 +506,7 @@

     # Populate deleted_objects, a data structure of all related objects that
     # will also be deleted.
-    deleted_objects = [u'%s: <a href="../../%s/">%s</a>' % (force_unicode(capfirst(opts.verbose_name)), force_unicode(object_id), escape(obj)), []]
+    deleted_objects = [u'%s: <a href="../../%s/">%s</a>' % (force_unicode(capfirst(opts.verbose_name)), quote(force_unicode(object_id)), escape(obj)), []]
     perms_needed = set()
     _get_deleted_objects(deleted_objects, perms_needed, request.user, obj, opts, 1)

Index: db/backends/sqlite3/base.py
===================================================================
--- db/backends/sqlite3/base.py	(revision 6603)
+++ db/backends/sqlite3/base.py	(working copy)
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
<<< END DJANGO PATCH <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<