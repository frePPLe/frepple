/***************************************************************************
 *                                                                         *
 * Copyright (C) 2015 by frePPLe bvba                                      *
 *                                                                         *
 * All information contained herein is, and remains the property of        *
 * frePPLe.                                                                *
 * You are allowed to use and modify the source code, as long as the       *
 * software is used within your company.                                   *
 * You are not allowed to distribute the software, either in the form of   *
 * source code or in the form of compiled binaries.                        *
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

    /*
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

  /* YYY
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
  o << "Ship '" << dest->getItem()->getName() << "' from '" << src->getName() << "' to '" << dest->getName() << "' (*)";
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
  // Remove from the list of operations of this supplier item
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
