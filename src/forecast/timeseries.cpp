/***************************************************************************
 *                                                                         *
 * Copyright (C) 2012-2016 by frePPLe bv                                   *
 *                                                                         *
 * Permission is hereby granted, free of charge, to any person obtaining   *
 * a copy of this software and associated documentation files (the         *
 * "Software"), to deal in the Software without restriction, including     *
 * without limitation the rights to use, copy, modify, merge, publish,     *
 * distribute, sublicense, and/or sell copies of the Software, and to      *
 * permit persons to whom the Software is furnished to do so, subject to   *
 * the following conditions:                                               *
 *                                                                         *
 * The above copyright notice and this permission notice shall be          *
 * included in all copies or substantial portions of the Software.         *
 *                                                                         *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,         *
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF      *
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                   *
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE  *
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION  *
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION   *
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.         *
 *                                                                         *
 ***************************************************************************/

#include "forecast.h"

namespace frepple {

#define ACCURACY 0.01

double ForecastSolver::Forecast_maxDeviation = 4.0;
int ForecastSolver::Forecast_DeadAfterInactivity(365);
unsigned long ForecastSolver::Forecast_Iterations(15L);
double ForecastSolver::Forecast_SmapeAlfa(0.95);
unsigned long ForecastSolver::Forecast_Skip(5);
double ForecastSolver::weight[ForecastSolver::MAXBUCKETS];
const MetaClass* ProblemOutlier::metadata = nullptr;

void ForecastSolver::computeBaselineForecast(const Forecast* fcst) {
  // Load history data in memory
  auto data = fcst->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);

  // Delete previous outlier problems
  deleteOutliers(fcst);

  // Skip all buckets till the first non-zero bucket
  auto bckt_start = data->getBuckets().begin();
  auto bckt_first = bckt_start;
  auto end = data->getBuckets().end();
  unsigned bucket_count = 1;
  while (bckt_start != end &&
         bckt_start->getEnd() <= Plan::instance().getFcstCurrent()) {
    if (Measures::orderstotal->getValue(*bckt_start) +
            Measures::ordersadjustment->getValue(*bckt_start) !=
        0.0)
      break;
    ++bckt_start;
    ++bucket_count;
  }

  // Count the number of history buckets
  unsigned int historycount = 0;
  for (auto bckt_cnt = bckt_start;
       bckt_cnt != end &&
       bckt_cnt->getEnd() <= Plan::instance().getFcstCurrent();
       ++bckt_cnt) {
    ++historycount;
    ++bucket_count;
  }

  // Copy the time series into an array
  // This speeds up the algorithm by avoiding the overhead of locking &
  // unlocking forecastdata cache
  vector<double> timeseries;
  vector<bool> no_data(historycount + 1);
  unsigned int count = 0;
  auto bckt_end = bckt_start;
  while (bckt_end != end &&
         bckt_end->getEnd() <= Plan::instance().getFcstCurrent()) {
    if (getAverageNoDataDays() ||
        Measures::nodata->getValue(*bckt_end) == 0.0) {
      timeseries.push_back(Measures::orderstotal->getValue(*bckt_end) +
                           Measures::ordersadjustment->getValue(*bckt_end));
      no_data[count] = Measures::nodata->getValue(*bckt_end) != 0.0;
      ++count;
    } else if (!getAverageNoDataDays())
      --historycount;
    ++bckt_end;
  }
  timeseries.push_back(0);

  auto bckt_plan_end = bckt_end;
  while (bckt_plan_end != end &&
         bckt_plan_end->getEnd() <= Plan::instance().getCurrent()) {
    ++bckt_plan_end;
  }

  // Filler logic to put a value for no-data buckets.
  // We use the average of the last and the next data point.
  if (getAverageNoDataDays()) {
    bckt_end = bckt_start;
    for (unsigned int i = 0; i < count;) {
      if (!no_data[i]) {
        // normal data point
        ++i;
        ++bckt_end;
      } else {
        // No value in the bucket
        int prev_data = i - 1;
        while (prev_data >= 0 && no_data[prev_data]) --prev_data;
        auto next_data = i + 1;
        while (next_data < count && no_data[next_data]) ++next_data;
        double val;
        if (prev_data >= 0 && next_data < count)
          // prev and next both found
          val = (timeseries[prev_data] + timeseries[next_data]) / 2;
        else if (prev_data >= 0)
          // only prev found
          val = timeseries[prev_data];
        else if (next_data < count)
          // only next found
          val = timeseries[next_data];
        else
          // nothing found
          val = 0.0;
        while (i < next_data) {
          if (getLogLevel() > 2)
            logger << fcst << ": filling missing data point for "
                   << bckt_end->getDates() << " with " << val << endl;
          timeseries[i] = val;
          no_data[i] = false;
          ++i;
          ++bckt_end;
        }
      }
    }
  }

  // Count zero buckets and track the number of inactive buckets.
  unsigned int zero = 0;
  unsigned int inactive_buckets = 0;
  for (size_t i = 0; i < count; ++i) {
    if (timeseries[i] == 0.0) {
      ++zero;
      ++inactive_buckets;
    } else
      inactive_buckets = 0;
  }

  // Convert DeadAfterInactivity from days to a number of buckets
  double DeadAfterInactivity =
      (bckt_end != end && bckt_first != end)
          ? ceil(static_cast<double>(getForecastDeadAfterInactivity()) * 86400 *
                 bucket_count /
                 static_cast<double>(bckt_end->getEnd() -
                                     bckt_first->getStart()))
          : inactive_buckets;

  // We create the forecasting objects in stack memory for best performance.
  MovingAverage moving_avg;
  Croston croston;
  SingleExponential single_exp;
  DoubleExponential double_exp;
  Seasonal seasonal;
  Manual manual;
  int numberOfMethods = 0;
  ForecastMethod* qualifiedmethods[6];

  // Rules to determine which forecast methods can be applied
  if (fcst->methods & Forecast::METHOD_MANUAL) {
    // When a manual forecast is selected, it is the one and only method.
    qualifiedmethods[numberOfMethods++] = &manual;
  } else if (historycount <= getForecastSkip() + 5) {
    // If there is too little history, only use moving average or the forced
    // methods
    if (fcst->methods & Forecast::METHOD_MOVINGAVERAGE)
      qualifiedmethods[numberOfMethods++] = &moving_avg;
  } else if (inactive_buckets >= DeadAfterInactivity) {
    // If the part has not been active recenty, switch to manual or the forced
    // methods unless a new demand is present in the future
    bool foundFutureDemand=false;
    for (auto bckt_iter = bckt_end;
       bckt_iter != end;
       ++bckt_iter) {
        if (Measures::orderstotal->getValue(*bckt_iter) +
            Measures::ordersadjustment->getValue(*bckt_iter) !=
        0.0) {
          foundFutureDemand = true;
          break;
        }
    }
    if (!foundFutureDemand)
      qualifiedmethods[numberOfMethods++] = &manual;
  } else {
    if (zero > Croston::getMinIntermittence() * historycount) {
      // If there are too many zeros: use croston or moving average.
      if (fcst->methods & Forecast::METHOD_CROSTON)
        qualifiedmethods[numberOfMethods++] = &croston;
    } else {
      // The most common case: enough values and not intermittent
      if (fcst->methods & Forecast::METHOD_MOVINGAVERAGE)
        qualifiedmethods[numberOfMethods++] = &moving_avg;
      if (fcst->methods & Forecast::METHOD_CONSTANT)
        qualifiedmethods[numberOfMethods++] = &single_exp;
      if (fcst->methods & Forecast::METHOD_TREND)
        qualifiedmethods[numberOfMethods++] = &double_exp;
      if (fcst->methods & Forecast::METHOD_SEASONAL)
        qualifiedmethods[numberOfMethods++] = &seasonal;
    }
  }

