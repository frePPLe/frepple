/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
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
  PythonType& x = FreppleCategory<Plan>::getPythonType();
  x.setName("parameters");
  x.setDoc("frePPLe global settings");
  x.supportgetattro();
  x.supportsetattro();
  int tmp = x.typeReady();
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();

  // Create a singleton plan object
  // Since we can count on the initialization being executed only once, also
  // in a multi-threaded configuration, we don't need a more advanced mechanism
  // to protect the singleton plan.
  thePlan = new Plan();

  // Add access to the information with a global attribute.
  PythonInterpreter::registerGlobalObject("settings", &Plan::instance());
  return tmp;
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

  // Let all operationplans check for new ProblemBeforeCurrent and
  // ProblemBeforeFence problems.
  for (auto& i : Operation::all()) i.setChanged();
}

void Plan::erase(const string& e) {
  if (e == "item")
    Item::clear();
  else if (e == "location")
    Location::clear();
  else if (e == "customer")
    Customer::clear();
  else if (e == "operation")
    Operation::clear();
  else if (e == "demand")
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
      if (!opplan->getConsumeMaterial()) continue;
      bool consumptionexists = false;
      bool productionexists = false;
      auto flplniter = opplan->beginFlowPlans();
      while (auto f = flplniter.next()) {
        if (f->getQuantity() < 0)
          consumptionexists = true;
        else if (f->getQuantity() > 0)
          productionexists = true;
      };
      if ((!productionexists || !consumptionexists) && opplan->getOwner()) {
        auto subopplans = opplan->getOwner()->getSubOperationPlans();
        while (auto subopplan = subopplans.next()) {
          auto subflplniter = subopplan->beginFlowPlans();
          while (auto f = subflplniter.next()) {
            if (f->getQuantity() < 0)
              consumptionexists = true;
            else if (f->getQuantity() > 0)
              productionexists = true;
          };
          if (productionexists && consumptionexists) break;
        }
      }
      for (auto& h : opplan->getOperation()->getFlows()) {
        if (!h.getAlternate() && ((!consumptionexists && h.isConsumer() &&
                                   opplan->getConsumeMaterial()) ||
                                  (!productionexists && h.isProducer() &&
                                   opplan->getProduceMaterial())))
          new FlowPlan(&*opplan, &h);
      }
      opplan->updateFeasible();
    }
  }
}

}  // namespace frepple
