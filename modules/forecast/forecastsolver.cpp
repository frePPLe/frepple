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


#include "forecast.h"

namespace module_forecast
{

const XMLtag tag_automatic("AUTOMATIC");


void ForecastSolver::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(tag_automatic))
    setAutomatic(pElement.getBool());
  else
    Solver::endElement(pIn, pElement);
}


void ForecastSolver::setAutomatic(bool b)
{
  if (automatic && !b)
  {
    // Disable the incremental solving (which is currently enabled)
    //FunctorInstance<Demand,ForecastSolver>::disconnect(this, SIG_BEFORE_CHANGE);
    FunctorInstance<Demand,ForecastSolver>::disconnect(this, SIG_AFTER_CHANGE);
    FunctorInstance<Demand,ForecastSolver>::disconnect(this, SIG_REMOVE);
  }
  else if (!automatic && b)
  {
    // Enable the incremental solving (which is currently disabled)
    //FunctorInstance<Demand,ForecastSolver>::connect(this, SIG_BEFORE_CHANGE);
    FunctorInstance<Demand,ForecastSolver>::connect(this, SIG_AFTER_CHANGE);
    FunctorInstance<Demand,ForecastSolver>::connect(this, SIG_REMOVE);
  }
  automatic = b;
}


bool ForecastSolver::callback(Demand* l, const Signal a)
{
  // Call the netting function
  solve(l, NULL);

  // Always return 'okay'
  return true;
}


void ForecastSolver::writeElement(XMLOutput *o, const XMLtag& tag, mode m) const
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

  Object::WLock<Demand> x(!getAutomatic() ? l : NULL);

  // Message
  if (getVerbose())
    cout << "  Netting of demand '" << l << "'  ('" << l->getCustomer() 
      << "','" << l->getItem() << "', '" << l->getDeliveryOperation() 
      << "')" << endl;

  // Find a matching forecast
  Forecast *fcst = matchDemand2Forecast(l);

  if (!fcst)
  {
    // Message
    if (getVerbose())
      cout << "     No matching forecast available" << endl;
    return;
  }

  // Message
  if (getVerbose())
    cout << "     " << fcst << endl;

}


void ForecastSolver::solve(void *v)
{
  /*
  for(Forecast::MapOfForecasts::const_iterator x = Forecast::ForecastDictionary.begin();
    x != Forecast::ForecastDictionary.end(); ++x)
    cout << "  FCST " << &*x << ":   " << x->first.first << "  " << x->first.second << "   " << x->second << endl;
  */

  // Disable automated netting during this solver loop
  bool autorun = getAutomatic();
  setAutomatic(false);

  // Netting loop
  for(Demand::iterator i = Demand::begin(); i != Demand::end(); ++i)
    if (!dynamic_cast<Forecast*>(&*i) && !i->getHidden()) 
      // Call the netting function for non-forecasts and non-hidden demand.
      solve(&*i, NULL);

  // Re-enable the automated netting if it was enabled
  if (autorun) setAutomatic(true);
}


Forecast* ForecastSolver::matchDemand2Forecast(const Demand* l)
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

}       // end namespace
