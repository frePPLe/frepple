#
# Copyright (C) 2007-2013 by frePPLe bvba
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

from django.conf.urls import url

import freppledb.execute.views

# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = [
  url(r'^execute/$', freppledb.execute.views.TaskReport.as_view(), name="execute"),
  url(r'^execute/logfrepple/(.+)/$', freppledb.execute.views.logfile, name="execute_view_log"),
  url(r'^execute/launch/(.+)/$', freppledb.execute.views.LaunchTask, name="execute_launch"),
  url(r'^execute/cancel/(.+)/$', freppledb.execute.views.CancelTask, name="execute_cancel"),
  url(r'^execute/logdownload/(.+)/$', freppledb.execute.views.DownloadLogFile, name="execute_download_log"),
  url(r'^execute/api/(.+)/$', freppledb.execute.views.APITask, name="execute_api"),
  url(r'^execute/uploadtofolder/(.+)/$', freppledb.execute.views.FileManager.uploadFiletoFolder, name="copy_file_to_folder"),
  url(r'^execute/downloadfromfolder/(.+)/(.+)/$', freppledb.execute.views.FileManager.downloadFilefromFolder, name="download_file_from_folder"),
  url(r'^execute/deletefromfolder/(.+)/(.+)/$', freppledb.execute.views.FileManager.deleteFilefromFolder, name="delete_file_from_folder"),
  ]
