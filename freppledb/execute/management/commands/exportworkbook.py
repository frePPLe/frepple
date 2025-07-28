#
# Copyright (C) 2011-2013 by frePPLe bv
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

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string

from freppledb import __version__


class Command(BaseCommand):
    help = """
       This command exports data in a spreadsheet. It is only available only
       from the user interface.

       TODO implement a command line version of this command. Also unify that
       command with the view function that is serving the spreadsheet from the
       user interface.
       """

    def get_version(self):
        return __version__

    requires_system_checks = []
    title = _("Export a spreadsheet")
    index = 1900
    help_url = "command-reference.html#exportworkbook"

    @staticmethod
    def getHTML(request):
        return render_to_string("commands/exportworkbook.html", request=request)

    # def add_arguments(self, parser):
    #   parser.add_argument(
    #     '--user', help='User running the command'
    #     )
    #   parser.add_argument(
    #     '--database', default=DEFAULT_DB_ALIAS,
    #     help='Nominates a specific database to load data from and export results into'
    #     )
    #   parser.add_argument(
    #     '--task', type=int,
    #     help='Task identifier (generated automatically if not provided)'
    #     )
    #   parser.add_argument(
    #     'file', nargs='+',
    #     help='spreadsheet file name'
    #     )

    # def handle(self, **options):
    #   # Pick up the options
    #   database = options['database']
    #   if database not in get_databases():
    #     raise CommandError("No database settings known for '%s'" % database )
    #   if options['user']:
    #     try:
    #       user = User.objects.all().using(database).get(username=options['user'])
    #     except Exception:
    #       raise CommandError("User '%s' not found" % options['user'] )
    #   else:
    #     user = None
    #
    #   now = datetime.now()
    #   task = None
    #   try:
    #     # Initialize the task
    #     if options['task']:
    #       try:
    #         task = Task.objects.all().using(database).get(pk=options['task'])
    #       except Exception:
    #         raise CommandError("Task identifier not found")
    #       if task.started or task.finished or task.status != "Waiting" or task.name != 'export spreadsheet':
    #         raise CommandError("Invalid task identifier")
    #       task.status = '0%'
    #       task.started = now
    #     else:
    #       task = Task(name='export spreadsheet', submitted=now, started=now, status='0%', user=user)
    #     task.arguments = ' '.join(options['file'])
    #     task.save(using=database)
    #
    #     # Execute
    #     # TODO: if frePPLe is available as a module, we don't really need to spawn another process.
    #     os.environ['FREPPLE_HOME'] = settings.FREPPLE_HOME.replace('\\', '\\\\')
    #     os.environ['FREPPLE_APP'] = settings.FREPPLE_APP
    #     os.environ['FREPPLE_DATABASE'] = database
    #     os.environ['PATH'] = settings.FREPPLE_HOME + os.pathsep + os.environ['PATH'] + os.pathsep + settings.FREPPLE_APP
    #     os.environ['LD_LIBRARY_PATH'] = settings.FREPPLE_HOME
    #     if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    #       os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
    #     if os.path.exists(os.path.join(os.environ['FREPPLE_HOME'], 'python36.zip')):
    #       # For the py2exe executable
    #       os.environ['PYTHONPATH'] = os.path.join(
    #         os.environ['FREPPLE_HOME'],
    #         'python%d%d.zip' % (sys.version_info[0], sys.version_info[1])
    #         ) + os.pathsep + os.path.normpath(os.environ['FREPPLE_APP'])
    #     else:
    #       # Other executables
    #       os.environ['PYTHONPATH'] = os.path.normpath(os.environ['FREPPLE_APP'])
    #     cmdline = [ '"%s"' % i for i in options['file'] ]
    #     cmdline.insert(0, 'frepple')
    #     cmdline.append( '"%s"' % os.path.join(settings.FREPPLE_APP, 'freppledb', 'execute', 'loadxml.py') )
    #     (out,ret) = subprocess.run(' '.join(cmdline))
    #     if ret:
    #       raise Exception('Exit code of the batch run is %d' % ret)
    #
    #     # Task update
    #     task.status = 'Done'
    #     task.finished = datetime.now()
    #
    #   except Exception as e:
    #     if task:
    #       task.status = 'Failed'
    #       task.message = '%s' % e
    #       task.finished = datetime.now()
    #     raise e
    #
    #   finally:
    #     if task:
    #       task.save(using=database)
