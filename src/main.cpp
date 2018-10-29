/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bvba                                 *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            *
 * GNU Affero General Public License for more details.                     *
 *                                                                         *
 * You should have received a copy of the GNU Affero General Public        *
 * License along with this program.                                        *
 * If not, see <http://www.gnu.org/licenses/>.                             *
 *                                                                         *
 ***************************************************************************/

#include "freppleinterface.h"
#include <iostream>
#include <sstream>
#include <cstring>
#include <cstdlib>
#include <signal.h>
using namespace std;


void usage()
{
  cout << "\nfrePPLe v" << FreppleVersion() << " command line application\n"
      "\nUsage:\n"
      "  frepple [options] [files | directories]\n"
      "\nThis program reads XML input data, and executes the modeling and\n"
      "planning commands included in them.\n"
      "The XML input can be provided in the following ways:\n"
      "  - Passing one or more XML files and/or directories as arguments.\n"
      "    When a directory is specified, the application will process\n"
      "    all files with the extension '.xml'.\n"
      "  - Passing one or more Python files with the extension '.py'\n"
      "    The Python commands are executed in the embedded interpreter.\n"
      "  - When passing no file or directory arguments, input will be read\n"
      "    from the standard input. XML data can be piped to the application.\n"
      "\nOptions:\n"
      "  -validate -v  Validate the XML input for correctness.\n"
      "  -check -c     Only validate the input, without executing the content.\n"
      "  -? -h -help   Show these instructions.\n"
      "\nEnvironment: The variable FREPPLE_HOME optionally points to a\n"
      "     directory where the initialization files init.xml, init.py,\n"
      "     frepple.xsd and module libraries will be searched.\n"
      "\nReturn codes: 0 when successful, non-zero in case of errors\n"
      "\nMore information on this program: http://www.frepple.com\n\n"
      << endl;
}


void handler(int sig)
{
  ostringstream o;
  o << "Planning engine terminating due to ";
  switch (sig)
  {
#ifdef SIGHUP
  case SIGHUP:
    o << "hangup signal";
    break;
#endif
#ifdef SIGINT
  case SIGINT:
    o << "interrupt signal";
    break;
#endif
#ifdef SIGQUIT
  case SIGQUIT:
    o << "quit signal";
    break;
#endif
#ifdef SIGILL
  case SIGILL:
    o << "illegal instruction";
    break;
#endif
#ifdef SIGABRT
  case SIGABRT:
    o << "abort signal";
    break;
#endif
#ifdef SIGBUS
  case SIGBUS:
    o << "bad memory access";
    break;
#endif
#ifdef SIGFPE
  case SIGFPE:
    o << "floating-point exception";
    break;
#endif
#ifdef SIGKILL
  case SIGKILL:
    o << "kill signal";
    break;
#endif
#ifdef SIGSEGV
  case SIGSEGV:
    o << "segmentation violation";
    break;
#endif
#ifdef SIGTERM
  case SIGTERM:
    o << "termination signal";
    break;
#endif
#ifdef SIGSTKFLT
  case SIGSTKFLT:
    o << "stack fault on coprocressor";
    break;
#endif
#ifdef SIGXCPU
  case SIGXCPU:
    o << "CPU limit reached";
    break;
#endif
#ifdef SIGXFSZ
  case SIGXFSZ:
    o << "file size limit reached";
    break;
#endif
  default:
    o << "signal " << sig;
  }
  o << endl;
  FreppleLog(o.str().c_str());
  exit(sig);
}


int main (int argc, char *argv[])
{
  // Install signal handlers.
  // In a debug build we don't do it, to allow debuggers to handle the
  // signal themselves.
#if !defined(DEBUG)
#ifdef SIGHUP
  signal(SIGHUP, handler);
#endif
#ifdef SIGINT
  signal(SIGINT, handler);
#endif
#ifdef SIGQUIT
  signal(SIGQUIT, handler);
#endif
#ifdef SIGILL
  signal(SIGILL, handler);
#endif
#ifdef SIGABRT
  signal(SIGABRT, handler);
#endif
#ifdef SIGBUS
  signal(SIGBUS, handler);
#endif
#ifdef SIGFPE
  signal(SIGFPE, handler);
#endif
#ifdef SIGKILL
  signal(SIGKILL, handler);
#endif
#ifdef SIGSEGV
  signal(SIGSEGV, handler);
#endif
#ifdef SIGTERM
  signal(SIGTERM, handler);
#endif
#ifdef SIGSTKFLT
  signal(SIGSTKFLT, handler);
#endif
#ifdef SIGXCPU
  signal(SIGXCPU, handler);
#endif
#ifdef SIGXFSZ
  signal(SIGXFSZ, handler);
#endif
#endif

  // Storing the chosen options...
  bool validate = false;
  bool validate_only = false;
  bool input = false;

  try
  {
    // Analyze the command line arguments.
    for (int i = 1; i < argc; ++i)
    {
      if (argv[i][0] == '-')
      {
        // An option on the command line
        if (!strcmp(argv[i],"-validate") || !strcmp(argv[i],"-v"))
          validate = true;
        else if (!strcmp(argv[i],"-check") || !strcmp(argv[i],"-c"))
          validate_only = true;
        else
        {
          if (strcmp(argv[i],"-?")
              && strcmp(argv[i],"-h")
              && strcmp(argv[i],"-help"))
            cout << "\nError: Option '" << argv[i]
                << "' not recognized." << endl;
          usage();
          return EXIT_FAILURE;
        }
      }
      else
      {
        // A file or directory name on the command line
        if (!input)
        {
          // Initialize the library if this wasn't done before
          FreppleInitialize();
          input = true;
        }
        if (strlen(argv[i])>=3 && !strcmp(argv[i]+strlen(argv[i])-3,".py"))
          // Execute as Python file
          FreppleReadPythonFile(argv[i]);
        else
          // Execute as XML file
          FreppleReadXMLFile(argv[i], validate, validate_only);
      }
    }

    // When no filenames are specified, we read the standard input
    if (!input)
    {
      FreppleInitialize();
      FreppleReadXMLFile(nullptr, validate, validate_only);
    }
  }
  catch (const exception& e)
  {
    ostringstream ch;
    ch << "Error: " << e.what();
    FreppleLog(ch.str());
    return EXIT_FAILURE;
  }
  catch (...)
  {
    FreppleLog("Error: Unknown exception type");
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}

