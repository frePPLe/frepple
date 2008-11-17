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
const MetaClass ForecastBucket::metadata;
const MetaClass ForecastSolver::metadata;


Forecast::MapOfForecasts Forecast::ForecastDictionary;
bool Forecast::Customer_Then_Item_Hierarchy = true;
bool Forecast::Match_Using_Delivery_Operation = true;
TimePeriod Forecast::Net_Late(0L);
TimePeriod Forecast::Net_Early(0L);
unsigned long Forecast::Forecast_Iterations(15L);
double Forecast::Forecast_MadAlfa(0.95);
unsigned long Forecast::Forecast_Skip(5);


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
  try 
  {
    // Netting 
    if (x->first == "Net.CustomerThenItemHierarchy")
      Forecast::setCustomerThenItemHierarchy(x->second.getBool());
    else if (x->first == "Net.MatchUsingDeliveryOperation")
      Forecast::setMatchUsingDeliveryOperation(x->second.getBool());
    else if (x->first == "Net.NetEarly")
      Forecast::setNetEarly(x->second.getTimeperiod());
    else if (x->first == "Net.NetLate")
      Forecast::setNetLate(x->second.getTimeperiod());
    // Forecasting
    else if (x->first == "Forecast.Iterations")
      Forecast::setForecastIterations(x->second.getUnsignedLong());
    else if (x->first == "Forecast.madAlfa")
      Forecast::setForecastMadAlfa(x->second.getDouble());
    else if (x->first == "Forecast.Skip")
      Forecast::setForecastSkip(x->second.getUnsignedLong());
    // Moving average forecast method
    else if (x->first == "MovingAverage.buckets")
      Forecast::MovingAverage::setDefaultBuckets(x->second.getUnsignedLong());    
    // Single exponential forecast method
    else if (x->first == "Forecast.SingleExponential.initialAlfa")
      Forecast::SingleExponential::setInitialAlfa(x->second.getDouble());
    else if (x->first == "Forecast.SingleExponential.minAlfa")
      Forecast::SingleExponential::setMinAlfa(x->second.getDouble());
    else if (x->first == "Forecast.SingleExponential.maxAlfa")
      Forecast::SingleExponential::setMaxAlfa(x->second.getDouble());
    // Double exponential forecast method
    else if (x->first == "Forecast.DoubleExponential.initialAlfa")
      Forecast::DoubleExponential::setInitialAlfa(x->second.getDouble());
    else if (x->first == "Forecast.DoubleExponential.minAlfa")
      Forecast::DoubleExponential::setMinAlfa(x->second.getDouble());
    else if (x->first == "Forecast.DoubleExponential.maxAlfa")
      Forecast::DoubleExponential::setMaxAlfa(x->second.getDouble());
    else if (x->first == "Forecast.DoubleExponential.initialGamma")
      Forecast::DoubleExponential::setInitialGamma(x->second.getDouble());
    else if (x->first == "Forecast.DoubleExponential.minGamma")
      Forecast::DoubleExponential::setMinGamma(x->second.getDouble());
    else if (x->first == "Forecast.DoubleExponential.maxGamma")
      Forecast::DoubleExponential::setMaxGamma(x->second.getDouble());
    // Bullshit
    else
      logger << "Warning: Unrecognized parameter '" << x->first << "'" << endl;
  }
  catch (exception &e) 
  {
    // Avoid throwing errors during the initialization!
    logger << "Error: " << e.what() << endl;
  }

  try
  {
    // Initialize the metadata.
    Forecast::metadata.registerClass(
      "demand",
      "demand_forecast",
      Object::createString<Forecast>);
    ForecastBucket::metadata.registerClass(  // No factory method for this class
      "demand",
      "demand_forecastbucket");
    ForecastSolver::metadata.registerClass(
      "solver",
      "solver_forecast",
      Object::createString<ForecastSolver>);

    // Get notified when a calendar is deleted
    FunctorStatic<Calendar,Forecast>::connect(SIG_REMOVE);

    // Register the python functions
    initializePython();
  }
  catch (exception &e) 
  {
    // Avoid throwing errors during the initialization!
    logger << "Error: " << e.what() << endl;
  }

  // Return the name of the module
  return name;
}

}       // end namespace
