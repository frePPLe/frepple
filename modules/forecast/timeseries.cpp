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

#define ACCURACY 0.01

void Forecast::generateFutureValues(
  const double history[], unsigned int historycount, 
  const Date buckets[], unsigned int bucketcount, 
  bool debug)
{
  // Validate the input
  if (!history || !buckets) 
    throw RuntimeException("Null argument to forecast function");
  if (bucketcount < 2) 
    throw DataException("Need at least 2 forecast dates");

  // Create a list of forecasting methods.
  // We create the forecasting objects in stack memory for best performance.
  MovingAverage moving_avg;
  SingleExponential single_exp;
  DoubleExponential double_exp;
  int numberOfMethods = 3;
  ForecastMethod* methods[3];
  methods[0] = &single_exp;
  methods[1] = &double_exp;
  methods[2] = &moving_avg;

  // Initialize a vector with the mad weights
  double *madWeight = new double[historycount+1];
  madWeight[historycount] = madWeight[historycount-1] = 1.0;
  for (int i=historycount-2; i>=0; --i)
    madWeight[i] = madWeight[i+1] * Forecast::getForecastMadAlfa();

  // Evaluate each forecast method
  double best_error = DBL_MAX;
  int best_method = -1;
  double error;
  try 
  {
    for (int i=0; i<numberOfMethods; ++i)
    {    
      error = methods[i]->generateForecast(this, history, historycount, madWeight, debug);  
      if (error<best_error) 
      {
        best_error = error;
        best_method = i;
      }
    }
  }
  catch (...)
  {
    delete madWeight;
    throw;
  }
  delete madWeight;
  
  // Apply the most appropriate forecasting method
  if (best_method >= 0)
  {
    if (debug)
      logger << getName() << ": chosen method : " << methods[best_method]->getName() << endl;
    methods[best_method]->applyForecast(this, buckets, bucketcount, debug);
  }
}


//
// MOVING AVERAGE FORECAST
//


unsigned int Forecast::MovingAverage::defaultbuckets = 5;


double Forecast::MovingAverage::generateForecast
  (Forecast* fcst, const double history[], unsigned int count, const double madWeight[], bool debug)
{
  double error_mad = 0.0;
  double sum = 0.0;

  // Calculate the forecast and forecast error.
  for (unsigned int i = 1; i <= count; ++i)
  {
    sum += history[i-1];
    if (i>buckets) 
    {
      sum -= history[i-1-buckets];
      avg = sum / buckets;
    }
    else
      avg = sum / i;
    if (i >= fcst->getForecastSkip())
      error_mad += fabs(avg - history[i]) * madWeight[i];
  }

  // Echo the result
  if (debug)
    logger << (fcst ? fcst->getName() : "") << ": moving average : " 
      << "mad " << error_mad 
      << ", forecast " << avg << endl;
  return error_mad;
}


void Forecast::MovingAverage::applyForecast 
  (Forecast* forecast, const Date buckets[], unsigned int bucketcount, bool debug)
{
  // Loop over all buckets and set the forecast to a constant value
  if (avg < 0) return;
  for (unsigned int i = 1; i < bucketcount; ++i)
    forecast->setTotalQuantity(
      DateRange(buckets[i-1], buckets[i]), 
      avg
      );
}


//
// SINGLE EXPONENTIAL FORECAST
//


double Forecast::SingleExponential::initial_alfa = 0.2;
double Forecast::SingleExponential::min_alfa = 0.03;
double Forecast::SingleExponential::max_alfa = 1.0;


