/***************************************************************************
  file : $URL: https://frepple.svn.sourceforge.net/svnroot/frepple/trunk/modules/forecast/forecastsolver.cpp $
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


double Forecast::generateFutureValues(const double history[], unsigned int count, bool debug)
{
  // Validate presence of history
  if (!history) throw RuntimeException("Null argument to forecast function");

  // Create a list of forecasting methods.    @todo list should be dynamic, based on availability of hsitory
  // We create the forecasting objects in stack memory for best performance.
  SingleExponential single_exp;
  DoubleExponential double_exp;
  int numberOfMethods = 2;
  ForecastMethod* methods[2];
  methods[0] = &single_exp;
  methods[1] = &double_exp;

  // Evaluate each forecast method
  double best_error = DBL_MAX;
  int best_method = 0;
  double error;
  for (int i=0; i<numberOfMethods; ++i)
  {    
    error = methods[i]->generateForecast(history, count, debug);  
    if (error<best_error) 
    {
      best_error = error;
      best_method = i;
    }
  }
  
  // Apply the most appropriate forecasting method

  return best_error;
}


double Forecast::SingleExponential::initial_alfa = 0.2;
double Forecast::SingleExponential::min_alfa = 0.0;
double Forecast::SingleExponential::max_alfa = 1.0;
unsigned int Forecast::SingleExponential::skip = 7;


double Forecast::SingleExponential::generateForecast
  (const double history[], unsigned int count, bool debug)
{
  // Verify whether this is a valid forecast method.
  //   - We need at least 10 buckets after the warmup period.
  if (count < skip + 10)
    return DBL_MAX;

  unsigned int iteration = 1;
  bool upperboundarytested = false;
  bool lowerboundarytested = false;
  double error_mad, delta, df_dalfa_i, sum_11, sum_12;
  for (; iteration <= Forecast::getForecastIterations(); ++iteration)
  {
    // Initialize the iteration
    f_i = history[0];
    df_dalfa_i = 0; 
    sum_11 = 0;
    sum_12 = 0;
    error_mad = 0;

    // Calculate the forecast and forecast error.
    // We also compute the sums required for the Marquardt optimization.
    for (unsigned long i = 0; i < count; ++i)
    {
      df_dalfa_i = history[i-1] - f_i + (1 - alfa) * df_dalfa_i;
      f_i = history[i-1] * alfa + (1 - alfa) * f_i;
      sum_12 += df_dalfa_i * (history[i] - f_i);
      sum_11 += df_dalfa_i * df_dalfa_i;
      if (i > skip) // Don't measure during the warmup period
        error_mad += fabs(f_i - history[i]);
    }

    // Calculate a delta for the alfa parameter
    delta = sum_11 ? sum_12 / sum_11 : sum_12;
    alfa += delta;

    // Stop when we repeatedly bounce against the limits.
    // Testing a limits once is allowed.
    if (alfa > max_alfa) 
    { 
      alfa = max_alfa; 
      if (upperboundarytested) break; 
      upperboundarytested = true;
    }
    else if (alfa < min_alfa)
    { 
      alfa = min_alfa; 
      if (lowerboundarytested) break; 
      lowerboundarytested = true;
    }
    
    // Stop when we are close enough
    if (fabs(delta) < 0.01) break;
  }

  // Echo the result
  if (debug)
    logger << "single exponential" //"Forecast "  << fcst.getName() xxx
      << ": alfa " << alfa 
      << ", mad " << error_mad 
      << ", " << iteration << " iterations"
      << ", delta alfa " << delta 
      << ", forecast " << f_i << endl;
  return error_mad;
}


double Forecast::DoubleExponential::initial_alfa = 0.2;
double Forecast::DoubleExponential::min_alfa = 0.0;
double Forecast::DoubleExponential::max_alfa = 1.0;
double Forecast::DoubleExponential::initial_gamma = 0.05;
double Forecast::DoubleExponential::min_gamma = 0.0;
double Forecast::DoubleExponential::max_gamma = 1.0;
unsigned int Forecast::DoubleExponential::skip = 7;


double Forecast::DoubleExponential::generateForecast  /* @todo optimization not implemented yet*/
  (const double history[], unsigned int count, bool debug)
{
  // Verify whether this is a valid forecast method.
  //   - We need at least 10 buckets after the warmup period.
  if (count < skip + 10)
    return DBL_MAX;

  unsigned int iteration = 1;
  double error_mad, trend_i, constant_i, constant_i_minus_1;
  //xxxfor (; iteration <= Forecast::getForecastIterations(); ++iteration)
  for (; iteration <= 1; ++iteration)
  {
    // Initialize the iteration
    constant_i = history[0];
    trend_i = history[1] - history[0]; 
    error_mad = 0;

    // Calculate the forecast and forecast error.
    // We also compute the sums required for the Marquardt optimization.
    for (unsigned long i = 0; i < count; ++i)
    {
      constant_i_minus_1 = constant_i;
      constant_i = history[i-1] * alfa + (1 - alfa) * (constant_i + trend_i);
      trend_i = gamma * (constant_i - constant_i_minus_1) + (1 - gamma) * trend_i;
      if (i > skip) // Don't measure during the warmup period
        error_mad += fabs(constant_i + trend_i - history[i]);
    }
  }

  // Echo the result
  if (debug)
    logger << "double exponential" //"Forecast "  << fcst.getName() xxx
      << ": alfa " << alfa 
      << ", gamma " << gamma 
      << ", mad " << error_mad 
      << ", " << iteration << " iterations"
      << ", constant " << constant_i
      << ", trend " << trend_i
      << ", forecast " << (trend_i + constant_i) << endl;
  return error_mad;
}

}       // end namespace
