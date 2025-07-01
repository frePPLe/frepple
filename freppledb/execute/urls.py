#
# Copyright (C) 2007-2013 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from django.urls import re_path

from freppledb import mode

# Automatically add these URLs when the application is installed
autodiscover = True

if mode == "WSGI":
    from . import views

    urlpatterns = [
        re_path(r"^execute/$", views.TaskReport.as_view(), name="execute"),
        re_path(
            r"^execute/logfrepple/(.+)/$",
            views.logfile,
            name="execute_view_log",
        ),
        re_path(
            r"^execute/launch/(.+)/$",
            views.LaunchTask,
            name="execute_launch",
        ),
        re_path(
            r"^execute/cancel/(.+)/$",
            views.CancelTask,
            name="execute_cancel",
        ),
        re_path(
            r"^execute/logdownload/(.+)/$",
            views.DownloadLogFile,
            name="execute_download_log",
        ),
        re_path(
            r"^execute/logdelete/(.+)/$",
            views.DeleteLogFile,
            name="execute_delete_log",
        ),
        re_path(r"^execute/api/(.+)/$", views.APITask, name="execute_api"),
        re_path(
            r"^execute/uploadtofolder/(.+)/$",
            views.FileManager.uploadFiletoFolder,
            name="copy_file_to_folder",
        ),
        re_path(
            r"^execute/downloadfromfolder/(.+)/(.+)/$",
            views.FileManager.downloadFilefromFolder,
            name="download_file_from_folder",
        ),
        re_path(
            r"^execute/downloadfromfolder/(.+)/$",
            views.FileManager.downloadFilefromFolder,
            name="download_all_files_from_folder",
        ),
        re_path(
            r"^execute/deletefromfolder/(.+)/(.+)/$",
            views.FileManager.deleteFilefromFolder,
            name="delete_file_from_folder",
        ),
        re_path(
            r"^execute/exports/$",
            views.exports,
            name="exports",
        ),
        re_path(
            r"^execute/scheduletasks/$",
            views.scheduletasks,
            name="scheduletasks",
        ),
        re_path(
            r"^execute/scenario_add/$",
            views.scenario_add,
            name="scenario_add",
        ),
        re_path(
            r"^execute/scenario_delete/$",
            views.scenario_delete,
            name="scenario_delete",
        ),
    ]
