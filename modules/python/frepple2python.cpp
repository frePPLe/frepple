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

#include "embeddedpython.h"

namespace module_python
{

//
// INTERFACE FOR PLAN
//


int PythonPlan::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = getType();
  x.setName("parameters");
  x.setDoc("frePPLe global settings");
  x.supportgetattro();
  x.supportsetattro();
  int tmp =x.typeReady(m);

  // Add access to the information with a global attribute
  return PyModule_AddObject(m, "settings", new PythonPlan) + tmp;
}


PyObject* PythonPlan::getattro(const XMLElement& field)
{
  if (field.isA(Tags::tag_name))
    return PythonObject(Plan::instance().getName());
  if (field.isA(Tags::tag_description))
    return PythonObject(Plan::instance().getDescription());
  if (field.isA(Tags::tag_current))
    return PythonObject(Plan::instance().getCurrent());
  if (field.isA(Tags::tag_logfile))
    return PythonObject(Environment::getLogFile());
  return NULL;
}


int PythonPlan::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    Plan::instance().setName(value.getString());  
  else if (field.isA(Tags::tag_description))
    Plan::instance().setDescription(value.getString());
  else if (field.isA(Tags::tag_current))
    Plan::instance().setCurrent(value.getDate()); 
  else if (field.isA(Tags::tag_logfile))
    Environment::setLogFile(value.getString());
  else
    return -1; // Error
  return 0;  // OK
}


//
// INTERFACE FOR BUFFER
//


PyObject* PythonBuffer::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (field.isA(Tags::tag_description))
    return PythonObject(obj->getDescription());
  if (field.isA(Tags::tag_category))
    return PythonObject(obj->getCategory());
  if (field.isA(Tags::tag_subcategory))
    return PythonObject(obj->getSubCategory());
  if (field.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (field.isA(Tags::tag_location))
    return PythonObject(obj->getLocation());
  if (field.isA(Tags::tag_producing))
    return PythonObject(obj->getProducingOperation());
  if (field.isA(Tags::tag_item))
    return PythonObject(obj->getItem());
  if (field.isA(Tags::tag_onhand))
    return PythonObject(obj->getOnHand());
  if (field.isA(Tags::tag_flowplans))
    return new PythonFlowPlanIterator(obj);
  if (field.isA(Tags::tag_maximum))
    return PythonObject(obj->getMaximum());
  if (field.isA(Tags::tag_minimum))
    return PythonObject(obj->getMinimum());
  if (field.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
  if (field.isA(Tags::tag_flows))
    return new PythonFlowIterator(obj);
  if (field.isA(Tags::tag_level))
    return PythonObject(obj->getLevel());
  if (field.isA(Tags::tag_cluster))
    return PythonObject(obj->getCluster());
  // @todo support member iteration for buffer, res, dem, item, ...
  // PythonBufferIterator becomes an abstract class: defines the pytype and an abstract iternext.
  // 2 subclasses then implement it: an iterator over all buffers, and another one over all members.
	return NULL;
}


int PythonBuffer::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    obj->setName(value.getString());
  else if (field.isA(Tags::tag_description))
    obj->setDescription(value.getString());
  else if (field.isA(Tags::tag_category))
    obj->setCategory(value.getString());
  else if (field.isA(Tags::tag_subcategory))
    obj->setSubCategory(value.getString());
  else if (field.isA(Tags::tag_owner))
  {
    if (!value.check(PythonBuffer::getType()))
    {
      PyErr_SetString(PythonDataException, "buffer owner must be of type buffer");
      return -1;
    }
    Buffer* y = static_cast<PythonBuffer*>(static_cast<PyObject*>(value))->obj;
    obj->setOwner(y);
  }
  else if (field.isA(Tags::tag_location))
  {
    if (!value.check(PythonLocation::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer location must be of type location");
      return -1;
    }
    Location* y = static_cast<PythonLocation*>(static_cast<PyObject*>(value))->obj;
    obj->setLocation(y);
  }
  else if (field.isA(Tags::tag_item))
  {
    if (!value.check(PythonItem::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer item must be of type item");
      return -1;
    }
    Item* y = static_cast<PythonItem*>(static_cast<PyObject*>(value))->obj;
    obj->setItem(y);
  }
  else if (field.isA(Tags::tag_maximum))
  {
    if (!value.check(PythonCalendarDouble::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer maximum must be of type calendar_double");
      return -1;
    }
    CalendarDouble* y = static_cast<PythonCalendarDouble*>(static_cast<PyObject*>(value))->obj;
    obj->setMaximum(y);
  }
  else if (field.isA(Tags::tag_minimum))
  {
    if (!value.check(PythonCalendarDouble::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer minimum must be of type calendar_double");
      return -1;
    }
    CalendarDouble* y = static_cast<PythonCalendarDouble*>(static_cast<PyObject*>(value))->obj;
    obj->setMinimum(y);
  }
  else if (field.isA(Tags::tag_onhand))
    obj->setOnHand(value.getDouble());
  else if (field.isA(Tags::tag_producing))
  {
    if (!value.check(PythonOperation::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer producing must be of type operation");
      return -1;
    }
    Operation* y = static_cast<PythonOperation*>(static_cast<PyObject*>(value))->obj;
    obj->setProducingOperation(y);
  }
  else if (field.isA(Tags::tag_hidden))
    obj->setHidden(value.getBool());
  else
    return -1;  // Error
  return 0;  // OK
}


PyObject* PythonBufferDefault::getattro(const XMLElement& field)
{
  return PythonBuffer(obj).getattro(field); 
}


int PythonBufferDefault::setattro(const XMLElement& field, const PythonObject& value)
{
  // @todo avoid constructing a PythonBuffer object to call the base class
  // This is currently not really feasible (no casting between the classes is possible)
  // When the XML and Python framework will be unified, this will be solved: we'll basically
  // have a single call to the getAttribute() method of the default buffer, which can call
  // the getAttribute function of the parent class.
  return PythonBuffer(obj).setattro(field,value);  
}


PyObject* PythonBufferInfinite::getattro(const XMLElement& field)
{
  return PythonBuffer(obj).getattro(field);
}


int PythonBufferInfinite::setattro(const XMLElement& field, const PythonObject& value)
{
  return PythonBuffer(obj).setattro(field,value);
}


PyObject* PythonBufferProcure::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_leadtime))
    return PythonObject(obj->getLeadtime());
  if (field.isA(Tags::tag_mininventory))
    return PythonObject(obj->getMinimumInventory());
  if (field.isA(Tags::tag_maxinventory))
    return PythonObject(obj->getMaximumInventory());
  if (field.isA(Tags::tag_mininterval))
    return PythonObject(obj->getMinimumInterval());
  if (field.isA(Tags::tag_maxinterval))
    return PythonObject(obj->getMaximumInterval());
  if (field.isA(Tags::tag_fence))
    return PythonObject(obj->getFence());
  if (field.isA(Tags::tag_size_minimum))
    return PythonObject(obj->getSizeMinimum());
  if (field.isA(Tags::tag_size_multiple))
    return PythonObject(obj->getSizeMultiple());
  if (field.isA(Tags::tag_size_maximum))
    return PythonObject(obj->getSizeMaximum());
  return PythonBuffer(obj).getattro(field);
}


int PythonBufferProcure::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_leadtime))
    obj->setLeadtime(value.getTimePeriod());
  else if (field.isA(Tags::tag_mininventory))
    obj->setMinimumInventory(value.getDouble());
  else if (field.isA(Tags::tag_maxinventory))
    obj->setMaximumInventory(value.getDouble());
  else if (field.isA(Tags::tag_mininterval))
    obj->setMinimumInterval(value.getTimePeriod());
  else if (field.isA(Tags::tag_maxinterval))
    obj->setMaximumInterval(value.getTimePeriod());
  else if (field.isA(Tags::tag_size_minimum))
    obj->setSizeMinimum(value.getDouble());
  else if (field.isA(Tags::tag_size_multiple))
    obj->setSizeMultiple(value.getDouble());
  else if (field.isA(Tags::tag_size_maximum))
    obj->setSizeMaximum(value.getDouble());
  else if (field.isA(Tags::tag_fence))
    obj->setFence(value.getTimePeriod());
  else
    return PythonBuffer(obj).setattro(field,value);
  return 0;
}


