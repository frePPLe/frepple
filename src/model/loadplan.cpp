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

const MetaCategory* LoadPlan::metacategory;
const MetaClass* LoadPlan::metadata;

int LoadPlan::initialize() {
  // Initialize the metadata
  metacategory =
      MetaCategory::registerCategory<LoadPlan>("loadplan", "loadplans", reader);
  registerFields<LoadPlan>(const_cast<MetaCategory*>(metacategory));
  metadata = MetaClass::registerClass<LoadPlan>("loadplan", "loadplan", true);

  // Initialize the Python type
  auto& x = FreppleCategory<LoadPlan>::getPythonType();
  x.setName("loadplan");
  x.setDoc("frePPLe loadplan");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  metadata->setPythonClass(x);
  return x.typeReady();
}

LoadPlan::LoadPlan(OperationPlan* o, const Load* r, Resource* assigned) {
  // Initialize the Python type
  initType(metadata);

  assert(o);
  ld = const_cast<Load*>(r);
  oper = o;

  // Update the resource field
  if (assigned)
    res = assigned;
  else
    res = r->findPreferredResource(o->getSetupEnd(), o);

  // Add to the operationplan
  nextLoadPlan = nullptr;
  if (o->firstloadplan) {
    // Append to the end
    auto c = o->firstloadplan;
    while (c->nextLoadPlan) c = c->nextLoadPlan;
    c->nextLoadPlan = this;
  } else
    // First in the list
    o->firstloadplan = this;

  // Insert in the resource timeline
  if (ld)
    res->loadplans.insert(this, ld->getLoadplanQuantity(this),
                          ld->getLoadplanDate(this));
  else
    res->loadplans.insert(this, getQuantity() ? getQuantity() : 1,
                          isStart() ? o->getStart() : o->getEnd());

  // For continuous resources, create a loadplan to mark
  // the end of the operationplan.
  if (!getResource()->hasType<ResourceBuckets>()) new LoadPlan(o, r, this);

  // For pooled resource, create individual loadplans when activated
  if (ld && ld->getResource()->isGroup() && ld->getQuantity() > 1.0 &&
      Plan::instance().getIndividualPoolResources() && !assigned) {
    for (auto tmp = ld->getQuantity(); tmp > 1.0; tmp -= 1.0) {
      auto n = new LoadPlan(o, r, static_cast<LoadPlan*>(nullptr));
      if (!n->getResource()->hasType<ResourceBuckets>()) new LoadPlan(o, r, n);
    }
  }

  // Mark the operation and resource as being changed. This will trigger
  // the recomputation of their problems
  getResource()->setChanged();
  o->getOperation()->setChanged();
}

LoadPlan::LoadPlan(OperationPlan* o, const Load* r, LoadPlan* lp)
    : otherLoadPlan(lp) {
  ld = const_cast<Load*>(r);
  oper = o;
  if (lp) {
    flags |= TYPE_END;
    lp->otherLoadPlan = this;
  }

  // Update the resource field
  res = lp ? lp->getResource() : r->findPreferredResource(o->getSetupEnd(), o);

  // Add to the operationplan
  nextLoadPlan = nullptr;
  if (o->firstloadplan) {
    // Append to the end
    auto c = o->firstloadplan;
    while (c->nextLoadPlan) c = c->nextLoadPlan;
    c->nextLoadPlan = this;
  } else
    // First in the list
    o->firstloadplan = this;

  // Insert in the resource timeline
  if (ld)
    getResource()->loadplans.insert(this, ld->getLoadplanQuantity(this),
                                    ld->getLoadplanDate(this));
  else
    getResource()->loadplans.insert(this, -lp->getQuantity(), o->getEnd());

  // Initialize the Python type
  initType(metadata);
}