  // Special case: no method qualifies at all based on our criteria
  // We will take only the enforced methods.
  if (numberOfMethods == 0) {
    if (getLogLevel() > 0)
      logger << fcst
             << ": Warning: The specified forecast methods are potentially not "
                "suitable!"
             << endl;
    if (fcst->methods & Forecast::METHOD_MOVINGAVERAGE)
      qualifiedmethods[numberOfMethods++] = &moving_avg;
    if (fcst->methods & Forecast::METHOD_CROSTON)
      qualifiedmethods[numberOfMethods++] = &croston;
    if (fcst->methods & Forecast::METHOD_CONSTANT)
      qualifiedmethods[numberOfMethods++] = &single_exp;
    if (fcst->methods & Forecast::METHOD_TREND)
      qualifiedmethods[numberOfMethods++] = &double_exp;
    if (fcst->methods & Forecast::METHOD_SEASONAL)
      qualifiedmethods[numberOfMethods++] = &seasonal;
  }

  // Evaluate each forecast method
  double best_error = DBL_MAX;
  int best_method = -1;
  for (int i = 0; i < numberOfMethods; ++i) {
    Metrics res = qualifiedmethods[i]->generateForecast(
        fcst, data->getBuckets(), bckt_start->getIndex(), timeseries,
        historycount, this);
    if (res.smape < best_error || res.force) {
      best_error = res.smape;
      best_method = i;
      const_cast<Forecast*>(fcst)->setDeviation(res.standarddeviation);
      if (res.force) {
        const_cast<Forecast*>(fcst)->setDeviation(res.standarddeviation);
        break;
      }
    }
  }
  if (fcst->methods == fcst->METHOD_SEASONAL && best_error == DBL_MAX) {
    // Special case: the only allowed forecast method is seasonal and we
    // couldn't detect any cycles. We fall back to the trend method.
    qualifiedmethods[0] = &double_exp;
    best_method = 0;
    Metrics res = double_exp.generateForecast(fcst, data->getBuckets(),
                                              bckt_start->getIndex(),
                                              timeseries, historycount, this);
    best_error = res.smape;
    const_cast<Forecast*>(fcst)->setDeviation(res.standarddeviation);
    // Special case in the special case: Trend doesn't apply as there are less
    // than 5 buckets after the warmup period, switch to moving average
    if (best_error == DBL_MAX) {
      qualifiedmethods[0] = &moving_avg;
      best_method = 0;
      Metrics res = moving_avg.generateForecast(fcst, data->getBuckets(),
                                                bckt_start->getIndex(),
                                                timeseries, historycount, this);
      best_error = res.smape;
      const_cast<Forecast*>(fcst)->setDeviation(res.standarddeviation);
    }
  }

  // Apply the most appropriate forecasting method
  if (best_method >= 0) {
    const_cast<Forecast*>(fcst)->setMethod(
        qualifiedmethods[best_method]->getCode());
    const_cast<Forecast*>(fcst)->setSMAPEerror(best_error);
    if (getLogLevel() > 0)
      logger << fcst << ": chosen method: " << fcst->getMethod()
             << ", standard deviation: " << fcst->getDeviation()
             << ", smape error: " << fcst->getSMAPEerror() << endl;
    qualifiedmethods[best_method]->applyForecast(
        const_cast<Forecast*>(fcst), data->getBuckets(),
        bckt_plan_end->getIndex(), !getAutocommit() ? commands : nullptr);
  } else {
    const_cast<Forecast*>(fcst)->setMethod(0);
    const_cast<Forecast*>(fcst)->setSMAPEerror(0.0);
  }
}

//
// MOVING AVERAGE FORECAST
//

unsigned int ForecastSolver::MovingAverage::defaultorder = 5;

ForecastSolver::Metrics ForecastSolver::MovingAverage::generateForecast(
    const Forecast* fcst, vector<ForecastBucketData>& bucketdata,
    short firstbckt, vector<double>& timeseries, unsigned int count,
    ForecastSolver* solver) {
  double error_smape, error_smape_weights;
  double* clean_history = new double[count + 1];

  // Loop over the outliers 'scan'/0 and 'filter'/1 modes
  double standarddeviation = 0.0;
  double maxdeviation = 0.0;
  for (short outliers = 0; outliers <= 1; ++outliers) {
    if (outliers) clean_history[0] = timeseries[0];
    error_smape = 0.0;
    error_smape_weights = 0.0;

    // Calculate the forecast and forecast error.
    for (unsigned int i = 1; i <= count; ++i) {
      double actual = timeseries[i];
      if (outliers == 0) {
        double sum = 0.0;
        for (unsigned int j = 0; j < order && j < i; ++j)
          sum += timeseries[i - j - 1];
        avg = sum / order;
        if (i == count) break;

        // Scan outliers by computing the standard deviation
        // and keeping track of the difference between actuals and forecast

        standarddeviation += (avg - actual) * (avg - actual);
        if (fabs(avg - actual) > maxdeviation)
          maxdeviation = fabs(avg - actual);
      } else {
        double sum = 0.0;
        for (unsigned int j = 0; j < order && j < i; ++j)
          sum += clean_history[i - j - 1];
        avg = sum / order;
        if (i == count) break;

        // Clean outliers from history.
        // We copy the cleaned history data in a new array.
        if (actual >
            avg + ForecastSolver::Forecast_maxDeviation * standarddeviation) {
          clean_history[i] =
              avg + ForecastSolver::Forecast_maxDeviation * standarddeviation;
          new ProblemOutlier(
              bucketdata[i + firstbckt].getOrCreateForecastBucket(), this,
              true);
        } else if (actual < avg - ForecastSolver::Forecast_maxDeviation *
                                      standarddeviation) {
          clean_history[i] =
              avg - ForecastSolver::Forecast_maxDeviation * standarddeviation;
          new ProblemOutlier(
              bucketdata[i + firstbckt].getOrCreateForecastBucket(), this,
              true);
        } else
          clean_history[i] = actual;
      }

      if (i >= solver->getForecastSkip() && i < count &&
          fabs(avg + actual) > ROUNDING_ERROR) {
        error_smape +=
            fabs(avg - actual) / fabs(avg + actual) * weight[count - i];
        error_smape_weights += weight[count - i];
      }
    }

    // Check outliers
    if (outliers == 0) {
      if (count > 1) {
        standarddeviation = sqrt(standarddeviation / (count - 1));
        maxdeviation /= standarddeviation;
        // Don't repeat if there are no outliers
        if (maxdeviation < Forecast_maxDeviation) break;
      } else {
        // Single data point - never an outlier
        standarddeviation = sqrt(standarddeviation);
        maxdeviation = 0.0;
        break;
      }
    }
  }  // End loop: 'scan' or 'filter' mode for outliers

  // Echo the result
  if (error_smape_weights) error_smape /= error_smape_weights;
  if (solver->getLogLevel() > 0)
    logger << (fcst ? fcst->getName() : "") << ": moving average : "
           << "smape " << error_smape << ", forecast " << avg
           << ", standard deviation " << standarddeviation << endl;
  delete[] clean_history;
  return ForecastSolver::Metrics(error_smape, standarddeviation, false);
}

void ForecastSolver::MovingAverage::applyForecast(
    Forecast* forecast, vector<ForecastBucketData>& bucketdata, short bcktstart,
    CommandManager* mgr) {
  // Loop over all buckets and set the forecast to a constant value
  if (forecast->getDiscrete()) {
    double carryover = 0.0;
    for (auto bckt = bucketdata.begin() + bcktstart;
         bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
         ++bckt) {
      carryover += avg;
      double val = ceil(carryover - 0.5);
      carryover -= val;
      Measures::forecastbaseline->disaggregate(*bckt, val > 0.0 ? val : 0.0,
                                               mgr);
    }
  } else {
    for (auto bckt = bucketdata.begin() + bcktstart;
         bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
         ++bckt)
      Measures::forecastbaseline->disaggregate(*bckt, avg > 0.0 ? avg : 0.0,
                                               mgr);
  }

  deleteOutliers(forecast, this);
}

