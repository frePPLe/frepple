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

template<class Customer> DECLARE_EXPORT Tree utils::HasName<Customer>::st;
DECLARE_EXPORT const MetaCategory* Customer::metadata;
DECLARE_EXPORT const MetaClass* CustomerDefault::metadata;


int Customer::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("customer", "customers", reader, writer);

  // Initialize the Python class
  return FreppleCategory<Customer>::initialize();
}


int CustomerDefault::initialize()
{
  // Initialize the metadata
  CustomerDefault::metadata = new MetaClass(
    "customer",
    "customer_default",
    Object::createString<CustomerDefault>, true);

  // Initialize the Python class
  return FreppleClass<CustomerDefault,Customer>::initialize();
}


DECLARE_EXPORT void Customer::writeElement(Serializer* o, const Keyword& tag, mode m) const
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
  HasHierarchy<Customer>::writeElement(o, tag);

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOTAIL && m != NOHEADTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void Customer::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  PythonDictionary::read(pIn, pAttr, getDict());
  HasHierarchy<Customer>::beginElement(pIn, pAttr);
}


DECLARE_EXPORT void Customer::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  HasDescription::endElement(pIn, pAttr, pElement);
  HasHierarchy<Customer>::endElement(pIn, pAttr, pElement);
}


DECLARE_EXPORT Customer::~Customer()
{
  // Remove all references from demands to this customer
  for (Demand::iterator i = Demand::begin(); i != Demand::end(); ++i)
    if (i->getCustomer() == this) i->setCustomer(NULL);
}


DECLARE_EXPORT PyObject* Customer::getattro(const Attribute& attr)
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
    return new CustomerIterator(this);
  return NULL;
}


DECLARE_EXPORT int Customer::setattro(const Attribute& attr, const PythonObject& field)
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
    if (!field.check(Customer::metadata))
    {
      PyErr_SetString(PythonDataException, "customer owner must be of type customer");
      return -1;
    }
    Customer* y = static_cast<Customer*>(static_cast<PyObject*>(field));
    setOwner(y);
  }
  else if (attr.isA(Tags::tag_hidden))
    setHidden(field.getBool());
  else
    return -1;
  return 0;
}


} // end namespace
