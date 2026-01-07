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

#include "frepple/model.h"
namespace frepple {

const MetaCategory* Load::metadata;
const MetaClass* LoadDefault::metadata;
const MetaClass* LoadBucketizedPercentage::metadata;
const MetaClass* LoadBucketizedFromStart::metadata;
const MetaClass* LoadBucketizedFromEnd::metadata;

int Load::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Load>(
      "load", "loads", Association<Operation, Resource, Load>::reader, finder);
  registerFields<Load>(const_cast<MetaCategory*>(metadata));
  LoadDefault::metadata = MetaClass::registerClass<LoadDefault>(
      "load", "load", Object::create<LoadDefault>, true);

  // Initialize the Python class
  auto& x = FreppleCategory<Load>::getPythonType();
  x.setName("load");
  x.setDoc("frePPLe load");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  Load::metadata->setPythonClass(x);
  return x.typeReady();
}

int LoadBucketizedPercentage::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<LoadBucketizedPercentage>(
      "load", "load_bucketized_percentage",
      Object::create<LoadBucketizedPercentage>);
  registerFields<LoadBucketizedPercentage>(const_cast<MetaClass*>(metadata));
  return metadata ? 0 : 1;
}

int LoadBucketizedFromStart::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<LoadBucketizedFromStart>(
      "load", "load_bucketized_from_start",
      Object::create<LoadBucketizedFromStart>);
  registerFields<LoadBucketizedFromStart>(const_cast<MetaClass*>(metadata));
  return metadata ? 0 : 1;
}

int LoadBucketizedFromEnd::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<LoadBucketizedFromEnd>(
      "load", "load_bucketized_from_end",
      Object::create<LoadBucketizedFromEnd>);
  registerFields<LoadBucketizedFromEnd>(const_cast<MetaClass*>(metadata));
  return metadata ? 0 : 1;
}

Load::~Load() {
  // Set a flag to make sure the level computation is triggered again
  HasLevel::triggerLazyRecomputation();

  // Delete existing loadplans
  if (getOperation() && getResource()) {
    // Loop over operationplans
    for (OperationPlan::iterator i(getOperation()); i != OperationPlan::end();
         ++i)
      // Loop over loadplans
      for (auto j = i->beginLoadPlans(); j != i->endLoadPlans();)
        if (j->getLoad() == this)
          j.deleteLoadPlan();
        else
          ++j;
  }

  // Delete the load from the operation and resource
  if (getOperation()) getOperation()->loaddata.erase(this);
  if (getResource()) getResource()->loads.erase(this);
}

void Load::setOperation(Operation* o) {
  // Validate the input
  if (!setup.empty() && o) {
    // Guarantuee that only a single load has a setup.
    // Alternates of that load can have a setup as well.
    for (auto& i : o->loaddata)
      if (&i != this && !i.setup.empty() && i.getName() != getName()) {
        logger
            << "Warning: Only a single load of an operation can specify a setup"
            << '\n';
        return;
      }
  }

  // Update the field
  if (o) setPtrA(o, o->getLoads());
}

void Load::setSetupString(const string& n) {
  // Validate the input
  if (!n.empty() && getOperation()) {
    // Guarantuee that only a single load has a setup.
    // Alternates of that load can have a setup as well.
    for (auto& i : getOperation()->loaddata)
      if (&i != this && !i.setup.empty() && i.getName() != getName()) {
        logger
            << "Warning:Only a single load of an operation can specify a setup"
            << '\n';
        return;
      }
  }

  // Update the field
  setup = n;
}