double Forecast::SingleExponential::generateForecast
  (Forecast* fcst, const double history[], unsigned int count, const double madWeight[], bool debug)
{
  // Verify whether this is a valid forecast method.
  //   - We need at least 5 buckets after the warmup period.
  if (count < fcst->getForecastSkip() + 5)
    return DBL_MAX;

  unsigned int iteration = 1;
  bool upperboundarytested = false;
  bool lowerboundarytested = false;
  double error_mad = 0.0, delta, df_dalfa_i, sum_11, sum_12;
  double best_error_mad = DBL_MAX, best_alfa, best_f_i;
  for (; iteration <= Forecast::getForecastIterations(); ++iteration)
  {
    // Initialize the iteration
    f_i = history[0];
    df_dalfa_i = sum_11 = sum_12 = error_mad = 0.0;

    // Calculate the forecast and forecast error.
    // We also compute the sums required for the Marquardt optimization.
    for (unsigned long i = 1; i <= count; ++i)
    {
      df_dalfa_i = history[i-1] - f_i + (1 - alfa) * df_dalfa_i;
      f_i = history[i-1] * alfa + (1 - alfa) * f_i;
      if (i == count) break;
      sum_12 += df_dalfa_i * (history[i] - f_i) * madWeight[i];
      sum_11 += df_dalfa_i * df_dalfa_i * madWeight[i];
      if (i >= fcst->getForecastSkip()) 
        error_mad += fabs(f_i - history[i]) * madWeight[i];
    }

    // Better than earlier iterations?
    if (error_mad < best_error_mad)
    {
      best_error_mad = error_mad;
      best_alfa = alfa;
      best_f_i = f_i;
    }

    // Add Levenberg - Marquardt damping factor
    if (fabs(sum_11 + error_mad / iteration) > ROUNDING_ERROR)
      sum_11 += error_mad / iteration;
 
    // Calculate a delta for the alfa parameter
    if (fabs(sum_11) < ROUNDING_ERROR) break;
    delta = sum_12 / sum_11;

    // Stop when we are close enough and have tried hard enough
    if (fabs(delta) < ACCURACY && iteration > 3) break;

    // New alfa
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
  }

  // Keep the best result
  f_i = best_f_i;

  // Echo the result
  if (debug)
    logger << (fcst ? fcst->getName() : "") << ": single exponential : " 
      << "alfa " << best_alfa 
      << ", mad " << best_error_mad 
      << ", " << iteration << " iterations"
      << ", forecast " << f_i << endl;
  return best_error_mad;
}


void Forecast::SingleExponential::applyForecast 
  (Forecast* forecast, const Date buckets[], unsigned int bucketcount, bool debug)
{
  // Loop over all buckets and set the forecast to a constant value
  if (f_i < 0) return;
  for (unsigned int i = 1; i < bucketcount; ++i)
    forecast->setTotalQuantity(
      DateRange(buckets[i-1], buckets[i]), 
      f_i
      );
}


//
// DOUBLE EXPONENTIAL FORECAST
//


double Forecast::DoubleExponential::initial_alfa = 0.2;
double Forecast::DoubleExponential::min_alfa = 0.02;
double Forecast::DoubleExponential::max_alfa = 1.0;
double Forecast::DoubleExponential::initial_gamma = 0.2;
double Forecast::DoubleExponential::min_gamma = 0.05;
double Forecast::DoubleExponential::max_gamma = 1.0;


