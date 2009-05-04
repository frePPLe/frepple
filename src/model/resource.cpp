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

template<class Resource> DECLARE_EXPORT Tree utils::HasName<Resource>::st;


DECLARE_EXPORT void Resource::setMaximum(CalendarDouble* c)
{
  // Resetting the same calendar
  if (max_cal == c) return;

  // Mark as changed
  setChanged();

  // Calendar is already set. Need to remove the current max events.
  if (max_cal)
  {
    for (loadplanlist::iterator oo=loadplans.begin(); oo!=loadplans.end(); )
      if (oo->getType() == 4)
      {
        loadplans.erase(&(*oo));
        delete &(*(oo++));
      }
      else ++oo;
  }

  // Null pointer passed
  if (!c) return;

  // Create timeline structures for every bucket.
  max_cal = c;
  double curMax = 0.0;
  for (CalendarDouble::EventIterator x(max_cal); x.getDate()<Date::infiniteFuture; ++x)
    if (curMax != x.getValue())
    {
      curMax = x.getValue();
      loadplanlist::EventMaxQuantity *newBucket =
        new loadplanlist::EventMaxQuantity(x.getDate(), curMax);
      loadplans.insert(newBucket);
    }
}


DECLARE_EXPORT void Resource::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
{
  // Write a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }

  // Write the complete object
  if (m != NOHEADER) o->BeginObject(tag, Tags::tag_name, getName());

  // Write my fields
  HasDescription::writeElement(o, tag);
  HasHierarchy<Resource>::writeElement(o, tag);
  o->writeElement(Tags::tag_maximum, max_cal);
  if (getCost() != 1.0) o->writeElement(Tags::tag_cost, getCost());
  o->writeElement(Tags::tag_location, loc);
  Plannable::writeElement(o, tag);

  // Write the loads
  if (!loads.empty())
  {
    o->BeginObject (Tags::tag_loads);
    for (loadlist::const_iterator i = loads.begin(); i != loads.end(); ++i)
      // We use the FULL mode, to force the loads being written regardless
      // of the depth in the XML tree.
      o->writeElement(Tags::tag_load, &*i, FULL);
    o->EndObject (Tags::tag_loads);
  }

  // Write extra plan information
  loadplanlist::const_iterator i = loadplans.begin();
  if (o->getContentType() == XMLOutput::PLAN  && i!=loadplans.end())
  {
    o->BeginObject(Tags::tag_loadplans);
    for (; i!=loadplans.end(); ++i)
      if (i->getType()==1)
      {
        const LoadPlan *lp = dynamic_cast<const LoadPlan*>(&*i);
        o->BeginObject(Tags::tag_loadplan);
        o->writeElement(Tags::tag_date, lp->getDate());
        o->writeElement(Tags::tag_quantity, lp->getQuantity());
        o->writeElement(Tags::tag_onhand, lp->getOnhand());
        o->writeElement(Tags::tag_minimum, lp->getMin());
        o->writeElement(Tags::tag_maximum, lp->getMax());
        o->writeElement(Tags::tag_operationplan, &*(lp->getOperationPlan()), FULL);
        o->EndObject(Tags::tag_loadplan);
      }
    o->EndObject(Tags::tag_loadplans);
  }

  // That was it
  o->EndObject(tag);
}


DECLARE_EXPORT void Resource::beginElement (XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_load)
      && pIn.getParentElement().first.isA(Tags::tag_loads))
  {
    Load* l = new Load();
    l->setResource(this);
    pIn.readto(&*l);
  }
  else if (pAttr.isA (Tags::tag_maximum))
    pIn.readto( Calendar::reader(Calendar::metadata,pIn.getAttributes()) );
  else if (pAttr.isA(Tags::tag_loadplans))
    pIn.IgnoreElement();
  else if (pAttr.isA(Tags::tag_location))
    pIn.readto( Location::reader(Location::metadata,pIn.getAttributes()) );
  else
    HasHierarchy<Resource>::beginElement(pIn, pAttr);
}


