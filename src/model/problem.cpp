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

bool Plannable::anyChange = false;
bool Plannable::computationBusy = false;
const MetaCategory* Problem::metadata;
const MetaClass *ProblemMaterialShortage::metadata, *ProblemExcess::metadata,
    *ProblemShort::metadata, *ProblemEarly::metadata, *ProblemLate::metadata,
    *ProblemInvalidData::metadata, *ProblemDemandNotPlanned::metadata,
    *ProblemPrecedence::metadata, *ProblemBeforeFence::metadata,
    *ProblemBeforeCurrent::metadata, *ProblemCapacityUnderload::metadata,
    *ProblemCapacityOverload::metadata, *ProblemAwaitSupply::metadata,
    *ProblemSyncDemand::metadata;

int Problem::initialize() {
  // Initialize the problem metadata.
  metadata = MetaCategory::registerCategory<Problem>("problem", "problems");
  registerFields<Problem>(const_cast<MetaCategory*>(metadata));

  // Register classes.
  // We register them as default to avoid saving an xsi:type header. This
  // has no further impact as there is no factory method.
  ProblemMaterialShortage::metadata =
      MetaClass::registerClass<ProblemMaterialShortage>(
          "problem", "material shortage", true);
  ProblemExcess::metadata =
      MetaClass::registerClass<ProblemExcess>("problem", "excess", true);
  ProblemShort::metadata =
      MetaClass::registerClass<ProblemShort>("problem", "short", true);
  ProblemEarly::metadata =
      MetaClass::registerClass<ProblemEarly>("problem", "early", true);
  ProblemLate::metadata =
      MetaClass::registerClass<ProblemLate>("problem", "late", true);
  ProblemInvalidData::metadata = MetaClass::registerClass<ProblemInvalidData>(
      "problem", "invalid data", true);
  ProblemDemandNotPlanned::metadata =
      MetaClass::registerClass<ProblemDemandNotPlanned>("problem", "unplanned",
                                                        true);
  ProblemPrecedence::metadata = MetaClass::registerClass<ProblemPrecedence>(
      "problem", "precedence", true);
  ProblemBeforeFence::metadata = MetaClass::registerClass<ProblemBeforeFence>(
      "problem", "before fence", true);
  ProblemBeforeCurrent::metadata =
      MetaClass::registerClass<ProblemBeforeCurrent>("problem",
                                                     "before current", true);
  ProblemAwaitSupply::metadata = MetaClass::registerClass<ProblemAwaitSupply>(
      "problem", "await supply", true);
  ProblemSyncDemand::metadata = MetaClass::registerClass<ProblemSyncDemand>(
      "problem", "sync demand", true);
  ProblemCapacityUnderload::metadata =
      MetaClass::registerClass<ProblemCapacityUnderload>("problem", "underload",
                                                         true);
  ProblemCapacityOverload::metadata =
      MetaClass::registerClass<ProblemCapacityOverload>("problem", "overload",
                                                        true);

  // Initialize the Python type
  auto& x = PythonExtension<Problem>::getPythonType();
  x.setName("problem");
  x.setDoc("frePPLe problem");
  x.supportgetattro();
  x.supportstr();
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  metadata->setPythonClass(x);
  return x.typeReady();
}

bool Problem::operator<(const Problem& a) const {
  // 1. Sort based on entity
  assert(owner == a.owner);

  // 2. Sort based on type
  if (getType() != a.getType()) return getType() < a.getType();

  // 3. Sort based on start date
  return getDates().getStart() < a.getDates().getStart();
}

void Problem::addProblem() {
  assert(owner);
  if ((owner->firstProblem && *this < *(owner->firstProblem)) ||
      !owner->firstProblem) {
    // Insert as the first problem in the list
    nextProblem = owner->firstProblem;
    owner->firstProblem = this;
  } else {
    // Insert in the middle or at the end of the list
    Problem* curProblem = owner->firstProblem->nextProblem;
    Problem* prevProblem = owner->firstProblem;
    while (curProblem && !(*this < *curProblem)) {
      prevProblem = curProblem;
      curProblem = curProblem->nextProblem;
    }
    nextProblem = curProblem;
    prevProblem->nextProblem = this;
  }
}