//
// INTERFACE FOR LOCATION
//


PyObject* PythonLocation::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (field.isA(Tags::tag_description))
    return PythonObject(obj->getDescription());
  if (field.isA(Tags::tag_category))
    return PythonObject(obj->getCategory());
  if (field.isA(Tags::tag_subcategory))
    return PythonObject(obj->getSubCategory());
  if (field.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (field.isA(Tags::tag_available))
    return PythonObject(obj->getAvailable());
  if (field.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
	return NULL;
}


int PythonLocation::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    obj->setName(value.getString());
  else if (field.isA(Tags::tag_description))
    obj->setDescription(value.getString());
  else if (field.isA(Tags::tag_category))
    obj->setCategory(value.getString());
  else if (field.isA(Tags::tag_subcategory))
    obj->setSubCategory(value.getString());
  else if (field.isA(Tags::tag_owner))
  {
    if (!value.check(PythonLocation::getType())) 
    {
      PyErr_SetString(PythonDataException, "location owner must be of type location");
      return -1;
    }
    Location* y = static_cast<PythonLocation*>(static_cast<PyObject*>(value))->obj;
    obj->setOwner(y);
  }
  else if (field.isA(Tags::tag_available))
  {
    if (!value.check(PythonCalendarBool::getType())) 
    {
      PyErr_SetString(PythonDataException, "location calendar must be of type calendar_bool");
      return -1;
    }
    CalendarBool* y = static_cast<PythonCalendarBool*>(static_cast<PyObject*>(value))->obj;
    obj->setAvailable(y);
  }
  else if (field.isA(Tags::tag_hidden))
    obj->setHidden(value.getBool());
  else
    return -1;
  return 0;
}


PyObject* PythonLocationDefault::getattro(const XMLElement& field)
{
  return PythonLocation(obj).getattro(field);
}


int PythonLocationDefault::setattro(const XMLElement& field, const PythonObject& value)
{
 return PythonLocation(obj).setattro(field,value);
}




//
// INTERFACE FOR CUSTOMER
//


PyObject* PythonCustomer::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (field.isA(Tags::tag_description))
    return PythonObject(obj->getDescription());
  if (field.isA(Tags::tag_category))
    return PythonObject(obj->getCategory());
  if (field.isA(Tags::tag_subcategory))
    return PythonObject(obj->getSubCategory());
  if (field.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (field.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
	return NULL;
}


int PythonCustomer::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    obj->setName(value.getString());
  else if (field.isA(Tags::tag_description))
    obj->setDescription(value.getString());
  else if (field.isA(Tags::tag_category))
    obj->setCategory(value.getString());
  else if (field.isA(Tags::tag_subcategory))
    obj->setSubCategory(value.getString());
  else if (field.isA(Tags::tag_owner))
  {
    if (!value.check(PythonCustomer::getType())) 
    {
      PyErr_SetString(PythonDataException, "customer owner must be of type customer");
      return -1;
    }
    Customer* y = static_cast<PythonCustomer*>(static_cast<PyObject*>(value))->obj;
    obj->setOwner(y);
  }
  else if (field.isA(Tags::tag_hidden))
    obj->setHidden(value.getBool());
  else
    return -1;
  return 0;
}


