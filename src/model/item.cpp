/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007 by Johan De Taeye                                    *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Lesser General Public License as published   *
 * by the Free Software Foundation; either version 2.1 of the License, or  *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser *
 * General Public License for more details.                                *
 *                                                                         *
 * You should have received a copy of the GNU Lesser General Public        *
 * License along with this library; if not, write to the Free Software     *
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{

template<class Item> DECLARE_EXPORT Tree utils::HasName<Item>::st;


DECLARE_EXPORT Item::~Item()
{
  // Remove references from the buffers
  for (Buffer::iterator buf = Buffer::begin(); buf != Buffer::end(); ++buf)
    if (buf->getItem() == this) buf->setItem(NULL);

  // Remove references from the demands
  for (Demand::iterator l = Demand::begin(); l != Demand::end(); ++l)
    if (l->getItem() == this) l->setItem(NULL);
}


DECLARE_EXPORT void Item::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }

  // Write the complete item
  if (m != NOHEADER) o->BeginObject(tag, Tags::tag_name, getName());

  // Write the fields
  HasDescription::writeElement(o, tag);
  HasHierarchy<Item>::writeElement(o, tag);
  o->writeElement(Tags::tag_operation, deliveryOperation);
  if (getPrice() != 0.0) o->writeElement(Tags::tag_price, getPrice());
  o->EndObject(tag);
}


DECLARE_EXPORT void Item::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else
    HasHierarchy<Item>::beginElement(pIn, pAttr);
}


DECLARE_EXPORT void Item::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_operation))
  {
    Operation *o = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (o) setOperation(o);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_price))
    setPrice(pElement.getDouble());
  else
  {
    HasDescription::endElement(pIn, pAttr, pElement);
    HasHierarchy<Item>::endElement(pIn, pAttr, pElement);
  }
}


DECLARE_EXPORT PyObject* PythonItem::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (attr.isA(Tags::tag_description))
    return PythonObject(obj->getDescription());
  if (attr.isA(Tags::tag_category))
    return PythonObject(obj->getCategory());
  if (attr.isA(Tags::tag_subcategory))
    return PythonObject(obj->getSubCategory());
  if (attr.isA(Tags::tag_price))
    return PythonObject(obj->getPrice());
  if (attr.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (attr.isA(Tags::tag_operation))
    return PythonObject(obj->getOperation());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
	return NULL;
}


DECLARE_EXPORT int PythonItem::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    obj->setName(field.getString());
  else if (attr.isA(Tags::tag_description))
    obj->setDescription(field.getString());
  else if (attr.isA(Tags::tag_category))
    obj->setCategory(field.getString());
  else if (attr.isA(Tags::tag_subcategory))
    obj->setSubCategory(field.getString());
  else if (attr.isA(Tags::tag_price))
    obj->setPrice(field.getDouble());
  else if (attr.isA(Tags::tag_owner))
  {
    if (!field.check(PythonItem::getType())) 
    {
      PyErr_SetString(PythonDataException, "item owner must be of type item");
      return -1;
    }
    Item* y = static_cast<PythonItem*>(static_cast<PyObject*>(field))->obj;
    obj->setOwner(y);
  }
  else if (attr.isA(Tags::tag_operation))
  {
    if (!field.check(PythonOperation::getType())) 
    {
      PyErr_SetString(PythonDataException, "item operation must be of type operation");
      return -1;
    }
    Operation* y = static_cast<PythonOperation*>(static_cast<PyObject*>(field))->obj;
    obj->setOperation(y);
  }
  else if (attr.isA(Tags::tag_hidden))
    obj->setHidden(field.getBool());
  else
    return -1;
  return 0;
}


DECLARE_EXPORT PyObject* PythonItemDefault::getattro(const Attribute& attr)
{
  return PythonItem(obj).getattro(attr);
}


DECLARE_EXPORT int PythonItemDefault::setattro(const Attribute& attr, const PythonObject& field)
{
 return PythonItem(obj).setattro(attr, field);
}

} // end namespace
