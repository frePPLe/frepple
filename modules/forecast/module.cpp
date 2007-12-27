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

const MetaClass Forecast::metadata;
const MetaClass ForecastSolver::metadata;
Forecast::MapOfForecasts Forecast::ForecastDictionary;
bool Forecast::Customer_Then_Item_Hierarchy = true;
bool Forecast::Match_Using_Delivery_Operation = true;
TimePeriod Forecast::Net_Late(0L);
TimePeriod Forecast::Net_Early(0L);


MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z)
{
  // Initialize only once
  static bool init = false;
  static const char* name = "forecast";
  if (init)
  {
    logger << "Warning: Initializing module forecast more than once." << endl;
    return name;
  }
  init = true;

  // Process the module parameters
  for (CommandLoadLibrary::ParameterList::const_iterator x = z.begin();
    x != z.end(); ++x)
  {
    if (x->first == "Customer_Then_Item_Hierarchy")
      Forecast::setCustomerThenItemHierarchy(x->second.getBool());
    else if (x->first == "Match_Using_Delivery_Operation")
      Forecast::setMatchUsingDeliveryOperation(x->second.getBool());
    else if (x->first == "Net_Early")
      Forecast::setNetEarly(x->second.getTimeperiod());
    else if (x->first == "Net_Late")
      Forecast::setNetLate(x->second.getTimeperiod());
    else
      logger << "Warning: Unrecognized parameter '" << x->first << "'" << endl;
  }

  // Initialize the metadata.
  Forecast::metadata.registerClass(
    "DEMAND",
    "DEMAND_FORECAST",
    Object::createString<Forecast>);
  ForecastSolver::metadata.registerClass(
    "SOLVER",
    "SOLVER_FORECAST",
    Object::createString<ForecastSolver>);

  // Get notified when a calendar is deleted
  FunctorStatic<Calendar,Forecast>::connect(SIG_REMOVE);

  // Register the python functions if the python module is loaded
  if (CommandLoadLibrary::isLoaded("python"))
    initializePython();

  // Return the name of the module
  return name;
}

}       // end namespace
