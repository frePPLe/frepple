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
from django.utils.encoding import force_unicode
from django.utils.importlib import import_module
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseNotAllowed, Http404
from django.utils.text import capfirst


class WidgetRegistry:
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
          mod = import_module('%s.widget' % app)
        except ImportError as e:
          # Silently ignore if it's the widget module which isn't found
          if str(e) != 'No module named widget': raise e
    return cls.__registry__


  @classmethod
  def dispatch(cls, request, name):
    if request.method != 'GET':
      return HttpResponseNotAllowed(['get'])
    w = cls.__registry__.get(name, None)
    if not w: raise Http404("Unknown widget")
    return w.render(request)
