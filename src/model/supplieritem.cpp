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

DECLARE_EXPORT const MetaCategory* SupplierItem::metacategory;
DECLARE_EXPORT const MetaClass* SupplierItem::metadata;


int SupplierItem::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<SupplierItem>(
	  "supplieritem", "supplieritems", MetaCategory::ControllerDefault
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

}