//
// SINGLE EXPONENTIAL FORECAST
//

double ForecastSolver::SingleExponential::initial_alfa = 0.2;
double ForecastSolver::SingleExponential::min_alfa = 0.03;
double ForecastSolver::SingleExponential::max_alfa = 1.0;

ForecastSolver::Metrics ForecastSolver::SingleExponential::generateForecast(
    const Forecast* fcst, vector<ForecastBucketData>& bucketdata,
    short firstbckt, vector<double>& timeseries, unsigned int count,
    ForecastSolver* solver) {
  // Verify whether this is a valid forecast method.
  //   - We need at least 5 buckets after the warmup period.
  if (count < solver->getForecastSkip() + 5)
    return ForecastSolver::Metrics(DBL_MAX, DBL_MAX, false);

  unsigned int iteration = 1;
  bool upperboundarytested = false;
  bool lowerboundarytested = false;
  double error = 0.0, error_smape = 0.0, error_smape_weights = 0.0,
         best_smape = 0.0, delta, df_dalfa_i, sum_11, sum_12;
  double best_error = DBL_MAX, best_alfa = initial_alfa, best_f_i = 0.0;
  double best_standarddeviation = 0.0;
  for (; iteration <= solver->getForecastIterations(); ++iteration) {
    // Loop over the outliers 'scan'/0 and 'filter'/1 modes
    double standarddeviation = 0.0;
    double maxdeviation = 0.0;
    for (short outliers = 0; outliers <= 1; outliers++) {
      // Initialize variables
      df_dalfa_i = sum_11 = sum_12 = error_smape = error_smape_weights = error =
          0.0;

      // Initialize the iteration with the average of the first 3 values.
      double history_0 = timeseries[0];
      double history_1 = timeseries[1];
      double history_2 = timeseries[2];
      f_i = (history_0 + history_1 + history_2) / 3;
      if (outliers == 1) {
        // TODO this logic isn't the right concept?
        double t = 0.0;
        if (history_0 >
            f_i + ForecastSolver::Forecast_maxDeviation * standarddeviation) {
          t += f_i + ForecastSolver::Forecast_maxDeviation * standarddeviation;
        } else if (history_0 < f_i - ForecastSolver::Forecast_maxDeviation *
                                         standarddeviation) {
          t += f_i - ForecastSolver::Forecast_maxDeviation * standarddeviation;
        } else
          t += history_0;
        if (history_1 >
            f_i + ForecastSolver::Forecast_maxDeviation * standarddeviation) {
          t += f_i + ForecastSolver::Forecast_maxDeviation * standarddeviation;
        } else if (history_1 < f_i - ForecastSolver::Forecast_maxDeviation *
                                         standarddeviation) {
          t += f_i - ForecastSolver::Forecast_maxDeviation * standarddeviation;
        } else
          t += history_1;
        if (history_2 >
            f_i + ForecastSolver::Forecast_maxDeviation * standarddeviation) {
          t += f_i + ForecastSolver::Forecast_maxDeviation * standarddeviation;
        } else if (history_2 < f_i - ForecastSolver::Forecast_maxDeviation *
                                         standarddeviation) {
          t += f_i - ForecastSolver::Forecast_maxDeviation * standarddeviation;
        } else
          t += history_2;
        f_i = t / 3;
      }

      // Calculate the forecast and forecast error.
      // We also compute the sums required for the Marquardt optimization.
      double history_i = history_0;
      double history_i_min_1 = history_0;
      for (unsigned long i = 1; i <= count; ++i) {
        history_i_min_1 = history_i;
        history_i = timeseries[i];
        df_dalfa_i = history_i_min_1 - f_i + (1 - alfa) * df_dalfa_i;
        f_i = history_i_min_1 * alfa + (1 - alfa) * f_i;
        if (i == count) break;
        if (outliers == 0) {
          // Scan outliers by computing the standard deviation
          // and keeping track of the difference between actuals and forecast
          standarddeviation += (f_i - history_i) * (f_i - history_i);
          if (fabs(f_i - history_i) > maxdeviation)
            maxdeviation = fabs(f_i - history_i);
        } else {
          // Clean outliers from history
          if (history_i >
              f_i + ForecastSolver::Forecast_maxDeviation * standarddeviation) {
            history_i =
                f_i + ForecastSolver::Forecast_maxDeviation * standarddeviation;
            if (iteration == 1)
              new ProblemOutlier(
                  bucketdata[i + firstbckt].getOrCreateForecastBucket(), this,
                  true);
          } else if (history_i < f_i - ForecastSolver::Forecast_maxDeviation *
                                           standarddeviation) {
            history_i =
                f_i - ForecastSolver::Forecast_maxDeviation * standarddeviation;
            if (iteration == 1)
              new ProblemOutlier(
                  bucketdata[i + firstbckt].getOrCreateForecastBucket(), this,
                  true);
          }
        }
        sum_12 += df_dalfa_i * (history_i - f_i) * weight[count - i];
        sum_11 += df_dalfa_i * df_dalfa_i * weight[count - i];
        if (i >= solver->getForecastSkip()) {
          error += (f_i - history_i) * (f_i - history_i) * weight[count - i];
          if (fabs(f_i + history_i) > ROUNDING_ERROR) {
            error_smape +=
                fabs(f_i - history_i) / (f_i + history_i) * weight[count - i];
            error_smape_weights += weight[count - i];
          }
        }
      }

      // Check outliers
      if (outliers == 0) {
        standarddeviation = sqrt(standarddeviation / (count - 1));
        maxdeviation /= standarddeviation;
        // Don't repeat if there are no outliers
        if (maxdeviation < ForecastSolver::Forecast_maxDeviation) break;
      }
    }  // End loop: 'scan' or 'filter' mode for outliers

    // Better than earlier iterations?
    if (error < best_error) {
      best_error = error;
      best_smape =
          error_smape_weights ? error_smape / error_smape_weights : 0.0;
      best_alfa = alfa;
      best_f_i = f_i;
      best_standarddeviation = standarddeviation;
    }

    // Add Levenberg - Marquardt damping factor
    if (fabs(sum_11 + error / iteration) > ROUNDING_ERROR)
      sum_11 += error / iteration;

    // Calculate a delta for the alfa parameter
    if (fabs(sum_11) < ROUNDING_ERROR) break;
    delta = sum_12 / sum_11;

    // Stop when we are close enough and have tried hard enough
    if (fabs(delta) < ACCURACY && iteration > 3) break;

    // Debugging info on the iteration
    if (solver->getLogLevel() > 5)
      logger << (fcst ? fcst->getName() : "")
             << ": single exponential : iteration " << iteration << ": alfa "
             << alfa << ", smape "
             << (error_smape_weights ? error_smape / error_smape_weights : 0.0)
             << endl;

    // New alfa
    alfa += delta;

    // Stop when we repeatedly bounce against the limits.
    // Testing a limits once is allowed.
    if (alfa > max_alfa) {
      alfa = max_alfa;
      if (upperboundarytested) break;
      upperboundarytested = true;
    } else if (alfa < min_alfa) {
      alfa = min_alfa;
      if (lowerboundarytested) break;
      lowerboundarytested = true;
    }
  }

  // Keep the best result
  f_i = best_f_i;

  // Echo the result
  if (solver->getLogLevel() > 0)
    logger << (fcst ? fcst->getName() : "") << ": single exponential : "
           << "alfa " << best_alfa << ", smape " << best_smape << ", "
           << iteration << " iterations"
           << ", forecast " << f_i << ", standard deviation "
           << best_standarddeviation << endl;
  return ForecastSolver::Metrics(best_smape, best_standarddeviation, false);
}

