/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/include/freppleinterface.h $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : johan_de_taeye@yahoo.com
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


#ifndef FREPPLE_INTERFACE_H
#define FREPPLE_INTERFACE_H

#include <string>


// For the windows build we want to use the C calling convention.
// That's because only such functions can be called from VBA...
#if (defined(HAVE_WINDOWS_H) || defined(WIN32)) && !defined(STATIC)
#define APIDEF __stdcall
#else
#define APIDEF
#endif
  
/** The complete frepple public interface is synchroneous, i.e. a client
  * function call returns only when the complete processing is finished.
  * The interface can throw exceptions, and the client is responsible for
  * defining the correct handlers for these.
  */

/** This function should be called once when the client application starts, 
  * and before calling any other function in the API. 
  * The parameter is a string with the name of the Frepple home directory.
  * If the parameter is NULL, the setting of the environment variable 
  * FREPPLE_HOME is used instead.
  */
void APIDEF FreppleInitialize(const char*);

/** The character buffer pointed to by the first parameter contains data in
  * XML format that is passed on to Frepple for processing.<br>
  * The second argument specifies whether frepple should validate the data
  * against the XSD schema.<br>
  * The last argument specifies whether Frepple needs to perform only the
  * validation and skip the actual processing.<br>
  * The client is responsible for the memory management in the data buffer.
  */
void APIDEF FreppleReadXMLData(char*, bool, bool);

/** The first parameter is the name of a file that contains data in XML 
  * format for Frepple processing. If a NULL pointer is passed, frepple 
  * will read from the standard input.<br>
  * The second argument specifies whether frepple should validate the data
  * against the XSD schema.<br>
  * The last argument specifies whether Frepple needs to perform only the
  * validation and skip the actual processing.
  */
void APIDEF FreppleReadXMLFile(const char*, bool, bool);

/** Calling this function will save the Frepple data in the file that
  * is passed as the argument. */
void APIDEF FreppleSaveFile(char*);

/** Calling this function returns a text buffer with the frepple data 
  * model.<br>
  * This method can consume a lot of memory for big models!
  */
std::string APIDEF FreppleSaveString();

/** This function causes the frepple executable to shut down in an orderly 
  * way. */
void APIDEF FreppleExit();


/* The functions listed below can be called from C. */
#ifdef __cplusplus
extern "C" {
#endif

/** Same as FreppleInitialize, but catches all exceptions.<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleInitialize
  */
int APIDEF FreppleWrapperInitialize(const char*);

/** Same as FreppleReadXMLData, but catches all exceptions.<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleReadXMLData
  */
int APIDEF FreppleWrapperReadXMLData(char*, bool, bool);

/** Same as FreppleReadXMLFile, but catches all exceptions.<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleReadXMLFile
  */
int APIDEF FreppleWrapperReadXMLFile(const char*, bool, bool);

/** Same as FreppleSaveFile, but catches all exceptions.<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleSaveFile
  */
int APIDEF FreppleWrapperSaveFile(char*);

/** Same as FreppleSaveString, but catches all exceptions and also 
  * leaves the memory buffer management to the user.<br>
  * This function can consume a lot of memory for big models!<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleSaveString
  */
int APIDEF FreppleWrapperSaveString(char*, unsigned long);

/** Same as FreppleExit, but catches all exceptions.<br>
  * Use this function when calling the library from C or VB applications.
  * @see FreppleExit
  */
int APIDEF FreppleWrapperExit();

#ifdef __cplusplus
}  // End of "extern C"
#endif

#endif    // End of FREPPLE_INTERFACE_H