PyObject* PythonCustomerDefault::getattro(const XMLElement& field)
{
  return PythonCustomer(obj).getattro(field);
}


int PythonCustomerDefault::setattro(const XMLElement& field, const PythonObject& value)
{
 return PythonCustomer(obj).setattro(field,value);
}


//
// INTERFACE FOR ITEM
//


PyObject* PythonItem::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (field.isA(Tags::tag_description))
    return PythonObject(obj->getDescription());
  if (field.isA(Tags::tag_category))
    return PythonObject(obj->getCategory());
  if (field.isA(Tags::tag_subcategory))
    return PythonObject(obj->getSubCategory());
  if (field.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (field.isA(Tags::tag_operation))
    return PythonObject(obj->getOperation());
  if (field.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
	return NULL;
}


int PythonItem::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    obj->setName(value.getString());
  else if (field.isA(Tags::tag_description))
    obj->setDescription(value.getString());
  else if (field.isA(Tags::tag_category))
    obj->setCategory(value.getString());
  else if (field.isA(Tags::tag_subcategory))
    obj->setSubCategory(value.getString());
  else if (field.isA(Tags::tag_owner))
  {
    if (!value.check(PythonItem::getType())) 
    {
      PyErr_SetString(PythonDataException, "item owner must be of type item");
      return -1;
    }
    Item* y = static_cast<PythonItem*>(static_cast<PyObject*>(value))->obj;
    obj->setOwner(y);
  }
  else if (field.isA(Tags::tag_operation))
  {
    if (!value.check(PythonOperation::getType())) 
    {
      PyErr_SetString(PythonDataException, "item operation must be of type operation");
      return -1;
    }
    Operation* y = static_cast<PythonOperation*>(static_cast<PyObject*>(value))->obj;
    obj->setOperation(y);
  }
  else if (field.isA(Tags::tag_hidden))
    obj->setHidden(value.getBool());
  else
    return -1;
  return 0;
}


PyObject* PythonItemDefault::getattro(const XMLElement& field)
{
  return PythonItem(obj).getattro(field);
}


int PythonItemDefault::setattro(const XMLElement& field, const PythonObject& value)
{
 return PythonItem(obj).setattro(field,value);
}


//
// INTERFACE FOR CALENDAR
//


PyObject* PythonCalendar::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (field.isA(Tags::tag_buckets))
    return new PythonCalendarBucketIterator(obj);
	return NULL;
}


int PythonCalendar::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    obj->setName(value.getString());
  else
    return -1;  // Error
  return 0;  // OK
}


PyObject* PythonCalendarVoid::getattro(const XMLElement& field)
{
  return PythonCalendar(obj).getattro(field); 
}


int PythonCalendarVoid::setattro(const XMLElement& field, const PythonObject& value)
{
   return PythonCalendar(obj).setattro(field,value);
}


PyObject* PythonCalendarBool::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_default))
    return PythonObject(obj->getDefault());
  return PythonCalendar(obj).getattro(field); 
}


int PythonCalendarBool::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_default))
    obj->setDefault(value.getBool());
  else
    return PythonCalendar(obj).setattro(field,value);
  return 0;
}


PyObject* PythonCalendarDouble::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_default))
    return PythonObject(obj->getDefault());
  return PythonCalendar(obj).getattro(field); 
}


int PythonCalendarDouble::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_default))
    obj->setDefault(value.getDouble());
  else
    return PythonCalendar(obj).setattro(field,value);
  return 0;
}


int PythonCalendarBucketIterator::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonCalendarBucketIterator>::getType();
  x.setName("calendarBucketIterator");
  x.setDoc("frePPLe iterator for calendar buckets");
  x.supportiter();
  return x.typeReady(m);
}


PyObject* PythonCalendarBucketIterator::iternext()
{  
  if (i == cal->endBuckets()) return NULL;
  return new PythonCalendarBucket(cal, &*(i++));
}


int PythonCalendarBucket::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonCalendarBucket>::getType();
  x.setName("calendarBucket");
  x.setDoc("frePPLe calendar bucket");
  x.supportgetattro();
  x.supportsetattro();
  return x.typeReady(m);
}


PyObject* PythonCalendarBucket::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_start))
    return PythonObject(obj->getStart());
  if (field.isA(Tags::tag_end))
    return PythonObject(obj->getEnd());
  if (field.isA(Tags::tag_value))
  {
    if (cal->getType() == CalendarDouble::metadata)
      return PythonObject(dynamic_cast< CalendarValue<double>::BucketValue* >(obj)->getValue());
    if (cal->getType() == CalendarBool::metadata)
      return PythonObject(dynamic_cast< CalendarValue<bool>::BucketValue* >(obj)->getValue());
    if (cal->getType() == CalendarInt::metadata)
      return PythonObject(dynamic_cast< CalendarValue<int>::BucketValue* >(obj)->getValue());
    if (cal->getType() == CalendarString::metadata)
      return PythonObject(dynamic_cast< CalendarValue<string>::BucketValue* >(obj)->getValue());
    if (cal->getType() == CalendarVoid::metadata) return Py_None;
    PyErr_SetString(PythonLogicException, "calendar type not recognized");
    return NULL;
  }
  if (field.isA(Tags::tag_priority))
    return PythonObject(obj->getPriority());
  if (field.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  return NULL; 
}


