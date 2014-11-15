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

DECLARE_EXPORT const MetaCategory* Load::metadata;


int Load::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory
  ("load", "loads", MetaCategory::ControllerDefault, writer);
  const_cast<MetaCategory*>(metadata)->registerClass(
    "load","load",true,Object::createDefault<Load>
  );

  // Initialize the Python class
  PythonType& x = FreppleCategory<Load>::getType();
  x.setName("load");
  x.setDoc("frePPLe load");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaCategory*>(Load::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


void Load::writer(const MetaCategory* c, XMLOutput* o)
{
  bool firstload = true;
  for (Operation::iterator i = Operation::begin(); i != Operation::end(); ++i)
    for (Operation::loadlist::const_iterator j = i->getLoads().begin(); j != i->getLoads().end(); ++j)
    {
      if (firstload)
      {
        o->BeginObject(Tags::tag_loads);
        firstload = false;
      }
      // We use the FULL mode, to force the loads being written regardless
      // of the depth in the XML tree.
      o->writeElement(Tags::tag_load, &*j, FULL);
    }
  if (!firstload) o->EndObject(Tags::tag_loads);
}


DECLARE_EXPORT void Load::validate(Action action)
{
  // Catch null operation and resource pointers
  Operation *oper = getOperation();
  Resource *res = getResource();
  if (!oper || !res)
  {
    // Invalid load model
    if (!oper && !res)
      throw DataException("Missing operation and resource on a load");
    else if (!oper)
      throw DataException("Missing operation on a load on resource '"
          + res->getName() + "'");
    else if (!res)
      throw DataException("Missing resource on a load on operation '"
          + oper->getName() + "'");
  }

  // Check if a load with 1) identical resource, 2) identical operation and
  // 3) overlapping effectivity dates already exists
  Operation::loadlist::const_iterator i = oper->getLoads().begin();
  for (; i != oper->getLoads().end(); ++i)
    if (i->getResource() == res
        && i->getEffective().overlap(getEffective())
        && &*i != this)
      break;

  // Apply the appropriate action
  switch (action)
  {
    case ADD:
      if (i != oper->getLoads().end())
      {
        throw DataException("Load of '" + oper->getName() + "' and '"
            + res->getName() + "' already exists");
      }
      break;
    case CHANGE:
      throw DataException("Can't update a load");
    case ADD_CHANGE:
      // ADD is handled in the code after the switch statement
      if (i == oper->getLoads().end()) break;
      throw DataException("Can't update a load");
    case REMOVE:
      // This load was only used temporarily during the reading process
      delete this;
      if (i == oper->getLoads().end())
        // Nothing to delete
        throw DataException("Can't remove nonexistent load of '"
            + oper->getName() + "' and '" + res->getName() + "'");
      delete &*i;
      // Set a flag to make sure the level computation is triggered again
      HasLevel::triggerLazyRecomputation();
      return;
  }

  // The statements below should be executed only when a new load is created.

  // Set a flag to make sure the level computation is triggered again
  HasLevel::triggerLazyRecomputation();
}


DECLARE_EXPORT Load::~Load()
{
  // Set a flag to make sure the level computation is triggered again
  HasLevel::triggerLazyRecomputation();

  // Delete existing loadplans
  if (getOperation() && getResource())
  {
    // Loop over operationplans
    for(OperationPlan::iterator i(getOperation()); i != OperationPlan::end(); ++i)
      // Loop over loadplans
      for(OperationPlan::LoadPlanIterator j = i->beginLoadPlans(); j != i->endLoadPlans(); )
        if (j->getLoad() == this) j.deleteLoadPlan();
        else ++j;
  }

  // Delete the load from the operation and resource
  if (getOperation()) getOperation()->loaddata.erase(this);
  if (getResource()) getResource()->loads.erase(this);

  // Clean up alternate loads
  if (hasAlts)
  {
    // The load has alternates.
    // Make a new load the leading one. Or if there is only one alternate
    // present it is not marked as an alternate any more.
    unsigned short cnt = 0;
    int minprio = INT_MAX;
    Load* newLeader = NULL;
    for (Operation::loadlist::iterator i = getOperation()->loaddata.begin();
        i != getOperation()->loaddata.end(); ++i)
      if (i->altLoad == this)
      {
        cnt++;
        if (i->priority < minprio)
        {
          newLeader = &*i;
          minprio = i->priority;
        }
      }
    if (cnt < 1)
      throw LogicException("Alternate loads update failure");
    else if (cnt == 1)
      // No longer an alternate any more
      newLeader->altLoad = NULL;
    else
    {
      // Mark a new leader load
      newLeader->hasAlts = true;
      newLeader->altLoad = NULL;
      for (Operation::loadlist::iterator i = getOperation()->loaddata.begin();
          i != getOperation()->loaddata.end(); ++i)
        if (i->altLoad == this) i->altLoad = newLeader;
    }
  }
  if (altLoad)
  {
    // The load is an alternate of another one.
    // If it was the only alternate, then the hasAlts flag on the parent
    // load needs to be set back to false
    bool only_one = true;
    for (Operation::loadlist::iterator i = getOperation()->loaddata.begin();
        i != getOperation()->loaddata.end(); ++i)
      if (i->altLoad == altLoad)
      {
        only_one = false;
        break;
      }
    if (only_one) altLoad->hasAlts = false;
  }
}


DECLARE_EXPORT void Load::setAlternate(Load *f)
{
  // Can't be an alternate to oneself.
  // No need to flag as an exception.
  if (f == this) return;

  // Validate the argument
  if (!f)
    throw DataException("Setting NULL alternate load");
  if (hasAlts || f->altLoad)
    throw DataException("Nested alternate loads are not allowed");

  // Update both flows
  f->hasAlts = true;
  altLoad = f;
}


DECLARE_EXPORT void Load::setAlternate(const string& n)
{
  if (!getOperation())
    throw LogicException("Can't set an alternate load before setting the operation");
  Load *x = getOperation()->loaddata.find(n);
  if (!x) throw DataException("Can't find load with name '" + n + "'");
  setAlternate(x);
}


DECLARE_EXPORT void Load::setSetup(const string n)
{
  setup = n;

  if (!setup.empty())
  {
    // Guarantuee that only a single load has a setup.
    // Alternates of that load can have a setup as well.
    for (Operation::loadlist::iterator i = getOperation()->loaddata.begin();
        i != getOperation()->loaddata.end(); ++i)
      if (&*i != this && !i->setup.empty()
          && i->getAlternate() != this && getAlternate() != &*i
          && i->getAlternate() != getAlternate())
        throw DataException("Only a single load of an operation can specify a setup");
  }
}


DECLARE_EXPORT void Load::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
{
  // If the load has already been saved, no need to repeat it again
  // A 'reference' to a load is not useful to be saved.
  if (m == REFERENCE) return;
  assert(m != NOHEAD && m != NOHEADTAIL);

  o->BeginObject(tag);

  // If the load is defined inside of an operation tag, we don't need to save
  // the operation. Otherwise we do save it...
  if (!dynamic_cast<Operation*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_operation, getOperation());

  // If the load is defined inside of an resource tag, we don't need to save
  // the resource. Otherwise we do save it...
  if (!dynamic_cast<Resource*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_resource, getResource());

  // Write the quantity, priority, name and alternate
  if (qty != 1.0) o->writeElement(Tags::tag_quantity, qty);
  if (getPriority()!=1) o->writeElement(Tags::tag_priority, getPriority());
  if (!getName().empty()) o->writeElement(Tags::tag_name, getName());
  if (getAlternate())
    o->writeElement(Tags::tag_alternate, getAlternate()->getName());
  if (search != PRIORITY)
  {
    ostringstream ch;
    ch << getSearch();
    o->writeElement(Tags::tag_search, ch.str());
  }

  // Write the effective daterange
  if (getEffective().getStart() != Date::infinitePast)
    o->writeElement(Tags::tag_effective_start, getEffective().getStart());
  if (getEffective().getEnd() != Date::infiniteFuture)
    o->writeElement(Tags::tag_effective_end, getEffective().getEnd());

  // Write the required setup
  if (!setup.empty()) o->writeElement(Tags::tag_setup, setup);

  // Write the required skill
  if (skill) o->writeElement(Tags::tag_skill, skill);

  // Write source field
  o->writeElement(Tags::tag_source, getSource());

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void Load::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_resource))
    pIn.readto( Resource::reader(Resource::metadata,pIn.getAttributes()) );
  else if (pAttr.isA (Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else if (pAttr.isA (Tags::tag_skill))
    pIn.readto( Skill::reader(Skill::metadata,pIn.getAttributes()) );
  else
    PythonDictionary::read(pIn, pAttr, getDict());
}


DECLARE_EXPORT void Load::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA (Tags::tag_resource))
  {
    Resource *r = dynamic_cast<Resource*>(pIn.getPreviousObject());
    if (r) setResource(r);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA (Tags::tag_operation))
  {
    Operation *o = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (o) setOperation(o);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_quantity))
    setQuantity(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_priority))
    setPriority(pElement.getInt());
  else if (pAttr.isA(Tags::tag_name))
    setName(pElement.getString());
  else if (pAttr.isA(Tags::tag_alternate))
    setAlternate(pElement.getString());
  else if (pAttr.isA(Tags::tag_search))
    setSearch(pElement.getString());
  else if (pAttr.isA(Tags::tag_setup))
    setSetup(pElement.getString());
  else if (pAttr.isA(Tags::tag_action))
  {
    delete static_cast<Action*>(pIn.getUserArea());
    pIn.setUserArea(
      new Action(MetaClass::decodeAction(pElement.getString().c_str()))
    );
  }
  else if (pAttr.isA(Tags::tag_effective_end))
    setEffectiveEnd(pElement.getDate());
  else if (pAttr.isA(Tags::tag_effective_start))
    setEffectiveStart(pElement.getDate());
  else if (pAttr.isA (Tags::tag_skill))
  {
    Skill *s = dynamic_cast<Skill*>(pIn.getPreviousObject());
    if (s) setSkill(s);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_source))
    setSource(pElement.getString());
  else if (pIn.isObjectEnd())
  {
    // The load data is now all read in. See if it makes sense now...
    Action a = pIn.getUserArea() ?
        *static_cast<Action*>(pIn.getUserArea()) :
        ADD_CHANGE;
    delete static_cast<Action*>(pIn.getUserArea());
    try { validate(a); }
    catch (...)
    {
      delete this;
      throw;
    }
  }
}