void ForecastSolver::SingleExponential::applyForecast(
    Forecast* forecast, vector<ForecastBucketData>& bucketdata, short bcktstart,
    CommandManager* mgr) {
  // Loop over all buckets and set the forecast to a constant value
  if (forecast->discrete) {
    double carryover = 0.0;
    for (auto bckt = bucketdata.begin() + bcktstart;
         bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
         ++bckt) {
      carryover += f_i;
      double val = ceil(carryover - 0.5);
      carryover -= val;
      Measures::forecastbaseline->disaggregate(*bckt, val > 0.0 ? val : 0.0,
                                               mgr);
    }
  } else {
    for (auto bckt = bucketdata.begin() + bcktstart;
         bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
         ++bckt)
      Measures::forecastbaseline->disaggregate(*bckt, f_i > 0.0 ? f_i : 0.0,
                                               mgr);
  }

  deleteOutliers(forecast, this);
}

//
// DOUBLE EXPONENTIAL FORECAST
//

double ForecastSolver::DoubleExponential::initial_alfa = 0.2;
double ForecastSolver::DoubleExponential::min_alfa = 0.02;
double ForecastSolver::DoubleExponential::max_alfa = 1.0;
double ForecastSolver::DoubleExponential::initial_gamma = 0.2;
double ForecastSolver::DoubleExponential::min_gamma = 0.05;
double ForecastSolver::DoubleExponential::max_gamma = 1.0;
double ForecastSolver::DoubleExponential::dampenTrend = 0.8;

ForecastSolver::Metrics ForecastSolver::DoubleExponential::generateForecast(
    const Forecast* fcst, vector<ForecastBucketData>& bucketdata,
    short firstbckt, vector<double>& timeseries, unsigned int count,
    ForecastSolver* solver) {
  // Verify whether this is a valid forecast method.
  //   - We need at least 5 buckets after the warmup period.
  if (count < solver->getForecastSkip() + 5)
    return ForecastSolver::Metrics(DBL_MAX, DBL_MAX, false);

  // Define variables
  double error = 0.0, error_smape = 0.0, error_smape_weights = 0.0, delta_alfa,
         delta_gamma, determinant;
  double constant_i_prev, trend_i_prev, d_constant_d_gamma_prev,
      d_constant_d_alfa_prev, d_constant_d_alfa, d_constant_d_gamma,
      d_trend_d_alfa, d_trend_d_gamma, d_forecast_d_alfa, d_forecast_d_gamma,
      sum11, sum12, sum22, sum13, sum23;
  double best_error = DBL_MAX, best_smape = 0, best_alfa = initial_alfa,
         best_gamma = initial_gamma, best_constant_i = 0.0, best_trend_i = 0.0;
  double best_standarddeviation = 0.0;

  // Iterations
  unsigned int iteration = 1, boundarytested = 0;
  for (; iteration <= solver->getForecastIterations(); ++iteration) {
    // Loop over the outliers 'scan'/0 and 'filter'/1 modes
    double standarddeviation = 0.0;
    double maxdeviation = 0.0;
    for (short outliers = 0; outliers <= 1; outliers++) {
      // Initialize variables
      error = error_smape = error_smape_weights = sum11 = sum12 = sum22 =
          sum13 = sum23 = 0.0;
      d_constant_d_alfa = d_constant_d_gamma = d_trend_d_alfa =
          d_trend_d_gamma = 0.0;
      d_forecast_d_alfa = d_forecast_d_gamma = 0.0;

      // Initialize the iteration
      double history_0 = timeseries[0];
      double history_1 = timeseries[1];
      double history_2 = timeseries[2];
      double history_3 = timeseries[3];
      constant_i = (history_0 + history_1 + history_2) / 3;
      trend_i = (history_3 - history_0) / 3;
      if (outliers == 1) {
        // TODO this logic isn't the right concept?
        double t1 = 0.0;
        if (history_0 > constant_i + ForecastSolver::Forecast_maxDeviation *
                                         standarddeviation)
          t1 = constant_i +
               ForecastSolver::Forecast_maxDeviation * standarddeviation;
        else if (history_0 <
                 constant_i -
                     ForecastSolver::Forecast_maxDeviation * standarddeviation)
          t1 = constant_i -
               ForecastSolver::Forecast_maxDeviation * standarddeviation;
        else
          t1 = history_0;
        double t2 = -t1;
        if (history_1 >
            constant_i + trend_i +
                ForecastSolver::Forecast_maxDeviation * standarddeviation)
          t1 += constant_i + trend_i +
                ForecastSolver::Forecast_maxDeviation * standarddeviation;
        else if (history_1 <
                 constant_i + trend_i -
                     ForecastSolver::Forecast_maxDeviation * standarddeviation)
          t1 += constant_i + trend_i -
                ForecastSolver::Forecast_maxDeviation * standarddeviation;
        else
          t1 += history_1;
        if (history_2 >
            constant_i + 2 * trend_i +
                ForecastSolver::Forecast_maxDeviation * standarddeviation) {
          t1 += constant_i + 2 * trend_i +
                ForecastSolver::Forecast_maxDeviation * standarddeviation;
          t2 += constant_i + 2 * trend_i +
                ForecastSolver::Forecast_maxDeviation * standarddeviation;
        } else if (history_2 < constant_i + 2 * trend_i -
                                   ForecastSolver::Forecast_maxDeviation *
                                       standarddeviation) {
          t1 += constant_i + 2 * trend_i -
                ForecastSolver::Forecast_maxDeviation * standarddeviation;
          t2 += constant_i + 2 * trend_i -
                ForecastSolver::Forecast_maxDeviation * standarddeviation;
        } else {
          t1 += history_2;
          t2 += history_2;
        }
        constant_i = t1 / 3;
        trend_i = t2 / 3;
      }

      // Calculate the forecast and forecast error.
      // We also compute the sums required for the Marquardt optimization.
      double history_i = history_0;
      double history_i_min_1 = history_0;
      for (unsigned long i = 1; i <= count; ++i) {
        history_i_min_1 = history_i;
        history_i = timeseries[i];
        constant_i_prev = constant_i;
        trend_i_prev = trend_i;
        constant_i = history_i_min_1 * alfa +
                     (1 - alfa) * (constant_i_prev + trend_i_prev);
        trend_i =
            gamma * (constant_i - constant_i_prev) + (1 - gamma) * trend_i_prev;
        if (i == count) break;
        if (outliers == 0) {
          // Scan outliers by computing the standard deviation
          // and keeping track of the difference between actuals and forecast
          standarddeviation += (constant_i + trend_i - history_i) *
                               (constant_i + trend_i - history_i);
          if (fabs(constant_i + trend_i - history_i) > maxdeviation)
            maxdeviation = fabs(constant_i + trend_i - history_i);
        } else {
          // Clean outliers from history
          if (history_i >
              constant_i + trend_i +
                  ForecastSolver::Forecast_maxDeviation * standarddeviation) {
            history_i =
                constant_i + trend_i +
                ForecastSolver::Forecast_maxDeviation * standarddeviation;
            if (iteration == 1)
              new ProblemOutlier(
                  bucketdata[i + firstbckt].getOrCreateForecastBucket(), this,
                  true);
          } else if (history_i < constant_i + trend_i -
                                     ForecastSolver::Forecast_maxDeviation *
                                         standarddeviation) {
            history_i =
                constant_i + trend_i -
                ForecastSolver::Forecast_maxDeviation * standarddeviation;
            if (iteration == 1)
              new ProblemOutlier(
                  bucketdata[i + firstbckt].getOrCreateForecastBucket(), this,
                  true);
          }
        }
        d_constant_d_gamma_prev = d_constant_d_gamma;
        d_constant_d_alfa_prev = d_constant_d_alfa;
        d_constant_d_alfa = history_i_min_1 - constant_i_prev - trend_i_prev +
                            (1 - alfa) * d_forecast_d_alfa;
        d_constant_d_gamma = (1 - alfa) * d_forecast_d_gamma;
        d_trend_d_alfa = gamma * (d_constant_d_alfa - d_constant_d_alfa_prev) +
                         (1 - gamma) * d_trend_d_alfa;
        d_trend_d_gamma =
            constant_i - constant_i_prev - trend_i_prev +
            gamma * (d_constant_d_gamma - d_constant_d_gamma_prev) +
            (1 - gamma) * d_trend_d_gamma;
        d_forecast_d_alfa = d_constant_d_alfa + d_trend_d_alfa;
        d_forecast_d_gamma = d_constant_d_gamma + d_trend_d_gamma;
        sum11 += weight[count - i] * d_forecast_d_alfa * d_forecast_d_alfa;
        sum12 += weight[count - i] * d_forecast_d_alfa * d_forecast_d_gamma;
        sum22 += weight[count - i] * d_forecast_d_gamma * d_forecast_d_gamma;
        sum13 += weight[count - i] * d_forecast_d_alfa *
                 (history_i - constant_i - trend_i);
        sum23 += weight[count - i] * d_forecast_d_gamma *
                 (history_i - constant_i - trend_i);
        if (i >=
            solver
                ->getForecastSkip())  // Don't measure during the warmup period
        {
          error += (constant_i + trend_i - history_i) *
                   (constant_i + trend_i - history_i) * weight[count - i];
          if (fabs(constant_i + trend_i + history_i) > ROUNDING_ERROR) {
            error_smape += fabs(constant_i + trend_i - history_i) /
                           fabs(constant_i + trend_i + history_i) *
                           weight[count - i];
            error_smape_weights += weight[count - i];
          }
        }
      }

      // Check outliers
      if (outliers == 0) {
        standarddeviation = sqrt(standarddeviation / (count - 1));
        maxdeviation /= standarddeviation;
        // Don't repeat if there are no outliers
        if (maxdeviation < ForecastSolver::Forecast_maxDeviation) break;
      }
    }  // End loop: 'scan' or 'filter' mode for outliers

    // Better than earlier iterations?
    if (error < best_error) {
      best_error = error;
      best_smape =
          error_smape_weights ? error_smape / error_smape_weights : 0.0;
      best_alfa = alfa;
      best_gamma = gamma;
      best_constant_i = constant_i;
      best_trend_i = trend_i;
      best_standarddeviation = standarddeviation;
    }

    // Add Levenberg - Marquardt damping factor
    // if (alfa < max_alfa && alfa > min_alfa)
    sum11 += error / iteration;  // * d_forecast_d_alfa;
    // if (gamma < max_gamma && gamma > min_gamma)
    sum22 += error / iteration;  // * d_forecast_d_gamma;

    // Calculate a delta for the alfa and gamma parameters
    determinant = sum11 * sum22 - sum12 * sum12;
    if (fabs(determinant) < ROUNDING_ERROR) {
      // Almost singular matrix. Try without the damping factor.
      // if (alfa < max_alfa && alfa > min_alfa)
      sum11 -= error / iteration;
      // if (gamma < max_gamma && gamma > min_gamma)
      sum22 -= error / iteration;
      determinant = sum11 * sum22 - sum12 * sum12;
      if (fabs(determinant) < ROUNDING_ERROR)
        // Still singular - stop iterations here
        break;
    }
    delta_alfa = (sum13 * sum22 - sum23 * sum12) / determinant;
    delta_gamma = (sum23 * sum11 - sum13 * sum12) / determinant;

    // Stop when we are close enough and have tried hard enough
    if (fabs(delta_alfa) + fabs(delta_gamma) < 2 * ACCURACY && iteration > 3)
      break;

    // Debugging info on the iteration
    if (solver->getLogLevel() > 5)
      logger << (fcst ? fcst->getName() : "")
             << ": double exponential : iteration " << iteration << ": alfa "
             << alfa << ", gamma " << gamma << ", smape "
             << (error_smape_weights ? error_smape / error_smape_weights : 0)
             << endl;

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
    if ((gamma == min_gamma || gamma == max_gamma) &&
        (alfa == min_alfa || alfa == max_alfa)) {
      if (boundarytested++ > 5) break;
    }
  }

  // Keep the best result
  constant_i = best_constant_i;
  trend_i = best_trend_i;

  // Echo the result
  if (solver->getLogLevel() > 0)
    logger << (fcst ? fcst->getName() : "") << ": double exponential : "
           << "alfa " << best_alfa << ", gamma " << best_gamma << ", smape "
           << best_smape << ", " << iteration << " iterations"
           << ", constant " << constant_i << ", trend " << trend_i
           << ", forecast " << (trend_i + constant_i) << ", standard deviation "
           << best_standarddeviation << endl;
  return ForecastSolver::Metrics(best_smape, best_standarddeviation, false);
}