int PythonCalendarBucket::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    obj->setName(value.getString());
  else if (field.isA(Tags::tag_start))
    obj->setStart(value.getDate());
  else if (field.isA(Tags::tag_end))
    obj->setEnd(value.getDate());
  else if (field.isA(Tags::tag_priority))
    obj->setPriority(value.getInt());
  else if (field.isA(Tags::tag_value))
  {
    if (cal->getType() == CalendarDouble::metadata)
      dynamic_cast< CalendarValue<double>::BucketValue* >(obj)->setValue(value.getDouble());
    else if (cal->getType() == CalendarBool::metadata)
      dynamic_cast< CalendarValue<bool>::BucketValue* >(obj)->setValue(value.getBool());
    else if (cal->getType() == CalendarInt::metadata)
      dynamic_cast< CalendarValue<int>::BucketValue* >(obj)->setValue(value.getInt());
    else if (cal->getType() == CalendarString::metadata)
      dynamic_cast< CalendarValue<string>::BucketValue* >(obj)->setValue(value.getString());
    else if (cal->getType() == CalendarVoid::metadata) 
      return -1;
    else
    {
      PyErr_SetString(PythonLogicException, "calendar type not recognized");
      return -1;
    }
  }
  else
    return -1;
  return 0;
}


//
// INTERFACE FOR DEMAND
//


PyObject* PythonDemand::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (field.isA(Tags::tag_quantity))
    return PythonObject(obj->getQuantity());
  if (field.isA(Tags::tag_due))
    return PythonObject(obj->getDue());
  if (field.isA(Tags::tag_priority))
    return PythonObject(obj->getPriority());
  if (field.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (field.isA(Tags::tag_item))
    return PythonObject(obj->getItem());
  if (field.isA(Tags::tag_customer))
    return PythonObject(obj->getCustomer());
  if (field.isA(Tags::tag_operation))
    return PythonObject(obj->getOperation());
  if (field.isA(Tags::tag_description))
    return PythonObject(obj->getDescription());
  if (field.isA(Tags::tag_category))
    return PythonObject(obj->getCategory());
  if (field.isA(Tags::tag_subcategory))
    return PythonObject(obj->getSubCategory());
  if (field.isA(Tags::tag_minshipment))
    return PythonObject(obj->getMinShipment());
  if (field.isA(Tags::tag_maxlateness))
    return PythonObject(obj->getMaxLateness());
  if (field.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
  if (field.isA(Tags::tag_operationplans))
    return new PythonDemandPlanIterator(obj);
  if (field.isA(Tags::tag_pegging))
    return new PythonPeggingIterator(obj);
  return NULL;
}


int PythonDemand::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    obj->setName(value.getString());
  else if (field.isA(Tags::tag_priority))
    obj->setPriority(value.getInt());
  else if (field.isA(Tags::tag_quantity))
    obj->setQuantity(value.getDouble());
  else if (field.isA(Tags::tag_due))
    obj->setDue(value.getDate());
  else if (field.isA(Tags::tag_item))
  {
    if (!value.check(PythonItem::getType())) 
    {
      PyErr_SetString(PythonDataException, "demand item must be of type item");
      return -1;
    }
    Item* y = static_cast<PythonItem*>(static_cast<PyObject*>(value))->obj;
    obj->setItem(y);
  }
  else if (field.isA(Tags::tag_customer))
  {
    if (!value.check(PythonCustomer::getType())) 
    {
      PyErr_SetString(PythonDataException, "demand customer must be of type customer");
      return -1;
    }
    Customer* y = static_cast<PythonCustomer*>(static_cast<PyObject*>(value))->obj;
    obj->setCustomer(y);
  }
  else if (field.isA(Tags::tag_description))
    obj->setDescription(value.getString());
  else if (field.isA(Tags::tag_category))
    obj->setCategory(value.getString());
  else if (field.isA(Tags::tag_subcategory))
    obj->setSubCategory(value.getString());
  else if (field.isA(Tags::tag_minshipment))
    obj->setMinShipment(value.getDouble());
  else if (field.isA(Tags::tag_maxlateness))
    obj->setMaxLateness(value.getTimePeriod());
  else if (field.isA(Tags::tag_owner))
  {
    if (!value.check(PythonDemand::getType()))
    {
      PyErr_SetString(PythonDataException, "demand owner must be of type demand");
      return -1;
    }
    Demand* y = static_cast<PythonDemand*>(static_cast<PyObject*>(value))->obj;
    obj->setOwner(y);
  }
  else if (field.isA(Tags::tag_operation))
  {
    if (!value.check(PythonOperation::getType()))
    {
      PyErr_SetString(PythonDataException, "demand operation must be of type operation");
      return -1;
    }
    Operation* y = static_cast<PythonOperation*>(static_cast<PyObject*>(value))->obj;
    obj->setOperation(y);
  }
  else if (field.isA(Tags::tag_hidden))
    obj->setHidden(value.getBool());
  else
    return -1;  // Error
  return 0;  // OK
}


PyObject* PythonDemandDefault::getattro(const XMLElement& field)
{
  return PythonDemand(obj).getattro(field); 
}


int PythonDemandDefault::setattro(const XMLElement& field, const PythonObject& value)
{
  return PythonDemand(obj).setattro(field,value);
}


//
// INTERFACE FOR RESOURCE
//


