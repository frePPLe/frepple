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
#include "frepple/model.h"
#include <sys/stat.h>

namespace frepple
{

// Generic Python type for timeline events
PythonType* EventPythonType = nullptr;

void LibraryModel::initialize()
{
  // Initialize only once
  static bool init = false;
  if (init)
  {
    logger << "Warning: Calling frepple::LibraryModel::initialize() more "
        << "than once." << endl;
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
  nok += Item::initialize();
  nok += ItemDefault::initialize();
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

  EventPythonType = Object::registerPythonType(
    sizeof(TimeLine<Flow>::EventMaxQuantity),
    &typeid(TimeLine<Flow>::EventMaxQuantity)
    );

  // Exit if errors were found
  if (nok)
    throw RuntimeException("Error registering new Python types");

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
  PythonInterpreter::registerGlobalMethod(
    "readXMLfile", readXMLfile, METH_VARARGS,
    "Read an XML file.");
  PythonInterpreter::registerGlobalMethod(
    "saveXMLfile", saveXMLfile, METH_VARARGS,
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
    "problems", PythonIterator<Problem::iterator, Problem>::create, METH_NOARGS,
    "Returns an iterator over the problems.");
  PythonInterpreter::registerGlobalMethod(
    "setupmatrices", SetupMatrix::createIterator, METH_NOARGS,
    "Returns an iterator over the setup matrices.");
  PythonInterpreter::registerGlobalMethod(
    "skills", Skill::createIterator, METH_NOARGS,
    "Returns an iterator over the skills.");
}


}