void Problem::removeProblem() {
  // Fast delete method: the code triggering this method is responsible of
  // maintaining the problem container
  if (!owner) return;

  if (owner->firstProblem == this)
    // Removal from the head of the list
    owner->firstProblem = nextProblem;
  else {
    // Removal from the middle of the list
    Problem* prev = owner->firstProblem;
    for (Problem* cur = owner->firstProblem; cur; cur = cur->nextProblem) {
      if (cur == this) {
        // Found it!
        prev->nextProblem = nextProblem;
        return;
      }
      prev = cur;
    }
    // The problem wasn't found in the list. This shouldn't happen...
    throw LogicException("Corrupted problem list");
  }
}

void Plannable::setDetectProblems(bool b) {
  if (useProblemDetection && !b)
    // We are switching from 'yes' to 'no': delete all existing problems
    Problem::clearProblems(*this);
  else if (!useProblemDetection && b)
    // We are switching from 'no' to 'yes': mark as changed for the next
    // problem detection call
    setChanged();
  // Update the flag
  useProblemDetection = b;
}

void Problem::List::transfer(HasProblems* newowner) {
  if (!newowner) return;
  if (!newowner->firstProblem) {
    newowner->firstProblem = first;
  } else {
    auto* ptr = newowner->firstProblem;
    while (ptr->nextProblem) ptr = ptr->nextProblem;
    ptr->nextProblem = first;
  }
  first = nullptr;
}

void Plannable::computeProblems() {
  // Exit immediately if the list is up to date
  if (!anyChange && !computationBusy) return;

  computationBusy = true;
  // Get exclusive access to this function in a multi-threaded environment.
  static mutex computationbusy;
  {
    lock_guard<mutex> l(computationbusy);

    // Another thread may already have computed it while this thread was
    // waiting for the lock
    while (anyChange) {
      // Reset to change flag. Note that during the computation the flag
      // could be switched on again by some model change in a different thread.
      anyChange = false;

      // Loop through all entities
      for (HasProblems::EntityIterator i; i != HasProblems::endEntity(); ++i) {
        Plannable* e = i->getEntity();
        if (e->getChanged() && e->getDetectProblems()) i->updateProblems();
      }

      // Mark the entities as unchanged
      for (HasProblems::EntityIterator j; j != HasProblems::endEntity(); ++j) {
        Plannable* e = j->getEntity();
        if (e->getChanged() && e->getDetectProblems()) e->setChanged(false);
      }
    }

    // Unlock the exclusive access to this function
    computationBusy = false;
  }
}

void Problem::clearProblems() {
  // Loop through all entities, and call clearProblems(i)
  for (HasProblems::EntityIterator i = HasProblems::beginEntity();
       i != HasProblems::endEntity(); ++i) {
    clearProblems(*i);
    i->getEntity()->setChanged(true);
  }
}

void Problem::clearConstraints(Object& p) {
  for (auto dmd = Demand::begin(); dmd != Demand::end(); ++dmd)
    dmd->getConstraints().erase(p);
}

void Problem::clearProblems(HasProblems& p, bool setchanged,
                            bool includeInvalidData) {
  // Nothing to do
  if (!p.firstProblem) return;

  // Delete all problems in the list
  Problem* keepfirst = nullptr;
  for (Problem* cur = p.firstProblem; cur;) {
    Problem* del = cur;
    cur = cur->nextProblem;
    if (includeInvalidData || typeid(*del) != typeid(ProblemInvalidData)) {
      del->owner = nullptr;
      delete del;
    } else if (!keepfirst) {
      keepfirst = del;
      if (keepfirst) keepfirst->nextProblem = del;
      del->nextProblem = nullptr;
    }
  }
  p.firstProblem = keepfirst;

  // Mark as changed
  if (setchanged) {
    auto tmp = p.getEntity();
    if (tmp) tmp->setChanged();
  }
}