LoadPlan::LoadPlan(OperationPlan* o, SetupEvent* e, bool start) : oper(o) {
  assert(o && e && e->getRule() && e->getRule()->getResource());

  // Initialize
  initType(metadata);
  res = e->getRule()->getResource();
  if (!start) flags |= TYPE_END;

  // Add to the operationplan
  nextLoadPlan = nullptr;
  if (o->firstloadplan) {
    // Append to the end
    auto c = o->firstloadplan;
    while (c->nextLoadPlan) c = c->nextLoadPlan;
    c->nextLoadPlan = this;
  } else
    // First in the list
    o->firstloadplan = this;

  // Insert in the resource timeline
  getResource()->loadplans.insert(this, e->getLoadplanQuantity(this),
                                  e->getLoadplanDate(this));

  // For continuous resources, create a loadplan to mark the end of the setup.
  if (!getResource()->hasType<ResourceBuckets>() && start)
    new LoadPlan(o, e, false);

  // Mark the resource as being changed.
  getResource()->setChanged();
}

void LoadPlan::setResource(Resource* newres, bool check, bool use_start) {
  // Nothing to do
  if (res == newres) return;

  // Validate the argument
  if (!newres) throw DataException("Can't switch to nullptr resource");
  if (!getLoad()) throw DataException("Can't switch setup resources");
  if (check) {
    // New resource must be a subresource of the load's resource, or have the
    // load name.
    bool ok = false;
    for (auto lditer = getOperationPlan()->getOperation()->getLoads().begin();
         lditer != getOperationPlan()->getOperation()->getLoads().end() && !ok;
         ++lditer) {
      if ((getLoad()->getName().empty() ||
           lditer->getName() == getLoad()->getName()) &&
          newres->getTop() == lditer->getResource()->getTop())
        ok = true;
    }
    if (!ok)
      logger << "Warning: Resource isn't matching the resource specified on "
                "the load"
             << endl;

    // New resource must have the required skill
    if (getLoad()->getSkill()) {
      ok = false;
      Resource::skilllist::const_iterator s = newres->getSkills();
      while (ResourceSkill* rs = s.next())
        if (rs->getSkill() == getLoad()->getSkill()) {
          ok = true;
          break;
        }
      if (!ok)
        logger << "Warning: Resource misses the skill specified on the load"
               << endl;
    }
  }

  // Mark entities as changed
  Resource* oldRes = res;
  if (oper) oper->getOperation()->setChanged();
  if (res && res != newres) res->setChanged();
  newres->setChanged();

  // Change this loadplan and its brother
  LoadPlan* ldplan =
      getResource()->hasType<ResourceBuckets>() ? this : getOtherLoadPlan();
  while (ldplan) {
    // Remove from the old resource, if there is one
    if (res) {
      res->loadplans.erase(ldplan);
      res->setChanged();
    }

    // Insert in the new resource.
    // This code assumes the date and quantity of the loadplan don't change
    // when a new resource is assigned.
    ldplan->res = newres;
    newres->loadplans.insert(ldplan, getLoad()->getLoadplanQuantity(ldplan),
                             getLoad()->getLoadplanDate(ldplan));

    // Repeat for the brother loadplan or exit
    if (ldplan != this)
      ldplan = this;
    else
      break;
  }

  // Clear the setup event
  oper->setStartEndAndQuantity(oper->getSetupEnd(), oper->getEnd(),
                               oper->getQuantity());
  oper->clearSetupEvent();

  // The new resource may have a different availability calendar,
  // and we need to make sure to respect it.
  if (use_start)
    oper->setStart(oper->getStart());
  else
    oper->setEnd(oper->getEnd());

  // Update the setup time on the old resource
  if (oldRes) oldRes->updateSetupTime();

  // Change the resource
  newres->setChanged();

  // Switch also other steps in a routing if the use the same tool
  if ((newres->getTool() || newres->getToolPerPiece()) &&
      getOperationPlan()->getOwner() && getResource()->getOwner() &&
      getLoad() &&
      getOperationPlan()
          ->getOwner()
          ->getOperation()
          ->hasType<OperationRouting>()) {
    // Scan for other steps that use the same tool and same skill
    auto routingopplan = getOperationPlan()->getOwner();
    auto subopplans = routingopplan->getSubOperationPlans();
    while (auto subopplan = subopplans.next()) {
      if (subopplan == getOperationPlan()) continue;
      auto subldplniter = subopplan->getLoadPlans();
      while (auto subldpln = subldplniter.next()) {
        if (subldpln->getLoad() &&
            subldpln->getLoad()->getResource() == getLoad()->getResource() &&
            subldpln->getLoad()->getSkill() == getLoad()->getSkill() &&
            subldpln->getResource() != getResource()) {
          // Switch another step to this resource
          // Note that we switch only a single loadplan. The call below continue
          // to deeper levels
          subldpln->setResource(newres, false, use_start);
          return;
        }
      }
    }
  }
}

