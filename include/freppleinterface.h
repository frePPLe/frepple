/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007 by Johan De Taeye                                    *
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


#ifndef FREPPLE_INTERFACE_H
#define FREPPLE_INTERFACE_H

#include <string>

// For a windows shared library we use the C calling convention: __stdcall.
// Only such functions can be called from VBA...
#undef DECLARE_EXPORT
#if defined(WIN32) && !defined(DOXYGEN_SHOULD_SKIP_THIS)
  #ifdef FREPPLE_CORE
    #define DECLARE_EXPORT(type) __declspec (dllexport) type __stdcall
  #else
    #define DECLARE_EXPORT(type) __declspec (dllimport) type __stdcall
  #endif
#else
  #define DECLARE_EXPORT(type) type
#endif

/** This method returns a version string. */
DECLARE_EXPORT(const char*) FreppleVersion();

/** This function should be called once when the client application starts, 
  * and before calling any other function in the API.<br>
  * The parameter is a string with the name of the Frepple home directory.
  * If the parameter is NULL, the setting of the environment variable 
  * FREPPLE_HOME is used instead.<br>
  * This method is synchroneous, i.e. it returns only when the complete 
  * processing is finished. The method can throw exceptions, and the client 
  * is responsible for defining the correct handlers for these.
  */
DECLARE_EXPORT(void) FreppleInitialize(const char*);

/** The character buffer pointed to by the first parameter contains data in
  * XML format that is passed on to Frepple for processing.<br>
  * The second argument specifies whether frepple should validate the data
  * against the XSD schema.<br>
  * The last argument specifies whether Frepple needs to perform only the
  * validation and skip the actual processing.<br>
  * The client is responsible for the memory management in the data buffer.
  * This method is synchroneous, i.e. it returns only when the complete 
  * processing is finished. The method can throw exceptions, and the client 
  * is responsible for defining the correct handlers for these.
  */
DECLARE_EXPORT(void) FreppleReadXMLData(char*, bool, bool);

/** The first parameter is the name of a file that contains data in XML 
  * format for Frepple processing. If a NULL pointer is passed, frepple 
  * will read from the standard input.<br>
  * The second argument specifies whether frepple should validate the data
  * against the XSD schema.<br>
  * The last argument specifies whether Frepple needs to perform only the
  * validation and skip the actual processing.
  * This method is synchroneous, i.e. it returns only when the complete 
  * processing is finished. The method can throw exceptions, and the client 
  * is responsible for defining the correct handlers for these.
  */
DECLARE_EXPORT(void) FreppleReadXMLFile(const char*, bool, bool);

/** Calling this function will save the Frepple data in the file that
  * is passed as the argument. 
  * This method is synchroneous, i.e. it returns only when the complete 
  * processing is finished. The method can throw exceptions, and the client 
  * is responsible for defining the correct handlers for these.
  */
DECLARE_EXPORT(void) FreppleSaveFile(char*);

/** Calling this function returns a text buffer with the frepple data 
  * model.<br>
  * This method can consume a lot of memory for big models!<br>
  * This method is synchroneous, i.e. it returns only when the complete 
  * processing is finished. The method can throw exceptions, and the client 
  * is responsible for defining the correct handlers for these.
  */
DECLARE_EXPORT(std::string) FreppleSaveString();

/** This function causes the frepple executable to shut down in an orderly 
  * way.
  * This method is synchroneous, i.e. it returns only when the complete 
  * processing is finished. The method can throw exceptions, and the client 
  * is responsible for defining the correct handlers for these.
  */
DECLARE_EXPORT(void) FreppleExit();


/* The functions listed below can be called from C. */
#ifdef __cplusplus
extern "C" {
#endif

/** Same as FreppleInitialize, but catches all exceptions and returns a
  * status instead.<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleInitialize
  */
DECLARE_EXPORT(int) FreppleWrapperInitialize(const char*);

/** Same as FreppleReadXMLData, but catches all exceptions and returns a
  * status instead.<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleReadXMLData
  */
DECLARE_EXPORT(int) FreppleWrapperReadXMLData(char*, bool, bool);

/** Same as FreppleReadXMLFile, but catches all exceptions and returns a
  * status instead.<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleReadXMLFile
  */
DECLARE_EXPORT(int) FreppleWrapperReadXMLFile(const char*, bool, bool);

/** Same as FreppleSaveFile, but catches all exceptions and returns a
  * status instead.<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleSaveFile
  */
DECLARE_EXPORT(int) FreppleWrapperSaveFile(char*);

/** Same as FreppleSaveString, but catches all exceptions, returns a status 
  * code and also leaves the memory buffer management to the user.<br>
  * This function can consume a lot of memory for big models!<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleSaveString
  */
DECLARE_EXPORT(int) FreppleWrapperSaveString(char*, unsigned long);

/** Same as FreppleExit, but catches all exceptions and returns a
  * status instead.<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleExit
  */
DECLARE_EXPORT(int) FreppleWrapperExit();

#ifdef __cplusplus
}  // End of "extern C"
#endif

#endif    // End of FREPPLE_INTERFACE_H