void ForecastSolver::DoubleExponential::applyForecast(
    Forecast* forecast, vector<ForecastBucketData>& bucketdata, short bcktstart,
    CommandManager* mgr) {
  // Loop over all buckets and set the forecast to a linearly changing value
  if (forecast->discrete) {
    double carryover = 0.0;
    for (auto bckt = bucketdata.begin() + bcktstart;
         bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
         ++bckt) {
      constant_i += trend_i;
      trend_i *= dampenTrend;  // Reduce slope in the future
      carryover += constant_i;
      double val = ceil(carryover - 0.5);
      carryover -= val;
      Measures::forecastbaseline->disaggregate(*bckt, val > 0.0 ? val : 0.0,
                                               mgr);
    }
  } else {
    for (auto bckt = bucketdata.begin() + bcktstart;
         bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
         ++bckt) {
      constant_i += trend_i;
      trend_i *= dampenTrend;  // Reduce slope in the future
      Measures::forecastbaseline->disaggregate(
          *bckt, constant_i > 0.0 ? constant_i : 0.0, mgr);
    }
  }

  deleteOutliers(forecast, this);
}

//
// SEASONAL FORECAST
//

unsigned int ForecastSolver::Seasonal::min_period = 2;
unsigned int ForecastSolver::Seasonal::max_period = 14;
double ForecastSolver::Seasonal::dampenTrend = 0.8;
double ForecastSolver::Seasonal::initial_alfa = 0.2;
double ForecastSolver::Seasonal::min_alfa = 0.02;
double ForecastSolver::Seasonal::max_alfa = 1.0;
double ForecastSolver::Seasonal::initial_beta = 0.2;
double ForecastSolver::Seasonal::min_beta = 0.2;
double ForecastSolver::Seasonal::max_beta = 1.0;
double ForecastSolver::Seasonal::gamma = 0.05;
double ForecastSolver::Seasonal::min_autocorrelation = 0.5;
double ForecastSolver::Seasonal::max_autocorrelation = 0.8;

void ForecastSolver::Seasonal::detectCycle(vector<double>& timeseries,
                                           unsigned int count) {
  // We need at least 2 cycles
  if (count < min_period * 2) return;

  // Compute the average value
  double average = 0.0;
  for (unsigned int i = 0; i < count; ++i) average += timeseries[i];
  average /= count;

  // Compute variance
  double variance = 0.0;
  for (unsigned int i = 0; i < count; ++i)
    variance += (timeseries[i] - average) * (timeseries[i] - average);
  variance /= count;

  // Compute autocorrelation for different periods
  unsigned short best_period = 0;
  double best_autocorrelation =
      min_autocorrelation;  // Minimum required correlation!
  double correlations[7] = {10, 10, 10, 10, 10, 10, 10};
  for (auto p = min_period; p <= max_period && p < count / 2; ++p) {
    // Shift the previous correlation values
    for (short i = 6; i > 0; --i) correlations[i] = correlations[i - 1];

    // Compute correlation
    correlations[0] = 0.0;
    for (unsigned int i = p; i < count; ++i)
      correlations[0] +=
          (timeseries[i - p] - average) * (timeseries[i] - average);
    correlations[0] /= count - p;
    correlations[0] /= variance;

    // Detect autocorrelation peaks in a time window.
    if (p > min_period + 1 && correlations[1] > correlations[2] * 1.1 &&
        correlations[1] > correlations[0] * 1.1 &&
        correlations[1] > best_autocorrelation) {
      // Autocorrelation peak at a single period
      best_autocorrelation = correlations[1];
      best_period = p - 1;
    }
    if (p > min_period + 4 && correlations[2] > best_autocorrelation &&
        correlations[2] > (correlations[0] + correlations[1]) / 2 &&
        correlations[2] > (correlations[3] + correlations[4]) / 2) {
      // Autocorrelation peak with a 2 period average
      best_autocorrelation = correlations[2];
      best_period = p - 2;
    }
    if (p > min_period + 6 && correlations[3] > best_autocorrelation &&
        correlations[3] >
            (correlations[0] + correlations[1] + correlations[2]) / 3 &&
        correlations[3] >
            (correlations[4] + correlations[5] + correlations[6]) / 3) {
      // Autocorrelation peak with a 3 period average
      best_autocorrelation = correlations[3];
      best_period = p - 3;
    }
  }
  autocorrelation = best_autocorrelation;
  period = best_period;
}

