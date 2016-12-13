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
  cout << "Planning engine terminated with signal " << sig << endl;
  exit(1);
}


int main (int argc, char *argv[])
{
  // Install signal handlers
  signal(SIGABRT, handler);
  signal(SIGFPE, handler);
  signal(SIGILL, handler);
  signal(SIGINT, handler);
  signal(SIGSEGV, handler);
  signal(SIGTERM, handler);

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
