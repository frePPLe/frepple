/***************************************************************************
 *                                                                         *
 * Copyright (C) 2015 by Johan De Taeye, frePPLe bvba                      *
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

DECLARE_EXPORT const MetaCategory* SupplierItem::metacategory;
DECLARE_EXPORT const MetaClass* SupplierItem::metadata;


int SupplierItem::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<SupplierItem>(
	  "supplieritem", "supplieritems", MetaCategory::ControllerDefault, writer
	  );
  metadata = MetaClass::registerClass<SupplierItem>(
    "supplieritem", "supplieritem", Object::create<SupplierItem>, true
  );
  registerFields<SupplierItem>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<SupplierItem>::getPythonType();
  x.setName("supplieritem");
  x.setDoc("frePPLe supplieritem");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(SupplierItem::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT SupplierItem::~SupplierItem()
{
  // TODO Delete existing procurements?
  //if (getSupplier() && getItem()) {}

  // Delete the associated from the related objects
  if (getSupplier()) getSupplier()->items.erase(this);
  if (getItem()) getItem()->suppliers.erase(this);
}


DECLARE_EXPORT SupplierItem::SupplierItem(Supplier* s, Item* r, int u)
  : size_minimum(1.0), size_multiple(0.0), cost(0.0)
{
  setSupplier(s);
  setItem(r);
  setPriority(u);
  initType(metadata);
  try { validate(ADD); }
  catch (...)
  {
    if (getSupplier()) getSupplier()->items.erase(this);
    if (getItem()) getItem()->suppliers.erase(this);
    resetReferenceCount();
    throw;
  }
}


DECLARE_EXPORT SupplierItem::SupplierItem(Supplier* s, Item* r, int u, DateRange e)
  : size_minimum(1.0), size_multiple(0.0), cost(0.0)
{
  setSupplier(s);
  setItem(r);
  setPriority(u);
  setEffective(e);
  initType(metadata);
  try { validate(ADD); }
  catch (...)
  {
    if (getSupplier()) getSupplier()->items.erase(this);
    if (getItem()) getItem()->suppliers.erase(this);
    resetReferenceCount();
    throw;
  }
}


void SupplierItem::writer(const MetaCategory* c, Serializer* o)
{
  bool first = true;
  for (Supplier::iterator i = Supplier::begin(); i != Supplier::end(); ++i)
    for (Supplier::itemlist::const_iterator j = i->getItems().begin(); j != i->getItems().end(); ++j)
    {
      if (first)
      {
        o->BeginList(Tags::tag_supplieritems);
        first = false;
      }
      // We use the FULL mode, to force the supplieritems being written regardless
      // of the depth in the XML tree.
      o->writeElement(Tags::tag_supplieritem, &*j, FULL);
    }
  if (!first) o->EndList(Tags::tag_supplieritems);
}


/** @todo this method implementation is not generic enough and not extendible by subclasses. */
PyObject* SupplierItem::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Pick up the supplier
    PyObject* sup = PyDict_GetItemString(kwds,"supplier");
    if (!PyObject_TypeCheck(sup, Supplier::metadata->pythonClass))
      throw DataException("supplieritem supplier must be of type supplier");

    // Pick up the item
    PyObject* it = PyDict_GetItemString(kwds,"item");
    if (!PyObject_TypeCheck(it, Item::metadata->pythonClass))
      throw DataException("supplieritem item must be of type item");

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

    // Create the supplieritem
    SupplierItem *l = new SupplierItem(
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
        Attribute attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::tag_effective_end) && !attr.isA(Tags::tag_effective_start)
          && !attr.isA(Tags::tag_supplier) && !attr.isA(Tags::tag_item)
          && !attr.isA(Tags::tag_priority) && !attr.isA(Tags::tag_type)
          && !attr.isA(Tags::tag_action) && !attr.isA(Tags::tag_cost)
          && !attr.isA(Tags::tag_size_minimum) && !attr.isA(Tags::tag_size_multiple)
          && !attr.isA(Tags::tag_leadtime))
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


DECLARE_EXPORT void SupplierItem::validate(Action action)
{
  // Catch null supplier and item pointers 
  Supplier *sup = getSupplier();
  Item *it = getItem();
  if (!sup || !it)
  {
    // Invalid load model
    if (!sup && !it)
      throw DataException("Missing supplier and item on a supplieritem");
    else if (!sup)
      throw DataException("Missing supplier on a supplieritem on item '"
          + it->getName() + "'");
    else if (!it)
      throw DataException("Missing item on a supplieritem on supplier '"
          + sup->getName() + "'");
  }

  // Check if a supplieritem with 1) identical supplier, 2) identical item and
  // 3) overlapping effectivity dates already exists
  Supplier::itemlist::const_iterator i = sup->getItems().begin();
  for (; i != sup->getItems().end(); ++i)
    if (i->getItem() == it
        && i->getEffective().overlap(getEffective())
        && &*i != this)
      break;
  
  // Apply the appropriate action
  switch (action)
  {
    case ADD:
      if (i != sup->getItems().end())
      {
        throw DataException("Supplieritem of '" + sup->getName() + "' and '"
            + it->getName() + "' already exists");
      }
      break;
    case CHANGE:
      throw DataException("Can't update a supplieritem");
    case ADD_CHANGE:
      // ADD is handled in the code after the switch statement
      if (i == sup->getItems().end()) break;
      throw DataException("Can't update a supplieritem");
    case REMOVE:
      // This supplieritem was only used temporarily during the reading process
      delete this;
      if (i == sup->getItems().end())
        // Nothing to delete
        throw DataException("Can't remove nonexistent supplieritem of '"
            + sup->getName() + "' and '" + it->getName() + "'");
      delete &*i;
      return;
  }
}


int SupplierItemIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<SupplierItemIterator>::getPythonType();
  x.setName("supplierItemIterator");
  x.setDoc("frePPLe iterator for supplier items");
  x.supportiter();
  return x.typeReady();
}


PyObject* SupplierItemIterator::iternext()
{
  PyObject* result;
  if (sup)
  {
    // Iterate over items on a supplier
    if (ir == sup->getItems().end()) return NULL;
    result = const_cast<SupplierItem*>(&*ir);
    ++ir;
  }
  else
  {
    // Iterate over resources having a skill
    if (is == it->getSuppliers().end()) return NULL;
    result = const_cast<SupplierItem*>(&*is);
    ++is;
  }
  Py_INCREF(result);
  return result;
}

}