ForecastSolver::Metrics
    ForecastSolver::Seasonal::generateForecast  // TODO No outlier detection in
                                                // this method
    (const Forecast* fcst, vector<ForecastBucketData>& bucketdata,
     short firstbckt, vector<double>& timeseries, unsigned int count,
     ForecastSolver* solver) {
  // Check for seasonal cycles
  detectCycle(timeseries, count);

  // Return if no seasonality is found
  if (!period) return ForecastSolver::Metrics(DBL_MAX, DBL_MAX, false);

  // Define variables
  double error = 0.0, error_smape = 0.0, error_smape_weights = 0.0, determinant,
         delta_alfa, delta_beta;
  double forecast_i, d_forecast_d_alfa, d_forecast_d_beta;
  double d_L_d_alfa, d_L_d_beta;
  double d_T_d_alfa, d_T_d_beta;
  double d_S_d_alfa[80], d_S_d_beta[80];
  double d_L_d_alfa_prev, d_L_d_beta_prev;
  double d_T_d_alfa_prev, d_T_d_beta_prev;
  double d_S_d_alfa_prev, d_S_d_beta_prev;
  double sum11, sum12, sum13, sum22, sum23;
  double best_error = DBL_MAX, best_smape = 0, best_alfa = initial_alfa,
         best_beta = initial_beta, best_standarddeviation = 0.0;
  double initial_S_i[80];
  double best_S_i[80];

  // Compute initialization values for the timeseries and seasonal index.
  // L_i = average over first cycle
  // T_i = average delta measured in second cycle
  // S_i[index] = seasonality index, measured over all complete cycles
  double L_i_initial = 0.0;
  double T_i_initial = 0.0;
  for (unsigned short i = 0; i < period; ++i) {
    L_i_initial += timeseries[i];
    T_i_initial += timeseries[i + period] - timeseries[i];
    initial_S_i[i] = 0.0;
  }
  T_i_initial /= period;
  L_i_initial = L_i_initial / period;
  double best_L_i = L_i_initial;
  double best_T_i = T_i_initial;

  unsigned short cyclecount = 0;
  for (unsigned int i = 0; i + period <= count; i += period) {
    ++cyclecount;
    double cyclesum = 0.0;
    for (unsigned short j = 0; j < period; ++j) cyclesum += timeseries[i + j];
    if (cyclesum) {
      for (unsigned short j = 0; j < period; ++j)
        initial_S_i[j] += timeseries[i + j] / cyclesum * period;
    }
  }
  for (unsigned long i = 0; i < period; ++i) initial_S_i[i] /= cyclecount;

  // Iterations
  double L_i_prev;
  unsigned int iteration = 1, boundarytested = 0;
  double cyclesum;
  double standarddeviation = 0.0;
  for (; iteration <= solver->getForecastIterations(); ++iteration) {
    // Initialize variables
    error = error_smape = error_smape_weights = sum11 = sum12 = sum13 = sum22 =
        sum23 = standarddeviation = 0.0;
    d_L_d_alfa = d_L_d_beta = 0.0;
    d_T_d_alfa = d_T_d_beta = 0.0;
    L_i = L_i_initial;
    T_i = T_i_initial;
    cyclesum = 0.0;

    for (unsigned short i = 0; i < period; ++i) {
      S_i[i] = initial_S_i[i];
      d_S_d_alfa[i] = 0.0;
      d_S_d_beta[i] = 0.0;
      if (i) cyclesum += timeseries[i - 1];
    }

    // Calculate the forecast and forecast error.
    // We also compute the sums required for the Marquardt optimization.
    unsigned int prevcycleindex = period - 1;
    cycleindex = 0;
    for (unsigned int i = period; i <= count; ++i) {
      // Base calculations
      L_i_prev = L_i;
      double actual = (i == count) ? 0 : timeseries[i];
      cyclesum += timeseries[i - 1];
      if (i > period) cyclesum -= timeseries[i - period - 1];

      // Textbook approach for Holt-Winters multiplicative method:
      // L_i = alfa * history[i-1] / S_i[prevcycleindex] + (1 - alfa) * (L_i +
      // T_i); FrePPLe uses a variation to compute the constant component. The
      // alternative gives more stable and intuitive results for data that
      // show variability.
      L_i = alfa * cyclesum / period + (1 - alfa) * (L_i + T_i);
      if (L_i < 0) L_i = 0.0;
      T_i = beta * (L_i - L_i_prev) + (1 - beta) * T_i;
      double factor = -S_i[prevcycleindex];
      if (L_i)
        S_i[prevcycleindex] =
            gamma * timeseries[i - 1] / L_i + (1 - gamma) * S_i[prevcycleindex];
      if (S_i[prevcycleindex] < 0.0) S_i[prevcycleindex] = 0.0;

      // Rescale the seasonal indexes to add up to "period"
      factor = period / (period + factor + S_i[prevcycleindex]);
      for (unsigned short i2 = 0; i2 < period; ++i2) S_i[i2] *= factor;

      if (i == count) break;
      // Calculations for the delta of the parameters
      d_L_d_alfa_prev = d_L_d_alfa;
      d_L_d_beta_prev = d_L_d_beta;
      d_T_d_alfa_prev = d_T_d_alfa;
      d_T_d_beta_prev = d_T_d_beta;
      d_S_d_alfa_prev = d_S_d_alfa[prevcycleindex];
      d_S_d_beta_prev = d_S_d_beta[prevcycleindex];
      d_L_d_alfa = cyclesum / period - (L_i + T_i) +
                   (1 - alfa) * (d_L_d_alfa_prev + d_T_d_alfa_prev);
      d_L_d_beta = (1 - alfa) * (d_L_d_beta_prev + d_T_d_beta_prev);

      if (L_i > ROUNDING_ERROR) {
        d_S_d_alfa[prevcycleindex] =
            -gamma * timeseries[i - 1] / L_i / L_i * d_L_d_alfa_prev +
            (1 - gamma) * d_S_d_alfa_prev;
        d_S_d_beta[prevcycleindex] =
            -gamma * timeseries[i - 1] / L_i / L_i * d_L_d_beta_prev +
            (1 - gamma) * d_S_d_beta_prev;
      } else {
        d_S_d_alfa[prevcycleindex] = (1 - gamma) * d_S_d_alfa_prev;
        d_S_d_beta[prevcycleindex] = (1 - gamma) * d_S_d_beta_prev;
      }
      d_T_d_alfa =
          beta * (d_L_d_alfa - d_L_d_alfa_prev) + (1 - beta) * d_T_d_alfa_prev;
      d_T_d_beta = (L_i - L_i_prev) + beta * (d_L_d_beta - d_L_d_beta_prev) -
                   T_i + (1 - beta) * d_T_d_beta_prev;
      d_forecast_d_alfa = (d_L_d_alfa + d_T_d_alfa) * S_i[cycleindex] +
                          (L_i + T_i) * d_S_d_alfa[cycleindex];
      d_forecast_d_beta = (d_L_d_beta + d_T_d_beta) * S_i[cycleindex] +
                          (L_i + T_i) * d_S_d_beta[cycleindex];
      forecast_i = (L_i + T_i) * S_i[cycleindex];
      sum11 += weight[count - i] * d_forecast_d_alfa * d_forecast_d_alfa;
      sum12 += weight[count - i] * d_forecast_d_alfa * d_forecast_d_beta;
      sum22 += weight[count - i] * d_forecast_d_beta * d_forecast_d_beta;
      sum13 += weight[count - i] * d_forecast_d_alfa * (actual - forecast_i);
      sum23 += weight[count - i] * d_forecast_d_beta * (actual - forecast_i);
      if (i >=
          solver->getForecastSkip())  // Don't measure during the warmup period
      {
        double fcst = (L_i + T_i) * S_i[cycleindex];
        error += (fcst - actual) * (fcst - actual) * weight[count - i];
        if (fabs(fcst + actual) > ROUNDING_ERROR) {
          error_smape +=
              fabs(fcst - actual) / fabs(fcst + actual) * weight[count - i];
          error_smape_weights += weight[count - i];
          standarddeviation += (fcst - actual) * (fcst - actual);
        }
      }
      if (++cycleindex >= period) cycleindex = 0;
      if (++prevcycleindex >= period) prevcycleindex = 0;
    }

    // Better than earlier iterations?
    if (error < best_error) {
      best_error = error;
      best_smape =
          error_smape_weights ? error_smape / error_smape_weights : 0.0;
      best_alfa = alfa;
      best_beta = beta;
      best_L_i = L_i;
      best_T_i = T_i;
      best_standarddeviation = sqrt(standarddeviation / (count - period - 1));
      for (unsigned short i = 0; i < period; ++i) best_S_i[i] = S_i[i];
    }

    // Add Levenberg - Marquardt damping factor
    // if (alfa < max_alfa && alfa > min_alfa)
    sum11 += error / iteration;  // * d_forecast_d_alfa;
    // if (beta < max_beta && beta > min_beta)
    sum22 += error / iteration;  // * d_forecast_d_beta;

    // Calculate a delta for the alfa and gamma parameters
    determinant = sum11 * sum22 - sum12 * sum12;
    if (fabs(determinant) < ROUNDING_ERROR) {
      // Almost singular matrix. Try without the damping factor.
      // if (alfa < max_alfa && alfa > min_alfa)
      sum11 -= error / iteration;
      // if (beta < max_beta && beta > min_beta)
      sum22 -= error / iteration;
      determinant = sum11 * sum22 - sum12 * sum12;
      if (fabs(determinant) < ROUNDING_ERROR)
        // Still singular - stop iterations here
        break;
    }
    delta_alfa = (sum13 * sum22 - sum23 * sum12) / determinant;
    delta_beta = (sum23 * sum11 - sum13 * sum12) / determinant;

    // Stop when we are close enough and have tried hard enough
    if ((fabs(delta_alfa) + fabs(delta_beta)) < 3 * ACCURACY && iteration > 3)
      break;

    // Debugging info on the iteration
    if (solver->getLogLevel() > 5)
      logger << (fcst ? fcst->getName() : "") << ": seasonal : iteration "
             << iteration << ": alfa " << alfa << ", beta " << beta
             << ", smape "
             << (error_smape_weights ? error_smape / error_smape_weights : 0.0)
             << endl;

    // New values for the next iteration
    alfa += delta_alfa;
    beta += delta_beta;

    // Limit the parameters in their allowed range.
    if (alfa > max_alfa)
      alfa = max_alfa;
    else if (alfa < min_alfa)
      alfa = min_alfa;
    if (beta > max_beta)
      beta = max_beta;
    else if (beta < min_beta)
      beta = min_beta;

    // Verify repeated running with any parameters at the boundary
    if ((beta == min_beta || beta == max_beta) &&
        (alfa == min_alfa || alfa == max_alfa)) {
      if (boundarytested++ > 5) break;
    }
  }

  if (period > solver->getForecastSkip()) {
    // Correction on the error: we counted less buckets. We now
    // proportionally increase the error to account for this and have a
    // value that can be compared with the other forecast methods.
    best_smape *= (count - solver->getForecastSkip());
    best_smape /= (count - period);
  }

  // Restore best results
  alfa = best_alfa;
  beta = best_beta;
  L_i = best_L_i;
  T_i = best_T_i;

  for (unsigned short i = 0; i < period; ++i) S_i[i] = best_S_i[i];

  // Echo the result
  if (solver->getLogLevel() > 0)
    logger << (fcst ? fcst->getName() : "") << ": seasonal : "
           << "alfa " << best_alfa << ", beta " << best_beta << ", smape "
           << best_smape << ", " << iteration << " iterations"
           << ", period " << period << ", constant " << L_i << ", trend " << T_i
           << ", forecast " << ((L_i + T_i / period) * S_i[count % period])
           << ", standard deviation " << best_standarddeviation
           << ", autocorrelation " << autocorrelation << endl;

  // If the autocorrelation is high enough (ie there is a very obvious
  // seasonal pattern) the third element in the return struct is "true".
  // This enforces the use of the seasonal method.
  return ForecastSolver::Metrics(best_smape, best_standarddeviation,
                                 autocorrelation > max_autocorrelation);
}

