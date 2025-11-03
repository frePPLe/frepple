/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
 *                                                                         *
 * Permission is hereby granted, free of charge, to any person obtaining   *
 * a copy of this software and associated documentation files (the         *
 * "Software"), to deal in the Software without restriction, including     *
 * without limitation the rights to use, copy, modify, merge, publish,     *
 * distribute, sublicense, and/or sell copies of the Software, and to      *
 * permit persons to whom the Software is furnished to do so, subject to   *
 * the following conditions:                                               *
 *                                                                         *
 * The above copyright notice and this permission notice shall be          *
 * included in all copies or substantial portions of the Software.         *
 *                                                                         *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,         *
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF      *
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                   *
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE  *
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION  *
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION   *
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.         *
 *                                                                         *
 ***************************************************************************/

/* This is the public header file for high-level access to the library
 * functionality.
 * The methods listed provide also a safe interface API for accessing the
 * library functionality from C, C++, Visual Basic and other programming
 * languages.
 *
 * When extending the library, use the header file frepple.h instead.
 * It provides a more detailed API to interface with frePPLe.
 */

#pragma once
#ifndef FREPPLE_INTERFACE_H
#define FREPPLE_INTERFACE_H

#ifdef __cplusplus
#include <string>
#endif

// For a windows shared library we use the C calling convention: __stdcall.
// Only such functions can be called from VBA...
#undef DECLARE_EXPORT
#if defined(WIN32)
#ifdef FREPPLE_CORE
#define DECLARE_EXPORT(type) __declspec(dllexport) type __stdcall
#else
#define DECLARE_EXPORT(type) __declspec(dllimport) type __stdcall
#endif
#else
#define DECLARE_EXPORT(type) type
#endif

/* This method returns a version string. */
DECLARE_EXPORT(const char*) FreppleVersion();

/* This function should be called once when the client application starts,
 * and before calling any other function in the API.
 *
 * This method is synchronous, i.e. it returns only when the complete
 * processing is finished. The method can throw exceptions, and the client
 * is responsible for defining the correct handlers for these.
 */
DECLARE_EXPORT(void) FreppleInitialize(bool = true);

/* The character buffer pointed to by the first parameter contains data in
 * XML format that is passed on to frePPLe for processing.
 * The second argument specifies whether frePPLe should validate the data
 * against the XSD schema.
 * The last argument specifies whether frePPLe needs to perform only the
 * validation and skip the actual processing.
 *
 * The client is responsible for the memory management in the data buffer.
 *
 * This method is synchroneous, i.e. it returns only when the complete
 * processing is finished. The method can throw exceptions, and the client
 * is responsible for defining the correct handlers for these.
 */
DECLARE_EXPORT(void) FreppleReadXMLData(const char*, bool, bool);

/* The first parameter is the name of a file that contains data in XML
 * format for frePPLe processing. If a nullptr pointer is passed, frepple
 * will read from the standard input.
 * The second argument specifies whether frePPLe should validate the data
 * against the XSD schema.
 * The last argument specifies whether frePPLe needs to perform only the
 * validation and skip the actual processing.
 *
 * This method is synchroneous, i.e. it returns only when the complete
 * processing is finished. The method can throw exceptions, and the client
 * is responsible for defining the correct handlers for these.
 */
DECLARE_EXPORT(void) FreppleReadXMLFile(const char*, bool, bool);

/* Execute the Python code in a file.
 *
 * This method is synchroneous, i.e. it returns only when the complete
 * processing is finished. The method can throw exceptions, and the client
 * is responsible for defining the correct handlers for these.
 */
DECLARE_EXPORT(void) FreppleReadPythonFile(const char*);

/* Calling this function will save the frePPLe data in the file that
 * is passed as the argument.
 *
 * This method is synchroneous, i.e. it returns only when the complete
 * processing is finished. The method can throw exceptions, and the client
 * is responsible for defining the correct handlers for these.
 */
DECLARE_EXPORT(void) FreppleSaveFile(const char*);

/* This function causes the frepple executable to shut down in an orderly
 * way.
 *
 * This method is synchroneous, i.e. it returns only when the complete
 * processing is finished. The method can throw exceptions, and the client
 * is responsible for defining the correct handlers for these.
 */
DECLARE_EXPORT(void) FreppleExit();

#ifdef __cplusplus
/* Echo a message in the frePPLe log stream (which is either a file or
 * the standard output stream).
 *
 * This function is only available when using C++. The same functionality
 * is available to C with the function FreppleLog(const char*).
 */
DECLARE_EXPORT(void) FreppleLog(const std::string&);

/* The functions listed below can be called from C. */
extern "C" {

#endif
/* Echo a message in the frePPLe log stream (which is either a file or
 * the standard output stream).
 */
DECLARE_EXPORT(void) FreppleLog(const char*);

/* Same as FreppleInitialize, but catches all exceptions and returns a
 * status instead.
 *
 * Use this function when calling the library from C or VB applications.
 */
DECLARE_EXPORT(int) FreppleWrapperInitialize();

/* Same as FreppleReadXMLData, but catches all exceptions and returns a
 * status instead.
 *
 * Use this function when calling the library from C or VB applications.
 */
DECLARE_EXPORT(int) FreppleWrapperReadXMLData(char*, bool, bool);

/* Same as FreppleReadXMLFile, but catches all exceptions and returns a
 * status instead.
 *
 * Use this function when calling the library from C or VB applications.
 */
DECLARE_EXPORT(int) FreppleWrapperReadXMLFile(const char*, bool, bool);

/* Same as FreppleReadPythonFile, but catches all exceptions and returns a
 * status instead.
 *
 * Use this function when calling the library from C or VB applications.
 */
DECLARE_EXPORT(int) FreppleWrapperReadPythonFile(const char*);

/* Same as FreppleSaveFile, but catches all exceptions and returns a
 * status instead.
 *
 * Use this function when calling the library from C or VB applications.
 */
DECLARE_EXPORT(int) FreppleWrapperSaveFile(char*);

/* Same as FreppleExit, but catches all exceptions and returns a
 * status instead.
 *
 * Use this function when calling the library from C or VB applications.
 */
DECLARE_EXPORT(int) FreppleWrapperExit();

#ifdef __cplusplus
}  // End of "extern C"
#endif

#endif  // End of FREPPLE_INTERFACE_H
