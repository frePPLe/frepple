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

template<class Item> DECLARE_EXPORT Tree utils::HasName<Item>::st;
DECLARE_EXPORT const MetaCategory* Item::metadata;
DECLARE_EXPORT const MetaClass* ItemDefault::metadata;


int Item::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("item", "items", reader, writer);

  // Initialize the Python class
  return FreppleCategory<Item>::initialize();
}


int ItemDefault::initialize()
{
  // Initialize the metadata
  ItemDefault::metadata = new MetaClass("item", "item_default",
      Object::createString<ItemDefault>, true);

  // Initialize the Python class
  return FreppleClass<ItemDefault,Item>::initialize();
}


DECLARE_EXPORT Item::~Item()
{
  // Remove references from the buffers
  for (Buffer::iterator buf = Buffer::begin(); buf != Buffer::end(); ++buf)
    if (buf->getItem() == this) buf->setItem(NULL);

  // Remove references from the demands
  for (Demand::iterator l = Demand::begin(); l != Demand::end(); ++l)
    if (l->getItem() == this) l->setItem(NULL);
}


DECLARE_EXPORT void Item::writeElement(Serializer *o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL)
    o->BeginObject(tag, Tags::tag_name, getName());

  // Write the fields
  HasDescription::writeElement(o, tag);
  HasHierarchy<Item>::writeElement(o, tag);
  o->writeElement(Tags::tag_operation, deliveryOperation);
  if (getPrice() != 0.0) o->writeElement(Tags::tag_price, getPrice());

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void Item::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else
  {
    PythonDictionary::read(pIn, pAttr, getDict());
    HasHierarchy<Item>::beginElement(pIn, pAttr);
  }
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


DECLARE_EXPORT PyObject* Item::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_name))
    return PythonObject(getName());
  if (attr.isA(Tags::tag_description))
    return PythonObject(getDescription());
  if (attr.isA(Tags::tag_category))
    return PythonObject(getCategory());
  if (attr.isA(Tags::tag_subcategory))
    return PythonObject(getSubCategory());
  if (attr.isA(Tags::tag_source))
    return PythonObject(getSource());
  if (attr.isA(Tags::tag_price))
    return PythonObject(getPrice());
  if (attr.isA(Tags::tag_owner))
    return PythonObject(getOwner());
  if (attr.isA(Tags::tag_operation))
    return PythonObject(getOperation());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(getHidden());
  if (attr.isA(Tags::tag_members))
    return new ItemIterator(this);
  return NULL;
}


DECLARE_EXPORT int Item::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    setName(field.getString());
  else if (attr.isA(Tags::tag_description))
    setDescription(field.getString());
  else if (attr.isA(Tags::tag_category))
    setCategory(field.getString());
  else if (attr.isA(Tags::tag_subcategory))
    setSubCategory(field.getString());
  else if (attr.isA(Tags::tag_source))
    setSource(field.getString());
  else if (attr.isA(Tags::tag_price))
    setPrice(field.getDouble());
  else if (attr.isA(Tags::tag_owner))
  {
    if (!field.check(Item::metadata))
    {
      PyErr_SetString(PythonDataException, "item owner must be of type item");
      return -1;
    }
    Item* y = static_cast<Item*>(static_cast<PyObject*>(field));
    setOwner(y);
  }
  else if (attr.isA(Tags::tag_operation))
  {
    if (!field.check(Operation::metadata))
    {
      PyErr_SetString(PythonDataException, "item operation must be of type operation");
      return -1;
    }
    Operation* y = static_cast<Operation*>(static_cast<PyObject*>(field));
    setOperation(y);
  }
  else if (attr.isA(Tags::tag_hidden))
    setHidden(field.getBool());
  else
    return -1;
  return 0;
}


} // end namespace