Problem::iterator Plannable::getProblems() const {
  if (getChanged()) const_cast<Plannable*>(this)->updateProblems();
  return Problem::iterator(firstProblem);
}

HasProblems::EntityIterator::EntityIterator() : type(0) {
  // Buffer
  bufIter = new Buffer::iterator(Buffer::begin());
  if (*bufIter != Buffer::end()) return;

  // Move on to resource if there are no buffers
  delete bufIter;
  type = 1;
  resIter = new Resource::iterator(Resource::begin());
  if (*resIter != Resource::end()) return;

  // Move on to operationplans if there are no resources either
  delete resIter;
  type = 2;
  operIter = new OperationPlan::iterator(OperationPlan::begin());
  if (*operIter != OperationPlan::end()) return;

  // Move on to demands if there are no operationplans either
  delete operIter;
  type = 3;
  demIter = new Demand::iterator(Demand::begin());
  if (*demIter != Demand::end()) return;

  // Move on to operations if there are no demands either
  delete demIter;
  type = 4;
  opIter = new Operation::iterator(Operation::begin());
  if (*opIter == Operation::end()) {
    // There is nothing at all in this model
    delete opIter;
    type = 5;
  }
}

HasProblems::EntityIterator& HasProblems::EntityIterator::operator++() {
  switch (type) {
    case 0:
      // Buffer
      if (*bufIter != Buffer::end())
        if (++(*bufIter) != Buffer::end()) return *this;
      ++type;
      delete bufIter;
      resIter = new Resource::iterator(Resource::begin());
      if (*resIter != Resource::end()) return *this;
      // Note: no break statement
    case 1:
      // Resource
      if (*resIter != Resource::end())
        if (++(*resIter) != Resource::end()) return *this;
      ++type;
      delete resIter;
      operIter = new OperationPlan::iterator(OperationPlan::begin());
      if (*operIter != OperationPlan::end()) return *this;
      // Note: no break statement
    case 2:
      // Operationplan
      if (*operIter != OperationPlan::end())
        if (++(*operIter) != OperationPlan::end()) return *this;
      ++type;
      delete operIter;
      demIter = new Demand::iterator(Demand::begin());
      if (*demIter != Demand::end()) return *this;
      // Note: no break statement
    case 3:
      // Demand
      if (*demIter != Demand::end())
        if (++(*demIter) != Demand::end()) return *this;
      ++type;
      delete demIter;
      opIter = new Operation::iterator(Operation::begin());
      if (*opIter != Operation::end()) return *this;
      // Note: no break statement
    case 4:
      // Operation
      if (*opIter != Operation::end())
        if (++(*opIter) != Operation::end()) return *this;
      // Ended recursing of all entities
      ++type;
      delete opIter;
      opIter = nullptr;
      return *this;
  }
  throw LogicException("Unreachable code reached");
}

HasProblems::EntityIterator::~EntityIterator() {
  switch (type) {
    case 0:
      delete bufIter;
      return;
    case 1:
      delete resIter;
      return;
    case 2:
      delete operIter;
      return;
    case 3:
      delete demIter;
      return;
    case 4:
      delete opIter;
      return;
  }
}

HasProblems::EntityIterator::EntityIterator(const EntityIterator& o) {
  // Delete old iterator
  this->~EntityIterator();
  // Populate new values
  type = o.type;
  if (type == 0)
    bufIter = new Buffer::iterator(*(o.bufIter));
  else if (type == 1)
    resIter = new Resource::iterator(*(o.resIter));
  else if (type == 2)
    operIter = new OperationPlan::iterator(*(o.operIter));
  else if (type == 3)
    demIter = new Demand::iterator(*(o.demIter));
  else if (type == 4)
    opIter = new Operation::iterator(*(o.opIter));
}

HasProblems::EntityIterator& HasProblems::EntityIterator::operator=(
    const EntityIterator& o) {
  // Gracefully handle self assignment
  if (this == &o) return *this;
  // Delete old iterator
  this->~EntityIterator();
  // Populate new values
  type = o.type;
  if (type == 0)
    bufIter = new Buffer::iterator(*(o.bufIter));
  else if (type == 1)
    resIter = new Resource::iterator(*(o.resIter));
  else if (type == 2)
    operIter = new OperationPlan::iterator(*(o.operIter));
  else if (type == 3)
    demIter = new Demand::iterator(*(o.demIter));
  else if (type == 4)
    opIter = new Operation::iterator(*(o.opIter));
  return *this;
}