DECLARE_EXPORT PyObject* Load::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_resource))
    return PythonObject(getResource());
  if (attr.isA(Tags::tag_operation))
    return PythonObject(getOperation());
  if (attr.isA(Tags::tag_quantity))
    return PythonObject(getQuantity());
  if (attr.isA(Tags::tag_priority))
    return PythonObject(getPriority());
  if (attr.isA(Tags::tag_effective_end))
    return PythonObject(getEffective().getEnd());
  if (attr.isA(Tags::tag_effective_start))
    return PythonObject(getEffective().getStart());
  if (attr.isA(Tags::tag_name))
    return PythonObject(getName());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(getHidden());
  if (attr.isA(Tags::tag_alternate))
    return PythonObject(getAlternate());
  if (attr.isA(Tags::tag_search))
  {
    ostringstream ch;
    ch << getSearch();
    return PythonObject(ch.str());
  }
  if (attr.isA(Tags::tag_setup))
    return PythonObject(getSetup());
  if (attr.isA(Tags::tag_skill))
    return PythonObject(getSkill());
  if (attr.isA(Tags::tag_source))
    return PythonObject(getSource());
  return NULL;
}


DECLARE_EXPORT int Load::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_resource))
  {
    if (!field.check(Resource::metadata))
    {
      PyErr_SetString(PythonDataException, "load resource must be of type resource");
      return -1;
    }
    Resource* y = static_cast<Resource*>(static_cast<PyObject*>(field));
    setResource(y);
  }
  else if (attr.isA(Tags::tag_operation))
  {
    if (!field.check(Operation::metadata))
    {
      PyErr_SetString(PythonDataException, "load operation must be of type operation");
      return -1;
    }
    Operation* y = static_cast<Operation*>(static_cast<PyObject*>(field));
    setOperation(y);
  }
  else if (attr.isA(Tags::tag_quantity))
    setQuantity(field.getDouble());
  else if (attr.isA(Tags::tag_priority))
    setPriority(field.getInt());
  else if (attr.isA(Tags::tag_effective_end))
    setEffectiveEnd(field.getDate());
  else if (attr.isA(Tags::tag_effective_start))
    setEffectiveStart(field.getDate());
  else if (attr.isA(Tags::tag_name))
    setName(field.getString());
  else if (attr.isA(Tags::tag_alternate))
  {
    if (!field.check(Load::metadata))
      setAlternate(field.getString());
    else
    {
      Load *y = static_cast<Load*>(static_cast<PyObject*>(field));
      setAlternate(y);
    }
  }
  else if (attr.isA(Tags::tag_search))
    setSearch(field.getString());
  else if (attr.isA(Tags::tag_setup))
    setSetup(field.getString());
  else if (attr.isA(Tags::tag_skill))
  {
    if (!field.check(Skill::metadata))
    {
      PyErr_SetString(PythonDataException, "load skill must be of type skill");
      return -1;
    }
    Skill* y = static_cast<Skill*>(static_cast<PyObject*>(field));
    setSkill(y);
  }
  else if (attr.isA(Tags::tag_source))
    setSource(field.getString());
  else
    return -1;
  return 0;
}


