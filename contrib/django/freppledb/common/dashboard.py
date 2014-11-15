#
# Copyright (C) 2013 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseNotAllowed, HttpResponseForbidden, Http404
from django.utils.importlib import import_module


class Dashboard:
  '''
  Widgets are UI components that can be added to the dashboard.
  Subclasses need to follow these conventions:
    - They can only be defined in a file "widget.py" in an application module.
    - In the file widget.py each widget needs to register itself by calling
      the method Widget.register().
    - We don't expect widgets to be instantiated.
    - Class attribute "name" needs to provide a short, unique identifier
      for the widget. This string is also used for the URL to access the
      widget, so keep it short and avoid special characters.
    - Class attribute 'title' needs to a translatable title string for
      the title bar of the widget.
    - Class attribute 'async' is a boolean specifying whether the widget
      is immediately rendered in the page, or asynchronously with an
      Ajax request.
    - Class method render(request) is called to render the widget to the
      client browser.
      It should return HTML content for synchronous widgets.
      It should return a Django response object for asynchronous widgets.
  '''

  __registry__ = {}


  @classmethod
  def register(cls, w):
    cls.__registry__[w.name] = w


  @classmethod
  def buildList(cls):
    if not cls.__registry__:
      # Adding the widget modules of each installed application.
      # Note that the application list is processed in reverse order.
      # This is required to allow the first apps to override the entries
      # of the later ones.
      for app in reversed(settings.INSTALLED_APPS):
        try:
          import_module('%s.widget' % app)
        except ImportError as e:
          # Silently ignore if it's the widget module which isn't found
          if str(e) not in ("No module named %s.widget" % app, "No module named '%s.widget'" % app):
            raise e
    return cls.__registry__


  @classmethod
  def dispatch(cls, request, name):
    if request.method != 'GET':
      return HttpResponseNotAllowed(['get'])
    w = cls.__registry__.get(name, None)
    if not w:
      raise Http404("Unknown widget")
    if not w.async:
      raise Http404("This widget is synchronous")
    if not w.has_permission(request.user):
      return HttpResponseForbidden()
    return w.render(request)


  @classmethod
  def createWidgetPermissions(cls, app):
    # Registered all permissions defined by dashboard widgets
    content_type = None
    for widget in cls.buildList().values():
      if widget.__module__.startswith(app):
        # Loop over all permissions of the widget class
        for k in widget.permissions:
          if content_type is None:
            # Create a dummy contenttype in the app
            content_type = ContentType.objects.get_or_create(name="reports", model="", app_label=app.split('.')[-1])[0]
          # Create the permission object
          # TODO: cover the case where the permission refers to a permission of a model in the same app.
          # TODO: cover the case where app X wants to refer to a permission defined in app Y.
          p = Permission.objects.get_or_create(codename=k[0], content_type=content_type)[0]
          p.name = k[1]
          p.save()


class Widget:
  '''
  Widgets are UI components that can be added to the dashboard.
  Subclasses need to follow these conventions:
    - They can only be defined in a file "widget.py" in an application module.
    - In the file widget.py each widget needs to register itself by calling
      the method Widget.register().
    - We don't expect widgets to be instantiated.
    - Class attribute 'name' defines a unique identifier for the widget.
      This string is also used for the URL to access the widget, so keep it
      short and avoid special characters.
    - Class attribute 'title' defines a translatable title string for the widget.
    - Class attribute 'async' needs to be set to true for asynchronous widgets.
      Such widgets are rendered in 2 steps: initially the dashboard displays a
      loading icon, and next an ajax request is launched to populate the widget
      content.
    - Class method render(request) is called to render the widget to the
      client browser.
      It returns a string for synchronous widgets.
      It returns a HTTPResponse object for asynchronous widgets.
    - Class attribute 'url' optionally defines a url to a report with a more
      complete content than can be displayed in the dashboard widget.
  '''
  name = "Undefined"
  title = "Undefined"
  permissions = ()
  async = False       # Asynchroneous widget
  url = None          # URL opened when the header is clicked
  exporturl = False   # Enable or disable a download icon
  args = ''           # Arguments passed in the url for asynchronous widgets
  javascript = ''     # Javascript called for rendering the widget

  def __init__(self, **options):
    # Store all options as attributes on the instance
    for k, v in options.items():
      setattr(self, k, v)


  def render(self, request=None):
    return "Not implemented"

  @classmethod
  def has_permission(cls, user):
    for perm in cls.permissions:
      if not user.has_perm("%s.%s" % (cls.getAppLabel(), perm[0])):
        return False
    return True

  @classmethod
  def getAppLabel(cls):
    '''
    Return the name of the Django application which defines this widget.
    '''
    if hasattr(cls, 'app_label'):
      return cls.app_label
    s = cls.__module__.split('.')
    for i in range(len(s), 0, -1):
      x = '.'.join(s[0:i])
      if x in settings.INSTALLED_APPS:
        cls.app_label = s[i - 1]
        return cls.app_label
    raise Exception("Can't identify app of widget %s" % cls)