PyObject* PythonResource::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (field.isA(Tags::tag_description))
    return PythonObject(obj->getDescription());
  if (field.isA(Tags::tag_category))
    return PythonObject(obj->getCategory());
  if (field.isA(Tags::tag_subcategory))
    return PythonObject(obj->getSubCategory());
  if (field.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (field.isA(Tags::tag_location))
    return PythonObject(obj->getLocation());
  if (field.isA(Tags::tag_maximum))
    return PythonObject(obj->getMaximum());
  if (field.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
  if (field.isA(Tags::tag_loadplans))
    return new PythonLoadPlanIterator(obj);
  if (field.isA(Tags::tag_loads))
    return new PythonLoadIterator(obj);
  if (field.isA(Tags::tag_level))
    return PythonObject(obj->getLevel());
  if (field.isA(Tags::tag_cluster))
    return PythonObject(obj->getCluster());
	return NULL;
}


int PythonResource::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    obj->setName(value.getString());
  else if (field.isA(Tags::tag_description))
    obj->setDescription(value.getString());
  else if (field.isA(Tags::tag_category))
    obj->setCategory(value.getString());
  else if (field.isA(Tags::tag_subcategory))
    obj->setSubCategory(value.getString());
  else if (field.isA(Tags::tag_owner))
  {
    if (!value.check(PythonResource::getType()))
    {
      PyErr_SetString(PythonDataException, "resource owner must be of type resource");
      return -1;
    }
    Resource* y = static_cast<PythonResource*>(static_cast<PyObject*>(value))->obj;
    obj->setOwner(y);
  }
  else if (field.isA(Tags::tag_location))
  {
    if (!value.check(PythonLocation::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer location must be of type location");
      return -1;
    }
    Location* y = static_cast<PythonLocation*>(static_cast<PyObject*>(value))->obj;
    obj->setLocation(y);
  }
  else if (field.isA(Tags::tag_maximum))
  {
    if (!value.check(PythonCalendarDouble::getType())) 
    {
      PyErr_SetString(PythonDataException, "resource maximum must be of type calendar_double");
      return -1;
    }
    CalendarDouble* y = static_cast<PythonCalendarDouble*>(static_cast<PyObject*>(value))->obj;
    obj->setMaximum(y);
  }
  else if (field.isA(Tags::tag_hidden))
    obj->setHidden(value.getBool());
  else
    return -1;  // Error
  return 0;  // OK
}


PyObject* PythonResourceDefault::getattro(const XMLElement& field)
{
  return PythonResource(obj).getattro(field); 
}


int PythonResourceDefault::setattro(const XMLElement& field, const PythonObject& value)
{
  return PythonResource(obj).setattro(field,value);
}


PyObject* PythonResourceInfinite::getattro(const XMLElement& field)
{
  return PythonResource(obj).getattro(field);
}


int PythonResourceInfinite::setattro(const XMLElement& field, const PythonObject& value)
{
  return PythonResource(obj).setattro(field,value);
}


//
// INTERFACE FOR OPERATION
//


PyObject* PythonOperation::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (field.isA(Tags::tag_description))
    return PythonObject(obj->getDescription());
  if (field.isA(Tags::tag_category))
    return PythonObject(obj->getCategory());
  if (field.isA(Tags::tag_subcategory))
    return PythonObject(obj->getSubCategory());
  if (field.isA(Tags::tag_location))
    return PythonObject(obj->getLocation());
  if (field.isA(Tags::tag_fence))
    return PythonObject(obj->getFence());
  if (field.isA(Tags::tag_size_minimum))
    return PythonObject(obj->getSizeMinimum());
  if (field.isA(Tags::tag_size_multiple))
    return PythonObject(obj->getSizeMultiple());
  if (field.isA(Tags::tag_pretime))
    return PythonObject(obj->getPreTime());
  if (field.isA(Tags::tag_posttime))
    return PythonObject(obj->getPostTime());
  if (field.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
  if (field.isA(Tags::tag_loads))
    return new PythonLoadIterator(obj);
  if (field.isA(Tags::tag_flows))
    return new PythonFlowIterator(obj);
  if (field.isA(Tags::tag_level))
    return PythonObject(obj->getLevel());
  if (field.isA(Tags::tag_cluster))
    return PythonObject(obj->getCluster());
	return NULL;
}


int PythonOperation::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    obj->setName(value.getString());
  else if (field.isA(Tags::tag_description))
    obj->setDescription(value.getString());
  else if (field.isA(Tags::tag_category))
    obj->setCategory(value.getString());
  else if (field.isA(Tags::tag_subcategory))
    obj->setSubCategory(value.getString());
  else if (field.isA(Tags::tag_location))
  {
    if (!value.check(PythonLocation::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer location must be of type location");
      return -1;
    }
    Location* y = static_cast<PythonLocation*>(static_cast<PyObject*>(value))->obj;
    obj->setLocation(y);
  }
  else if (field.isA(Tags::tag_fence))
    obj->setFence(value.getTimePeriod());
  else if (field.isA(Tags::tag_size_minimum))
    obj->setSizeMinimum(value.getDouble());
  else if (field.isA(Tags::tag_size_multiple))
    obj->setSizeMultiple(value.getDouble());
  else if (field.isA(Tags::tag_pretime))
    obj->setPreTime(value.getTimePeriod());
  else if (field.isA(Tags::tag_posttime))
    obj->setPostTime(value.getTimePeriod());
  else if (field.isA(Tags::tag_hidden))
    obj->setHidden(value.getBool());
  else
    return -1;  // Error
  return 0;  // OK
}


PyObject* PythonOperationFixedTime::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_duration))
    return PythonObject(obj->getDuration());
  return PythonOperation(obj).getattro(field); 
}


