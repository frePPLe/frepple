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
import socket
import sys
from warnings import warn

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.handlers.wsgi import WSGIHandler
from django.contrib.staticfiles.handlers import StaticFilesHandler

from freppledb import __version__


class Command(BaseCommand):
    help = """
      Runs a multithreaded web server for frePPLe.

      This command is deprecated.
      Use the "runserver" command instead for a development web server.
      Use the apache web server for all production usage.
      """

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument(
            "--port", type=int, default=settings.PORT, help="Port number of the server."
        )
        parser.add_argument("--address", help="IP address for the server to listen."),
        parser.add_argument(
            "--threads",
            type=int,
            default=25,
            help="Number of server threads (default: 25).",
        )

    def handle(self, **options):
        from cheroot import wsgi

        warn(
            "Deprecated: Use the runserver command instead for a development web server"
        )

        # Determine the port number
        port = options["port"]

        # Determine the number of threads
        threads = options["threads"]
        if threads < 1:
            raise Exception("Invalid number of threads: %s" % threads)

        # Determine the IP-address to listen on:
        # - either as command line argument
        # - either 0.0.0.0 by default, which means all active IPv4 interfaces
        address = options["address"] or "0.0.0.0"

        # Validate the address and port number
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((address, port))
            s.close()
        except socket.error as e:
            raise Exception(
                "Invalid address '%s' and/or port '%s': %s" % (address, port, e)
            )

        # Print a header message
        hostname = socket.getfqdn()
        print("Starting frePPLe %s web server\n" % __version__)
        print(
            "To access the server, point your browser to either of the following URLS:"
        )
        if address == "0.0.0.0":
            print("    http://%s:%s/" % (hostname, port))
            for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
                print("    http://%s:%s/" % (ip, port))
        else:
            print("    http://%s:%s/" % (address, port))
        print("Quit the server with CTRL-C.\n")

        # Run the WSGI server
        server = wsgi.Server(
            (address, port), StaticFilesHandler(WSGIHandler()), numthreads=threads
        )
        # Want SSL support? Just set these attributes apparently, but I haven't tested or verified this
        #  server.ssl_certificate = <filename>
        #  server.ssl_private_key = <filename>
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()
