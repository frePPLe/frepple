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

DECLARE_EXPORT const MetaCategory* SupplierItem::metadata;


int SupplierItem::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("supplieritem", "supplieritems", MetaCategory::ControllerDefault, writer);
  const_cast<MetaCategory*>(metadata)->registerClass(
    "supplieritem","supplieritem",true,Object::createDefault<SupplierItem>
  );

  // Initialize the Python class
  PythonType& x = FreppleCategory<SupplierItem>::getType();
  x.setName("supplieritem");
  x.setDoc("frePPLe supplieritem");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaCategory*>(SupplierItem::metadata)->pythonClass = x.type_object();
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


DECLARE_EXPORT void SupplierItem::writeElement(Serializer* o, const Keyword& tag, mode m) const
{
  // If the resourceskill has already been saved, no need to repeat it again
  // A 'reference' to a load is not useful to be saved.
  if (m == REFERENCE) return;
  assert(m != NOHEAD && m != NOHEADTAIL);

  o->BeginObject(tag);

  // If the supplieritem is defined inside of a resource tag, we don't need to save
  // the supplier. Otherwise we do save it...
  if (!dynamic_cast<Supplier*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_supplier, getSupplier());

  // If the supplieritem is defined inside of a item tag, we don't need to save
  // the item. Otherwise we do save it...
  if (!dynamic_cast<Item*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_item, getItem());

  // Write the cost, lead time and size constraints
  if (getLeadtime()) o->writeElement(Tags::tag_leadtime, getLeadtime());
  if (getSizeMinimum() != 1.0) o->writeElement(Tags::tag_size_minimum, getSizeMinimum());
  if (getSizeMultiple()) o->writeElement(Tags::tag_size_multiple, getSizeMultiple());
  if (getCost()) o->writeElement(Tags::tag_cost, getCost());

  // Write the priority and effective daterange
  if (getPriority()!=1) o->writeElement(Tags::tag_priority, getPriority());
  if (getEffective().getStart() != Date::infinitePast)
    o->writeElement(Tags::tag_effective_start, getEffective().getStart());
  if (getEffective().getEnd() != Date::infiniteFuture)
    o->writeElement(Tags::tag_effective_end, getEffective().getEnd());

  // Write source field
  o->writeElement(Tags::tag_source, getSource());

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void SupplierItem::beginElement(DataInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_supplier))
    pIn.readto( Supplier::reader(Supplier::metadata, pIn.getAttributes()) );
  else if (pAttr.isA (Tags::tag_item))
    pIn.readto( Item::reader(Item::metadata, pIn.getAttributes()) );
  else
    PythonDictionary::read(pIn, pAttr, getDict());
}


DECLARE_EXPORT void SupplierItem::endElement(DataInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA (Tags::tag_supplier))
  {
    Supplier *r = dynamic_cast<Supplier*>(pIn.getPreviousObject());
    if (r) setSupplier(r);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA (Tags::tag_item))
  {
    Item *s = dynamic_cast<Item*>(pIn.getPreviousObject());
    if (s) setItem(s);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_cost))
    setCost(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_size_minimum))
    setSizeMinimum(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_size_multiple))
    setSizeMultiple(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_leadtime))
    setLeadtime(pElement.getDuration());
  else if (pAttr.isA(Tags::tag_priority))
    setPriority(pElement.getInt());
  else if (pAttr.isA(Tags::tag_effective_end))
    setEffectiveEnd(pElement.getDate());
  else if (pAttr.isA(Tags::tag_effective_start))
    setEffectiveStart(pElement.getDate());
  else if (pAttr.isA(Tags::tag_source))
    setSource(pElement.getString());
  else if (pAttr.isA(Tags::tag_action))
  {
    delete static_cast<Action*>(pIn.getUserArea());
    pIn.setUserArea(
      new Action(MetaClass::decodeAction(pElement.getString().c_str()))
    );
  }
  else if (pIn.isObjectEnd())
  {
    // The supplieritem data is now all read in. See if it makes sense now...
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


DECLARE_EXPORT PyObject* SupplierItem::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_supplier))
    return PythonObject(getSupplier());
  if (attr.isA(Tags::tag_item))
    return PythonObject(getItem());
  if (attr.isA(Tags::tag_leadtime))
    return PythonObject(getLeadtime());
  if (attr.isA(Tags::tag_size_minimum))
    return PythonObject(getSizeMinimum());
  if (attr.isA(Tags::tag_size_multiple))
    return PythonObject(getSizeMultiple());
  if (attr.isA(Tags::tag_priority))
    return PythonObject(getPriority());
  if (attr.isA(Tags::tag_effective_end))
    return PythonObject(getEffective().getEnd());
  if (attr.isA(Tags::tag_effective_start))
    return PythonObject(getEffective().getStart());
  if (attr.isA(Tags::tag_source))
    return PythonObject(getSource());
  if (attr.isA(Tags::tag_cost))
    return PythonObject(getCost());
  return NULL;
}


DECLARE_EXPORT int SupplierItem::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_supplier))
  {
    if (!field.check(Supplier::metadata))
    {
      PyErr_SetString(PythonDataException, "supplieritem supplier must be of type supplier");
      return -1;
    }
    Supplier* y = static_cast<Supplier*>(static_cast<PyObject*>(field));
    setSupplier(y);
  }
  else if (attr.isA(Tags::tag_item))
  {
    if (!field.check(Item::metadata))
    {
      PyErr_SetString(PythonDataException, "supplieritem item must be of type item");
      return -1;
    }
    Item* y = static_cast<Item*>(static_cast<PyObject*>(field));
    setItem(y);
  }
  else if (attr.isA(Tags::tag_cost))
    setCost(field.getDouble());
  else if (attr.isA(Tags::tag_size_minimum))
    setSizeMinimum(field.getDouble());
  else if (attr.isA(Tags::tag_size_multiple))
    setSizeMultiple(field.getDouble());
  else if (attr.isA(Tags::tag_leadtime))
    setLeadtime(field.getDuration());
  else if (attr.isA(Tags::tag_priority))
    setPriority(field.getInt());
  else if (attr.isA(Tags::tag_effective_end))
    setEffectiveEnd(field.getDate());
  else if (attr.isA(Tags::tag_effective_start))
    setEffectiveStart(field.getDate());
  else if (attr.isA(Tags::tag_source))
    setSource(field.getString());
  else
    return -1;
  return 0;
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
    int q2 = q1 ? PythonObject(q1).getInt() : 1;

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
        PythonObject field(value);
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
  PythonType& x = PythonExtension<SupplierItemIterator>::getType();
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