int PythonOperationFixedTime::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_duration))
    obj->setDuration(value.getTimePeriod());
  else
    return PythonOperation(obj).setattro(field,value);
  return 0;
}


PyObject* PythonOperationTimePer::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_duration))
    return PythonObject(obj->getDuration());
  if (field.isA(Tags::tag_duration))
    return PythonObject(obj->getDurationPer());
  return PythonOperation(obj).getattro(field); 
}


int PythonOperationTimePer::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_duration))
    obj->setDuration(value.getTimePeriod());
  else if (field.isA(Tags::tag_duration_per))
    obj->setDurationPer(value.getTimePeriod());
  else
    return PythonOperation(obj).setattro(field,value);
  return 0;
}


PyObject* PythonOperationAlternate::getattro(const XMLElement& field)
{
  // @todo alternates
  return PythonOperation(obj).getattro(field); 
}


int PythonOperationAlternate::setattro(const XMLElement& field, const PythonObject& value)
{
  // @todo alternates
  return PythonOperation(obj).setattro(field,value);
}


PyObject* PythonOperationRouting::getattro(const XMLElement& field)
{
  // @todo steps
  return PythonOperation(obj).getattro(field); 
}


int PythonOperationRouting::setattro(const XMLElement& field, const PythonObject& value)
{
  // @todo steps
  return PythonOperation(obj).setattro(field,value);
}


//
// INTERFACE FOR PROBLEM
//


int PythonProblem::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = getType();
  x.setName("problem");
  x.setDoc("frePPLe problem");
  x.supportgetattro();
  const_cast<MetaCategory&>(Problem::metadata).factoryPythonProxy = proxy;
  return x.typeReady(m);
}


PyObject* PythonProblem::getattro(const XMLElement& field)
{
  if (!prob) return Py_None;
  if (field.isA(Tags::tag_name))
    return PythonObject(prob->getType().type);
  if (field.isA(Tags::tag_description))
    return PythonObject(prob->getDescription());
  if (field.isA(Tags::tag_entity))
    return PythonObject(prob->getOwner()->getEntity()->getType().category->group);
  if (field.isA(Tags::tag_start))
    return PythonObject(prob->getDateRange().getStart());
  if (field.isA(Tags::tag_end))
    return PythonObject(prob->getDateRange().getEnd());
  if (field.isA(Tags::tag_weight))
    return PythonObject(prob->getWeight());
  return NULL;
}


// 
// INTERFACE FOR OPERATIONPLAN
//


int PythonOperationPlan::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = getType();
  x.setName("operationplan");
  x.setDoc("frePPLe operationplan");
  x.supportgetattro();
  x.supportsetattro();
  const_cast<MetaCategory&>(OperationPlan::metadata).factoryPythonProxy = proxy;
  return x.typeReady(m);
}


PyObject* PythonOperationPlan::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_id))
    return PythonObject(obj->getIdentifier());
  if (field.isA(Tags::tag_operation))
    return PythonObject(obj->getOperation());
  if (field.isA(Tags::tag_quantity))
    return PythonObject(obj->getQuantity());
  if (field.isA(Tags::tag_start))
    return PythonObject(obj->getDates().getStart());
  if (field.isA(Tags::tag_end))
    return PythonObject(obj->getDates().getEnd());
  if (field.isA(Tags::tag_demand))
    return PythonObject(obj->getDemand());
  if (field.isA(Tags::tag_locked))
    return PythonObject(obj->getLocked());
  if (field.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (field.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
  return NULL;
}


int PythonOperationPlan::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_quantity))
    obj->setQuantity(value.getDouble());
  else if (field.isA(Tags::tag_start))
    obj->setStart(value.getDate());
  else if (field.isA(Tags::tag_end))
    obj->setEnd(value.getDate());
  else if (field.isA(Tags::tag_locked))
    obj->setLocked(value.getBool());
  else if (field.isA(Tags::tag_demand))
  {
    if (!value.check(PythonDemand::getType())) 
    {
      PyErr_SetString(PythonDataException, "operationplan demand must be of type demand");
      return -1;
    }
    Demand* y = static_cast<PythonDemand*>(static_cast<PyObject*>(value))->obj;
    obj->setDemand(y);
  }
  else if (field.isA(Tags::tag_owner))
  {
    if (!value.check(PythonOperationPlan::getType())) 
    {
      PyErr_SetString(PythonDataException, "operationplan demand must be of type demand");
      return -1;
    }
    OperationPlan* y = static_cast<PythonOperationPlan*>(static_cast<PyObject*>(value))->obj;
    obj->setOwner(y);
  }
  else
    return -1;
  return 0;  
}


//
// INTERFACE FOR FLOWPLAN
//


int PythonFlowPlan::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = getType();
  x.setName("flowplan");
  x.setDoc("frePPLe flowplan");
  x.supportgetattro();
  return x.typeReady(m);
}


PyObject* PythonFlowPlan::getattro(const XMLElement& field)
{
  if (!fl) return Py_None;
  if (field.isA(Tags::tag_operationplan))
    return PythonObject(fl->getOperationPlan());
  if (field.isA(Tags::tag_quantity))
    return PythonObject(fl->getQuantity());
  if (field.isA(Tags::tag_date))
    return PythonObject(fl->getDate());
  if (field.isA(Tags::tag_onhand))
    return PythonObject(fl->getOnhand());
  if (field.isA(Tags::tag_buffer))
    return PythonObject(fl->getFlow()->getBuffer());
  return NULL;
}