string LoadPlan::getStatus() const {
  if (flags & STATUS_CONFIRMED)
    return "confirmed";
  else if (flags & STATUS_CLOSED)
    return "closed";
  else
    return "proposed";
}

void LoadPlan::setStatus(const string& s) {
  if (s == "confirmed") {
    setConfirmed(true);
  } else if (s == "proposed")
    setProposed(true);
  else if (s == "closed") {
    setClosed(true);
  } else
    throw DataException("invalid operationplanresource status:" + s);
}

void LoadPlan::update() {
  if (ld) {
    // Update the timeline data structure
    getResource()->getLoadPlans().update(this, ld->getLoadplanQuantity(this),
                                         ld->getLoadplanDate(this));
    ld->getOperation()->setChanged();
  } else if (getOperationPlan()->getSetupEvent()) {
    auto s = getOperationPlan()->getSetupEvent();
    if (s->getRule() && s->getRule()->getResource())
      // Update the setup resource timeline data
      s->getRule()->getResource()->getLoadPlans().update(
          this, s->getLoadplanQuantity(this), s->getLoadplanDate(this));
  }

  // Mark the resource as being changed.
  getResource()->setChanged();
}

SetupEvent* LoadPlan::getSetup(bool myself_only) const {
  auto opplan = getOperationPlan();
  if (!getResource()->getSetupMatrix() || !opplan) return nullptr;
  if (myself_only) return opplan->getSetupEvent();
  Resource::loadplanlist::const_iterator tmp;
  if (opplan->getSetupEvent())
    // Setup event being used
    tmp = opplan->getSetupEvent();
  else if (isStart())
    // Start loadplan
    tmp = this;
  else
    // End loadplan
    tmp = getOtherLoadPlan();
  while (tmp != getResource()->getLoadPlans().end()) {
    if (tmp->getEventType() == 5 &&
        (tmp->getDate() < opplan->getSetupEnd() ||
         (tmp->getOperationPlan() && tmp->getDate() == opplan->getSetupEnd() &&
          *(tmp->getOperationPlan()) < *opplan)))
      return const_cast<SetupEvent*>(static_cast<const SetupEvent*>(&*tmp));
    --tmp;
  }
  return nullptr;
}

LoadPlan::~LoadPlan() {
  getResource()->setChanged();
  getResource()->loadplans.erase(this);
}

void LoadPlan::setLoad(Load* newld) {
  // No change
  if (newld == ld) return;

  // Verify the data
  if (!newld) throw DataException("Can't switch to nullptr load");
  if (ld && ld->getOperation() != newld->getOperation())
    throw DataException(
        "Only switching to a load on the same operation is allowed");
  if (ld && ld->getResource()->hasType<ResourceBuckets>() !=
                newld->getResource()->hasType<ResourceBuckets>())
    throw DataException(
        "Cannot switch between alternate loads from bucketized and default "
        "resources");

  // Update the load and resource fields
  LoadPlan* o = getOtherLoadPlan();
  if (o) o->ld = newld;
  ld = newld;
  setResource(newld->getResource(), false, false);
}

