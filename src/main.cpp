/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/main.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Lesser General Public License as published   *
 * by the Free Software Foundation; either version 2.1 of the License, or  *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser *
 * General Public License for more details.                                *
 *                                                                         *
 * You should have received a copy of the GNU Lesser General Public        *
 * License along with this library; if not, write to the Free Software     *
 * Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA *
 *                                                                         *
 ***************************************************************************/


#include "freppleinterface.h"
#include <iostream>
using namespace std;


void usage()
{
#ifdef VERSION
  cout << "\nFrepple v" << VERSION << "command line application\n";
#endif
  cout << "\nUsage:\n"
    "  frepple [options] [files | directories]\n"
    "\nThis program reads xml input data, and executes the modeling and\n"
    "planning commands included in them.\n"
    "The xml input can be provided in the following ways:\n"
    "  - Passing one or more XML files and/or directories as arguments.\n"
    "    When a directory is specified, the application will process\n"
    "    all files with the extension '.xml'.\n"
    "  - When passing no file or directory arguments, input will be read\n"
    "    from the standard input. XML data can be piped to the application.\n"
    "\nOptions:\n"
    "  -validate -v  Validate the xml input for correctness.\n"
    "  -check -c     Only validate the input, without executing the content.\n"
    "  -? -h -help   Show these instructions.\n"
#ifdef STATIC
    "  -home {Dir}   Points to the directory where the frepple will pick up\n"
    "                the schema file frepple.xsd and the initialization\n"
    "                file init.xml.\n"
    "                If the option is omitted frepple will locate these\n"
    "                files from the directory pointed to by the environment\n"
    "                variable FREPPLE_HOME.\n"
    "                If both are missing a warning message is generated.\n"
#else
    "\nEnvironment: The variable FREPPLE_HOME is required to point to a\n"
    "               directory. The application will use the files init.xml\n"
    "               and frepple.xsd from this directory.\n"
#endif
    "\nReturn codes: 0 when succesfull, non-zero in case of errors\n"
    "\nMore information on this program: http://frepple.sourceforge.net\n\n"
    << endl;
}


int main (int argc, char *argv[])
{

  // Storing the chosen options...
  bool validate = false;
  bool validate_only = false;
  bool initialized = false;
  bool input = false;
  string home;

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
        else if (!strcmp(argv[i],"-home"))
        {
          if (i < argc - 1) home = argv[++i];
          else
          {
            cout << "\nError: Option -home takes an extra parameter." << endl;
            return EXIT_FAILURE;
          }
        }
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
          FreppleInitialize(home.empty() ? NULL : home.c_str());
          input = true;
        }
        FreppleReadXMLFile(argv[i], validate, validate_only);
      }
    }

    // When no filenames are specified, we read the standard input
    if (!input) 
    {
      FreppleInitialize(home.empty() ? NULL : home.c_str());
      FreppleReadXMLFile(NULL, validate, validate_only);
    }
  }
  catch (exception& e)
  {
    cout << "Error: " << e.what() << endl;
    return EXIT_FAILURE;
  }
  catch (...)
  {
    cout << "Error: Unknown exception type" << endl;
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