int PythonFlowPlanIterator::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonFlowPlanIterator>::getType();
  x.setName("flowplanIterator");
  x.setDoc("frePPLe iterator for flowplan");
  x.supportiter();
  return x.typeReady(m);
}


PyObject* PythonFlowPlanIterator::iternext()
{
  // Skip uninteresting entries
  while (i != buf->getFlowPlans().end() && i->getQuantity()==0.0) 
    ++i;
  if (i == buf->getFlowPlans().end()) return NULL;

  // Return result
  return new PythonFlowPlan(const_cast<FlowPlan*>(dynamic_cast<const FlowPlan*>(&*(i++))));
}


//
// INTERFACE FOR LOADPLAN
//


int PythonLoadPlan::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = getType();
  x.setName("loadplan");
  x.setDoc("frePPLe loadplan");
  x.supportgetattro();
  return x.typeReady(m);
}


PyObject* PythonLoadPlan::getattro(const XMLElement& field)
{
  if (!fl) return Py_None;
  if (field.isA(Tags::tag_operationplan))
    return PythonObject(fl->getOperationPlan());
  if (field.isA(Tags::tag_quantity))
    return PythonObject(fl->getQuantity());
  if (field.isA(Tags::tag_startdate))
    return PythonObject(fl->getDate());
  if (field.isA(Tags::tag_enddate))
    return PythonObject(fl->getOtherLoadPlan()->getDate());
  if (field.isA(Tags::tag_resource))
    return PythonObject(fl->getLoad()->getResource());
  return NULL;
}


int PythonLoadPlanIterator::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonLoadPlanIterator>::getType();
  x.setName("loadplanIterator");
  x.setDoc("frePPLe iterator for loadplan");
  x.supportiter();
  return x.typeReady(m);
}


PyObject* PythonLoadPlanIterator::iternext()
{  
  // Skip zero quantity loadplans and load ends
  while (i != res->getLoadPlans().end() && i->getQuantity()<=0.0) 
    ++i;
  if (i == res->getLoadPlans().end()) return NULL;

  // Return result
  return new PythonLoadPlan(const_cast<LoadPlan*>(dynamic_cast<const LoadPlan*>(&*(i++))));
}


//
// INTERFACE FOR DEMAND DELIVERY OPERATIONPLANS
//


int PythonDemandPlanIterator::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonDemandPlanIterator>::getType();
  x.setName("demandplanIterator");
  x.setDoc("frePPLe iterator for demand delivery operationplans");
  x.supportiter();
  return x.typeReady(m);
}


PyObject* PythonDemandPlanIterator::iternext()
{  
  if (i == dem->getDelivery().end()) return NULL;
  return new PythonOperationPlan(const_cast<OperationPlan*>(&**(i++)));
}


//
// INTERFACE FOR DEMAND PEGGING
//


int PythonPeggingIterator::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonPeggingIterator>::getType();
  x.setName("peggingIterator");
  x.setDoc("frePPLe iterator for demand pegging");
  x.supportiter();
  return x.typeReady(m);
}


PyObject* PythonPeggingIterator::iternext()
{  
  if (!i) return NULL;

  // Pass the result to Python.
  // This is different than the other iterators! We need to capture the 
  // current state of the iterator before decrementing it. For other iterators
  // we can create a proxy object meeting this requirement, but not for the
  // pegging iterator.
  PyObject* result = Py_BuildValue("{s:i,s:N,s:N,s:N,s:N,s:N,s:f,s:f,s:i}",
    "level", i.getLevel(),
    "consuming", static_cast<PyObject*>(PythonObject(i.getConsumingOperationplan())),
    "cons_date", static_cast<PyObject*>(PythonObject(i.getConsumingDate())),
    "producing", static_cast<PyObject*>(PythonObject(i.getProducingOperationplan())),
    "prod_date", static_cast<PyObject*>(PythonObject(i.getProducingDate())),
    "buffer", static_cast<PyObject*>(PythonObject(i.getBuffer())),
    "quantity_demand", i.getQuantityDemand(),
    "quantity_buffer", i.getQuantityBuffer(),
    "pegged", i.getPegged() ? 1 : 0
    );

  --i;  
  return result;
}


//
// INTERFACE FOR LOAD
//


int PythonLoad::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = getType();
  x.setName("load");
  x.setDoc("frePPLe load");
  x.supportgetattro();
  x.supportsetattro();
  const_cast<MetaCategory&>(Load::metadata).factoryPythonProxy = proxy;
  return x.typeReady(m);
}


PyObject* PythonLoad::getattro(const XMLElement& field)
{
  if (!ld) return Py_None;
  if (field.isA(Tags::tag_resource))
    return PythonObject(ld->getResource());
  if (field.isA(Tags::tag_operation))
    return PythonObject(ld->getOperation());
  if (field.isA(Tags::tag_quantity))
    return PythonObject(ld->getQuantity());
  if (field.isA(Tags::tag_effective_end))
    return PythonObject(ld->getEffective().getEnd());
  if (field.isA(Tags::tag_effective_start))
    return PythonObject(ld->getEffective().getStart());
  return NULL;
}