PyObject* Load::create(PyTypeObject*, PyObject*, PyObject* kwds) {
  try {
    // Pick up the operation
    PyObject* oper = PyDict_GetItemString(kwds, "operation");
    if (!oper) throw DataException("missing operation on Load");
    if (!PyObject_TypeCheck(oper, Operation::metadata->pythonClass))
      throw DataException("load operation must be of type operation");

    // Pick up the resource
    PyObject* res = PyDict_GetItemString(kwds, "resource");
    if (!res) throw DataException("missing resource on Load");
    if (!PyObject_TypeCheck(res, Resource::metadata->pythonClass))
      throw DataException("load resource must be of type resource");

    // Pick up the quantity
    PyObject* q1 = PyDict_GetItemString(kwds, "quantity");
    double q2 = q1 ? PythonData(q1).getDouble() : 1.0;

    // Pick up the effective dates
    DateRange eff;
    PyObject* eff_start = PyDict_GetItemString(kwds, "effective_start");
    if (eff_start) {
      PythonData d(eff_start);
      eff.setStart(d.getDate());
    }
    PyObject* eff_end = PyDict_GetItemString(kwds, "effective_end");
    if (eff_end) {
      PythonData d(eff_end);
      eff.setEnd(d.getDate());
    }

    // Create the load
    Load* l = new LoadDefault(static_cast<Operation*>(oper),
                              static_cast<Resource*>(res), q2, eff);

    // Iterate over extra keywords, and set attributes.   @todo move this
    // responsibility to the readers...
    if (l) {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value)) {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::effective_end) &&
            !attr.isA(Tags::effective_start) && !attr.isA(Tags::operation) &&
            !attr.isA(Tags::resource) && !attr.isA(Tags::quantity) &&
            !attr.isA(Tags::type) && !attr.isA(Tags::action)) {
          const MetaFieldBase* fmeta = l->getType().findField(attr.getHash());
          if (!fmeta && l->getType().category)
            fmeta = l->getType().category->findField(attr.getHash());
          if (fmeta)
            // Update the attribute
            fmeta->setField(l, field);
          else
            l->setProperty(attr.getName(), value);
          ;
        }
      };
    }

    // Return the object
    Py_INCREF(l);
    return static_cast<PyObject*>(l);
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

Object* Load::finder(const DataValueDict& d) {
  // Check operation
  const DataValue* tmp = d.get(Tags::operation);
  if (!tmp) return nullptr;
  auto* oper = static_cast<Operation*>(tmp->getObject());

  // Check resource field
  tmp = d.get(Tags::resource);
  if (!tmp) return nullptr;
  auto* res = static_cast<Resource*>(tmp->getObject());

  // Walk over all loads of the operation, and return
  // the first one with matching
  const DataValue* hasEffectiveStart = d.get(Tags::effective_start);
  Date effective_start;
  if (hasEffectiveStart) effective_start = hasEffectiveStart->getDate();
  const DataValue* hasEffectiveEnd = d.get(Tags::effective_end);
  Date effective_end;
  if (hasEffectiveEnd) effective_end = hasEffectiveEnd->getDate();
  const DataValue* hasPriority = d.get(Tags::priority);
  int priority = 1;
  if (hasPriority) priority = hasPriority->getInt();
  const DataValue* hasName = d.get(Tags::name);
  string name;
  if (hasName) name = hasName->getString();
  for (const auto& ld : oper->getLoads()) {
    if (ld.getResource() != res) continue;
    if (hasEffectiveStart && ld.getEffectiveStart() != effective_start)
      continue;
    if (hasEffectiveEnd && ld.getEffectiveEnd() != effective_end) continue;
    if (hasPriority && ld.getPriority() != priority) continue;
    if (hasName && ld.getName() != name) continue;
    return const_cast<Load*>(&ld);
  }
  return nullptr;
}

Date Load::getLoadplanDate(const LoadPlan* lp) const {
  const DateRange& dr = lp->getOperationPlan()->getDates();
  if (lp->isStart())
    return dr.getStart() > getEffective().getStart()
               ? dr.getStart()
               : getEffective().getStart();
  else
    return dr.getEnd() < getEffective().getEnd() ? dr.getEnd()
                                                 : getEffective().getEnd();
}

Date LoadBucketizedFromEnd::getLoadplanDate(const LoadPlan* lp) const {
  const DateRange& tmp = lp->getOperationPlan()->getDates();
  if (!offset)
    return tmp.getEnd();
  else {
    DateRange d = lp->getOperation()->calculateOperationTime(
        lp->getOperationPlan(), tmp.getEnd(), offset, false);
    return d.getStart() > tmp.getStart() ? d.getStart() : tmp.getStart();
  }
}

