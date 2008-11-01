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
 * Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{

template<class Location> DECLARE_EXPORT Tree utils::HasName<Location>::st;


DECLARE_EXPORT void Location::writeElement(XMLOutput* o, const Keyword& tag, mode m) const
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
  HasHierarchy<Location>::writeElement(o, tag);
  o->writeElement(Tags::tag_available, available);
  o->EndObject(tag);
}


DECLARE_EXPORT void Location::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(Tags::tag_available) || pAttr.isA(Tags::tag_maximum))
    pIn.readto( Calendar::reader(Calendar::metadata,pIn.getAttributes()) );
  else
    HasHierarchy<Location>::beginElement(pIn, pAttr);
}


DECLARE_EXPORT void Location::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_available))
  {
    CalendarBool *cal = dynamic_cast<CalendarBool*>(pIn.getPreviousObject());
    if (cal)
      setAvailable(cal);
    else
    {
      Calendar *c = dynamic_cast<Calendar*>(pIn.getPreviousObject());
      if (!c)
        throw LogicException("Incorrect object type during read operation");
      throw DataException("Calendar '" + c->getName() +
          "' has invalid type for use as location calendar");
    }
  }
  else
  {
    HasDescription::endElement(pIn, pAttr, pElement);
    HasHierarchy<Location>::endElement(pIn, pAttr, pElement);
  }
}


DECLARE_EXPORT Location::~Location()
{
  // Remove all references from buffers to this location
  for (Buffer::iterator buf = Buffer::begin();
      buf != Buffer::end(); ++buf)
    if (buf->getLocation() == this) buf->setLocation(NULL);

  // Remove all references from resources to this location
  for (Resource::iterator res = Resource::begin();
      res != Resource::end(); ++res)
    if (res->getLocation() == this) res->setLocation(NULL);

  // Remove all references from operations to this location
  for (Operation::iterator oper = Operation::begin();
      oper != Operation::end(); ++oper)
    if (oper->getLocation() == this) oper->setLocation(NULL);
}


PyObject* PythonLocation::getattro(const Attribute& attr)
{
  if (!obj) return Py_None;
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
  if (attr.isA(Tags::tag_available))
    return PythonObject(obj->getAvailable());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
	return NULL;
}


int PythonLocation::setattro(const Attribute& attr, const PythonObject& field)
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
    if (!field.check(PythonLocation::getType())) 
    {
      PyErr_SetString(PythonDataException, "location owner must be of type location");
      return -1;
    }
    Location* y = static_cast<PythonLocation*>(static_cast<PyObject*>(field))->obj;
    obj->setOwner(y);
  }
  else if (attr.isA(Tags::tag_available))
  {
    if (!field.check(PythonCalendarBool::getType())) 
    {
      PyErr_SetString(PythonDataException, "location calendar must be of type calendar_bool");
      return -1;
    }
    CalendarBool* y = static_cast<PythonCalendarBool*>(static_cast<PyObject*>(field))->obj;
    obj->setAvailable(y);
  }
  else if (attr.isA(Tags::tag_hidden))
    obj->setHidden(field.getBool());
  else
    return -1;
  return 0;
}


PyObject* PythonLocationDefault::getattro(const Attribute& attr)
{
  return PythonLocation(obj).getattro(attr);
}


int PythonLocationDefault::setattro(const Attribute& attr, const PythonObject& field)
{
 return PythonLocation(obj).setattro(attr, field);
}

} // end namespace
