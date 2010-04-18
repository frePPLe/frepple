/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2010 by Johan De Taeye                                    *
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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
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


DECLARE_EXPORT(void) FreppleInitialize()
{
  // Initialize only once
  static bool initialized = false;
  if (initialized) return;
  initialized = true;

  // Initialize the libraries
  LibraryModel::initialize(); // also initializes the utils library
  LibrarySolver::initialize();

  // Search for the initialization PY file
  string init = Environment::searchFile("init.py");
  if (!init.empty())
  {
    // Execute the commands in the file
    try
    {
      CommandPython cmd;
      cmd.setFileName(init);
      cmd.execute();
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
    try {CommandReadXMLFile(init).execute();}
    catch (...)
    {
      logger << "Exception caught during execution of 'init.xml'" << endl;
      throw;
    }
  }
}


DECLARE_EXPORT(void) FreppleReadXMLData (const char* x, bool validate, bool validateonly)
{
  if (x) CommandReadXMLString(string(x), validate, validateonly).execute();
}


DECLARE_EXPORT(void) FreppleReadXMLFile (const char* x, bool validate, bool validateonly)
{
  CommandReadXMLFile(x, validate, validateonly).execute();
}


DECLARE_EXPORT(void) FreppleSaveFile(const char* x)
{
  CommandSave(x).execute();
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

