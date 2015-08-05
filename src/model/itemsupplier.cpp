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

DECLARE_EXPORT const MetaCategory* ItemSupplier::metacategory;
DECLARE_EXPORT const MetaClass* ItemSupplier::metadata;
DECLARE_EXPORT const MetaClass* OperationItemSupplier::metadata;


int ItemSupplier::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<ItemSupplier>(
	  "itemsupplier", "itemsuppliers", MetaCategory::ControllerDefault
	  );
  metadata = MetaClass::registerClass<ItemSupplier>(
    "itemsupplier", "itemsupplier", Object::create<ItemSupplier>, true
  );
  registerFields<ItemSupplier>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<ItemSupplier>::getPythonType();
  x.setName("itemsupplier");
  x.setDoc("frePPLe itemsupplier");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(ItemSupplier::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT ItemSupplier::~ItemSupplier()
{
  // Delete the association from the related objects
  if (getSupplier())
    getSupplier()->items.erase(this);
  if (getItem())
    getItem()->suppliers.erase(this);

  // Delete all owned purchase operations
  while (firstOperation)
    delete firstOperation;
}


DECLARE_EXPORT ItemSupplier::ItemSupplier(Supplier* s, Item* r, int u)
  : loc(NULL), size_minimum(1.0), size_multiple(0.0), cost(0.0), firstOperation(NULL)
{
  setSupplier(s);
  setItem(r);
  setPriority(u);
  initType(metadata);
}


DECLARE_EXPORT ItemSupplier::ItemSupplier(Supplier* s, Item* r, int u, DateRange e)
  : loc(NULL), size_minimum(1.0), size_multiple(0.0), cost(0.0), firstOperation(NULL)
{
  setSupplier(s);
  setItem(r);
  setPriority(u);
  setEffective(e);
  initType(metadata);
}


/** @todo this method implementation is not generic enough and not extendible by subclasses. */
PyObject* ItemSupplier::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Pick up the supplier
    PyObject* sup = PyDict_GetItemString(kwds,"supplier");
    if (!PyObject_TypeCheck(sup, Supplier::metadata->pythonClass))
      throw DataException("ItemSupplier supplier must be of type supplier");

    // Pick up the item
    PyObject* it = PyDict_GetItemString(kwds,"item");
    if (!PyObject_TypeCheck(it, Item::metadata->pythonClass))
      throw DataException("ItemSupplier item must be of type item");

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

    // Create the ItemSupplier
    ItemSupplier *l = new ItemSupplier(
      static_cast<Supplier*>(sup),
      static_cast<Item*>(it),
      q2, eff
    );

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
        if (!attr.isA(Tags::effective_end) && !attr.isA(Tags::effective_start)
          && !attr.isA(Tags::supplier) && !attr.isA(Tags::item)
          && !attr.isA(Tags::priority) && !attr.isA(Tags::type)
          && !attr.isA(Tags::action) && !attr.isA(Tags::cost)
          && !attr.isA(Tags::size_minimum) && !attr.isA(Tags::size_multiple)
          && !attr.isA(Tags::leadtime))
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


DECLARE_EXPORT void ItemSupplier::validate(Action action)
{
  // Catch null supplier and item pointers
  Supplier *sup = getSupplier();
  Item *it = getItem();
  Location *loc = getLocation();
  if (!sup || !it)
  {
    // Invalid ItemSupplier model
    if (!sup && !it)
      throw DataException("Missing supplier and item on a ItemSupplier");
    else if (!sup)
      throw DataException("Missing supplier on a ItemSupplier on item '"
          + it->getName() + "'");
    else if (!it)
      throw DataException("Missing item on a ItemSupplier on supplier '"
          + sup->getName() + "'");
  }

  // Check if a ItemSupplier with 1) identical supplier, 2) identical item
  // 3) identical location, and 4) overlapping effectivity dates already exists
  Supplier::itemlist::const_iterator i = sup->getItems().begin();
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
}


DECLARE_EXPORT void ItemSupplier::deleteOperationPlans(bool b)
{
  for (OperationItemSupplier* i = firstOperation; i; i = i->nextOperation)
    i->deleteOperationPlans(b);
}


int OperationItemSupplier::initialize()
{
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationItemSupplier>(
    "operation", "operation_ItemSupplier"
    );
  registerFields<OperationItemSupplier>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<FlowPlan>::getPythonType();
  x.setName("operation_ItemSupplier");
  x.setDoc("frePPLe operation_ItemSupplier");
  x.supportgetattro();
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT OperationItemSupplier::OperationItemSupplier(
  ItemSupplier* i, Buffer *b
  ) : supitem(i)
{
  if (!i || !b || !i->getSupplier())
    throw LogicException(
      "An OperationItemSupplier always needs to point to "
      "a ItemSupplier and a buffer"
      );
  stringstream o;
  o << "Purchase '" << b->getName() << "' from '" << i->getSupplier()->getName() << "' (*)";
  setName(o.str());
  setDuration(i->getLeadTime());
  setSizeMultiple(i->getSizeMultiple());
  setSizeMinimum(i->getSizeMinimum());
  setLocation(b->getLocation());
  setSource(i->getSource());
  setCost(i->getCost());
  setHidden(true);
  FlowEnd* fl = new FlowEnd(this, b, 1);
  initType(metadata);

  // Insert in the list of ItemSupplier operations.
  // We keep the list sorted by the name of the buffers.
  if (!i->firstOperation || b->getName() < i->firstOperation->getName())
  {
    // New head of the list
    nextOperation = i->firstOperation;
    i->firstOperation = this;
  }
  else
  {
    // Insert in the middle or at the tail
    OperationItemSupplier* o = i->firstOperation;
    while (o->nextOperation)
    {
      // There should always be a single flow on these operations.
      // We take it for granted and don't verify it.
      if (b->getName() < o->nextOperation->getFlows().begin()->getBuffer()->getName())
        break;
      o = o->nextOperation;
    }
    nextOperation = o->nextOperation;
    o->nextOperation = this;
  }
}


OperationItemSupplier::~OperationItemSupplier()
{
  // Remove from the list of operations of this supplier item
  if (supitem->firstOperation == this)
  {
    // We were at the head
    supitem->firstOperation = nextOperation;
  }
  else
  {
    // We were in the middle
    OperationItemSupplier* i = supitem->firstOperation;
    while (i->nextOperation != this && i->nextOperation)
      i = i->nextOperation;
    if (!i)
      throw LogicException("ItemSupplier operation list corrupted");
    else
      i->nextOperation = nextOperation;
  }
}


}
