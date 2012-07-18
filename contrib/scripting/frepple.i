/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2012 by Johan De Taeye                               *
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


//
// DEFINE FREPPLE MODULE AND ITS INTERFACE
//
%module frepple
%{
  #include "frepple.h"
  #include "freppleinterface.h"
	#include <stdexcept>
%}

%include "std_string.i"

// The following dummy type declaration is required to make the generated code
// compile properly with Visual Studio.
typedef boolean ff;

//
// DEFINE PERL EXCEPTION HANDLER
//
#ifdef SWIGPERL5
%exception {
	try {
		$function
	} catch(std::exception& e) {
		SWIG_croak(e.what());
	}catch(...) {
		SWIG_croak("Unknown exception");
	}
}
#endif


//
// DEFINE PYTHON EXCEPTION HANDLER
//
#ifdef SWIGPYTHON
%exception {
	try {
		$function
	} catch(std::exception& e) {
		PyErr_SetString(PyExc_RuntimeError, e.what());
		SWIG_fail;
	} catch(...) {
		PyErr_SetString(PyExc_RuntimeError, "Unknown exception");
		SWIG_fail;
	}
}
#endif


//
// DEFINE JAVA EXCEPTION HANDLER
//
#ifdef SWIGJAVA
%pragma(java) jniclasscode=%{
  static {
    try {
			System.loadLibrary("frepplejava");
			FreppleInitialize(null);
		} catch (UnsatisfiedLinkError e)
		{
			System.out.println("Frepple link error: " + e.getMessage());
      e.printStackTrace();
      System.exit(1);
		} catch (Exception e)
		{
			System.out.println("Frepple error: " + e.getMessage());
      e.printStackTrace();
      System.exit(1);
		}
	}
%}
#endif


//
// DEFINE THE EXPOSED API
//
#ifdef SWIGJAVA
  void FreppleInitialize() throw (std::exception);
  void FreppleReadXMLData(char* x, bool a, bool b) throw (std::exception);
  void FreppleReadXMLFile(char* x, bool a, bool b) throw (std::exception);
  void FreppleSaveFile(char* x) throw (std::exception);
  void FreppleExit() throw (std::exception);
#else
  void FreppleInitialize();
  void FreppleReadXMLData(char* x, bool a, bool b);
  void FreppleReadXMLFile(char* x, bool a, bool b);
  void FreppleSaveFile(char* x);
  void FreppleExit();
#endif