bool LoadPlan::getFeasible() const {
  if (!getResource()->getConstrained())
    // Unconstrained resource
    return true;
  if (getResource()->hasType<ResourceDefault>()) {
    auto ldpln = getQuantity() > 0 ? this : getOtherLoadPlan();
    auto curMax = ldpln->getMax();
    for (auto cur = getResource()->getLoadPlans().begin(ldpln);
         cur != getResource()->getLoadPlans().end(); ++cur) {
      if (cur->getOperationPlan() == getOperationPlan() &&
          cur->getQuantity() < 0)
        break;
      if (cur->getEventType() == 4) curMax = cur->getMax(false);
      if (cur->getEventType() != 5 && cur->isLastOnDate() &&
          cur->getOnhand() > curMax + ROUNDING_ERROR)
        // Overload on default resource
        return false;
    }
  } else if (getResource()->hasType<ResourceBuckets>()) {
    for (auto cur = getResource()->getLoadPlans().begin(this);
         cur != getResource()->getLoadPlans().end() && cur->getEventType() != 2;
         ++cur) {
      if (cur->getOnhand() < -ROUNDING_ERROR)
        // Overloaded capacity on bucketized resource
        return false;
    }
  }
  // Not overloaded
  return true;
}

Object* LoadPlan::reader(const MetaClass* cat, const DataValueDict& in,
                         CommandManager* mgr) {
  // Pick up the operationplan attribute. An error is reported if it's missing.
  const DataValue* opplanElement = in.get(Tags::operationplan);
  if (!opplanElement) throw DataException("Missing operationplan field");
  Object* opplanobject = opplanElement->getObject();
  if (!opplanobject || !opplanobject->hasType<OperationPlan>())
    throw DataException("Invalid operationplan field");
  OperationPlan* opplan = static_cast<OperationPlan*>(opplanobject);

  // Pick up the resource.
  const DataValue* resourceElement = in.get(Tags::resource);
  if (!resourceElement) throw DataException("Missing resource field");
  Object* resourceobject = resourceElement->getObject();
  if (!resourceobject ||
      resourceobject->getType().category != Resource::metadata)
    throw DataException("Invalid resource field");
  Resource* res = static_cast<Resource*>(resourceobject);

  // Find the load on the operationplan that has the same top resource.
  // If multiple exist, we pick up the first one.
  // If none is found, we throw a data error.
  auto ldplniter = opplan->getLoadPlans();
  LoadPlan* ldpln_tmp = nullptr;
  LoadPlan* ldpln = nullptr;
  const Load* ld = nullptr;
  auto individualresources = Plan::instance().getIndividualPoolResources();
  while ((ldpln_tmp = ldplniter.next())) {
    if ((individualresources && ldpln_tmp->getResource() == res) ||
        (!individualresources &&
         ldpln_tmp->getResource()->getTop() == res->getTop())) {
      ldpln = ldpln_tmp;
      break;
    }
  }

  // Pick up the action attribute and update accordingly
  const DataValue* statusElement = in.get(Tags::status);
  switch (MetaClass::decodeAction(in)) {
    case Action::ADD:
      // Only additions are allowed
      if (ldpln) {
        ostringstream o;
        o << "Loadplan already exists";
        throw DataException(o.str());
      }
      for (auto& g : opplan->getOperation()->getLoads())
        if (g.getResource()->getTop() == res->getTop()) ld = &g;
      ldpln = new LoadPlan(opplan, ld, res);
      if (statusElement) ldpln->setStatus(statusElement->getString());
      opplan->setStart(opplan->getStart());  // Recompute duration
      if (mgr) mgr->add(new CommandCreateObject(ldpln));
      return ldpln;
    case Action::CHANGE:
      // Only changes are allowed
      if (!ldpln) throw DataException("Loadplan not found");
      ldpln->setResource(res);
      if (statusElement) ldpln->setStatus(statusElement->getString());
      return ldpln;
    case Action::REMOVE:
      // Delete the entity
      if (!ldpln)
        throw DataException("Loadplan not found");
      else {
        // Delete it
        delete ldpln;
        opplan->setStart(opplan->getStart());  // Recompute duration
        return nullptr;
      }
    case Action::ADD_CHANGE:
      if (!ldpln) {
        // Adding a new loadplan
        for (auto& g : opplan->getOperation()->getLoads())
          if (g.getResource()->getTop() == res->getTop()) ld = &g;
        ldpln = new LoadPlan(opplan, ld, res);
        opplan->setStart(opplan->getStart());  // Recompute duration
        if (mgr) mgr->add(new CommandCreateObject(ldpln));
      } else
        ldpln->setResource(res);
      if (statusElement) ldpln->setStatus(statusElement->getString());
      return ldpln;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}

PyObject* LoadPlan::create(PyTypeObject* pytype, PyObject* args,
                           PyObject* kwds) {
  try {
    // Find or create the C++ object
    PythonDataValueDict atts(kwds);
    Object* ldpln = reader(LoadPlan::metadata, atts);
    if (!ldpln) {
      Py_INCREF(Py_None);
      return Py_None;
    }
    Py_INCREF(ldpln);

    // Iterate over extra keywords, and set attributes.
    PyObject *key, *value;
    Py_ssize_t pos = 0;
    while (PyDict_Next(kwds, &pos, &key, &value)) {
      PythonData field(value);
      PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
      DataKeyword attr(PyBytes_AsString(key_utf8));
      Py_DECREF(key_utf8);
      if (!attr.isA(Tags::operationplan) && !attr.isA(Tags::resource) &&
          !attr.isA(Tags::action) && !attr.isA(Tags::status)) {
        const MetaFieldBase* fmeta = ldpln->getType().findField(attr.getHash());
        if (!fmeta && ldpln->getType().category)
          fmeta = ldpln->getType().category->findField(attr.getHash());
        if (fmeta)
          // Update the attribute
          fmeta->setField(ldpln, field);
        else
          ldpln->setProperty(attr.getName(), value);
        ;
      }
    };
    return static_cast<PyObject*>(ldpln);
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

double Load::getLoadplanQuantity(const LoadPlan* lp) const {
  if ((!lp->getOperationPlan()->getProposed() &&
       !lp->getOperationPlan()->getConsumeCapacity()) ||
      !lp->getOperationPlan()->getQuantity() ||
      lp->getOperationPlan()->getClosed() ||
      lp->getOperationPlan()->getCompleted())
    // No capacity consumption required
    return 0.0;
  if (lp->getConfirmed()) return lp->getQuantity();
  if (!lp->getOperationPlan()->getDates().overlap(getEffective()) &&
      (lp->getOperationPlan()->getDates().getDuration() ||
       !getEffective().within(lp->getOperationPlan()->getStart())))
    // Load is not effective during this time.
    // The extra check is required to make sure that zero duration
    // operationplans operationplans don't get resized to 0
    return 0.0;
  if (lp->getResource()->hasType<ResourceBuckets>()) {
    // Bucketized resource
    auto efficiency =
        (lp->getResource()->getEfficiencyCalendar()
             ? lp->getResource()->getEfficiencyCalendar()->getValue(
                   lp->getDate())
             : lp->getResource()->getEfficiency()) /
        100.0;
    if (efficiency <= 0.0) return DBL_MIN;
    auto q = -(getQuantityFixed() +
               getQuantity() * lp->getOperationPlan()->getQuantity()) /
             efficiency;
    if (lp->getOperationPlan()->getQuantity() &&
        lp->getOperationPlan()->getQuantityCompleted())
      q *= lp->getOperationPlan()->getQuantityRemaining() /
           lp->getOperationPlan()->getQuantity();
    return q;
  } else if (lp->getLoad()->getResource()->isGroup() &&
             lp->getLoad()->getQuantity() > 1.0 &&
             Plan::instance().getIndividualPoolResources())
    // Continuous pooled resource with individual assignments
    return lp->isStart() ? 1.0 : -1.0;
  else if (lp->getResource()->getToolPerPiece())
    // Tool-per-piece resource
    return (lp->isStart() ? getQuantity() : -getQuantity()) *
           lp->getOperationPlan()->getQuantity();
  else
    // Continuous resource
    return (lp->isStart() ? getQuantity() : -getQuantity());
}

tuple<double, Date, double> LoadPlan::getBucketEnd() const {
  assert(getResource()->hasType<ResourceBuckets>());
  double available_before = getOnhand();
  for (auto cur = res->getLoadPlans().begin(this);
       cur != res->getLoadPlans().end(); ++cur) {
    if (cur->getEventType() == 2)
      return make_tuple(available_before, cur->getDate(), cur->getOnhand());
    available_before = cur->getOnhand();
  }
  return make_tuple(available_before, Date::infiniteFuture, 0);
}

tuple<double, Date, double> LoadPlan::getBucketStart() const {
  assert(getResource()->hasType<ResourceBuckets>());
  double available_after = getOnhand();
  for (auto cur = res->getLoadPlans().begin(this);
       cur != res->getLoadPlans().end(); --cur) {
    available_after = cur->getQuantity();
    if (cur->getEventType() == 2) {
      auto tmp = cur->getDate();
      --cur;
      return make_tuple(
          cur != res->getLoadPlans().end() ? cur->getOnhand() : 0.0, tmp,
          available_after);
    }
  }
  return make_tuple(0.0, Date::infinitePast, available_after);
}

int LoadPlanIterator::initialize() {
  // Initialize the type
  auto& x = PythonExtension<LoadPlanIterator>::getPythonType();
  x.setName("loadplanIterator");
  x.setDoc("frePPLe iterator for loadplan");
  x.supportiter();
  return x.typeReady();
}

PyObject* LoadPlanIterator::iternext() {
  LoadPlan* ld;
  if (resource_or_opplan) {
    // Skip zero quantity loadplans
    while (*resiter != res->getLoadPlans().end() &&
           (*resiter)->getQuantity() == 0.0)
      ++(*resiter);
    if (*resiter == res->getLoadPlans().end()) return nullptr;

    // Return result
    ld = const_cast<LoadPlan*>(static_cast<const LoadPlan*>(&*((*resiter)++)));
  } else {
    while (*opplaniter != opplan->endLoadPlans() &&
           (*opplaniter)->getQuantity() == 0.0)
      ++(*opplaniter);
    if (*opplaniter == opplan->endLoadPlans()) return nullptr;
    ld = static_cast<LoadPlan*>(&*((*opplaniter)++));
  }
  Py_INCREF(ld);
  return const_cast<LoadPlan*>(ld);
}

LoadPlan::AlternateIterator::AlternateIterator(const LoadPlan* o) : ldplan(o) {
  // There are 2 types of alternates:
  // - loads with the same name
  // - subresources of a resource group
  auto l = ldplan->getLoad();
  if (l) {
    for (auto lditer = l->getOperation()->getLoads().begin();
         lditer != l->getOperation()->getLoads().end(); ++lditer) {
      if (l->getName().empty()) {
        if (l != &*lditer || !l->getResource()->isGroup()) continue;
      } else {
        if (l->getName() != lditer->getName()) continue;
      }
      for (Resource::memberRecursiveIterator i(lditer->getResource());
           !i.empty(); ++i) {
        if (ldplan->getResource() == &*i || i->isGroup()) continue;
        Skill* sk = lditer->getSkill();
        if (!sk || i->hasSkill(sk, ldplan->getDate(), ldplan->getDate())) {
          auto my_eff = i->getEfficiencyCalendar()
                            ? i->getEfficiencyCalendar()->getValue(
                                  ldplan->getOperationPlan()->getStart())
                            : i->getEfficiency();
          if (my_eff <= 0.0) continue;
          bool already_assigned = false;
          auto ldplniter = ldplan->getOperationPlan()->getLoadPlans();
          while (auto checkldpln = ldplniter.next())
            if (checkldpln->getResource() == &*i) {
              already_assigned = true;
              break;
            }
          if (!already_assigned) resources.push_back(&*i);
        }
      }
    }
  }
  resIter = resources.begin();
}

Resource* LoadPlan::AlternateIterator::next() {
  if (resIter == resources.end()) return nullptr;
  auto tmp = *resIter;
  ++resIter;
  return tmp;
}

}  // namespace frepple
