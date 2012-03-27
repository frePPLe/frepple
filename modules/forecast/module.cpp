/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba                 *
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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

#include "forecast.h"

namespace module_forecast
{

Forecast::MapOfForecasts Forecast::ForecastDictionary;
bool Forecast::Customer_Then_Item_Hierarchy = true;
bool Forecast::Match_Using_Delivery_Operation = true;
TimePeriod Forecast::Net_Late(0L);
TimePeriod Forecast::Net_Early(0L);
unsigned long Forecast::Forecast_Iterations(15L);
double Forecast::Forecast_SmapeAlfa(0.95);
unsigned long Forecast::Forecast_Skip(5);


MODULE_EXPORT const char* initialize(const Environment::ParameterList& z)
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
  for (Environment::ParameterList::const_iterator x = z.begin();
      x != z.end(); ++x)
    try
    {
      // Forecast buckets
      if (x->first == "DueAtEndOfBucket")
        ForecastBucket::setDueAtEndOfBucket(x->second.getBool());
      // Netting
      else if (x->first == "Net_CustomerThenItemHierarchy")
        Forecast::setCustomerThenItemHierarchy(x->second.getBool());
      else if (x->first == "Net_MatchUsingDeliveryOperation")
        Forecast::setMatchUsingDeliveryOperation(x->second.getBool());
      else if (x->first == "Net_NetEarly")
        Forecast::setNetEarly(x->second.getTimeperiod());
      else if (x->first == "Net_NetLate")
        Forecast::setNetLate(x->second.getTimeperiod());
      // Forecasting
      else if (x->first == "Forecast_Iterations")
        Forecast::setForecastIterations(x->second.getUnsignedLong());
      else if (x->first == "Forecast_SmapeAlfa")
        Forecast::setForecastSmapeAlfa(x->second.getDouble());
      else if (x->first == "Forecast_Skip")
        Forecast::setForecastSkip(x->second.getUnsignedLong());
      // Moving average forecast method
      else if (x->first == "MovingAverage_buckets")
        Forecast::MovingAverage::setDefaultBuckets(x->second.getUnsignedLong());
      // Single exponential forecast method
      else if (x->first == "Forecast_SingleExponential_initialAlfa")
        Forecast::SingleExponential::setInitialAlfa(x->second.getDouble());
      else if (x->first == "Forecast_SingleExponential_minAlfa")
        Forecast::SingleExponential::setMinAlfa(x->second.getDouble());
      else if (x->first == "Forecast_SingleExponential_maxAlfa")
        Forecast::SingleExponential::setMaxAlfa(x->second.getDouble());
      // Double exponential forecast method
      else if (x->first == "Forecast_DoubleExponential_initialAlfa")
        Forecast::DoubleExponential::setInitialAlfa(x->second.getDouble());
      else if (x->first == "Forecast_DoubleExponential_minAlfa")
        Forecast::DoubleExponential::setMinAlfa(x->second.getDouble());
      else if (x->first == "Forecast_DoubleExponential_maxAlfa")
        Forecast::DoubleExponential::setMaxAlfa(x->second.getDouble());
      else if (x->first == "Forecast_DoubleExponential_initialGamma")
        Forecast::DoubleExponential::setInitialGamma(x->second.getDouble());
      else if (x->first == "Forecast_DoubleExponential_minGamma")
        Forecast::DoubleExponential::setMinGamma(x->second.getDouble());
      else if (x->first == "Forecast_DoubleExponential_maxGamma")
        Forecast::DoubleExponential::setMaxGamma(x->second.getDouble());
      else if (x->first == "Forecast_DoubleExponential_dampenTrend")
        Forecast::DoubleExponential::setDampenTrend(x->second.getDouble());
      // Seasonal forecast method
      else if (x->first == "Forecast_Seasonal_initialAlfa")
        Forecast::Seasonal::setInitialAlfa(x->second.getDouble());
      else if (x->first == "Forecast_Seasonal_minAlfa")
        Forecast::Seasonal::setMinAlfa(x->second.getDouble());
      else if (x->first == "Forecast_Seasonal_maxAlfa")
        Forecast::Seasonal::setMaxAlfa(x->second.getDouble());
      else if (x->first == "Forecast_Seasonal_initialBeta")
        Forecast::Seasonal::setInitialGamma(x->second.getDouble());
      else if (x->first == "Forecast_Seasonal_minBeta")
        Forecast::Seasonal::setMinBeta(x->second.getDouble());
      else if (x->first == "Forecast_Seasonal_maxBeta")
        Forecast::Seasonal::setMaxBeta(x->second.getDouble());
      else if (x->first == "Forecast_Seasonal_initialGamma")
        Forecast::Seasonal::setInitialBeta(x->second.getDouble());
      else if (x->first == "Forecast_Seasonal_minGamma")
        Forecast::Seasonal::setMinGamma(x->second.getDouble());
      else if (x->first == "Forecast_Seasonal_maxGamma")
        Forecast::Seasonal::setMaxGamma(x->second.getDouble());
      else if (x->first == "Forecast_Seasonal_dampenTrend")
        Forecast::Seasonal::setDampenTrend(x->second.getDouble());
      else if (x->first == "Forecast_Seasonal_minPeriod")
        Forecast::Seasonal::setMinPeriod(x->second.getInt());
      else if (x->first == "Forecast_Seasonal_maxPeriod")
        Forecast::Seasonal::setMaxPeriod(x->second.getInt());
      // Croston forecast method
      else if (x->first == "Forecast_Croston_initialAlfa")
        Forecast::Croston::setInitialAlfa(x->second.getDouble());
      else if (x->first == "Forecast_Croston_minAlfa")
        Forecast::Croston::setMinAlfa(x->second.getDouble());
      else if (x->first == "Forecast_Croston_maxAlfa")
        Forecast::Croston::setMaxAlfa(x->second.getDouble());
      else if (x->first == "Forecast_Croston_minIntermittence")
        Forecast::Croston::setMinIntermittence(x->second.getDouble());
      // That's bullshit
      else
        logger << "Warning: Unrecognized parameter '" << x->first << "'" << endl;
    }
    catch (const exception &e)
    {
      // Avoid throwing errors during the initialization!
      logger << "Error: " << e.what() << endl;
    }
    catch (...)
    {
      logger << "Error: unknown exception" << endl;
    }

  // Register the Python extensions
  PyGILState_STATE state = PyGILState_Ensure();
  try
  {
    // Register new Python data types
    if (Forecast::initialize())
      throw RuntimeException("Error registering forecast");
    if (ForecastBucket::initialize())
      throw RuntimeException("Error registering forecastbucket");
    if (ForecastSolver::initialize())
      throw RuntimeException("Error registering forecastsolver");
    PyGILState_Release(state);
  }
  catch (const exception &e)
  {
    PyGILState_Release(state);
    logger << "Error: " << e.what() << endl;
  }
  catch (...)
  {
    PyGILState_Release(state);
    logger << "Error: unknown exception" << endl;
  }

  // Return the name of the module
  return name;
}

}       // end namespace