Date LoadBucketizedFromStart::getLoadplanDate(const LoadPlan* lp) const {
  const DateRange& tmp = lp->getOperationPlan()->getDates();
  if (!offset)
    return tmp.getStart();
  else {
    DateRange d = lp->getOperation()->calculateOperationTime(
        lp->getOperationPlan(), tmp.getStart(), offset, true);
    return d.getEnd() > tmp.getEnd() ? tmp.getEnd() : d.getEnd();
  }
}

Date LoadBucketizedPercentage::getLoadplanDate(const LoadPlan* lp) const {
  const DateRange& tmp = lp->getOperationPlan()->getDates();
  if (offset == 0.0)
    return tmp.getStart();
  else if (offset == 100.0)
    return tmp.getEnd();
  else {
    DateRange d = lp->getOperation()->calculateOperationTime(
        lp->getOperationPlan(), tmp.getStart(),
        Duration(static_cast<long>(static_cast<long>(tmp.getDuration()) *
                                   offset / 100.0)),
        true);
    return d.getEnd();
  }
}

Date Load::getOperationPlanDate(const LoadPlan* lp, Date ldplandate,
                                bool start) const {
  // TODO Ignores effective range of the load
  if (start) {
    if (lp->isStart())
      return ldplandate;
    else {
      OperationPlanState tmp =
          lp->getOperationPlan()->setOperationPlanParameters(
              lp->getOperationPlan()->getQuantity(), Date::infinitePast,
              ldplandate, true, false);
      return tmp.start;
    }
  } else {
    if (lp->isStart()) {
      OperationPlanState tmp =
          lp->getOperationPlan()->setOperationPlanParameters(
              lp->getOperationPlan()->getQuantity(), ldplandate,
              Date::infinitePast, false, false);
      return tmp.end;
    } else
      return ldplandate;
  }
}

Date LoadBucketizedFromEnd::getOperationPlanDate(const LoadPlan* lp,
                                                 Date ldplandate,
                                                 bool start) const {
  // TODO Ignores effective range of the load

  DateRange d = lp->getOperation()->calculateOperationTime(
      lp->getOperationPlan(), ldplandate, offset, true);
  OperationPlanState tmp = lp->getOperationPlan()->setOperationPlanParameters(
      lp->getOperationPlan()->getQuantity(), Date::infinitePast, d.getEnd(),
      true, false);
  if (tmp.start <= ldplandate)
    // Total duration exceeds the offset
    return start ? tmp.start : tmp.end;
  else if (start)
    // Offset is smaller than the effective duration.
    // The loadplan will coincide with the operationplan start date.
    return ldplandate;
  else {
    // Offset is smaller than the effective duration.
    OperationPlanState tmp = lp->getOperationPlan()->setOperationPlanParameters(
        lp->getOperationPlan()->getQuantity(), ldplandate, Date::infinitePast,
        false, false);
    return tmp.end;
  }
}

Date LoadBucketizedFromStart::getOperationPlanDate(const LoadPlan* lp,
                                                   Date ldplandate,
                                                   bool start) const {
  // TODO Ignores effective range of the load

  DateRange d = lp->getOperation()->calculateOperationTime(
      lp->getOperationPlan(), ldplandate, offset, false);
  OperationPlanState tmp = lp->getOperationPlan()->setOperationPlanParameters(
      lp->getOperationPlan()->getQuantity(), d.getStart(), Date::infinitePast,
      true, false);
  if (tmp.end >= ldplandate)
    // Total duration exceeds the offset
    return start ? tmp.start : tmp.end;
  else if (start) {
    // Offset is smaller than the effective duration.
    OperationPlanState tmp = lp->getOperationPlan()->setOperationPlanParameters(
        lp->getOperationPlan()->getQuantity(), Date::infinitePast, ldplandate,
        true, false);
    return tmp.start;
  } else
    // Offset is smaller than the effective duration.
    // The loadplan will coincide with the operationplan end date.
    return ldplandate;
}

