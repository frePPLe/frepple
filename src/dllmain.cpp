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

#define FREPPLE_CORE
#include "forecast/forecast.h"
#include "frepple.h"
#include "frepple/database.h"
#include "freppleinterface.h"
using namespace frepple;

DECLARE_EXPORT(const char*) FreppleVersion() { return PACKAGE_VERSION; }

DECLARE_EXPORT(void) FreppleInitialize(bool procesInitializationFiles) {
  // Initialize only once
  static bool initialized = false;
  if (initialized) return;
  initialized = true;

  // Initialize the libraries
  LibraryUtils::initialize();
  LibraryModel::initialize();
  LibrarySolver::initialize();
  Cache::initialize();

  PyGILState_STATE state = PyGILState_Ensure();
  try {
    PythonInterpreter::registerGlobalMethod(
        "readJSONdata", readJSONdata, METH_VARARGS,
        "Processes a JSON string passed as argument.");
    PythonInterpreter::registerGlobalMethod("readJSONfile", readJSONfile,
                                            METH_VARARGS, "Read a JSON file.");
    PythonInterpreter::registerGlobalMethod("saveJSONfile", saveJSONfile,
                                            METH_VARARGS,
                                            "Save the model to a JSON file.");
    PythonInterpreter::registerGlobalMethod(
        "runDatabaseThread", runDatabaseThread, METH_VARARGS,
        "Start a thread to persist data in a PostgreSQL database.");

    // Initialize the forecast module
    int nok = 0;
    nok += ForecastBucket::initialize();
    nok += Forecast::initialize();
    nok += ForecastSolver::initialize();
    nok += ForecastMeasure::initialize();
    nok += ForecastMeasureAggregated::initialize();
    nok += ForecastMeasureAggregatedPlanned::initialize();
    nok += ForecastMeasureLocal::initialize();
    nok += ForecastMeasureComputed::initialize();
    nok += ForecastMeasureComputedPlanned::initialize();
    nok += ForecastMeasureTemp::initialize();
    if (nok) throw RuntimeException("Error registering forecasting module");

    Measures::forecasttotal = new ForecastMeasureComputed(
        "forecasttotal",
        "if(forecastoverride == -1, forecastbaseline, forecastoverride)");
    Measures::forecastnet =
        new ForecastMeasureAggregatedPlanned("forecastnet", 0);
    Measures::forecastconsumed =
        new ForecastMeasureAggregatedPlanned("forecastconsumed", 0);
    Measures::forecastbaseline =
        new const ForecastMeasureAggregated("forecastbaseline", 0);
    Measures::forecastoverride = new ForecastMeasureAggregated(
        "forecastoverride", -1, false, Measures::forecastbaseline);
    Measures::orderstotal = new ForecastMeasureAggregated("orderstotal", 0);
    Measures::ordersadjustment =
        new ForecastMeasureAggregated("ordersadjustment", 0);
    Measures::ordersopen = new ForecastMeasureAggregated("ordersopen", 0);
    Measures::forecastplanned =
        new ForecastMeasureAggregatedPlanned("forecastplanned", 0);
    Measures::ordersplanned = new ForecastMeasureAggregated("ordersplanned", 0);
    auto tmp = new ForecastMeasureLocal("outlier", 0);
    tmp->setStored(false);
    Measures::outlier = tmp;
    tmp = new ForecastMeasureLocal("leaf", 0);
    Measures::leaf = tmp;
    tmp->setStored(false);
    auto t1 = new ForecastMeasureLocal("outlier", 0);
    t1->setStored(false);
    Measures::outlier = t1;
    Measures::nodata = new ForecastMeasureLocal("nodata", 0);
    ForecastMeasureComputed::compileMeasures();

    PyGILState_Release(state);
  } catch (const exception& e) {
    PyGILState_Release(state);
    logger << "Error: " << e.what() << endl;
  } catch (...) {
    PyGILState_Release(state);
    logger << "Error: unknown exception" << endl;
  }

  // Search for the initialization PY file
  if (!procesInitializationFiles) return;
  string init = Environment::searchFile("init.py");
  if (!init.empty()) {
    // Execute the commands in the file
    try {
      PythonInterpreter::executeFile(init);
    } catch (...) {
      logger << "Exception caught during execution of 'init.py'" << endl;
      throw;
    }
  }

  // Search for the initialization XML file
  init = Environment::searchFile("init.xml");
  if (!init.empty()) {
    // Execute the commands in the file
    try {
      XMLInputFile(init).parse(&Plan::instance(), true);
    } catch (...) {
      logger << "Exception caught during execution of 'init.xml'" << endl;
      throw;
    }
  }
}

DECLARE_EXPORT(void)
FreppleReadXMLData(const char* x, bool validate, bool validateonly) {
  if (!x) return;
  if (validateonly)
    XMLInputString(x).parse(nullptr, true);
  else
    XMLInputString(x).parse(&Plan::instance(), validate);
}

DECLARE_EXPORT(void)
FreppleReadXMLFile(const char* filename, bool validate, bool validateonly) {
  if (!filename) {
    // Read from standard input
    xercesc::StdInInputSource in;
    if (validateonly)
      // When no root object is passed, only the input validation happens
      XMLInput().parse(in, nullptr, true);
    else
      XMLInput().parse(in, &Plan::instance(), validate);
  } else if (validateonly)
    // Read and validate a file
    XMLInputFile(filename).parse(nullptr, true);
  else
    // Read, execute and optionally validate a file
    XMLInputFile(filename).parse(&Plan::instance(), validate);
}

DECLARE_EXPORT(void) FreppleReadPythonFile(const char* filename) {
  if (!filename) throw DataException("No Python file passed to execute");
  PythonInterpreter::executeFile(filename);
}

DECLARE_EXPORT(void) FreppleSaveFile(const char* x) {
  XMLSerializerFile o(x);
  o.writeElementWithHeader(Tags::plan, &Plan::instance());
}

/* Closing any resources still used by frePPle.
 * Allocated memory is not freed up with this call - for performance
 * reasons it is easier to "leak" the memory. The memory is freed when
 * the process exits.
 */
DECLARE_EXPORT(void) FreppleExit() {
  // Close the log file
  Environment::setLogFile("");
}

DECLARE_EXPORT(void) FreppleLog(const string& msg) { logger << msg << endl; }

extern "C" DECLARE_EXPORT(void) FreppleLog(const char* msg) {
  logger << msg << endl;
}

extern "C" DECLARE_EXPORT(int) FreppleWrapperInitialize() {
  try {
    FreppleInitialize();
  } catch (...) {
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}

extern "C" DECLARE_EXPORT(int)
    FreppleWrapperReadXMLData(char* d, bool v, bool c) {
  try {
    FreppleReadXMLData(d, v, c);
  } catch (...) {
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}

extern "C" DECLARE_EXPORT(int)
    FreppleWrapperReadXMLFile(const char* f, bool v, bool c) {
  try {
    FreppleReadXMLFile(f, v, c);
  } catch (...) {
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}

extern "C" DECLARE_EXPORT(int) FreppleWrapperReadPythonFile(const char* f) {
  try {
    FreppleReadPythonFile(f);
  } catch (...) {
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}

extern "C" DECLARE_EXPORT(int) FreppleWrapperSaveFile(char* f) {
  try {
    FreppleSaveFile(f);
  } catch (...) {
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}

extern "C" DECLARE_EXPORT(int) FreppleWrapperExit() {
  try {
    FreppleExit();
  } catch (...) {
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