double Forecast::DoubleExponential::generateForecast
  (Forecast* fcst, const double history[], unsigned int count, const double madWeight[], bool debug)
{
  // Verify whether this is a valid forecast method.
  //   - We need at least 5 buckets after the warmup period.
  if (count < fcst->getForecastSkip() + 5)
    return DBL_MAX;

  // Define variables
  double error_mad = 0.0, delta_alfa, delta_gamma, determinant;
  double constant_i_prev, trend_i_prev, d_constant_d_gamma_prev,
    d_constant_d_alfa_prev, d_constant_d_alfa, d_constant_d_gamma,	
    d_trend_d_alfa, d_trend_d_gamma, d_forecast_d_alfa, d_forecast_d_gamma,
    sum11, sum12, sum22, sum13, sum23;
  double best_error_mad = DBL_MAX, best_alfa, best_gamma, best_constant_i, best_trend_i;

  // Iterations
  unsigned int iteration = 1, boundarytested = 0;
  for (; iteration <= Forecast::getForecastIterations(); ++iteration)
  {
    // Initialize the iteration
    constant_i = history[0];
    trend_i = history[1] - history[0]; 
    error_mad = sum11 = sum12 = sum22 = sum13 = sum23 = 0.0;
    d_constant_d_alfa =	d_constant_d_gamma = d_trend_d_alfa = d_trend_d_gamma = 0.0;
    d_forecast_d_alfa = d_forecast_d_gamma = 0.0;

    // Calculate the forecast and forecast error.
    // We also compute the sums required for the Marquardt optimization.
    for (unsigned long i = 1; i <= count; ++i)
    {
      constant_i_prev = constant_i;
      trend_i_prev = trend_i;
      constant_i = history[i-1] * alfa + (1 - alfa) * (constant_i_prev + trend_i_prev);
      trend_i = gamma * (constant_i - constant_i_prev) + (1 - gamma) * trend_i_prev;
      if (i == count) break;
      d_constant_d_gamma_prev = d_constant_d_gamma;
      d_constant_d_alfa_prev = d_constant_d_alfa;
      d_constant_d_alfa = history[i-1] - constant_i_prev - trend_i_prev 
        + (1 - alfa) * d_forecast_d_alfa;
      d_constant_d_gamma = (1 - alfa) * d_forecast_d_gamma;
      d_trend_d_alfa = gamma * (d_constant_d_alfa - d_constant_d_alfa_prev)
        + (1 - gamma) * d_trend_d_alfa;
      d_trend_d_gamma = constant_i - constant_i_prev - trend_i_prev 
        + gamma * (d_constant_d_gamma - d_constant_d_gamma_prev)
        + (1 - gamma) * d_trend_d_gamma;
      d_forecast_d_alfa = d_constant_d_alfa + d_trend_d_alfa;
      d_forecast_d_gamma = d_constant_d_gamma + d_trend_d_gamma;
      sum11 += madWeight[i] * d_forecast_d_alfa * d_forecast_d_alfa;
      sum12 += madWeight[i] * d_forecast_d_alfa * d_forecast_d_gamma;
      sum22 += madWeight[i] * d_forecast_d_gamma * d_forecast_d_gamma;
      sum13 += madWeight[i] * d_forecast_d_alfa * (history[i] - constant_i - trend_i);
      sum23 += madWeight[i] * d_forecast_d_gamma * (history[i] - constant_i - trend_i);
      if (i >= fcst->getForecastSkip()) // Don't measure during the warmup period
        error_mad += fabs(constant_i + trend_i - history[i]) * madWeight[i];
    }

    // Better than earlier iterations?
    if (error_mad < best_error_mad)
    {
      best_error_mad = error_mad;
      best_alfa = alfa;
      best_gamma = gamma;
      best_constant_i = constant_i;
      best_trend_i = trend_i;
    }

    // Add Levenberg - Marquardt damping factor
    sum11 += error_mad / iteration;
    sum22 += error_mad / iteration;

    // Calculate a delta for the alfa and gamma parameters
    determinant = sum11 * sum22 - sum12 * sum12;
    if (fabs(determinant) < ROUNDING_ERROR) 
    {
      // Almost singular matrix. Try without the damping factor.
      sum11 -= error_mad / iteration;
      sum22 -= error_mad / iteration;
      determinant = sum11 * sum22 - sum12 * sum12;
    }
    if (fabs(determinant) < ROUNDING_ERROR) break; // Still singular
    delta_alfa = (sum13 * sum22 - sum23 * sum12) / determinant;
    delta_gamma = (sum23 * sum11 - sum13 * sum12) / determinant;

    // Stop when we are close enough and have tried hard enough
    if (fabs(delta_alfa) + fabs(delta_gamma) < ACCURACY && iteration > 3) 
      break;

    // New values for the next iteration
    alfa += delta_alfa;
    gamma += delta_gamma;

    // Limit the parameters in their allowed range.
    if (alfa > max_alfa) 
      alfa = max_alfa; 
    else if (alfa < min_alfa)
      alfa = min_alfa; 
    if (gamma > max_gamma) 
      gamma = max_gamma; 
    else if (gamma < min_gamma)
      gamma = min_gamma;    

    // Verify repeated running with both parameters at the boundary
    if ((gamma == min_gamma || gamma == max_gamma) 
      && (alfa == min_alfa || alfa == max_alfa))
    {
      if (boundarytested++ > 2) break;
    }
  }

  // Keep the best result
  constant_i = best_constant_i;
  trend_i = best_trend_i;

  // Echo the result
  if (debug)
    logger << (fcst ? fcst->getName() : "") << ": double exponential : " 
      << "alfa " << best_alfa 
      << ", gamma " << best_gamma 
      << ", mad " << best_error_mad 
      << ", " << iteration << " iterations"
      << ", constant " << constant_i
      << ", trend " << trend_i
      << ", forecast " << (trend_i + constant_i) << endl;
  return best_error_mad;
}


void Forecast::DoubleExponential::applyForecast
  (Forecast* forecast, const Date buckets[], unsigned int bucketcount, bool debug)
{
  // Loop over all buckets and set the forecast to a linearly changing value
  for (unsigned int i = 1; i < bucketcount; ++i)
    if (constant_i + i * trend_i > 0)
      forecast->setTotalQuantity(
        DateRange(buckets[i-1], buckets[i]), 
        constant_i + i * trend_i
        );
}


}       // end namespace
