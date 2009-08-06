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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,*
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{

template<class Customer> DECLARE_EXPORT Tree utils::HasName<Customer>::st;


DECLARE_EXPORT void Customer::writeElement(XMLOutput* o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }

  // Write the complete object
  if (m != NOHEADER) o->BeginObject(tag, Tags::tag_name, getName());

  // Write the fields
  HasDescription::writeElement(o, tag);
  HasHierarchy<Customer>::writeElement(o, tag);
  o->EndObject(tag);
}


DECLARE_EXPORT void Customer::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
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


DECLARE_EXPORT PyObject* PythonCustomer::getattro(const Attribute& attr)
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
  if (attr.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
	return NULL;
}


DECLARE_EXPORT int PythonCustomer::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    obj->setName(field.getString());
  else if (attr.isA(Tags::tag_description))
    obj->setDescription(field.getString());
  else if (attr.isA(Tags::tag_category))
    obj->setCategory(field.getString());
  else if (attr.isA(Tags::tag_subcategory))
    obj->setSubCategory(field.getString());
  else if (attr.isA(Tags::tag_owner))
  {
    if (!field.check(PythonCustomer::getType())) 
    {
      PyErr_SetString(PythonDataException, "customer owner must be of type customer");
      return -1;
    }
    Customer* y = static_cast<PythonCustomer*>(static_cast<PyObject*>(field))->obj;
    obj->setOwner(y);
  }
  else if (attr.isA(Tags::tag_hidden))
    obj->setHidden(field.getBool());
  else
    return -1;
  return 0;
}


DECLARE_EXPORT PyObject* PythonCustomerDefault::getattro(const Attribute& attr)
{
  return PythonCustomer(obj).getattro(attr);
}


DECLARE_EXPORT int PythonCustomerDefault::setattro(const Attribute& attr, const PythonObject& field)
{
 return PythonCustomer(obj).setattro(attr, field);
}


} // end namespace
