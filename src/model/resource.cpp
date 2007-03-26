/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
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

template<class Resource> DECLARE_EXPORT Tree HasName<Resource>::st;


DECLARE_EXPORT void Resource::setMaximum(CalendarFloat* c)
{
  // Resetting the same calendar
  if (max_cal == c) return;

  // Mark as changed
  setChanged();

  // Calendar is already set. Need to remove the current max events.
  if(max_cal)
  {
    for(loadplanlist::iterator oo=loadplans.begin(); oo!=loadplans.end(); )
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
  float curMax = 0.0f;
  for (Calendar::BucketIterator x = max_cal->beginBuckets();
       x != max_cal->endBuckets(); ++x)
    if (curMax != max_cal->getValue(x))
    {
      curMax = max_cal->getValue(x);
      loadplanlist::EventMaxQuantity *newBucket =
        new loadplanlist::EventMaxQuantity(x->getStart(), curMax);
      loadplans.insert(newBucket);
    }
}


DECLARE_EXPORT void Resource::writeElement(XMLOutput *o, const XMLtag& tag, mode m) const
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
  o->writeElement(Tags::tag_location, loc);
  Plannable::writeElement(o, tag);

  // Write the loads
  if (!loads.empty())
  {
    o->BeginObject (Tags::tag_loads);
    for (loadlist::const_iterator i = loads.begin(); i != loads.end();)
      // We use the FULL mode, to force the loads being written regardless
      // of the depth in the XML tree.
      o->writeElement(Tags::tag_load, &(*(i++)), FULL);
    o->EndObject (Tags::tag_loads);
  }

  // Write extra plan information
  loadplanlist::const_iterator i = loadplans.begin();
  if (o->getContentType() == XMLOutput::PLAN  && i!=loadplans.end())
  {
    o->BeginObject(Tags::tag_load_plans);
    for (; i!=loadplans.end(); ++i)
      if (i->getType()==1)
      {
        const LoadPlan *lp = dynamic_cast<const LoadPlan*>(&*i);
        o->BeginObject(Tags::tag_load_plan);
        o->writeElement(Tags::tag_date, lp->getDate());
        o->writeElement(Tags::tag_quantity, lp->getQuantity());
        o->writeElement(Tags::tag_onhand, lp->getOnhand());
        o->writeElement(Tags::tag_minimum, lp->getMin());
        o->writeElement(Tags::tag_maximum, lp->getMax());
        o->writeElement(Tags::tag_operation_plan, lp->getOperationPlan(), FULL);
        o->EndObject(Tags::tag_load_plan);
      }
    o->EndObject(Tags::tag_load_plans);
  }

  // That was it
  o->EndObject(tag);
}


DECLARE_EXPORT void Resource::beginElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_load)
      && pIn.getParentElement().isA(Tags::tag_loads))
  {
    Load * l = new Load();
    LockManager::getManager().obtainWriteLock(l);   // @todo
    l->setResource(this);
    pIn.readto(l);
  }
  else if (pElement.isA (Tags::tag_maximum))
    pIn.readto( Calendar::reader(Calendar::metadata,pIn) );
  else if (pElement.isA(Tags::tag_load_plans))
    pIn.IgnoreElement();
  else
    HasHierarchy<Resource>::beginElement(pIn, pElement);
}


DECLARE_EXPORT void Resource::endElement (XMLInput& pIn, XMLElement& pElement)
{
  /* Note that while restoring the size, the parent's size is NOT
     automatically updated. The getDescription of the 'set_size' function may
     suggest this would be the case... */
  if (pElement.isA (Tags::tag_maximum))
  {
    CalendarFloat * c = dynamic_cast<CalendarFloat*>(pIn.getPreviousObject());
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
  else
  {
    Plannable::endElement(pIn, pElement);
    HasDescription::endElement(pIn, pElement);
    HasHierarchy<Resource>::endElement (pIn, pElement);
  }
}


DECLARE_EXPORT void Resource::deleteOperationPlans(bool deleteLocked)
{
  // Delete the operationplans
  for(loadlist::iterator i=loads.begin(); i!=loads.end(); ++i)
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
(XMLOutput *o, const XMLtag &tag, mode m) const
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


}
