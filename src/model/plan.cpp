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
#include "frepple/model.h"

namespace frepple {

Plan* Plan::thePlan;
const MetaClass* Plan::metadata;
const MetaCategory* Plan::metacategory;

int Plan::initialize() {
  // Initialize the plan metadata.
  metacategory = MetaCategory::registerCategory<Plan>("plan", "");
  Plan::metadata =
      MetaClass::registerClass<OperationPlan>("plan", "plan", true);
  registerFields<Plan>(const_cast<MetaCategory*>(metacategory));

  // Initialize the Python type
  auto& x = FreppleCategory<Plan>::getPythonType();
  x.setName("parameters");
  x.setDoc("frePPLe global settings");
  x.supportgetattro();
  x.supportsetattro();
  x.addMethod("setBaseClass", setBaseClass, METH_VARARGS,
              "specifies a Python base class to use for the engine objects");
  int tmp = x.typeReady();
  metadata->setPythonClass(x);

  // Create a singleton plan object
  // Since we can count on the initialization being executed only once, also
  // in a multi-threaded configuration, we don't need a more advanced mechanism
  // to protect the singleton plan.
  thePlan = new Plan();

  // Add access to the information with a global attribute.
  PythonInterpreter::registerGlobalObject("settings", &Plan::instance());
  return tmp;
}

PyObject* Plan::setBaseClass(PyObject* self, PyObject* args) {
  PyObject* class_cpp = nullptr;
  PyObject* class_py = nullptr;
  if (!PyArg_ParseTuple(args, "OO:setBaseClass", &class_cpp, &class_py))
    return nullptr;
  if (!class_cpp || !PyType_Check(class_cpp)) {
    PyErr_SetString(PyExc_TypeError, "First argument must be a type");
    return nullptr;
  }
  if (!class_py || !PyType_Check(class_py)) {
    PyErr_SetString(PyExc_TypeError, "Second argument must be a type");
    return nullptr;
  }
  auto t = MetaClass::findClass(class_cpp);
  if (t) const_cast<MetaClass*>(t)->pythonBaseClass = (PyTypeObject*)(class_py);
  return Py_BuildValue("");
}

Plan::~Plan() {
  // Closing the logfile
  Environment::setLogFile("");

  // Clear the pointer to this singleton object
  thePlan = nullptr;
}

void Plan::setCurrent(Date l) {
  // Update the time
  cur_Date = l;

  // Also update the forecast current date if not set
  if (!fcst_cur_Date) fcst_cur_Date = l;

  // Let all operationplans check for new ProblemBeforeCurrent and
  // ProblemBeforeFence problems.
  for (auto& i : Operation::all()) i.setChanged();
}

void Plan::setFcstCurrent(Date l) { fcst_cur_Date = l; }

void Plan::erase(const string& e) {
  if (e == "item")
    Item::clear();
  else if (e == "location")
    Location::clear();
  else if (e == "customer")
    Customer::clear();
  else if (e == "operation")
    Operation::clear();
  else if (e == "demand" || e == "forecast")
    // TODO handling demand and forecast here as the same is not correct.
    // In this file, we can't make the distinction - as the forecast class isn't
    // known at this point yet.
    Demand::clear();
  else if (e == "buffer")
    Buffer::clear();
  else if (e == "skill")
    Skill::clear();
  else if (e == "resource")
    Resource::clear();
  else if (e == "setupmatrix")
    SetupMatrix::clear();
  else if (e == "calendar")
    Calendar::clear();
  else if (e == "supplier")
    Supplier::clear();
  else if (e == "operationplan")
    OperationPlan::clear();
  // Not supported on itemsupplier, itemdistribution, resourceskill, flow, load,
  // setupmatrixrule...
  else
    throw DataException("erase operation not supported");
}

void Plan::setSuppressFlowplanCreation(bool b) {
  suppress_flowplan_creation = b;

  if (!suppress_flowplan_creation) {
    // Delayed creation of flowplans - basically deplayed execution of
    // Operationplan::createFlowLoads.
    //
    // If an operationplan doesn't have a single consunming flowplan.yet, we
    // create them now. If there are existing flowplans, we assume they are
    // complete.
    // Similar logic for producing flowplans.
    for (auto opplan = OperationPlan::begin(); opplan != OperationPlan::end();
         ++opplan) {
      if (!opplan->getConsumeMaterial() && !opplan->getProduceMaterial())
        continue;
      bool consumptionexists = false;
      bool productionexists = false;
      auto flplniter = opplan->beginFlowPlans();
      while (auto f = flplniter.next()) {
        if (f->getQuantity() < 0)
          consumptionexists = true;
        else if (f->getQuantity() > 0)
          productionexists = true;
      };
      if (!productionexists || !consumptionexists) {
        for (auto& h : opplan->getOperation()->getFlows()) {
          if (!h.getAlternate() && ((!consumptionexists && h.isConsumer() &&
                                     opplan->getConsumeMaterial()) ||
                                    (!productionexists && h.isProducer() &&
                                     opplan->getProduceMaterial())))
            new FlowPlan(&*opplan, &h);
        }
      }
      opplan->updateFeasible();
    }
  }
}

}  // namespace frepple
