/***************************************************************************
 *                                                                         *
 * Copyright (C) 2014 by Johan De Taeye, frePPLe bvba                      *
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

template<class Supplier> DECLARE_EXPORT Tree utils::HasName<Supplier>::st;
DECLARE_EXPORT const MetaCategory* Supplier::metadata;
DECLARE_EXPORT const MetaClass* SupplierDefault::metadata;


int Supplier::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("supplier", "suppliers", reader, writer);

  // Initialize the Python class
  return FreppleCategory<Supplier>::initialize();
}


int SupplierDefault::initialize()
{
  // Initialize the metadata
  SupplierDefault::metadata = new MetaClass(
    "supplier",
    "supplier_default",
    Object::createString<SupplierDefault>, true);

  // Initialize the Python class
  return FreppleClass<SupplierDefault,Supplier>::initialize();
}


DECLARE_EXPORT void Supplier::writeElement(XMLOutput* o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL)
    o->BeginObject(tag, Tags::tag_name, XMLEscape(getName()));

  // Write the fields
  HasDescription::writeElement(o, tag);
  HasHierarchy<Supplier>::writeElement(o, tag);

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOTAIL && m != NOHEADTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void Supplier::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  PythonDictionary::read(pIn, pAttr, getDict());
  HasHierarchy<Supplier>::beginElement(pIn, pAttr);
}


DECLARE_EXPORT void Supplier::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  HasDescription::endElement(pIn, pAttr, pElement);
  HasHierarchy<Supplier>::endElement(pIn, pAttr, pElement);
}


DECLARE_EXPORT Supplier::~Supplier()
{
}


DECLARE_EXPORT PyObject* Supplier::getattro(const Attribute& attr)
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
  if (attr.isA(Tags::tag_owner))
    return PythonObject(getOwner());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(getHidden());
  if (attr.isA(Tags::tag_members))
    return new SupplierIterator(this);
  return NULL;
}


DECLARE_EXPORT int Supplier::setattro(const Attribute& attr, const PythonObject& field)
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
  else if (attr.isA(Tags::tag_owner))
  {
    if (!field.check(Supplier::metadata))
    {
      PyErr_SetString(PythonDataException, "supplier owner must be of type supplier");
      return -1;
    }
    Supplier* y = static_cast<Supplier*>(static_cast<PyObject*>(field));
    setOwner(y);
  }
  else if (attr.isA(Tags::tag_hidden))
    setHidden(field.getBool());
  else
    return -1;
  return 0;
}


} // end namespace