bool HasProblems::EntityIterator::operator!=(const EntityIterator& t) const {
  // Different iterator type, thus always different and return false
  if (type != t.type) return true;

  // Same iterator type, more granular comparison required
  switch (type) {
    case 0:
      return *bufIter != *(t.bufIter);
    case 1:
      return *resIter != *(t.resIter);
    case 2:
      return *operIter != *(t.operIter);
    case 3:
      return *demIter != *(t.demIter);
    case 4:
      return *opIter != *(t.opIter);
    default:
      // Always return true for higher type numbers. This should happen only
      // when comparing with the end of list element.
      return false;
  }
}

HasProblems& HasProblems::EntityIterator::operator*() const {
  switch (type) {
    case 0:
      return **bufIter;
    case 1:
      return **resIter;
    case 2:
      return **operIter;
    case 3:
      return **demIter;
    case 4:
      return **opIter;
    default:
      throw LogicException("Unknown problem entity found");
  }
}

HasProblems* HasProblems::EntityIterator::operator->() const {
  switch (type) {
    case 0:
      return &**bufIter;
    case 1:
      return &**resIter;
    case 2:
      return &**operIter;
    case 3:
      return &**demIter;
    case 4:
      return &**opIter;
    default:
      throw LogicException("Unknown problem entity found");
  }
}

HasProblems::EntityIterator HasProblems::beginEntity() {
  return EntityIterator();
}

HasProblems::EntityIterator HasProblems::endEntity() {
  // Note that we give call a constructor with type 5, in order to allow
  // a fast comparison.
  return EntityIterator(5);
}

Problem::iterator& Problem::iterator::operator++() {
  // Incrementing beyond the end
  if (!iter) return *this;

  // Move to the next problem
  iter = iter->nextProblem;

  // Move to the next entity
  // We need a while loop here because some entities can be without problems
  while (!iter && !owner && eiter && *eiter != HasProblems::endEntity()) {
    ++(*eiter);
    if (*eiter != HasProblems::endEntity()) iter = (*eiter)->firstProblem;
  }
  return *this;
}

Problem::iterator Problem::begin() { return iterator(); }

Problem::iterator Problem::begin(HasProblems* i, bool refresh) {
  // Null pointer passed, loop through the full list anyway
  if (!i) return begin();

  // Return an iterator for a single entity
  if (refresh) i->updateProblems();
  return iterator(i);
}

const Problem::iterator Problem::end() {
  return iterator(static_cast<Problem*>(nullptr));
}

void Problem::List::clear(Problem* c) {
  // Unchain the predecessor
  if (c) {
    for (Problem* x = first; x; x = x->nextProblem)
      if (x->nextProblem == c) {
        x->nextProblem = nullptr;
        break;
      }
  }

  // Delete each constraint in the list
  for (Problem* cur = c ? c : first; cur;) {
    Problem* del = cur;
    cur = cur->nextProblem;
    del->owner = nullptr;
    del->resetReferenceCount();
    delete del;
  }

  // Set the header to nullptr
  if (!c) first = nullptr;
}

void Problem::List::erase(Object& p) {
  Problem* prev = nullptr;
  for (Problem* x = first; x;) {
    if (x->getOwner() == &p ||
        (x->getOwner() && x->getOwner()->hasType<OperationPlan>() &&
         p.hasType<Operation>() &&
         static_cast<OperationPlan*>(x->getOwner())->getOperation() == &p)) {
      // Remove from the list
      auto tmp = x;
      if (prev)
        prev->nextProblem = x->nextProblem;
      else
        first = x->nextProblem;
      x = x->nextProblem;
      delete tmp;
    } else {
      prev = x;
      x = x->nextProblem;
    }
  }
}