int PythonLoad::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_resource))
  {
    if (!value.check(PythonResource::getType())) 
    {
      PyErr_SetString(PythonDataException, "load resource must be of type resource");
      return -1;
    }
    Resource* y = static_cast<PythonResource*>(static_cast<PyObject*>(value))->obj;
    ld->setResource(y);
  }
  else if (field.isA(Tags::tag_operation))
  {
    if (!value.check(PythonOperation::getType())) 
    {
      PyErr_SetString(PythonDataException, "load operation must be of type operation");
      return -1;
    }
    Operation* y = static_cast<PythonOperation*>(static_cast<PyObject*>(value))->obj;
    ld->setOperation(y);
  }
  else if (field.isA(Tags::tag_quantity))
    ld->setQuantity(value.getDouble());
  else if (field.isA(Tags::tag_effective_end))
    ld->setEffectiveEnd(value.getDate());
  else if (field.isA(Tags::tag_effective_start))
    ld->setEffectiveStart(value.getDate());
  else
    return -1;
  return 0;
}


int PythonLoadIterator::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonLoadIterator>::getType();
  x.setName("loadIterator");
  x.setDoc("frePPLe iterator for loads");
  x.supportiter();
  return x.typeReady(m);
}


PyObject* PythonLoadIterator::iternext()
{  
  if (res) 
  {
    // Iterate over loads on a resource 
    if (ir == res->getLoads().end()) return NULL;
    return PythonObject(const_cast<Load*>(&*(ir++)));
  }
  else
  {
    // Iterate over loads on an operation 
    if (io == oper->getLoads().end()) return NULL;
    return PythonObject(const_cast<Load*>(&*(io++)));
  }
}


//
// INTERFACE FOR FLOW
//


int PythonFlow::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = getType();
  x.setName("flow");
  x.setDoc("frePPLe flow");
  x.supportgetattro();
  x.supportsetattro();
  const_cast<MetaCategory&>(Flow::metadata).factoryPythonProxy = proxy;
  return x.typeReady(m);
}


PyObject* PythonFlow::getattro(const XMLElement& field)
{
  if (!fl) return Py_None;
  if (field.isA(Tags::tag_buffer))
    return PythonObject(fl->getBuffer());
  if (field.isA(Tags::tag_operation))
    return PythonObject(fl->getOperation());
  if (field.isA(Tags::tag_quantity))
    return PythonObject(fl->getQuantity());
  if (field.isA(Tags::tag_effective_end))
    return PythonObject(fl->getEffective().getEnd());
  if (field.isA(Tags::tag_effective_start))
    return PythonObject(fl->getEffective().getStart());
  return NULL;
}


int PythonFlow::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_buffer))
  {
    if (!value.check(PythonBuffer::getType())) 
    {
      PyErr_SetString(PythonDataException, "flow buffer must be of type buffer");
      return -1;
    }
    Buffer* y = static_cast<PythonBuffer*>(static_cast<PyObject*>(value))->obj;
    fl->setBuffer(y);
  }
  else if (field.isA(Tags::tag_operation))
  {
    if (!value.check(PythonOperation::getType())) 
    {
      PyErr_SetString(PythonDataException, "flow operation must be of type operation");
      return -1;
    }
    Operation* y = static_cast<PythonOperation*>(static_cast<PyObject*>(value))->obj;
    fl->setOperation(y);
  }
  else if (field.isA(Tags::tag_quantity))
    fl->setQuantity(value.getDouble());
  else if (field.isA(Tags::tag_effective_end))
    fl->setEffectiveEnd(value.getDate());
  else if (field.isA(Tags::tag_effective_start))
    fl->setEffectiveStart(value.getDate());
  else
    return -1;
  return 0;
}


int PythonFlowIterator::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonFlowIterator>::getType();
  x.setName("flowIterator");
  x.setDoc("frePPLe iterator for flows");
  x.supportiter();
  return x.typeReady(m);
}


PyObject* PythonFlowIterator::iternext()
{  
  if (buf) 
  {
    // Iterate over flows on a buffer 
    if (ib == buf->getFlows().end()) return NULL;
    return PythonObject(const_cast<Flow*>(&*(ib++)));
  }
  else
  {
    // Iterate over flows on an operation 
    if (io == oper->getFlows().end()) return NULL;
    return PythonObject(const_cast<Flow*>(&*(io++)));
  }
}


//
// INTERFACE FOR SOLVER
//


PyObject* PythonSolver::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (field.isA(Tags::tag_loglevel))
    return PythonObject(obj->getLogLevel());
	return NULL;
}


int PythonSolver::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_name))
    obj->setName(value.getString());
  else if (field.isA(Tags::tag_loglevel))
    obj->setLogLevel(value.getInt());
  else
    return -1;  // Error
  return 0;  // OK
}


PyObject* PythonSolverMRP::getattro(const XMLElement& field)
{
  if (!obj) return Py_None;
  if (field.isA(Tags::tag_constraints))
    return PythonObject(obj->getConstraints());
  if (field.isA(Tags::tag_maxparallel))
    return PythonObject(obj->getMaxParallel());
  return PythonSolver(obj).getattro(field); 
}


int PythonSolverMRP::setattro(const XMLElement& field, const PythonObject& value)
{
  if (field.isA(Tags::tag_constraints))
    obj->setConstraints(value.getInt());
  else if (field.isA(Tags::tag_maxparallel))
    obj->setMaxParallel(value.getInt());
  else
    return PythonSolver(obj).setattro(field,value);
  return 0;
}


PyObject *PythonSolver::solve(PyObject *self, PyObject *args)
{
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    Solver *sol = static_cast<PythonSolver*>(self)->obj;
    if (!sol) throw LogicException("Can't run NULL solver");
    sol->solve();    
  }
  catch(...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  Py_INCREF(Py_None);
  return Py_None;
}


} // End namespace
