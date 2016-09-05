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

#define FREPPLE_CORE
#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;
#include <sys/stat.h>


DECLARE_EXPORT(const char*) FreppleVersion()
{
  return PACKAGE_VERSION;
}


DECLARE_EXPORT(void) FreppleInitialize(bool procesInitializationFiles)
{
  // Initialize only once
  static bool initialized = false;
  if (initialized) return;
  initialized = true;

  // Initialize the libraries
  LibraryUtils::initialize();
  LibraryModel::initialize();
  LibrarySolver::initialize();

  if (!procesInitializationFiles)
    return;

  // Search for the initialization PY file
  string init = Environment::searchFile("init.py");
  if (!init.empty())
  {
    // Execute the commands in the file
    try
    {
      PythonInterpreter::executeFile(init);
    }
    catch (...)
    {
      logger << "Exception caught during execution of 'init.py'" << endl;
      throw;
    }
  }

  // Search for the initialization XML file
  init = Environment::searchFile("init.xml");
  if (!init.empty())
  {
    // Execute the commands in the file
    try { XMLInputFile(init).parse(&Plan::instance(),true); }
    catch (...)
    {
      logger << "Exception caught during execution of 'init.xml'" << endl;
      throw;
    }
  }
}


DECLARE_EXPORT(void) FreppleReadXMLData (const char* x, bool validate, bool validateonly)
{
  if (!x) return;
  if (validateonly)
    XMLInputString(x).parse(nullptr, true);
  else
    XMLInputString(x).parse(&Plan::instance(), validate);
}


DECLARE_EXPORT(void) FreppleReadXMLFile (const char* filename, bool validate, bool validateonly)
{
  if (!filename)
  {
    // Read from standard input
    xercesc::StdInInputSource in;
    if (validateonly)
      // When no root object is passed, only the input validation happens
      XMLInput().parse(in, nullptr, true);
    else
      XMLInput().parse(in, &Plan::instance(), validate);
  }
  else if (validateonly)
    // Read and validate a file
    XMLInputFile(filename).parse(nullptr, true);
  else
    // Read, execute and optionally validate a file
    XMLInputFile(filename).parse(&Plan::instance(), validate);
}


DECLARE_EXPORT(void) FreppleReadPythonFile(const char* filename)
{
  if (!filename)
    throw DataException("No Python file passed to execute");
  PythonInterpreter::executeFile(filename);
}


DECLARE_EXPORT(void) FreppleSaveFile(const char* x)
{
  XMLSerializerFile o(x);
  o.writeElementWithHeader(Tags::plan, &Plan::instance());
}


/** Closing any resources still used by frePPle.<br>
  * Allocated memory is not freed up with this call - for performance
  * reasons it is easier to "leak" the memory. The memory is freed when
  * the process exits.
  */
DECLARE_EXPORT(void) FreppleExit()
{
  // Close the log file
  Environment::setLogFile("");
}


DECLARE_EXPORT(void) FreppleLog(const string& msg)
{
  logger << msg << endl;
}


extern "C" DECLARE_EXPORT(void) FreppleLog(const char* msg)
{
  logger << msg << endl;
}


extern "C" DECLARE_EXPORT(int) FreppleWrapperInitialize()
{
  try {FreppleInitialize();}
  catch (...) {return EXIT_FAILURE;}
  return EXIT_SUCCESS;
}


extern "C" DECLARE_EXPORT(int) FreppleWrapperReadXMLData(char* d, bool v, bool c)
{
  try {FreppleReadXMLData(d, v, c);}
  catch (...) {return EXIT_FAILURE;}
  return EXIT_SUCCESS;
}


extern "C" DECLARE_EXPORT(int) FreppleWrapperReadXMLFile(const char* f, bool v, bool c)
{
  try {FreppleReadXMLFile(f, v, c);}
  catch (...) {return EXIT_FAILURE;}
  return EXIT_SUCCESS;
}


extern "C" DECLARE_EXPORT(int) FreppleWrapperReadPythonFile(const char* f)
{
  try {FreppleReadPythonFile(f);}
  catch (...) {return EXIT_FAILURE;}
  return EXIT_SUCCESS;
}


extern "C" DECLARE_EXPORT(int) FreppleWrapperSaveFile(char* f)
{
  try {FreppleSaveFile(f);}
  catch (...) {return EXIT_FAILURE;}
  return EXIT_SUCCESS;
}


extern "C" DECLARE_EXPORT(int) FreppleWrapperExit()
{
  try {FreppleExit();}
  catch (...) {return EXIT_FAILURE;}
  return EXIT_SUCCESS;
}