void ForecastSolver::Seasonal::applyForecast(
    Forecast* forecast, vector<ForecastBucketData>& bucketdata, short bcktstart,
    CommandManager* mgr) {
  // Loop over all buckets and set the forecast to a linearly changing value
  if (forecast->discrete) {
    double carryover = 0.0;
    for (auto bckt = bucketdata.begin() + bcktstart;
         bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
         ++bckt) {
      L_i += T_i;
      T_i *= dampenTrend;  // Reduce slope in the future
      carryover += L_i * S_i[cycleindex];
      double val = ceil(carryover - 0.5);
      carryover -= val;
      if (++cycleindex >= period) cycleindex = 0;
      Measures::forecastbaseline->disaggregate(*bckt, val > 0.0 ? val : 0.0,
                                               mgr);
    }
  } else
    for (auto bckt = bucketdata.begin() + bcktstart;
         bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
         ++bckt) {
      L_i += T_i;
      T_i *= dampenTrend;  // Reduce slope in the future
      double fcst = L_i * S_i[cycleindex];
      if (++cycleindex >= period) cycleindex = 0;
      Measures::forecastbaseline->disaggregate(*bckt, fcst > 0.0 ? fcst : 0.0,
                                               mgr);
    }

  deleteOutliers(forecast, this);
}

//
// CROSTON'S FORECAST METHOD
//

double ForecastSolver::Croston::initial_alfa = 0.1;
double ForecastSolver::Croston::min_alfa = 0.03;
double ForecastSolver::Croston::max_alfa = 0.8;
double ForecastSolver::Croston::min_intermittence = 0.33;
double ForecastSolver::Croston::decay_rate = 0.1;

