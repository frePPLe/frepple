/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
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

namespace frepple
{

DECLARE_EXPORT bool Plannable::anyChange = false;
DECLARE_EXPORT bool Plannable::computationBusy = false;
DECLARE_EXPORT const MetaCategory* Problem::metadata;
DECLARE_EXPORT const MetaClass* ProblemMaterialExcess::metadata,
               *ProblemMaterialShortage::metadata,
               *ProblemExcess::metadata,
               *ProblemShort::metadata,
               *ProblemEarly::metadata,
               *ProblemLate::metadata,
               *ProblemInvalidData::metadata,
               *ProblemDemandNotPlanned::metadata,
               *ProblemPrecedence::metadata,
               *ProblemBeforeFence::metadata,
               *ProblemBeforeCurrent::metadata,
               *ProblemCapacityUnderload::metadata,
               *ProblemCapacityOverload::metadata;


int Problem::initialize()
{
  // Initialize the problem metadata.
  Problem::metadata = new MetaCategory
  ("problem", "problems", NULL, Problem::writer);
  ProblemMaterialExcess::metadata = new MetaClass
  ("problem","material excess");
  ProblemMaterialShortage::metadata = new MetaClass
  ("problem","material shortage");
  ProblemExcess::metadata = new MetaClass
  ("problem","excess");
  ProblemShort::metadata = new MetaClass
  ("problem","short");
  ProblemEarly::metadata = new MetaClass
  ("problem","early");
  ProblemLate::metadata = new MetaClass
  ("problem","late");
  ProblemInvalidData::metadata = new MetaClass
  ("problem","invalid data");
  ProblemDemandNotPlanned::metadata = new MetaClass
  ("problem","unplanned");
  ProblemPrecedence::metadata = new MetaClass
  ("problem","precedence");
  ProblemBeforeFence::metadata = new MetaClass
  ("problem","before fence");
  ProblemBeforeCurrent::metadata = new MetaClass
  ("problem","before current");
  ProblemCapacityUnderload::metadata = new MetaClass
  ("problem","underload");
  ProblemCapacityOverload::metadata = new MetaClass
  ("problem","overload");

  // Initialize the Python type
  PythonType& x = PythonExtension<Problem>::getType();
  x.setName("problem");
  x.setDoc("frePPLe problem");
  x.supportgetattro();
  x.supportstr();
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaCategory*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT bool Problem::operator < (const Problem& a) const
{
  // 1. Sort based on entity
  assert(owner == a.owner);

  // 2. Sort based on type
  if (getType() != a.getType()) return getType() < a.getType();

  // 3. Sort based on start date
  return getDates().getStart() < a.getDates().getStart();
}


DECLARE_EXPORT void Problem::addProblem()
{
  assert(owner);
  if ((owner->firstProblem && *this < *(owner->firstProblem))
      || !owner->firstProblem)
  {
    // Insert as the first problem in the list
    nextProblem = owner->firstProblem;
    owner->firstProblem = this;
  }
  else
  {
    // Insert in the middle or at the end of the list
    Problem* curProblem = owner->firstProblem->nextProblem;
    Problem* prevProblem = owner->firstProblem;
    while (curProblem && !(*this < *curProblem))
    {
      prevProblem = curProblem;
      curProblem = curProblem->nextProblem;
    }
    nextProblem = curProblem;
    prevProblem->nextProblem = this;
  }
}


DECLARE_EXPORT void Problem::removeProblem()
{
  // Fast delete method: the code triggering this method is responsible of
  // maintaining the problem container
  if (!owner) return;

  if (owner->firstProblem == this)
    // Removal from the head of the list
    owner->firstProblem = nextProblem;
  else
  {
    // Removal from the middle of the list
    Problem *prev = owner->firstProblem;
    for (Problem* cur = owner->firstProblem; cur; cur=cur->nextProblem)
    {
      if (cur == this)
      {
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


DECLARE_EXPORT void Plannable::setDetectProblems(bool b)
{
  if (useProblemDetection && !b)
    // We are switching from 'yes' to 'no': delete all existing problems
    Problem::clearProblems(*this);
  else if (!useProblemDetection && b)
    // We are switching from 'no' to 'yes': mark as changed for the next
    // problem detection call
    setChanged();
  // Update the flag
  useProblemDetection=b;
}


DECLARE_EXPORT void Plannable::computeProblems()
{
  // Exit immediately if the list is up to date
  if (!anyChange && !computationBusy) return;

  computationBusy = true;
  // Get exclusive access to this function in a multi-threaded environment.
  static Mutex computationbusy;
  {
    ScopeMutexLock l(computationbusy);

    // Another thread may already have computed it while this thread was
    // waiting for the lock
    while (anyChange)
    {
      // Reset to change flag. Note that during the computation the flag
      // could be switched on again by some model change in a different thread.
      anyChange = false;

      // Loop through all entities
      for (HasProblems::EntityIterator i; i!=HasProblems::endEntity(); ++i)
      {
        Plannable *e = i->getEntity();
        if (e->getChanged() && e->getDetectProblems()) i->updateProblems();
      }

      // Mark the entities as unchanged
      for (HasProblems::EntityIterator j; j!=HasProblems::endEntity(); ++j)
      {
        Plannable *e = j->getEntity();
        if (e->getChanged() && e->getDetectProblems()) e->setChanged(false);
      }
    }

    // Unlock the exclusive access to this function
    computationBusy = false;
  }
}


DECLARE_EXPORT void Plannable::writeElement (Serializer* o, const Keyword& tag, mode m) const
{
  // We don't bother about the mode, since this method is only called from
  // within the writeElement() method of other classes.

  // Problem detection flag only written if different from the default value
  if (!getDetectProblems()) o->writeElement(Tags::tag_detectproblems, false);
}


DECLARE_EXPORT void Plannable::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA (Tags::tag_detectproblems))
  {
    bool b = pElement.getBool();
    setDetectProblems(b);
  }
}


DECLARE_EXPORT void Problem::clearProblems()
{
  // Loop through all entities, and call clearProblems(i)
  for (HasProblems::EntityIterator i = HasProblems::beginEntity();
      i != HasProblems::endEntity(); ++i)
  {
    clearProblems(*i);
    i->getEntity()->setChanged(true);
  }
}


DECLARE_EXPORT void Problem::clearProblems(HasProblems& p, bool setchanged)
{
  // Nothing to do
  if (!p.firstProblem) return;

  // Delete all problems in the list
  for (Problem *cur=p.firstProblem; cur; )
  {
    Problem *del = cur;
    cur = cur->nextProblem;
    del->owner = NULL;
    delete del;
  }
  p.firstProblem = NULL;

  // Mark as changed
  if (setchanged) p.getEntity()->setChanged();
}


DECLARE_EXPORT void Problem::writer(const MetaCategory* c, Serializer* o)
{
  const_iterator piter = begin();
  if (piter != end())
  {
    o->BeginList(*c->grouptag);
    for (; piter!=end(); ++piter)
      // Note: not the regular write, but a fast write to speed things up.
      // This is possible since problems aren't nested and are never
      // referenced.
      piter->writeElement(o, *c->typetag);
    o->EndList(*c->grouptag);
  }
}


DECLARE_EXPORT void Problem::writeElement(Serializer *o, const Keyword& tag, mode m) const
{
  // We ignore the mode, and always write the complete model
  o->BeginObject(tag);
  o->writeElement(Tags::tag_name, getType().type);
  o->writeElement(Tags::tag_description, getDescription());
  o->writeElement(Tags::tag_start, getDates().getStart());
  o->writeElement(Tags::tag_end, getDates().getEnd());
  o->writeElement(Tags::tag_weight, getWeight());
  o->EndObject(tag);
}


DECLARE_EXPORT HasProblems::EntityIterator::EntityIterator() : type(0)
{
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
  if (*demIter == Demand::end())
  {
    // There is nothing at all in this model
    delete demIter;
    type = 4;
  }
}


DECLARE_EXPORT HasProblems::EntityIterator& HasProblems::EntityIterator::operator++()
{
  switch (type)
  {
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
      // Ended recursing of all entities
      ++type;
      delete demIter;
      demIter = NULL;
      return *this;
  }
  throw LogicException("Unreachable code reached");
}


DECLARE_EXPORT HasProblems::EntityIterator::~EntityIterator()
{
  switch (type)
  {
      // Buffer
    case 0: delete bufIter; return;
      // Resource
    case 1: delete resIter; return;
      // Operation
    case 2: delete operIter; return;
      // Demand
    case 3: delete demIter; return;
  }
}


DECLARE_EXPORT HasProblems::EntityIterator::EntityIterator(const EntityIterator& o)
{
  // Delete old iterator
  this->~EntityIterator();
  // Populate new values
  type = o.type;
  if (type==0) bufIter = new Buffer::iterator(*(o.bufIter));
  else if (type==1) resIter = new Resource::iterator(*(o.resIter));
  else if (type==2) operIter = new OperationPlan::iterator(*(o.operIter));
  else if (type==3) demIter = new Demand::iterator(*(o.demIter));
}


DECLARE_EXPORT HasProblems::EntityIterator&
HasProblems::EntityIterator::operator=(const EntityIterator& o)
{
  // Gracefully handle self assignment
  if (this == &o) return *this;
  // Delete old iterator
  this->~EntityIterator();
  // Populate new values
  type = o.type;
  if (type==0) bufIter = new Buffer::iterator(*(o.bufIter));
  else if (type==1) resIter = new Resource::iterator(*(o.resIter));
  else if (type==2) operIter = new OperationPlan::iterator(*(o.operIter));
  else if (type==3) demIter = new Demand::iterator(*(o.demIter));
  return *this;
}


DECLARE_EXPORT bool
HasProblems::EntityIterator::operator != (const EntityIterator& t) const
{
  // Different iterator type, thus always different and return false
  if (type != t.type) return true;

  // Same iterator type, more granular comparison required
  switch (type)
  {
      // Buffer
    case 0: return *bufIter != *(t.bufIter);
      // Resource
    case 1: return *resIter != *(t.resIter);
      // Operationplan
    case 2: return *operIter != *(t.operIter);
      // Demand
    case 3: return *demIter != *(t.demIter);
      // Always return true for higher type numbers. This should happen only
      // when comparing with the end of list element.
    default: return false;
  }
}


DECLARE_EXPORT HasProblems& HasProblems::EntityIterator::operator*() const
{
  switch (type)
  {
      // Buffer
    case 0: return **bufIter;
      // Resource
    case 1: return **resIter;
      // Operation
    case 2: return **operIter;
      // Demand
    case 3: return **demIter;
    default: throw LogicException("Unreachable code reached");
  }
}


DECLARE_EXPORT HasProblems* HasProblems::EntityIterator::operator->() const
{
  switch (type)
  {
      // Buffer
    case 0: return &**bufIter;
      // Resource
    case 1: return &**resIter;
      // Operationplan
    case 2: return &**operIter;
      // Demand
    case 3: return &**demIter;
    default: throw LogicException("Unreachable code reached");
  }
}


DECLARE_EXPORT HasProblems::EntityIterator HasProblems::beginEntity()
{
  return EntityIterator();
}


DECLARE_EXPORT HasProblems::EntityIterator HasProblems::endEntity()
{
  // Note that we give call a constructor with type 4, in order to allow
  // a fast comparison.
  return EntityIterator(4);
}


DECLARE_EXPORT Problem::const_iterator& Problem::const_iterator::operator++()
{
  // Incrementing beyond the end
  if (!iter) return *this;

  // Move to the next problem
  iter = iter->nextProblem;

  // Move to the next entity
  // We need a while loop here because some entities can be without problems
  while (!iter && !owner && eiter!=HasProblems::endEntity())
  {
    ++eiter;
    if (eiter!=HasProblems::endEntity()) iter = eiter->firstProblem;
  }
  return *this;
}


DECLARE_EXPORT Problem::const_iterator Problem::begin()
{
  Plannable::computeProblems();
  return const_iterator();
}


DECLARE_EXPORT Problem::const_iterator Problem::begin(HasProblems* i, bool refresh)
{
  // Null pointer passed, loop through the full list anyway
  if (!i) return begin();

  // Return an iterator for a single entity
  if (refresh) i->updateProblems();
  return const_iterator(i);
}


DECLARE_EXPORT const Problem::const_iterator Problem::end()
{
  return const_iterator(static_cast<Problem*>(NULL));
}


PyObject* Problem::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_name))
    return PythonObject(getType().type);
  if (attr.isA(Tags::tag_description))
    return PythonObject(getDescription());
  if (attr.isA(Tags::tag_entity))
    return PythonObject(getEntity());
  if (attr.isA(Tags::tag_start))
    return PythonObject(getDates().getStart());
  if (attr.isA(Tags::tag_end))
    return PythonObject(getDates().getEnd());
  if (attr.isA(Tags::tag_weight))
    return PythonObject(getWeight());
  if (attr.isA(Tags::tag_owner))
    return PythonObject(getOwner());
  return NULL;
}


DECLARE_EXPORT void Problem::List::clear(Problem *c)
{
  // Unchain the predecessor
  if (c)
  {
    for (Problem *x = first; x; x = x->nextProblem)
      if (x->nextProblem == c)
      {
        x->nextProblem = NULL;
        break;
      }
  }

  // Delete each constraint in the list
  for (Problem *cur = c ? c : first; cur; )
  {
    Problem *del = cur;
    cur = cur->nextProblem;
    del->owner = NULL;
    delete del;
  }

  // Set the header to NULL
  if (!c) first = NULL;
}


DECLARE_EXPORT Problem* Problem::List::push(const MetaClass* m,
    const Object* o, Date st, Date nd, double w)
{
  // Find the end of the list
  Problem* cur = first;
  while (cur && cur->nextProblem && cur->getOwner() != o)
    cur = cur->nextProblem;
  if (cur && cur->getOwner() == o)
    // Duplicate problem: stop here.
    return cur;

  // Create a new problem
  Problem *p;
  if (m == ProblemCapacityOverload::metadata)
    p = new ProblemCapacityOverload(const_cast<Resource*>(dynamic_cast<const Resource*>(o)), st, nd, w, false);
  else if (m == ProblemMaterialShortage::metadata)
    p = new ProblemMaterialShortage(const_cast<Buffer*>(dynamic_cast<const Buffer*>(o)), st, nd, w, false);
  else if (m == ProblemBeforeCurrent::metadata)
    p = new ProblemBeforeCurrent(const_cast<Operation*>(dynamic_cast<const Operation*>(o)), st, nd, w);
  else if (m == ProblemBeforeFence::metadata)
    p = new ProblemBeforeFence(const_cast<Operation*>(dynamic_cast<const Operation*>(o)), st, nd, w);
  else
    throw LogicException("Problem factory can't create this type of problem");

  // Link the problem in the list
  if (cur)
    cur->nextProblem = p;
  else
    first = p;
  return p;
}


DECLARE_EXPORT void Problem::List::pop(Problem *p)
{
  Problem *q = NULL;
  if (p)
  {
    // Skip the problem that was passed as argument
    q = p->nextProblem;
    p->nextProblem = NULL;
  }
  else
  {
    // NULL argument: delete all
    q = first;
    first = NULL;
  }

  // Delete each constraint after the marked one
  while (q)
  {
    Problem *del = q;
    q = q->nextProblem;
    del->owner = NULL;
    delete del;
  }
}


DECLARE_EXPORT Problem* Problem::List::top() const
{
  for (Problem *p = first; p; p = p->nextProblem)
    if (!p->nextProblem) return p;
  return NULL;
}


} // End namespace