Problem* Problem::List::push(const MetaClass* m, const Object* o, Date st,
                             Date nd, double w) {
  // Find the end of the list
  Problem* cur = first;
  while (cur && cur->nextProblem && cur->getOwner() != o)
    cur = cur->nextProblem;
  if (cur && cur->getOwner() == o)
    // Duplicate problem: stop here.
    return cur;

  // Create a new problem
  Problem* p;
  if (m == ProblemCapacityOverload::metadata)
    p = new ProblemCapacityOverload(
        const_cast<Resource*>(dynamic_cast<const Resource*>(o)), st, nd, w,
        false);
  else if (m == ProblemMaterialShortage::metadata)
    p = new ProblemMaterialShortage(
        const_cast<Buffer*>(dynamic_cast<const Buffer*>(o)), st, nd, w, false);
  else if (m == ProblemBeforeCurrent::metadata) {
    if (Plan::instance().getMinimalBeforeCurrentConstraints()) {
      // Keep only the most constraining before-current problem
      for (auto chck = first; chck && chck->nextProblem;
           chck = chck->nextProblem)
        if (chck->getType() == *ProblemBeforeCurrent::metadata) {
          static_cast<ProblemBeforeCurrent*>(chck)->update(
              const_cast<Operation*>(dynamic_cast<const Operation*>(o)), st, nd,
              w);
          return chck;
        }
    }
    p = new ProblemBeforeCurrent(
        const_cast<Operation*>(dynamic_cast<const Operation*>(o)), st, nd, w);
  } else if (m == ProblemBeforeFence::metadata) {
    if (Plan::instance().getMinimalBeforeCurrentConstraints()) {
      // Keep only the most constraining before-fence problem
      for (auto chck = first; chck && chck->nextProblem;
           chck = chck->nextProblem)
        if (chck->getType() == *ProblemBeforeFence::metadata) {
          static_cast<ProblemBeforeFence*>(chck)->update(
              const_cast<Operation*>(dynamic_cast<const Operation*>(o)), st, nd,
              w);
          return chck;
        }
    }
    p = new ProblemBeforeFence(
        const_cast<Operation*>(dynamic_cast<const Operation*>(o)), st, nd, w);
  } else if (m == ProblemAwaitSupply::metadata) {
    auto owner = const_cast<Buffer*>(dynamic_cast<const Buffer*>(o));
    if (owner)
      p = new ProblemAwaitSupply(owner, st, nd, w);
    else {
      auto owner = const_cast<Operation*>(dynamic_cast<const Operation*>(o));
      if (owner) p = new ProblemAwaitSupply(owner, st, nd, w);
    }
  } else if (m == ProblemSyncDemand::metadata)
    p = new ProblemSyncDemand(
        const_cast<Demand*>(dynamic_cast<const Demand*>(o)), st, nd, w);
  else
    throw LogicException("Problem factory can't create this type of problem");

  // Link the problem in the list
  if (cur)
    cur->nextProblem = p;
  else
    first = p;
  Py_INCREF(p);
  return p;
}

void Problem::List::pop(Problem* p) {
  Problem* q = nullptr;
  if (p) {
    // Skip the problem that was passed as argument
    q = p->nextProblem;
    p->nextProblem = nullptr;
  } else {
    // nullptr argument: delete all
    q = first;
    first = nullptr;
  }

  // Delete each constraint after the marked one
  while (q) {
    Problem* del = q;
    q = q->nextProblem;
    del->owner = nullptr;
    del->resetReferenceCount();
    delete del;
  }
}

Problem* Problem::List::top() const {
  for (Problem* p = first; p; p = p->nextProblem)
    if (!p->nextProblem) return p;
  return nullptr;
}

void Problem::List::push(Problem* p) {
  // Find the end of the list
  Problem* cur = first;
  while (cur && cur->nextProblem && cur != p) cur = cur->nextProblem;

  if (!cur)
    // Link at the start of the list
    first = p;
  else if (cur == p)
    // Duplicate problem: stop here.
    return;
  else
    // Link at the end of the list
    cur->nextProblem = p;
  Py_INCREF(p);
}

}  // namespace frepple
