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

DECLARE_EXPORT const MetaCategory* ItemOperation::metacategory;
DECLARE_EXPORT const MetaClass* ItemOperation::metadata;


int ItemOperation::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<ItemOperation>(
	  "itemoperation", "itemoperations", nullptr, finder
	  );
  metadata = MetaClass::registerClass<ItemOperation>(
    "itemoperation", "itemoperation", Object::create<ItemOperation>, true
  );
  registerFields<ItemOperation>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<ItemOperation>::getPythonType();
  x.setName("itemoperation");
  x.setDoc("frePPLe itemoperation");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(ItemOperation::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT ItemOperation::~ItemOperation()
{
  // Unlink from item
  if (item)
  {
    if (item->firstItemOperation == this)
      // Remove from head
      item->firstItemOperation = next;
    else
    {
      // Remove from middle
      ItemOperation *j = item->firstItemOperation;
      while (j->next && j->next != this)
        j = j->next;
      if (j)
        j->next = next;
      else
        logger << "Error: Corrupted ItemOperation list" << endl;
    }
  }
}


DECLARE_EXPORT ItemOperation::ItemOperation() :
  item(nullptr), loc(nullptr), oper(nullptr), next(nullptr), priority(1)
{
  initType(metadata);
  HasLevel::triggerLazyRecomputation();
}


DECLARE_EXPORT ItemOperation::ItemOperation(Operation* s, Item* r, int u) :
  item(r), loc(nullptr), oper(s), next(nullptr), priority(u)
{
  initType(metadata);
  setItem(r);
  HasLevel::triggerLazyRecomputation();
}


DECLARE_EXPORT ItemOperation::ItemOperation(Operation* s, Item* r, int u, DateRange e) :
  item(nullptr), loc(nullptr), oper(s), effectivity(e), next(nullptr), priority(u)
{
  initType(metadata);
  setItem(r);
  HasLevel::triggerLazyRecomputation();
}


void ItemOperation::setItem(Item* i)
{
  // Unlink from previous item
  if (item)
  {
    if (item->firstItemOperation == this)
      // Remove from head
      item->firstItemOperation = next;
    else
    {
      // Remove from middle
      ItemOperation *j = item->firstItemOperation;
      while (j->next && j->next != this)
        j = j->next;
      if (j)
        j->next = next;
      else
        throw LogicException("Corrupted ItemOperation list");
    }
  }

  // Update item
  item = i;

  // Link at the new owner.
  // We insert ourself at the head of the list.
  if (item)
  {
    next = item->firstItemOperation;
    item->firstItemOperation = this;
  }

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}


PyObject* ItemOperation::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Pick up the operation
    PyObject* oper = PyDict_GetItemString(kwds,"operation");
    if (!oper)
      throw DataException("missing operation on ItemOperation");
    if (!PyObject_TypeCheck(oper, Operation::metadata->pythonClass))
      throw DataException("ItemOperation operation must be of type operation");

    // Pick up the item
    PyObject* it = PyDict_GetItemString(kwds,"item");
    if (!it)
      throw DataException("missing item on ItemOperation");
    if (!PyObject_TypeCheck(it, Item::metadata->pythonClass))
      throw DataException("ItemOperation item must be of type item");

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

    // Create the ItemOperation
    ItemOperation *l = new ItemOperation(
      static_cast<Operation*>(oper),
      static_cast<Item*>(it),
      q2, eff
    );

    // Iterate over extra keywords, and set attributes.
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
          && !attr.isA(Tags::operation) && !attr.isA(Tags::item)
          && !attr.isA(Tags::type) && !attr.isA(Tags::priority) && !attr.isA(Tags::action))
        {
          const MetaFieldBase* fmeta = l->getType().findField(attr.getHash());
          if (!fmeta && l->getType().category)
            fmeta = l->getType().category->findField(attr.getHash());
          if (fmeta)
            // Update the attribute
            fmeta->setField(l, field);
          else
            l->setProperty(attr.getName(), value);
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
    return nullptr;
  }
}


void ItemOperation::clear()
{
  for (Item::iterator it = Item::begin(); it != Item::end(); ++it)
  {
    Item::operationIterator itemoperiter(&*it);
    while (ItemOperation *itemoper = itemoperiter.next())
      delete itemoper;
  }
}


Object* ItemOperation::finder(const DataValueDict& d)
{
  // Check item
  const DataValue* tmp = d.get(Tags::item);
  if (!tmp)
    return nullptr;
  Item* item = static_cast<Item*>(tmp->getObject());

  // Check operation field
  tmp = d.get(Tags::operation);
  if (!tmp)
    return nullptr;
  Operation* oper = static_cast<Operation*>(tmp->getObject());

  // Walk over all operations of the item, and return
  // the first one with matching
  const DataValue* hasEffectiveStart = d.get(Tags::effective_start);
  Date effective_start;
  if (hasEffectiveStart)
    effective_start = hasEffectiveStart->getDate();
  const DataValue* hasEffectiveEnd = d.get(Tags::effective_end);
  Date effective_end;
  if (hasEffectiveEnd)
    effective_end = hasEffectiveEnd->getDate();
  const DataValue* hasPriority = d.get(Tags::priority);
  int priority;
  if (hasPriority)
    priority = hasPriority->getInt();
  Item::operationIterator itemoperiter(item);
  while ( ItemOperation *itemoper = itemoperiter.next())
  {
    if (itemoper->getOperation() != oper)
      continue;
    if (hasEffectiveStart && itemoper->getEffectiveStart() != effective_start)
      continue;
    if (hasEffectiveEnd && itemoper->getEffectiveEnd() != effective_end)
      continue;
    if (hasPriority && itemoper->getPriority() != priority)
      continue;
    return itemoper;
  }
  return nullptr;
}

}
