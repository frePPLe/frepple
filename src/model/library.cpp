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

#include <sys/stat.h>

#include "frepple/model.h"

namespace frepple {

// Generic Python type for timeline events
PythonType* EventPythonType = nullptr;

void LibraryModel::initialize() {
  // Initialize only once
  static bool init = false;
  if (init) {
    logger << "Warning: Calling frepple::LibraryModel::initialize() more "
           << "than once.\n";
    return;
  }
  init = true;

  // Register new types in Python
  // Ordering is important here!!! If a class contains a field of type
  // iterator, then the class it iterators over must be defined before.
  int nok = 0;
  nok += Solver::initialize();
  nok += Problem::initialize();
  nok += Customer::initialize();
  nok += CustomerDefault::initialize();
  nok += ItemSupplier::initialize();
  nok += Supplier::initialize();
  nok += SupplierDefault::initialize();
  nok += CalendarBucket::initialize();
  nok += Calendar::initialize();
  nok += CalendarDefault::initialize();
  nok += ResourceSkill::initialize();
  nok += LoadPlan::initialize();
  nok += FlowPlan::initialize();
  nok += PeggingIterator::initialize();
  nok += PeggingDemandIterator::initialize();
  nok += OperationPlanDependency::initialize();
  nok += OperationPlan::InterruptionIterator::intitialize();
  nok += OperationPlan::initialize();
  nok += Load::initialize();
  nok += LoadBucketizedFromStart::initialize();
  nok += LoadBucketizedFromEnd::initialize();
  nok += LoadBucketizedPercentage::initialize();
  nok += LoadPlanIterator::initialize();
  nok += Flow::initialize();
  nok += FlowPlanIterator::initialize();
  nok += SubOperation::initialize();
  nok += OperationDependency::initialize();
  nok += Operation::initialize();
  nok += OperationAlternate::initialize();
  nok += OperationSplit::initialize();
  nok += OperationFixedTime::initialize();
  nok += OperationTimePer::initialize();
  nok += OperationRouting::initialize();
  nok += OperationItemSupplier::initialize();
  nok += OperationItemDistribution::initialize();
  nok += OperationInventory::initialize();
  nok += OperationDelivery::initialize();
  nok += ItemDistribution::initialize();
  nok += Location::initialize();
  nok += LocationDefault::initialize();
  nok += Buffer::initialize();
  nok += BufferDefault::initialize();
  nok += BufferInfinite::initialize();
  nok += Demand::initialize();
  nok += DemandDefault::initialize();
  nok += DemandGroup::initialize();
  nok += Item::initialize();
  nok += ItemMTS::initialize();
  nok += ItemMTO::initialize();
  nok += SetupMatrixRule::initialize();
  nok += SetupMatrixRuleDefault::initialize();
  nok += SetupMatrix::initialize();
  nok += SetupMatrixDefault::initialize();
  nok += SetupEvent::initialize();
  nok += Skill::initialize();
  nok += SkillDefault::initialize();
  nok += Resource::initialize();
  nok += ResourceDefault::initialize();
  nok += ResourceInfinite::initialize();
  nok += Resource::PlanIterator::initialize();
  nok += ResourceBuckets::initialize();
  nok += Plan::initialize();

  EventPythonType =
      Object::registerPythonType(sizeof(TimeLine<Flow>::EventMaxQuantity),
                                 &typeid(TimeLine<Flow>::EventMaxQuantity));

  // Exit if errors were found
  if (nok) throw RuntimeException("Error registering new Python types");

  // Register new methods in Python
  PythonInterpreter::registerGlobalMethod(
      "printsize", printModelSize, METH_NOARGS,
      "Print information about the memory consumption.");
  PythonInterpreter::registerGlobalMethod(
      "erase", eraseModel, METH_VARARGS,
      "Removes the plan data from memory, and optionally the static info too.");
  PythonInterpreter::registerGlobalMethod(
      "readXMLdata", readXMLdata, METH_VARARGS,
      "Processes a XML string passed as argument.");
  PythonInterpreter::registerGlobalMethod("readXMLfile", readXMLfile,
                                          METH_VARARGS, "Read an XML file.");
  PythonInterpreter::registerGlobalMethod("saveXMLfile", saveXMLfile,
                                          METH_VARARGS,
                                          "Save the model to a XML file.");
  PythonInterpreter::registerGlobalMethod(
      "saveplan", savePlan, METH_VARARGS,
      "Save the main plan information to a file.");
  PythonInterpreter::registerGlobalMethod(
      "buffers", Buffer::createIterator, METH_NOARGS,
      "Returns an iterator over the buffers.");
  PythonInterpreter::registerGlobalMethod(
      "locations", Location::createIterator, METH_NOARGS,
      "Returns an iterator over the locations.");
  PythonInterpreter::registerGlobalMethod(
      "customers", Customer::createIterator, METH_NOARGS,
      "Returns an iterator over the customers.");
  PythonInterpreter::registerGlobalMethod(
      "suppliers", Supplier::createIterator, METH_NOARGS,
      "Returns an iterator over the suppliers.");
  PythonInterpreter::registerGlobalMethod(
      "items", Item::createIterator, METH_NOARGS,
      "Returns an iterator over the items.");
  PythonInterpreter::registerGlobalMethod(
      "calendars", Calendar::createIterator, METH_NOARGS,
      "Returns an iterator over the calendars.");
  PythonInterpreter::registerGlobalMethod(
      "demands", Demand::createIterator, METH_NOARGS,
      "Returns an iterator over the demands.");
  PythonInterpreter::registerGlobalMethod(
      "resources", Resource::createIterator, METH_NOARGS,
      "Returns an iterator over the resources.");
  PythonInterpreter::registerGlobalMethod(
      "operations", Operation::createIterator, METH_NOARGS,
      "Returns an iterator over the operations.");
  PythonInterpreter::registerGlobalMethod(
      "operationplans", OperationPlan::createIterator, METH_VARARGS,
      "Returns an iterator over the operationplans.");
  PythonInterpreter::registerGlobalMethod(
      "problems", PythonIterator<Problem::iterator, Problem>::create,
      METH_NOARGS, "Returns an iterator over the problems.");
  PythonInterpreter::registerGlobalMethod(
      "setupmatrices", SetupMatrix::createIterator, METH_NOARGS,
      "Returns an iterator over the setup matrices.");
  PythonInterpreter::registerGlobalMethod(
      "skills", Skill::createIterator, METH_NOARGS,
      "Returns an iterator over the skills.");
}

}  // namespace frepple