Date LoadBucketizedPercentage::getOperationPlanDate(const LoadPlan* lp,
                                                    Date ldplandate,
                                                    bool start) const {
  // TODO Ignores effective range of the load
  // Measure how long the operation really takes in effective time
  Duration actualduration;
  const DateRange& tmp = lp->getOperationPlan()->getDates();
  lp->getOperation()->calculateOperationTime(
      lp->getOperationPlan(), tmp.getStart(), tmp.getEnd(), &actualduration);

  // Compute offset
  if (start) {
    DateRange d = lp->getOperation()->calculateOperationTime(
        lp->getOperationPlan(), ldplandate,
        Duration(static_cast<long>(static_cast<long>(actualduration) * offset /
                                   100.0)),
        false);
    return d.getStart();
  } else {
    DateRange d = lp->getOperation()->calculateOperationTime(
        lp->getOperationPlan(), ldplandate,
        Duration(static_cast<long>(static_cast<long>(actualduration) *
                                   (100.0 - offset) / 100.0)),
        true);
    return d.getEnd();
  }
}

Resource* Load::findPreferredResource(Date d, OperationPlan* opplan) const {
  if (!getResource()->isGroup()) return getResource();

  // The preferred resource uses the following criteria in order:
  // - For approved and confirmed operationplans we choose the resource
  //   with the lowest resource load to level-load the pool.
  //   For proposed operationplans, we don't use the utlization.
  // - Choose the most efficient resource from the group regardless of its cost.
  // - Choose the resource with the lowest skill priority.
  // We avoid assigning the same resource twice.
  // TODO We ignore date effectivity.
  Resource* best_res = nullptr;
  Resource* backup_res = nullptr;
  double best_utilization = DBL_MAX;
  double best_eff = 0.0;
  double best_priority = DBL_MAX;
  for (Resource::memberRecursiveIterator mmbr(getResource()); !mmbr.empty();
       ++mmbr) {
    ResourceSkill* tmpRsrcSkill = nullptr;
    if (mmbr->isGroup()) continue;
    if (!backup_res) backup_res = &*mmbr;
    if (!getSkill() || mmbr->hasSkill(getSkill(), d, d, &tmpRsrcSkill)) {
      if (getQuantity() > 1.0 &&
          Plan::instance().getIndividualPoolResources()) {
        // Need to avoid assigning the same resource twice
        bool exists = false;
        for (auto g = opplan->getLoadPlans(); g != opplan->endLoadPlans();
             ++g) {
          if (g->getResource() == &*mmbr) {
            exists = true;
            break;
          }
        }
        if (exists) {
          backup_res = &*mmbr;
          continue;
        }
      }

      double my_utilization = DBL_MAX;
      if (opplan->getConfirmed() || opplan->getApproved()) {
        // Include utilization comparison for approved & confirmed
        my_utilization = mmbr->getUtilization(
            opplan->getStart() - Duration(3L * 24L * 3600L),
            opplan->getEnd() + Duration(3L * 24L * 3600L));
      }

      // Check if better a) utilization, b) efficiency and c) priority
      auto my_eff = mmbr->getEfficiencyCalendar()
                        ? mmbr->getEfficiencyCalendar()->getValue(d)
                        : mmbr->getEfficiency();
      if (my_utilization < best_utilization ||
          (my_utilization == best_utilization && my_eff > best_eff)) {
        best_res = &*mmbr;
        best_eff = my_eff;
        best_utilization = my_utilization;
        best_priority = tmpRsrcSkill ? tmpRsrcSkill->getPriority() : DBL_MAX;
      } else if (my_utilization == best_utilization &&
                 fabs(my_eff - best_eff) < ROUNDING_ERROR && tmpRsrcSkill &&
                 tmpRsrcSkill->getPriority() < best_priority) {
        best_res = &*mmbr;
        best_eff = my_eff;
        best_utilization = my_utilization;
        best_priority = tmpRsrcSkill->getPriority();
      }
    }
  }
  return best_res ? best_res : backup_res;
}

}  // namespace frepple
