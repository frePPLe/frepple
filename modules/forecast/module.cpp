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
    if (x->first == "Net_CustomerThenItemHierarchy")
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
    else if (x->first == "Forecast_madAlfa")
      Forecast::setForecastMadAlfa(x->second.getDouble());
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
    // Bullshit
    else
      logger << "Warning: Unrecognized parameter '" << x->first << "'" << endl;
  }
  catch (exception &e) 
  {
    // Avoid throwing errors during the initialization!
    logger << "Error: " << e.what() << endl;
  }
  catch (...)
  {
    logger << "Error: unknown exception" << endl;
  }

  try
  {
    // Register the Python extensions
    PyThreadState *myThreadState = PyGILState_GetThisThreadState();
    if (!Py_IsInitialized() || !myThreadState)
      throw RuntimeException("Python isn't initialized correctly");
    try
    {
      // Get the global lock.
      PyEval_RestoreThread(myThreadState);
      // Register new Python data types
      if (Forecast::initialize())
        throw RuntimeException("Error registering forecast");
      if (ForecastBucket::initialize())
        throw RuntimeException("Error registering forecastbucket");
      if (ForecastSolver::initialize())
        throw RuntimeException("Error registering forecastsolver");
    }
    // Release the global lock when leaving the function
    catch (...)
    {
      PyEval_ReleaseLock();
      throw;  // Rethrow the exception
    }
    PyEval_ReleaseLock();
  }
  catch (exception &e) 
  {
    // Avoid throwing errors during the initialization!
    logger << "Error: " << e.what() << endl;
  }
  catch (...)
  {
    logger << "Error: unknown exception" << endl;
  }

  // Return the name of the module
  return name;
}

}       // end namespace