PyObject* Load::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Pick up the operation
    PyObject* oper = PyDict_GetItemString(kwds,"operation");
    if (!PyObject_TypeCheck(oper, Operation::metadata->pythonClass))
      throw DataException("load operation must be of type operation");

    // Pick up the resource
    PyObject* res = PyDict_GetItemString(kwds,"resource");
    if (!PyObject_TypeCheck(res, Resource::metadata->pythonClass))
      throw DataException("load resource must be of type resource");

    // Pick up the quantity
    PyObject* q1 = PyDict_GetItemString(kwds,"quantity");
    double q2 = q1 ? PythonObject(q1).getDouble() : 1.0;

    // Pick up the effective dates
    DateRange eff;
    PyObject* eff_start = PyDict_GetItemString(kwds,"effective_start");
    if (eff_start)
    {
      PythonObject d(eff_start);
      eff.setStart(d.getDate());
    }
    PyObject* eff_end = PyDict_GetItemString(kwds,"effective_end");
    if (eff_end)
    {
      PythonObject d(eff_end);
      eff.setEnd(d.getDate());
    }

    // Create the load
    Load *l = new Load(
      static_cast<Operation*>(oper),
      static_cast<Resource*>(res),
      q2, eff
    );

    // Iterate over extra keywords, and set attributes.   @todo move this responsibility to the readers...
    if (l)
    {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value))
      {
        PythonObject field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        Attribute attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::tag_effective_end) && !attr.isA(Tags::tag_effective_start)
          && !attr.isA(Tags::tag_operation) && !attr.isA(Tags::tag_resource)
          && !attr.isA(Tags::tag_quantity) && !attr.isA(Tags::tag_type)
          && !attr.isA(Tags::tag_action))
        {
          int result = l->setattro(attr, field);
          if (result && !PyErr_Occurred())
            PyErr_Format(PyExc_AttributeError,
                "attribute '%S' on '%s' can't be updated",
                key, Py_TYPE(l)->tp_name);
        }
      };
    }

    // Return the object
    Py_INCREF(l);
    return static_cast<PyObject*>(l);
  }
  catch (...)
  {
    PythonType::evalException();
    return NULL;
  }
}


int LoadIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<LoadIterator>::getType();
  x.setName("loadIterator");
  x.setDoc("frePPLe iterator for loads");
  x.supportiter();
  return x.typeReady();
}


PyObject* LoadIterator::iternext()
{
  PyObject* result;
  if (res)
  {
    // Iterate over loads on a resource
    if (ir == res->getLoads().end()) return NULL;
    result = const_cast<Load*>(&*ir);
    ++ir;
  }
  else
  {
    // Iterate over loads on an operation
    if (io == oper->getLoads().end()) return NULL;
    result = const_cast<Load*>(&*io);
    ++io;
  }
  Py_INCREF(result);
  return result;
}

} // end namespace
