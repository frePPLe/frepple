/***************************************************************************
 *                                                                         *
 * Copyright (C) 2015 by frePPLe bvba                                      *
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

DECLARE_EXPORT const MetaCategory* ItemDistribution::metacategory;
DECLARE_EXPORT const MetaClass* ItemDistribution::metadata;
DECLARE_EXPORT const MetaClass* OperationItemDistribution::metadata;


int ItemDistribution::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<ItemDistribution>(
	  "itemdistribution", "itemdistributions", MetaCategory::ControllerDefault
	  );
  metadata = MetaClass::registerClass<ItemDistribution>(
    "itemdistribution", "itemdistribution", Object::create<ItemDistribution>, true
  );
  registerFields<ItemDistribution>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<ItemDistribution>::getPythonType();
  x.setName("itemdistribution");
  x.setDoc("frePPLe itemdistribution");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(ItemDistribution::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT ItemDistribution::ItemDistribution() : it(NULL),
  size_minimum(1.0), size_multiple(0.0), cost(0.0), firstOperation(NULL),
  next(NULL)
{
  initType(metadata);

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}


DECLARE_EXPORT ItemDistribution::~ItemDistribution()
{
  // Delete the association from the related objects
  if (getOrigin())
    getOrigin()->origins.erase(this);
  if (getDestination())
    getDestination()->destinations.erase(this);

  // Delete all owned distribution operations
  while (firstOperation)
    delete firstOperation;

  // Unlink from previous item
  if (it)
  {
    if (it->firstItemDistribution == this)
      // Remove from head
      it->firstItemDistribution = next;
    else
    {
      // Remove from middle
      ItemDistribution *j = it->firstItemDistribution;
      while (j->next && j->next != this)
        j = j->next;
      if (j)
        j->next = next;
      else
        throw LogicException("Corrupted ItemDistribution list");
    }
  }

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}


DECLARE_EXPORT void ItemDistribution::setItem(Item* i)
{
  // Unlink from previous item
  if (it)
  {
    if (it->firstItemDistribution == this)
      // Remove from head
      it->firstItemDistribution = next;
    else
    {
      // Remove from middle
      ItemDistribution *j = it->firstItemDistribution;
      while (j->next && j->next != this)
        j = j->next;
      if (j)
        j->next = next;
      else
        throw LogicException("Corrupted ItemDistribution list");
    }
  }

  // Update item
  it = i;

  // Link at the new owner.
  // We insert ourself at the head of the list.
  if (it)
  {
    next = it->firstItemDistribution;
    it->firstItemDistribution = this;
  }

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}


PyObject* ItemDistribution::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Pick up the item
    PyObject* it = PyDict_GetItemString(kwds,"item");
    if (!it)
      throw DataException("missing item on ItemDistribution");
    if (!PyObject_TypeCheck(it, Item::metadata->pythonClass))
      throw DataException("ItemDistribution item must be of type item");

    /* XXX
    // Pick up the priority
    PyObject* q1 = PyDict_GetItemString(kwds,"priority");
    int q2 = q1 ? PythonData(q1).getInt() : 1;

    // Pick up the effective dates
    DateRange eff;
    PyObject* eff_start = PyDict_GetItemString(kwds,"effective_start");
    if (eff_start)
    {
      PythonData d(eff_start);
      eff.setStart(d.getDate());
    }
    PyObject* eff_end = PyDict_GetItemString(kwds,"effective_end");
    if (eff_end)
    {
      PythonData d(eff_end);
      eff.setEnd(d.getDate());
    }
    */

    // Create the ItemDistribution
    ItemDistribution *l = new ItemDistribution();
    l->setItem(static_cast<Item*>(it));

    // Iterate over extra keywords, and set attributes.   @todo move this responsibility to the readers...
    if (l)
    {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value))
      {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::item) && !attr.isA(Tags::type)
          && !attr.isA(Tags::action))
        {
          const MetaFieldBase* fmeta = l->getType().findField(attr.getHash());
          if (!fmeta && l->getType().category)
            fmeta = l->getType().category->findField(attr.getHash());
          if (fmeta)
            // Update the attribute
            fmeta->setField(l, field);
          else
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


DECLARE_EXPORT void ItemDistribution::validate(Action action)
{
  // Catch null supplier and item pointers
  Item *it = getItem();
  if (!it)
    throw DataException("Missing item on a ItemDistribution");

  /* XXX
  // Check if an ItemDistribution with 1) identical item, 2) identical origin
  // 3) identical destination, and 4) overlapping effectivity dates already exists
  Location::distributionoriginlist::const_iterator i = sup->getItems().begin();
  for (; i != sup->getItems().end(); ++i)
    if (i->getItem() == it
        && i->getEffective().overlap(getEffective())
        && i->getLocation() == loc
        && &*i != this)
      break;

  // Apply the appropriate action
  switch (action)
  {
    case ADD:
      if (i != sup->getItems().end())
      {
        throw DataException("ItemSupplier of '" + sup->getName() + "' and '"
            + it->getName() + "' already exists");
      }
      break;
    case CHANGE:
      throw DataException("Can't update a ItemSupplier");
    case ADD_CHANGE:
      // ADD is handled in the code after the switch statement
      if (i == sup->getItems().end()) break;
      throw DataException("Can't update a ItemSupplier");
    case REMOVE:
      // This ItemSupplier was only used temporarily during the reading process
      delete this;
      if (i == sup->getItems().end())
        // Nothing to delete
        throw DataException("Can't remove nonexistent ItemSupplier of '"
            + sup->getName() + "' and '" + it->getName() + "'");
      delete &*i;
      return;
  }
  */
}


DECLARE_EXPORT void ItemDistribution::deleteOperationPlans(bool b)
{
  for (OperationItemDistribution* i = firstOperation; i; i = i->nextOperation)
    i->deleteOperationPlans(b);
}


int OperationItemDistribution::initialize()
{
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationItemDistribution>(
    "operation", "operation_itemdistribution"
    );
  registerFields<OperationItemDistribution>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<OperationItemDistribution>::getPythonType();
  x.setName("operation_itemdistribution");
  x.setDoc("frePPLe operation_itemdistribution");
  x.addMethod("createOrder", createOrder,
    METH_STATIC | METH_VARARGS | METH_KEYWORDS,
    "Create an operationplan representing a transfer order");
  x.supportgetattro();
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT OperationItemDistribution::OperationItemDistribution(
  ItemDistribution* i, Buffer *src, Buffer* dest
  ) : itemdist(i)
{
  if (!i || !src || !dest)
    throw LogicException(
      "An OperationItemDistribution always needs to point to "
      "a ItemDistribution, a source buffer and a destination buffer"
      );
  stringstream o;
  o << "Ship " << dest->getItem()->getName() << " from " << src->getName() << " to " << dest->getName();
  setName(o.str());
  setDuration(i->getLeadTime());
  setSizeMultiple(i->getSizeMultiple());
  setSizeMinimum(i->getSizeMinimum());
  setLocation(dest->getLocation());
  setSource(i->getSource());
  setCost(i->getCost());
  setHidden(true);
  new FlowEnd(this, dest, 1);
  new FlowStart(this, src, -1);
  initType(metadata);

  // Insert in the list of ItemDistribution operations.
  // We keep the list sorted by the operation name.
  if (!i->firstOperation || getName() < i->firstOperation->getName())
  {
    // New head of the list
    nextOperation = i->firstOperation;
    i->firstOperation = this;
  }
  else
  {
    // Insert in the middle or at the tail
    OperationItemDistribution* o = i->firstOperation;
    while (o->nextOperation)
    {
      if (getName() < o->nextOperation->getName())
        break;
      o = o->nextOperation;
    }
    nextOperation = o->nextOperation;
    o->nextOperation = this;
  }
}


OperationItemDistribution::~OperationItemDistribution()
{
  // Remove from the list of operations of this item distribution
  if (itemdist)
  {
    if (itemdist->firstOperation == this)
    {
      // We were at the head
      itemdist->firstOperation = nextOperation;
    }
    else
    {
      // We were in the middle
      OperationItemDistribution* i = itemdist->firstOperation;
      while (i->nextOperation != this && i->nextOperation)
        i = i->nextOperation;
      if (!i)
        throw LogicException("ItemDistribution operation list corrupted");
      else
        i->nextOperation = nextOperation;
    }
  }
}


DECLARE_EXPORT Buffer* OperationItemDistribution::getOrigin() const
{
  for (flowlist::const_iterator i = getFlows().begin(); i != getFlows().end(); ++i)
    if (i->getQuantity() < 0.0)
      return i->getBuffer();
  throw LogicException("Transfer operation doesn't consume material");
}


DECLARE_EXPORT Buffer* OperationItemDistribution::getDestination() const
{
  for (flowlist::const_iterator i = getFlows().begin(); i != getFlows().end(); ++i)
    if (i->getQuantity() > 0.0)
      return i->getBuffer();
  throw LogicException("Transfer operation doesn't produce material");
}


extern "C" PyObject* OperationItemDistribution::createOrder(
  PyObject *self, PyObject *args, PyObject *kwdict
  )
{
  // Parse the Python arguments
  PyObject* pydest = NULL;
  unsigned long id = 0;
  const char* ref = NULL;
  PyObject* pyitem = NULL;
  PyObject* pyorigin = NULL;
  double qty = 0;
  PyObject* pystart = NULL;
  PyObject* pyend = NULL;
  int consume = 1;
  const char* status = NULL;
  const char* source = NULL;
  static const char *kwlist[] = {
    "destination", "id", "reference", "item", "origin", "quantity", "start",
    "end", "consume_material", "status", "source", NULL
    };
  int ok = PyArg_ParseTupleAndKeywords(
    args, kwdict, "|OkzOOdOOpzz:createOrder", const_cast<char**>(kwlist),
    &pydest, &id, &ref, &pyitem, &pyorigin, &qty, &pystart, &pyend,
    &consume, &status, &source
    );
  if (!ok)
    return NULL;
  Date start = pystart ? PythonData(pystart).getDate() : Date::infinitePast;
  Date end = pyend ? PythonData(pyend).getDate() : Date::infinitePast;

  // Validate all arguments
  if (!pydest || !pyitem)
  {
    PyErr_SetString(PythonDataException, "item and destination arguments are mandatory");
    return NULL;
  }
  PythonData dest_tmp(pydest);
  if (!dest_tmp.check(Location::metadata))
  {
    PyErr_SetString(PythonDataException, "destination argument must be of type location");
    return NULL;
  }
  PythonData item_tmp(pyitem);
  if (!item_tmp.check(Item::metadata))
  {
    PyErr_SetString(PythonDataException, "item argument must be of type item");
    return NULL;
  }
  PythonData origin_tmp(pyorigin);
  if (pyorigin && !origin_tmp.check(Location::metadata))
  {
    PyErr_SetString(PythonDataException, "origin argument must be of type location");
    return NULL;
  }
  Item *item = static_cast<Item*>(item_tmp.getObject());
  Location *dest = static_cast<Location*>(dest_tmp.getObject());
  Location *origin = pyorigin ? static_cast<Location*>(origin_tmp.getObject()) : NULL;

  // Find or create the destination buffer.
  Buffer* destbuffer = NULL;
  for (Buffer::iterator bufiter = Buffer::begin(); bufiter != Buffer::end(); ++bufiter)
  {
    if (bufiter->getLocation() == dest && bufiter->getItem() == item)
    {
      if (destbuffer)
      {
        stringstream o;
        o << "Multiple buffers found for item '" << item << "'' and location'" << dest << "'";
        throw DataException(o.str());
      }
      destbuffer = &*bufiter;
    }
  }
  if (!destbuffer)
  {
    // Create the destination buffer
    destbuffer = new BufferDefault();
    stringstream o;
    o << item << " @ " << dest;
    destbuffer->setName(o.str());
    destbuffer->setItem(item);
    destbuffer->setLocation(dest);
  }

  // Look for a matching matching supplying operation on this buffer.
  // Here we also trigger the creation of its producing operation, which
  // contains the logic to build possible transfer operations.
  Operation *oper = NULL;
  Operation* prodOper = destbuffer->getProducingOperation();
  if (prodOper && prodOper->getType() == *OperationItemDistribution::metadata)
  {
    if (origin)
    {
      // Only one transfer is allowed. Check whether the source location of the
      // operation is matching this transfer.
      for (Operation::flowlist::const_iterator fl = prodOper->getFlows().begin();
          fl != prodOper->getFlows().end() && ok; ++ fl)
      {
        if (fl->getQuantity() < 0 && fl->getBuffer()->getLocation()->isMemberOf(origin))
          oper = prodOper;
      }
    }
    else
      oper = prodOper;
  }
  else if (prodOper && prodOper->getType() == *OperationAlternate::metadata)
  {
    SubOperation::iterator soperiter = prodOper->getSubOperationIterator();
    while (SubOperation *soper = soperiter.next())
    {
      if (soper->getType() == *OperationItemDistribution::metadata)
      {
        if (origin)
        {
          // Only one transfer is allowed. Check whether the source location of the
          // operation is matching this transfer.
          for (Operation::flowlist::const_iterator fl = prodOper->getFlows().begin();
              fl != prodOper->getFlows().end() && ok; ++ fl)
          {
            if (fl->getQuantity() < 0 && fl->getBuffer()->getLocation()->isMemberOf(origin))
              oper = prodOper;
          }
          if (oper)
            break;
        }
        else
        {
          oper = prodOper;
          break;
        }
      }
    }
  }

  // No matching operation is found.
  if (!oper)
  {
    // We'll create one now, but that requires that we have an origin defined.
    if (!origin)
      throw DataException("Origin location is needed on this distribution order");
    Buffer* originbuffer = NULL;
    for (Buffer::iterator bufiter = Buffer::begin(); bufiter != Buffer::end(); ++bufiter)
    {
      if (bufiter->getLocation() == origin && bufiter->getItem() == item)
      {
        if (originbuffer)
        {
          stringstream o;
          o << "Multiple buffers found for item '" << item << "'' and location'" << dest << "'";
          throw DataException(o.str());
        }
        originbuffer = &*bufiter;
      }
    }
    if (!originbuffer)
    {
      // Create the origin buffer
      originbuffer = new BufferDefault();
      stringstream o;
      o << item << " @ " << origin;
      originbuffer->setName(o.str());
      originbuffer->setItem(item);
      originbuffer->setLocation(origin);
    }
    // Note: We know that we need to create a new one. An existing one would
    // have created an operation on the buffer already.
    ItemDistribution *itemdist = new ItemDistribution();
    itemdist->setOrigin(origin);
    itemdist->setItem(item);
    itemdist->setDestination(dest);
    oper = new OperationItemDistribution(itemdist, originbuffer, destbuffer);
    new ProblemInvalidData(oper, "Distribution orders on unauthorized lanes", "operation",
      Date::infinitePast, Date::infiniteFuture, 1);
  }

  // Finally, create the operationplan
  OperationPlan *opplan = oper->createOperationPlan(qty, start, end, NULL, NULL, 0, false);
  if (status)
    opplan->setStatus(status);
  if (ref)
    opplan->setReference(ref);
  if (!consume)
    opplan->setConsumeMaterial(false);
  opplan->createFlowLoads();

  // Return result
  Py_INCREF(opplan);
  return opplan;
}


}
