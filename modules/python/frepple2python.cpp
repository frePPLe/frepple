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

// Type information of our Python extensions
PyTypeObject PythonProblem::InfoType;
PyTypeObject PythonFlowPlan::InfoType;
PyTypeObject PythonLoadPlan::InfoType;
PyTypeObject PythonOperationPlan::InfoType;
PyTypeObject PythonDemand::InfoType;
PyTypeObject PythonDemandPegging::InfoType;
PyTypeObject PythonDemandDelivery::InfoType;
PyTypeObject PythonBuffer::InfoType;
PyTypeObject PythonResource::InfoType;


//
// INTERFACE FOR PROBLEM
//


extern "C" PyObject* PythonProblem::create(PyTypeObject* type, PyObject *args, PyObject *kwargs)
{
  // Allocate memory
  PythonProblem* obj = PyObject_New(PythonProblem, &PythonProblem::InfoType);

  // Initialize the problem iterator
  Problem::begin();  // Required to trigger problem detection
  obj->iter = new Problem::const_iterator();

  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonProblem::next(PythonProblem* obj)
{
  if (*(obj->iter) != Problem::end())
  {
    PyObject* result = Py_BuildValue("{s:s,s:s,s:s,s:N,s:N,s:f}",
      "DESCRIPTION", (*(obj->iter))->getDescription().c_str(),
      "ENTITY", (*(obj->iter))->getOwner()->getEntity()->getType().category->group.c_str(),
      "TYPE", (*(obj->iter))->getType().type.c_str(),
      "START", PythonDateTime((*(obj->iter))->getDateRange().getStart()),
      "END", PythonDateTime((*(obj->iter))->getDateRange().getEnd()),
      "WEIGHT", (*(obj->iter))->getWeight()
      );
     ++*(obj->iter);
    return result;
  }
  else
    // Reached the end of the iteration
    return NULL;
}


//
// INTERFACE FOR FLOWPLAN
//


extern "C" PyObject* PythonFlowPlan::createFromBuffer(Buffer* v)
{
  // Allocate memory
  PythonFlowPlan* obj = PyObject_New(PythonFlowPlan, &PythonFlowPlan::InfoType);

  // Cast the buffer pointer and initialize the iterator
  obj->buf = v;
  obj->iter = obj->buf->getFlowPlans().begin();

  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonFlowPlan::next(PythonFlowPlan* obj)
{
  if (obj->iter != obj->buf->getFlowPlans().end())
  {
    const FlowPlan* f = dynamic_cast<const FlowPlan*>(&*(obj->iter));
    if (f && f->getHidden()) f = NULL;
    while (!f)
    {
      ++(obj->iter);
      if (obj->iter == obj->buf->getFlowPlans().end()) return NULL;
      f = dynamic_cast<const FlowPlan*>(&*(obj->iter));
      if (f && f->getHidden()) f = NULL;
    }
    PyObject* result = Py_BuildValue("{s:s,s:l,s:f,s:N,s:f}",
      "BUFFER", f->getFlow()->getBuffer()->getName().c_str(),
      "OPERATIONPLAN", f->getOperationPlan()->getIdentifier(),
      "QUANTITY", obj->iter->getQuantity(),
      "DATE", PythonDateTime(obj->iter->getDate()),
      "ONHAND", obj->iter->getOnhand()
      );
    ++(obj->iter);
    return result;
  }
  // Reached the end of the iteration
  return NULL;
}


//
// INTERFACE FOR LOADPLAN
//


extern "C" PyObject* PythonLoadPlan::createFromResource(Resource* v)
{
  // Allocate memory
  PythonLoadPlan* obj = PyObject_New(PythonLoadPlan, &PythonLoadPlan::InfoType);

  // Cast the resource pointer and initialize the iterator
  obj->res = v;
  obj->iter = obj->res->getLoadPlans().begin();

  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonLoadPlan::next(PythonLoadPlan* obj)
{
  if (obj->iter != obj->res->getLoadPlans().end())
  {
    const LoadPlan* f = dynamic_cast<const LoadPlan*>(&*(obj->iter));
    if (f && (f->getHidden() || f->getQuantity()<0)) f = NULL;
    while (!f)
    {
      ++(obj->iter);
      if (obj->iter == obj->res->getLoadPlans().end()) return NULL;
      f = dynamic_cast<const LoadPlan*>(&*(obj->iter));
      if (f && (f->getHidden() || f->getQuantity()<0)) f = NULL;
    }
    PyObject* result = Py_BuildValue("{s:s,s:l,s:f,s:N,s:N}",
      "RESOURCE", f->getLoad()->getResource()->getName().c_str(),
      "OPERATIONPLAN", f->getOperationPlan()->getIdentifier(),
      "QUANTITY", obj->iter->getQuantity(),
      "STARTDATE", PythonDateTime(f->getDate()),
      "ENDDATE", PythonDateTime(f->getOtherLoadPlan()->getDate())
      );
    ++(obj->iter);
    return result;
  }
  // Reached the end of the iteration
  return NULL;
}


//
// INTERFACE FOR DEMAND PEGGING
//


extern "C" PyObject* PythonDemandPegging::createFromDemand(Demand* v)
{
  // Allocate memory
  PythonDemandPegging* obj = PyObject_New(PythonDemandPegging, &PythonDemandPegging::InfoType);

  // Cast the demand pointer and initialize the iterator
  obj->dem = v;
  obj->iter = new PeggingIterator(v);

  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonDemandPegging::next(PythonDemandPegging* obj)
{
  // Reached the end of the iteration
  if (!obj->iter || !*(obj->iter)) return NULL;

  // Pass the result to Python
  OperationPlan::pointer p_opplan = obj->iter->getProducingOperationplan();
  OperationPlan::pointer c_opplan = obj->iter->getConsumingOperationplan();
  PyObject* result = Py_BuildValue("{s:i,s:l,s:N,s:l,s:N,s:z,s:f,s:f,s:i}",
    "LEVEL", obj->iter->getLevel(),
    "CONS_OPERATIONPLAN",
      (!c_opplan || c_opplan->getHidden()) ? 0 : c_opplan->getIdentifier(),
    "CONS_DATE", PythonDateTime(obj->iter->getConsumingDate()),
    "PROD_OPERATIONPLAN",
      (!p_opplan || p_opplan->getHidden()) ? 0 : p_opplan->getIdentifier(),
    "PROD_DATE", PythonDateTime(obj->iter->getProducingDate()),
    "BUFFER", obj->iter->getBuffer()->getHidden() ? NULL
      : obj->iter->getBuffer()->getName().c_str(),
    "QUANTITY_DEMAND", obj->iter->getQuantityDemand(),
    "QUANTITY_BUFFER", obj->iter->getQuantityBuffer(),
    "PEGGED", obj->iter->getPegged() ? 1 : 0
    );

  // Increment iterator
  --*(obj->iter);
  return result;
}


//
// INTERFACE FOR OPERATIONPLAN
//


extern "C" PyObject* PythonOperationPlan::create(PyTypeObject* type, PyObject *args, PyObject *kwargs)
{
  // Allocate memory
  PythonOperationPlan* obj = PyObject_New(PythonOperationPlan, &PythonOperationPlan::InfoType);

  // Initialize the iterator
  obj->iter = OperationPlan::begin();

  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonOperationPlan::next(PythonOperationPlan* obj)
{
  if (obj->iter != OperationPlan::end())
  {
    // Find a non-hidden demand linked to this operation plan
    const Demand *dem = obj->iter->getDemand();
    while (dem && dem->getHidden()) dem = dem->getOwner();
    // Build a python dictionary
    PyObject* result = Py_BuildValue("{s:l,s:s,s:f,s:N,s:N,s:z,s:b,s:l}",
      "IDENTIFIER", obj->iter->getIdentifier(),
      "OPERATION", obj->iter->getOperation()->getName().c_str(),
      "QUANTITY", obj->iter->getQuantity(),
      "START", PythonDateTime(obj->iter->getDates().getStart()),
      "END", PythonDateTime(obj->iter->getDates().getEnd()),
      "DEMAND", dem ? dem->getName().c_str() : NULL,
      "LOCKED", obj->iter->getLocked(),
      "OWNER", obj->iter->getOwner() ? obj->iter->getOwner()->getIdentifier() : 0
      );
    ++(obj->iter);
    return result;
  }
  // Reached the end of the iteration
  return NULL;
}


//
// INTERFACE FOR DEMAND
//

extern "C" PyObject* PythonDemand::create(PyTypeObject* type, PyObject *args, PyObject *kwargs)
{
  // Allocate memory
  PythonDemand* obj = PyObject_New(PythonDemand, &PythonDemand::InfoType);

  // Initialize the iterator
  obj->iter = Demand::begin();
  obj->peggingiterator = NULL;
  obj->deliveryiterator = NULL;

  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonDemand::next(PythonDemand* obj)
{
  if (obj->peggingiterator) 
  { 
    Py_DECREF(obj->peggingiterator);
    obj->peggingiterator = NULL;
  }
  if (obj->deliveryiterator) 
  {
    Py_DECREF(obj->deliveryiterator);
    obj->deliveryiterator = NULL;
  }
  if (obj->iter != Demand::end())
  {
    // Find a non-hidden demand owning this demand
    const Demand *dem = &*(obj->iter);
    while (dem && dem->getHidden()) dem = dem->getOwner();
    // Build a python dictionary
    obj->peggingiterator = PythonDemandPegging::createFromDemand(&*(obj->iter));
    obj->deliveryiterator = PythonDemandDelivery::createFromDemand(&*(obj->iter));
    PyObject* result = Py_BuildValue("{s:s,s:f,s:N,s:i,s:z,s:z,s:z,s:z,s:O,s:O}",
      "NAME", dem ? dem->getName().c_str() : "unspecified",
      "QUANTITY", obj->iter->getQuantity(),
			"DUE", PythonDateTime(obj->iter->getDue()),
      "PRIORITY", obj->iter->getPriority(),
      "ITEM", obj->iter->getItem() ? obj->iter->getItem()->getName().c_str() : NULL,
      "OPERATION", obj->iter->getOperation() ? obj->iter->getOperation()->getName().c_str() : NULL,
      "OWNER", obj->iter->getOwner() ? obj->iter->getOwner()->getName().c_str() : NULL,
      "CUSTOMER", obj->iter->getCustomer() ? obj->iter->getCustomer()->getName().c_str() : NULL,
      "PEGGING", obj->peggingiterator,
      "DELIVERY", obj->deliveryiterator
      );
    ++(obj->iter);
    return result;
  }
  // Reached the end of the iteration
  return NULL;
}


//
// INTERFACE FOR DEMAND DELIVERIES
//


extern "C" PyObject* PythonDemandDelivery::createFromDemand(Demand* v)
{
  // Allocate memory
  PythonDemandDelivery* obj = PyObject_New(PythonDemandDelivery, &PythonDemandDelivery::InfoType);

  // Cast the demand pointer and initialize the iterator
  obj->dem = v;
  obj->iter = v->getDelivery().begin();
  obj->cumPlanned = 0.0;
  // Find a non-hidden demand owning this demand
  obj->dem_owner = v;
  while (obj->dem_owner && obj->dem_owner->getHidden())
    obj->dem_owner = obj->dem_owner->getOwner();

  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonDemandDelivery::next(PythonDemandDelivery* obj)
{
  if (!obj->dem) return NULL;

  if (obj->iter != obj->dem->getDelivery().end())
  {
    float p = (*(obj->iter))->getQuantity();
    obj->cumPlanned += (*(obj->iter))->getQuantity();
    if (obj->cumPlanned > obj->dem->getQuantity())
    {
      // Planned more than requested
      p -= static_cast<float>(obj->cumPlanned - obj->dem->getQuantity());
      if (p < 0.0) p = 0.0;
    }
    // Build a python dictionary
    PyObject* result = Py_BuildValue("{s:z,s:N,s:f,s:N,s:f,s:l}",
      "DEMAND", obj->dem_owner ? obj->dem_owner->getName().c_str() : NULL,
			"DUE", PythonDateTime(obj->dem->getDue()),
      "QUANTITY", p,
			"PLANDATE", PythonDateTime((*(obj->iter))->getDates().getEnd()),
      "PLANQUANTITY", (*(obj->iter))->getQuantity(),
      "OPERATIONPLAN", (*(obj->iter))->getIdentifier()
      );
    ++(obj->iter);
    return result;
  }

  // A last record for cases where the demand is planned short
  if (obj->cumPlanned < obj->dem->getQuantity())
  {
    PyObject* result = Py_BuildValue("{s:z,s:N,s:f,s:z,s:z,s:z}",
      "DEMAND", obj->dem_owner ? obj->dem_owner->getName().c_str() : NULL,
			"DUE", PythonDateTime(obj->dem->getDue()),
      "QUANTITY", obj->dem->getQuantity() - obj->cumPlanned,
			"PLANDATE", NULL,
      "PLANQUANTITY", NULL,
      "OPERATIONPLAN", NULL
      );
    obj->dem = NULL; // To make sure this is the last iteration
    return result;
  }

  // Reached the end of the iteration
  return NULL;
}


//
// INTERFACE FOR BUFFER
//


extern "C" PyObject* PythonBuffer::create(PyTypeObject* type, PyObject *args, PyObject *kwargs)
{
  // Allocate memory
  PythonBuffer* obj = PyObject_New(PythonBuffer, &PythonBuffer::InfoType);

  // Initialize the iterator
  obj->iter = Buffer::begin();
  obj->flowplaniterator = NULL;

  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonBuffer::next(PythonBuffer* obj)
{
  if (obj->flowplaniterator)
  { 
    Py_DECREF(obj->flowplaniterator);
    obj->flowplaniterator = NULL;
  }

  if (obj->iter != Buffer::end())
  {
    // Find a non-hidden buffer
    const Buffer *buf = &*(obj->iter);
    while (buf && buf->getHidden()) buf = buf->getOwner();
    // Build a python dictionary
    obj->flowplaniterator = PythonFlowPlan::createFromBuffer(&*(obj->iter));
    PyObject* result = Py_BuildValue("{s:s,s:s,s:s,s:s,s:f,s:z,s:z,s:z,s:z,s:z,s:O}",
      "NAME", buf ? buf->getName().c_str() : "unspecified",
      "CATEGORY", obj->iter->getCategory().c_str(),
      "SUBCATEGORY", obj->iter->getSubCategory().c_str(),
      "DESCRIPTION", obj->iter->getDescription().c_str(),
      "ONHAND", obj->iter->getOnHand(),
      "LOCATION", obj->iter->getLocation() ? obj->iter->getLocation()->getName().c_str() : NULL,
      "ITEM", obj->iter->getItem() ? obj->iter->getItem()->getName().c_str() : NULL,
      "MINIMUM", obj->iter->getMinimum() ? obj->iter->getMinimum()->getName().c_str() : NULL,
      "MAXIMUM", obj->iter->getMaximum() ? obj->iter->getMaximum()->getName().c_str() : NULL,
      "PRODUCING", obj->iter->getProducingOperation() ? obj->iter->getProducingOperation()->getName().c_str() : NULL,
      "FLOWPLANS", obj->flowplaniterator
      );
    ++(obj->iter);
    return result;
  }
  // Reached the end of the iteration
  return NULL;
}


//
// INTERFACE FOR RESOURCE
//


extern "C" PyObject* PythonResource::create(PyTypeObject* type, PyObject *args, PyObject *kwargs)
{
  // Allocate memory
  PythonResource* obj = PyObject_New(PythonResource, &PythonResource::InfoType);

  // Initialize the iterator
  obj->iter = Resource::begin();
  obj->loadplaniterator = NULL;

  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonResource::next(PythonResource* obj)
{
  if (obj->loadplaniterator)
  { 
    Py_DECREF(obj->loadplaniterator);
    obj->loadplaniterator = NULL;
  }

  if (obj->iter != Resource::end())
  {
    // Find a non-hidden resource
    const Resource *res = &*(obj->iter);
    while (res && res->getHidden()) res = res->getOwner();
    // Build a python dictionary
    obj->loadplaniterator = PythonLoadPlan::createFromResource(&*(obj->iter));
    PyObject* result = Py_BuildValue("{s:s,s:s,s:s,s:s,s:z,s:z,s:z,s:O}",
      "NAME", res ? res->getName().c_str() : "unspecified",
      "CATEGORY", obj->iter->getCategory().c_str(),
      "SUBCATEGORY", obj->iter->getSubCategory().c_str(),
      "DESCRIPTION", obj->iter->getDescription().c_str(),
      "LOCATION", obj->iter->getLocation() ? obj->iter->getLocation()->getName().c_str() : NULL,
      "MAXIMUM", obj->iter->getMaximum() ? obj->iter->getMaximum()->getName().c_str() : NULL,
      "OWNER", obj->iter->getOwner() ? obj->iter->getOwner()->getName().c_str() : NULL,
      "LOADPLANS", obj->loadplaniterator
     );
    ++(obj->iter);
    return result;
  }
  // Reached the end of the iteration
  return NULL;
}


} // End namespace
