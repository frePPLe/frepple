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


#include "forecast.h"

namespace module_forecast
{

const Keyword tag_automatic("automatic");


void ForecastSolver::endElement(XMLInput& pIn, const Attribute& pAttr, DataElement& pElement)
{
  if (pAttr.isA(tag_automatic))
    setAutomatic(pElement.getBool());
  else
    Solver::endElement(pIn, pAttr, pElement);
}


void ForecastSolver::setAutomatic(bool b)
{
  if (automatic && !b)
    // Disable the incremental solving (which is currently enabled)
    FunctorInstance<Demand,ForecastSolver>::disconnect(this, SIG_REMOVE);
  else if (!automatic && b)
    // Enable the incremental solving (which is currently disabled)
    FunctorInstance<Demand,ForecastSolver>::connect(this, SIG_REMOVE);
  automatic = b;
}


bool ForecastSolver::callback(Demand* l, const Signal a)
{
  // Call the netting function
  solve(l, NULL);

  // Always return 'okay'
  return true;
}


void ForecastSolver::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
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
  if (automatic) o->writeElement(tag_automatic, automatic);

  // Write the parent class
  Solver::writeElement(o, tag, NOHEADER);
}


void ForecastSolver::solve(const Demand* l, void* v)
{
  // Forecast don't net themselves, and hidden demands either...
  if (!l || dynamic_cast<const Forecast*>(l) || l->getHidden()) return;

  const Demand* x(!getAutomatic() ? l : NULL);

  // Message
  if (getLogLevel()>0)
    logger << "  Netting of demand '" << l << "'  ('" << l->getCustomer()
      << "','" << l->getItem() << "', '" << l->getDeliveryOperation()
      << "'): " << l->getDue() << ", " << l->getQuantity() << endl;

  // Find a matching forecast
  Forecast *fcst = matchDemandToForecast(l);

  if (!fcst)
  {
    // Message
    if (getLogLevel()>0)
      logger << "    No matching forecast available" << endl;
    return;
  }
  else if (getLogLevel()>0)
    logger << "    Matching forecast: " << fcst << endl;

  // Netting the order from the forecast
  netDemandFromForecast(l,fcst);
}


void ForecastSolver::solve(void *v)
{
  // Definitions to sort the demand

  // Disable automated netting during this solver loop
  bool autorun = getAutomatic();
  setAutomatic(false);

  // Sort the demands using the same sort function as used for planning.
  // Note: the memory consumption of the sorted list can be significant
  sortedDemandList l;
  for (Demand::iterator i = Demand::begin(); i != Demand::end(); ++i)
    // Only sort non-forecast demand.
    if (!dynamic_cast<Forecast*>(&*i)
      && !dynamic_cast<Forecast::ForecastBucket*>(&*i))
        l.insert(&*i);

  // Netting loop
  for(sortedDemandList::iterator i = l.begin(); i != l.end(); ++i)
    try {solve(*i, NULL);}
    catch (...)
    {
      // Error message
      logger << "Error: Caught an exception while netting demand '"
        << (*i)->getName() << "':" << endl;
      try { throw; }
      catch (bad_exception&) {logger << "  bad exception" << endl;}
      catch (exception& e) {logger << "  " << e.what() << endl;}
      catch (...) {logger << "  Unknown type" << endl;}
    }

  // Re-enable the automated netting if it was enabled
  if (autorun) setAutomatic(true);
}


Forecast* ForecastSolver::matchDemandToForecast(const Demand* l)
{
  pair<const Item*, const Customer*> key
    = make_pair(&*(l->getItem()), &*(l->getCustomer()));

  do  // Loop through second dimension
  {
    do // Loop through first dimension
    {
      Forecast::MapOfForecasts::iterator x = Forecast::ForecastDictionary.lower_bound(key);

      // Loop through all matching keys
      while (x != Forecast::ForecastDictionary.end() && x->first == key)
      {
        if (!Forecast::getMatchUsingDeliveryOperation()
          || x->second->getDeliveryOperation() == l->getDeliveryOperation())
          // Bingo! Found a matching key, if required plus matching delivery operation
          return x->second;
        else
          ++ x;
      }
      // Not found: try a higher level match in first dimension
      if (Forecast::Customer_Then_Item_Hierarchy)
      {
        // First customer hierarchy
        if (key.second) key.second = key.second->getOwner();
        else break;
      }
      else
      {
        // First item hierarchy
        if (key.first) key.first = key.first->getOwner();
        else break;
      }
    }
    while (true);

    // Not found at any level in the first dimension

    // Try a new level in the second dimension
    if (Forecast::Customer_Then_Item_Hierarchy)
    {
      // Second is item
      if (key.first) key.first = key.first->getOwner();
      else return NULL;
      // Reset to lowest level in the first dimension again
      key.second = &*(l->getCustomer());
    }
    else
    {
      // Second is customer
      if (key.second) key.second = key.second->getOwner();
      else return NULL;
      // Reset to lowest level in the first dimension again
      key.first = &*(l->getItem());
    }
  }
  while (true);
}


void ForecastSolver::netDemandFromForecast(const Demand* dmd, Forecast* fcst)
{
  // Find the bucket with the due date
  Forecast::ForecastBucket* zerobucket = NULL;
  for (Forecast::memberIterator i = fcst->beginMember(); i != fcst->endMember(); ++i)
  {
    zerobucket = dynamic_cast<Forecast::ForecastBucket*>(&*i);
    if (zerobucket && zerobucket->timebucket.within(dmd->getDue())) break;
  }
  if (!zerobucket)
    throw LogicException("Can't find forecast bucket for "
      + string(dmd->getDue()) + " in forecast '" + fcst->getName() + "'");

  // Netting - looking for time buckets with net forecast
  double remaining = dmd->getQuantity();
  Forecast::ForecastBucket* curbucket = zerobucket;
  bool backward = true;
  while ( remaining > 0 && curbucket
    && (dmd->getDue()-Forecast::getNetEarly() < curbucket->timebucket.getEnd())
    && (dmd->getDue()+Forecast::getNetLate() >= curbucket->timebucket.getStart())
    )
  {
    // Net from the current bucket
    double available = curbucket->getQuantity();
    if (available > 0)
    {
      if (available >= remaining)
      {
        // Partially consume a bucket
        if (getLogLevel()>=2)
          logger << "    Consuming " << remaining << " from bucket "
            << curbucket->timebucket << " (" << available
            << " available)" << endl;
        curbucket->setQuantity(available - remaining);
        curbucket->consumed += remaining;
        remaining = 0;
      }
      else
      {
        // Completely consume a bucket
        if (getLogLevel()>=2)
          logger << "    Consuming " << available << " from bucket "
            << curbucket->timebucket << " (" << available
            << " available)" << endl;
        remaining -= available;
        curbucket->consumed += available;
        curbucket->setQuantity(0);
      }
    }
    else if (getLogLevel()>=2)
      logger << "    Nothing available in bucket "
        << curbucket->timebucket << endl;

    // Find the next forecast bucket
    if (backward)
    {
      // Moving to earlier buckets
      curbucket = curbucket->prev;
      if (!curbucket)
      {
        backward = false;
        curbucket = zerobucket->next;
      }
    }
    else
      // Moving to later buckets
      curbucket = curbucket->next;
  }

  // Quantity for which no bucket is found
  if (remaining > 0 && getLogLevel()>=2)
    logger << "    Remains " << remaining << " that can't be netted" << endl;

}

}       // end namespace