DECLARE_EXPORT void Resource::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  /* Note that while restoring the size, the parent's size is NOT
     automatically updated. The getDescription of the 'set_size' function may
     suggest this would be the case... */
  if (pAttr.isA (Tags::tag_maximum))
  {
    CalendarDouble * c = dynamic_cast<CalendarDouble*>(pIn.getPreviousObject());
    if (c)
      setMaximum(c);
    else
    {
      Calendar *c = dynamic_cast<Calendar*>(pIn.getPreviousObject());
      if (!c)
        throw LogicException("Incorrect object type during read operation");
      throw DataException("Calendar '" + c->getName() +
          "' has invalid type for use as resource max calendar");
    }
  }
  else if (pAttr.isA (Tags::tag_cost))
    setCost(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_location))
  {
    Location * d = dynamic_cast<Location*>(pIn.getPreviousObject());
    if (d) setLocation(d);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
  {
    Plannable::endElement(pIn, pAttr, pElement);
    HasDescription::endElement(pIn, pAttr, pElement);
    HasHierarchy<Resource>::endElement (pIn, pAttr, pElement);
  }
}


DECLARE_EXPORT void Resource::deleteOperationPlans(bool deleteLocked)
{
  // Delete the operationplans
  for (loadlist::iterator i=loads.begin(); i!=loads.end(); ++i)
    OperationPlan::deleteOperationPlans(i->getOperation(),deleteLocked);

  // Mark to recompute the problems
  setChanged();
}


DECLARE_EXPORT Resource::~Resource()
{
  // Delete all operationplans
  // An alternative logic would be to delete only the loadwplans for this
  // resource and leave the rest of the plan untouched. The currently
  // implemented method is way more drastic...
  deleteOperationPlans(true);

  // The Load objects are automatically deleted by the destructor
  // of the Association list class.
}


DECLARE_EXPORT void ResourceInfinite::writeElement
(XMLOutput *o, const Keyword &tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
      (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the complete object
  if (m != NOHEADER) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  Resource::writeElement(o, tag, NOHEADER);
}


DECLARE_EXPORT PyObject* PythonResource::getattro(const Attribute& attr)
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
  if (attr.isA(Tags::tag_location))
    return PythonObject(obj->getLocation());
  if (attr.isA(Tags::tag_maximum))
    return PythonObject(obj->getMaximum());
  if (attr.isA(Tags::tag_cost))
    return PythonObject(obj->getCost());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
  if (attr.isA(Tags::tag_loadplans))
    return new PythonLoadPlanIterator(obj);
  if (attr.isA(Tags::tag_loads))
    return new PythonLoadIterator(obj);
  if (attr.isA(Tags::tag_level))
    return PythonObject(obj->getLevel());
  if (attr.isA(Tags::tag_cluster))
    return PythonObject(obj->getCluster());
	return NULL;
}


DECLARE_EXPORT int PythonResource::setattro(const Attribute& attr, const PythonObject& field)
{
  if (!obj) return -1;
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
    if (!field.check(PythonResource::getType()))
    {
      PyErr_SetString(PythonDataException, "resource owner must be of type resource");
      return -1;
    }
    Resource* y = static_cast<PythonResource*>(static_cast<PyObject*>(field))->obj;
    obj->setOwner(y);
  }
  else if (attr.isA(Tags::tag_location))
  {
    if (!field.check(PythonLocation::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer location must be of type location");
      return -1;
    }
    Location* y = static_cast<PythonLocation*>(static_cast<PyObject*>(field))->obj;
    obj->setLocation(y);
  }
  else if (attr.isA(Tags::tag_maximum))
  {
    if (!field.check(PythonCalendarDouble::getType())) 
    {
      PyErr_SetString(PythonDataException, "resource maximum must be of type calendar_double");
      return -1;
    }
    CalendarDouble* y = static_cast<PythonCalendarDouble*>(static_cast<PyObject*>(field))->obj;
    obj->setMaximum(y);
  }
  else if (attr.isA(Tags::tag_hidden))
    obj->setHidden(field.getBool());
  else if (attr.isA(Tags::tag_cost))
    obj->setCost(field.getDouble());
  else
    return -1;  // Error
  return 0;  // OK
}


DECLARE_EXPORT PyObject* PythonResourceDefault::getattro(const Attribute& attr)
{
  return PythonResource(obj).getattro(attr); 
}


DECLARE_EXPORT int PythonResourceDefault::setattro(const Attribute& attr, const PythonObject& field)
{
  return PythonResource(obj).setattro(attr, field);
}


DECLARE_EXPORT PyObject* PythonResourceInfinite::getattro(const Attribute& attr)
{
  return PythonResource(obj).getattro(attr);
}


DECLARE_EXPORT int PythonResourceInfinite::setattro(const Attribute& attr, const PythonObject& field)
{
  return PythonResource(obj).setattro(attr, field);
}

}