ForecastSolver::Metrics ForecastSolver::Croston::generateForecast(
    const Forecast* fcst, vector<ForecastBucketData>& bucketdata,
    short firstbckt, vector<double>& timeseries, unsigned int count,
    ForecastSolver* solver) {
  // Count non-zero buckets
  double nonzero = 0.0;
  double totalsum = 0.0;
  unsigned long lastnonzero = 0;
  for (unsigned long i = 0; i < count; ++i) {
    if (timeseries[i]) {
      ++nonzero;
      totalsum += timeseries[i];
      lastnonzero = i;
    }
  }
  double periods_between_demands = count / nonzero;

  if (!nonzero) {
    // Demand history full of zeroes
    if (solver->getLogLevel() > 0)
      logger << (fcst ? fcst->getName() : "") << ": croston : "
             << "alfa " << min_alfa << ", smape " << 0 << ", " << 0
             << " iterations"
             << ", forecast " << 0 << ", standard deviation " << 0 << endl;
    return ForecastSolver::Metrics(0, 0, false);
  }

  unsigned int iteration = 0;
  double error_smape = 0.0, error_smape_weights = 0.0, best_smape = 0.0;
  double q_i, p_i;
  double best_error = DBL_MAX, best_alfa = min_alfa, best_f_i = 0.0;
  double best_standarddeviation = 0.0;
  unsigned int between_demands = 1;
  alfa = min_alfa;
  double delta = (max_alfa - min_alfa) / (solver->getForecastIterations() - 1);
  for (; iteration < solver->getForecastIterations(); ++iteration) {
    // Loop over the outliers 'scan'/0 and 'filter'/1 modes
    double standarddeviation = 0.0;
    double maxdeviation = 0.0;
    for (short outliers = 0; outliers <= 1; outliers++) {
      // Initialize variables.
      // We initialize to the overall average, since we potentially have
      // very few data points to adjust the forecast.
      // Since the time series only starts at the first non-zero value, we
      // initialize as if there are some extra zero buckets before it.
      error_smape = error_smape_weights = 0.0;
      q_i = totalsum / nonzero;
      p_i = (/* periods_between_demands + */ count) / nonzero;
      f_i = (1 - alfa / 2) * q_i / p_i;

      // Calculate the forecast and forecast error.
      double history_i_min_1 = timeseries[0];
      double history_i = history_i_min_1;
      for (unsigned long i = 1; i <= count; ++i) {
        history_i_min_1 = history_i;
        history_i = timeseries[i];
        if (history_i_min_1) {
          // Non-zero bucket
          q_i = alfa * history_i_min_1 + (1 - alfa) * q_i;
          p_i = alfa * between_demands + (1 - alfa) * p_i;
          f_i = (1 - alfa / 2) * q_i / p_i;
          between_demands = 1;
        } else if (i > lastnonzero &&
                   between_demands > 2 * periods_between_demands) {
          // Too many zeroes since the last hit: decay the forecast with a
          // certain factor every bucket.
          f_i = f_i * (1 - decay_rate);
          p_i = (1 - alfa / 2) * q_i / f_i;
        } else
          // Zero bucket
          ++between_demands;
        if (i == count) break;
        if (outliers == 0) {
          // Scan outliers by computing the standard deviation
          // and keeping track of the difference between actuals and forecast
          standarddeviation += (f_i - history_i) * (f_i - history_i);
          if (fabs(history_i - f_i) > maxdeviation)
            maxdeviation = fabs(f_i - history_i);
        } else {
          // Clean outliers from history. Note that there is no correction to
          // the lower limit for the Croston method (because 0's are normal
          // and accepted).
          if (history_i >
              f_i + ForecastSolver::Forecast_maxDeviation * standarddeviation) {
            history_i =
                f_i + ForecastSolver::Forecast_maxDeviation * standarddeviation;
            if (iteration == 1)
              new ProblemOutlier(
                  bucketdata[i + firstbckt].getOrCreateForecastBucket(), this,
                  true);
          }
        }
        if (i >= solver->getForecastSkip() &&
            p_i > 0)  // Don't measure during the warmup period
        {
          if (fabs(f_i + history_i) > ROUNDING_ERROR) {
            error_smape += fabs(f_i - history_i) / fabs(f_i + history_i) *
                           weight[count - i];
            error_smape_weights += weight[count - i];
          }
        }
      }

      // Check outliers
      if (outliers == 0) {
        standarddeviation = sqrt(standarddeviation / (count - 1));
        maxdeviation /= standarddeviation;
        // Don't repeat if there are no outliers
        if (maxdeviation < ForecastSolver::Forecast_maxDeviation) break;
      }
    }  // End loop: 'scan' or 'filter' mode for outliers

    // Better than earlier iterations?
    // Different than other methods we consider an equal SMAPE to be better.
    // This results in a higher alfa and a lower forecast value. For
    // situations with only 1 demand hit this gives better results, as it
    // compensates somewhat for empty buckets before the first hit and avoids
    // overforecasting.
    if (error_smape <= best_error) {
      best_error = error_smape;
      best_smape =
          error_smape_weights ? error_smape / error_smape_weights : 0.0;
      best_alfa = alfa;
      best_f_i = f_i;
      best_standarddeviation = standarddeviation;
    }

    // Debugging info on the iteration
    if (solver->getLogLevel() > 9)
      logger << (fcst ? fcst->getName() : "") << ": croston: iteration "
             << iteration << ": alfa " << alfa << ", smape "
             << (error_smape_weights ? error_smape / error_smape_weights : 0.0)
             << endl;

    // New alfa
    if (delta)
      alfa += delta;
    else
      break;  // min_alfa == max_alfa, and no loop is required
  }

  // Keep the best result
  f_i = best_f_i;
  alfa = best_alfa;

  // Echo the result
  if (solver->getLogLevel() > 0)
    logger << (fcst ? fcst->getName() : "") << ": croston : "
           << "alfa " << best_alfa << ", smape " << best_smape << ", "
           << iteration << " iterations"
           << ", forecast " << f_i << ", standard deviation "
           << best_standarddeviation << endl;
  return ForecastSolver::Metrics(best_smape, best_standarddeviation, false);
}

void ForecastSolver::Croston::applyForecast(
    Forecast* forecast, vector<ForecastBucketData>& bucketdata, short bcktstart,
    CommandManager* mgr) {
  // Loop over all buckets and set the forecast to a constant value
  if (forecast->discrete) {
    double carryover = 0.0;
    for (auto bckt = bucketdata.begin() + bcktstart;
         bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
         ++bckt) {
      carryover += f_i;
      double val = ceil(carryover - 0.5);
      carryover -= val;
      Measures::forecastbaseline->disaggregate(*bckt, val > 0.0 ? val : 0.0,
                                               mgr);
    }
  } else {
    for (auto bckt = bucketdata.begin() + bcktstart;
         bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
         ++bckt)
      Measures::forecastbaseline->disaggregate(*bckt, f_i > 0.0 ? f_i : 0.0,
                                               mgr);
  }

  deleteOutliers(forecast, this);
}

//
// MANUAL FORECAST METHOD
//

ForecastSolver::Metrics ForecastSolver::Manual::generateForecast(
    const Forecast* fcst, vector<ForecastBucketData>& bucketdata,
    short firstbckt, vector<double>& timeseries, unsigned int count,
    ForecastSolver* solver) {
  // Return dummy metrics.
  return Metrics(0, 0, true);
}

void ForecastSolver::Manual::applyForecast(
    Forecast* forecast, vector<ForecastBucketData>& bucketdata, short bcktstart,
    CommandManager* mgr) {
  // Loop over all buckets and set the forecast to 0
  for (auto bckt = bucketdata.begin() + bcktstart;
       bckt != bucketdata.end() && bckt->getEnd() != Date::infiniteFuture;
       ++bckt)
    Measures::forecastbaseline->disaggregate(*bckt, 0.0, mgr);

  deleteOutliers(forecast, this);
}

void ForecastSolver::deleteOutliers(
    const Forecast* forecast, ForecastSolver::ForecastMethod* appliedMethod) {
  // Delete all outlier problems
  for (auto bckt = forecast->getMembers(); bckt != forecast->end(); ++bckt) {
    if (bckt->hasType<ForecastBucket>() &&
        static_cast<ForecastBucket*>(&*bckt)->getDueRange().getEnd() <=
            Plan::instance().getFcstCurrent()) {
      // Find existing outlier problems
      for (auto j = Problem::begin(&*bckt, false); j != Problem::end();) {
        if (typeid(*j) != typeid(ProblemOutlier)) {
          ++j;
          continue;
        }

        // Need to increment now and define a pointer to the problem, since the
        // problem can be deleted soon (which invalidates the iterator).
        ProblemOutlier& problemOutlier = static_cast<ProblemOutlier&>(*j);
        ++j;
        if (!appliedMethod ||
            appliedMethod != problemOutlier.getForecastMethod())
          delete &problemOutlier;
      }
    }
  }
}

}  // namespace frepple
