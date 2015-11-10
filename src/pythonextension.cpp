/***************************************************************************
 *                                                                         *
 * Copyright (C) 2015 by frePPLe bvba                                      *
 *                                                                         *
 * All information contained herein is, and remains the property of        *
 * frePPLe.                                                                *
 * You are allowed to use and modify the source code, as long as the       *
 * software is used within your company.                                   *
 * You are not allowed to distribute the software, either in the form of   *
 * source code or in the form of compiled binaries.                        *
 *                                                                         *
 ***************************************************************************/

#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;

/** Used to initialize frePPLe as a Python extension module. */
PyMODINIT_FUNC PyInit_frepple(void)
{
  try
  {
    // Initialize frePPLe, without reading the configuration
    // files init.xml or init.py
    FreppleInitialize(false);
    return PythonInterpreter::getModule();
  }
  catch(const exception& e)
  {
    PyErr_SetString(PyExc_SystemError, e.what());
    return NULL;
  }
  catch (...)
  {
    PyErr_SetString(PyExc_SystemError, "Initialization failed");
    return NULL;
  }
}
