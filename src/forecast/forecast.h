/***************************************************************************
 *                                                                         *
 * Copyright (C) 2012 by frePPLe bv                                        *
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

#pragma once
#ifndef FORECAST_H
#define FORECAST_H

#define FREPPLE_CORE

// Configure the expression parser
#define exprtk_disable_comments
#define exprtk_disable_break_continue
#define exprtk_disable_return_statement
#define exprtk_disable_superscalar_unroll
#define exprtk_disable_rtl_io_file
#define exprtk_disable_rtl_vecops
#define exprtk_disable_caseinsensitivity
#include "exprtk.h"

// frepple headers
#include "frepple.h"
#include "frepple/cache.h"
#include "frepple/json.h"
using namespace frepple;

#include <tuple>
#include <unordered_set>

namespace frepple {

// Forward declarations
class ForecastMeasure;
class ForecastMeasureComputed;
class ForecastData;
class ForecastBucketData;
class Forecast;
class ForecastBase;
class ForecastSolver;
class ForecastBucket;
class MeasureValue;
class MeasureList;
class MeasurePool;
class MeasurePagePool;

/* Forecast measures represent data stored in the cube.
 * There are 3 methods that define their business logic:
 *   - disaggregate:
 *     Defines how an update of the value is disaggregated & distributed
 *     over leaf nodes.
 *     It ends by calling the update method for the leaf node.
 *     TODO rename to setValue.
 *   - update:
 *     Should be called only for leaf nodes, and models the relation between
 *     measures.
 *     It ends by calling invValue method on the forecastbucketdata.
 *     TODO merge with the setValue method. Only difference is whether we are
 *          dealing with a leaf or a parent.
 *   - TODO getValue:
 *     Models how get values of this measure.
 */
class ForecastMeasure : public HasName<ForecastMeasure> {
 public:
  ForecastMeasure() {}

  ForecastMeasure(const char* n, double d = 0.0, bool cmptd = false,
                  bool aggr = true, bool temp = false)
      : dflt(d), computed(cmptd), aggregate(aggr), temporary(temp) {
    setName(n);
  }

  ForecastMeasure(const PooledString& n, double d = 0.0, bool cmptd = false,
                  bool aggr = true, bool temp = false)
      : dflt(d), computed(cmptd), aggregate(aggr), temporary(temp) {
    setName(n);
  }

  ForecastMeasure(const string& n, double d = 0.0, bool cmptd = false,
                  bool aggr = true, bool temp = false)
      : dflt(d), computed(cmptd), aggregate(aggr), temporary(temp) {
    setName(n);
  }

  double getDefault() const { return dflt; }

  void setDefault(double v) { dflt = v; }

  void setComputed(bool c) { computed = c; }

  bool isComputed() const { return computed; }

  bool isAggregate() const { return aggregate; }

  bool isTemporary() const { return temporary; }

  bool getDiscrete() const { return discrete; }

  void setDiscrete(bool b) { discrete = b; }

  double getValue(const ForecastBucketData& f) const;

  pair<double, bool> getValueAndFound(const ForecastBucketData& f) const;

  void setName(const string& newname) {
    hashedname = newname;
    HasName<ForecastMeasure>::setName(newname);
  }

  virtual bool isLeaf(const ForecastBase* f) const;

  /* Magic method for distributing an update over all impacted buckets. */
  virtual double disaggregate(ForecastBase* fcst, Date startdate, Date enddate,
                              double val, bool multiply = false,
                              double remainder = 0.0,
                              CommandManager* mgr = nullptr) const = 0;

  /* Magic method for distributing an update over all impacted buckets. */
  virtual double disaggregate(ForecastBucketData& bckt, double val,
                              bool multiple = false, double remainder = 0.0,
                              CommandManager* mgr = nullptr) const = 0;

  /* This is the magic method that defines the relation between the measures of
   * a leaf node.
   * This return value is a quantity that couldn't be updated on this bucket,
   * and it should be carried over to the next bucket or forecast.
   * TODO The logic is currently hardcoded, but we'll need a way to customize
   * this (with or without recompiling c++ code).
   */
  virtual double update(ForecastBucketData&, double,
                        CommandManager* = nullptr) const;

  void computeDependentMeasures(ForecastBucketData&,
                                bool initialize = true) const;

  enum resetmode : short {
    PAST = 1,
    PAST_CURRENT = 2,
    ALL = 4,
    FUTURE_CURRENT = 8,
    FUTURE = 16
  };

  /* Remove the measure from the cube. */
  template <typename... Measures>
  static void resetMeasure(short mode, Measures*...);

  static void aggregateMeasures(const vector<ForecastMeasure*>&);
  static void aggregateMeasures(bool include_planned = true);
  static void computeMeasures(const vector<ForecastMeasure*>&);
  static void computeMeasures();
  static PyObject* updatePlannedForecastPython(PyObject*, PyObject*);
  static PyObject* aggregateMeasuresPython(PyObject*, PyObject*, PyObject*);
  static PyObject* computeMeasuresPython(PyObject*, PyObject*, PyObject*);

  void evalExpression(const string&, ForecastBase* = nullptr,
                      Date = Date::infinitePast, Date = Date::infiniteFuture);

  /* Reset measures.
   * The first argument is an integer with allowed values of:
   * - 1 = PAST: reset periods in the past
   * - 2 = PAST_CURRENT: reset the current and past periods
   * - 4 = ALL: reset all periods
   * - 8 = FUTURE_CURRENT: reset the current and future periods
   * - 16 = FUTURE: reset future periods
   */
  static PyObject* resetMeasuresPython(PyObject*, PyObject*);

  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "",
                              MANDATORY);
    m->addBoolField<Cls>(Tags::discrete, &Cls::getDiscrete, &Cls::setDiscrete);
    m->addDoubleField<Cls>(Tags::deflt, &Cls::getDefault, &Cls::setDefault);
  }

  const PooledString& getHashedName() const { return hashedname; }

 private:
  PooledString hashedname;
  double dflt = 0;
  bool computed = false;
  bool aggregate = true;
  bool temporary = false;
  bool discrete = false;

 public:
  list<const ForecastMeasureComputed*> dependents;
  list<const ForecastMeasureComputed*> alldependents;
  list<const ForecastMeasure*> assignments;
  double expressionvalue = 0.0;
};

inline ostream& operator<<(ostream& os, const ForecastMeasure* o) {
  if (o)
    os << o->getName();
  else
    os << "NULL";
  return os;
}

inline ostream& operator<<(ostream& os, const ForecastMeasure& o) {
  os << o.getName();
  return os;
}

class ForecastMeasureAggregated : public ForecastMeasure {
 public:
  explicit ForecastMeasureAggregated() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();

  ForecastMeasureAggregated(const char* n, double d = 0.0, bool cmptd = false,
                            const ForecastMeasure* o = nullptr)
      : ForecastMeasure(n, d, cmptd, true) {
    initType(metadata);
    if (o) setOverrides(const_cast<ForecastMeasure*>(o));
  }

  ForecastMeasureAggregated(const PooledString& n, double d = 0.0,
                            bool cmptd = false,
                            const ForecastMeasure* o = nullptr)
      : ForecastMeasure(n, d, cmptd, true) {
    initType(metadata);
    if (o) setOverrides(const_cast<ForecastMeasure*>(o));
  }

  double disaggregate(ForecastBase* fcst, Date startdate, Date enddate,
                      double val, bool multiply = false, double remainder = 0.0,
                      CommandManager* mgr = nullptr) const;

  double disaggregate(ForecastBucketData& bckt, double val,
                      bool multiple = false, double remainder = 0.0,
                      CommandManager* mgr = nullptr) const;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, ForecastMeasure>(tag_overrides, &Cls::getOverride,
                                             &Cls::setOverrides);
  }

  ForecastMeasure* getOverrides() const { return override_measure; }

  void setOverrides(ForecastMeasure* v) { override_measure = v; }

 protected:
  static const Keyword tag_overrides;

 private:
  /* Override measures are like aggregate measures but the disaggregation logic
   * is special to respect existing overrides as much as possible:
   *  - If the new value is -1:
   *    Mode 0: Remove the overrides on the children
   *  - Else if there are existing overrides:
   *      - Existing overridden quantities >= new value
   *        or all children have overrides:
   *        Mode 1: scale the existing overrides and set others expliclitly to
   * 0. A corner case is when all existing overrides are 0.
   *      - Existing overrides < new value
   *        Mode 2: Scale non-overriden values to sum up correctly.
   *                Existing overridden values are left untouched.
   *                A corner case is when all non-overriden values are 0.
   *  - Else if existing base is greater than 0:
   *      Mode 3: Scale all existing records proportional to the base.
   *  - Else:
   *      Mode 4: Divide the quantity evenly over all existing leafs.
   */
  double disaggregateOverride(ForecastBase* fcst, Date startdate, Date enddate,
                              double val, bool multiply = false,
                              double remainder = 0.0,
                              CommandManager* mgr = nullptr) const;

  double disaggregateOverride(ForecastBucketData& bckt, double val,
                              bool multiple = false, double remainder = 0.0,
                              CommandManager* mgr = nullptr) const;

  ForecastMeasure* override_measure = nullptr;
};

/* Identical to an aggregated measure, but the lowest level where data is
 * stored are the planned forecasts.
 *
 * TODO there is no protection for setting a value below the planned level.
 */
class ForecastMeasureAggregatedPlanned : public ForecastMeasureAggregated {
 public:
  explicit ForecastMeasureAggregatedPlanned() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();

  ForecastMeasureAggregatedPlanned(const char* n, double d = 0.0,
                                   bool cmptd = false)
      : ForecastMeasureAggregated(n, d, cmptd) {
    initType(metadata);
  }

  ForecastMeasureAggregatedPlanned(const PooledString& n, double d = 0.0,
                                   bool cmptd = false)
      : ForecastMeasureAggregated(n, d, cmptd) {
    initType(metadata);
  }

  virtual bool isLeaf(const ForecastBase* f) const;
};

class ForecastMeasureLocal : public ForecastMeasure {
 public:
  explicit ForecastMeasureLocal() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();

  ForecastMeasureLocal(const char* n, double d = 0.0, bool cmptd = false)
      : ForecastMeasure(n, d, cmptd, false) {
    initType(metadata);
  }

  ForecastMeasureLocal(const PooledString& n, double d = 0.0,
                       bool cmptd = false)
      : ForecastMeasure(n, d, cmptd, false) {
    initType(metadata);
  }

  double disaggregate(ForecastBase* fcst, Date startdate, Date enddate,
                      double val, bool multiply = false, double remainder = 0.0,
                      CommandManager* mgr = nullptr) const;

  double disaggregate(ForecastBucketData& bckt, double val,
                      bool multiple = false, double remainder = 0.0,
                      CommandManager* mgr = nullptr) const;

  virtual bool isLeaf(const ForecastBase* f) const;
};

class ForecastMeasureComputed : public ForecastMeasureAggregated {
  friend ForecastMeasure;

 public:
  explicit ForecastMeasureComputed() { initType(metadata); }

  explicit ForecastMeasureComputed(const char* n, const string& expr,
                                   double d = 0.0)
      : ForecastMeasureAggregated(n, d, true) {
    setComputeExpression(expr);
    initType(metadata);
  }
  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();

  void setComputeExpression(const string& s) {
    setComputed(!s.empty());
    compute_expression_string = s;
  }

  const string& getComputeExpression() const {
    return compute_expression_string;
  }

  void setUpdateExpression(const string& s) { update_expression_string = s; }

  const string& getUpdateExpression() const { return update_expression_string; }

  static PyObject* compileMeasuresPython(PyObject*, PyObject*);

  static void compileMeasures();

  double compute() const { return compute_expression.value(); }

  void update() const {
    if (!update_expression_string.empty()) update_expression.value();
  }

  ForecastMeasure* getOverrides() const {
    return ForecastMeasureAggregated::getOverrides();
  }

  void setOverrides(ForecastMeasure* v) {
    ForecastMeasureAggregated::setOverrides(v);
  }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(tag_compute_expression,
                              &Cls::getComputeExpression,
                              &Cls::setComputeExpression);
    m->addStringRefField<Cls>(tag_update_expression, &Cls::getUpdateExpression,
                              &Cls::setUpdateExpression);
    m->addPointerField<Cls, ForecastMeasure>(tag_overrides, &Cls::getOverrides,
                                             &Cls::setOverrides);
  }

 private:
  void appendDependents(list<const ForecastMeasureComputed*>& l) const;

  exprtk::expression<double> compute_expression;
  string compute_expression_string;
  exprtk::expression<double> update_expression;
  string update_expression_string;

  static double newvalue;
  static const Keyword tag_compute_expression;
  static const Keyword tag_update_expression;

  // Global stuff
  static exprtk::symbol_table<double> symboltable;
  static double cost;
  static ForecastBucket* fcstbckt;
  struct ItemAttribute;
  static ForecastMeasureComputed::ItemAttribute functionItemAttribute;
  struct LocationAttribute;
  static ForecastMeasureComputed::LocationAttribute functionLocationAttribute;
  struct CustomerAttribute;
  static ForecastMeasureComputed::CustomerAttribute functionCustomerAttribute;
};

class ForecastMeasureTemp : public ForecastMeasure {
 public:
  explicit ForecastMeasureTemp() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();

  ForecastMeasureTemp(ForecastMeasure& base)
      : ForecastMeasure(string("temp") + base.getName(), base.getDefault(),
                        false, base.isAggregate(), true) {
    initType(metadata);
  }

  virtual double disaggregate(ForecastBase*, Date, Date, double, bool = false,
                              double = 0.0,
                              CommandManager* mgr = nullptr) const {
    return 0.0;
  }

  virtual double disaggregate(ForecastBucketData&, double, bool = false,
                              double = 0.0, CommandManager* = nullptr) const {
    return 0.0;
  };
};

class Measures {
 public:
  static const ForecastMeasureComputed* forecasttotal;
  static const ForecastMeasureAggregatedPlanned* forecastconsumed;
  static const ForecastMeasureAggregatedPlanned* forecastnet;
  static const ForecastMeasureAggregated* forecastbaseline;
  static const ForecastMeasureAggregated* forecastoverride;
  static const ForecastMeasureAggregated* orderstotal;
  static const ForecastMeasureAggregated* ordersadjustment;
  static const ForecastMeasureAggregated* ordersopen;
  static const ForecastMeasureAggregatedPlanned* ordersplanned;
  static const ForecastMeasureAggregatedPlanned* forecastplanned;
  static const ForecastMeasureLocal* outlier;
  static const ForecastMeasureLocal* nodata;
  static const ForecastMeasureLocal* leaf;
};

class MeasureValue {
  friend class MeasureList;
  friend class MeasurePage;
  friend class MeasurePagePool;

 private:
  PooledString msr;
  double val;
  MeasureValue* prev;
  MeasureValue* next;

  MeasurePagePool& getPagePool() const;

  // Pool must be locked when calling this method
  void addToFree(MeasurePagePool&);
  void addToFree();

 public:
  double getValue() const { return val; }
  void setValue(double v) { val = v; }
  const PooledString& getMeasure() const { return msr; }
};

class MeasureList {
  friend class MeasurePage;

 private:
  MeasureValue* first = nullptr;
  MeasureValue* last = nullptr;

  void check();

 public:
  class iterator {
   private:
    MeasureValue* ptr = nullptr;

   public:
    iterator(MeasureValue* i) : ptr(i) {}

    iterator& operator++() {
      if (ptr) ptr = ptr->next;
      return *this;
    }

    bool operator!=(const iterator& t) const { return ptr != t.ptr; }

    bool operator==(const iterator& t) const { return ptr == t.ptr; }

    MeasureValue* operator*() { return ptr; }
  };

  iterator begin() { return iterator(first); }

  iterator end() { return iterator(nullptr); }

  class const_iterator {
   private:
    MeasureValue* ptr = nullptr;

   public:
    const_iterator(MeasureValue* i) : ptr(i) {}

    const_iterator& operator++() {
      if (ptr) ptr = ptr->next;
      return *this;
    }

    bool operator!=(const const_iterator& t) const { return ptr != t.ptr; }

    bool operator==(const const_iterator& t) const { return ptr == t.ptr; }

    const MeasureValue* operator*() { return ptr; }
  };

  const_iterator begin() const { return const_iterator(first); }

  const_iterator end() const { return const_iterator(nullptr); }

  void insert(const PooledString&, double, bool check = true);
  void erase(const PooledString&);
  void erase(MeasureValue*);
  void sort();

  ~MeasureList() {
    auto p = first;
    while (p) {
      auto tmp = p;
      p = p->next;
      tmp->addToFree();
    }
  }

  MeasureValue* find(const PooledString& k) const {
    for (auto p = first; p; p = p->next)
      if (p->msr == k) return p;
    return nullptr;
  }

  double find(const PooledString& k, double dflt) const {
    for (auto p = first; p; p = p->next)
      if (p->msr == k) return p->val;
    return dflt;
  }

  pair<double, bool> findAndFound(const PooledString& k, double dflt) const {
    for (auto p = first; p; p = p->next)
      if (p->msr == k) return make_pair(p->val, true);
    return make_pair(dflt, false);
  }

  size_t size() const {
    size_t count = 0;
    for (auto p = first; p; p = p->next) ++count;
    return count;
  }
};

class MeasurePage {
  friend class MeasureList;
  friend class MeasurePagePool;

 private:
  static const int DATA_PER_PAGE = 2 * 1024 * 1024 / sizeof(MeasureValue);
  MeasurePage* next;
  MeasurePage* prev;
  MeasureValue data[DATA_PER_PAGE];

  MeasurePage(MeasurePagePool&);

  bool empty() const {
    for (auto& v : data)
      if (v.msr) return false;
    return true;
  }

 public:
  short status() const;
};

class MeasurePagePool {
  friend class MeasureValue;
  friend class MeasurePage;
  friend class MeasureList;

 private:
  MeasurePage* firstpage = nullptr;
  MeasurePage* lastpage = nullptr;
  MeasureValue* firstfree = nullptr;
  MeasureValue* lastfree = nullptr;
  string name;

 public:
  mutex lock;

  static MeasurePagePool measurepages_default;
  static MeasurePagePool measurepages_temp;

  MeasurePagePool(string n) : name(n) {}

  void releaseEmptyPages();
  static void check(const string& = "");

  static PyObject* releaseEmptyPagesPython(PyObject* self, PyObject* args) {
    measurepages_default.releaseEmptyPages();
    measurepages_temp.releaseEmptyPages();
    check("after release");
    return Py_BuildValue("");
  }
};

inline MeasurePagePool& MeasureValue::getPagePool() const {
  return msr.starts_with("temp") ? MeasurePagePool::measurepages_temp
                                 : MeasurePagePool::measurepages_default;
}

class ForecastBucketData {
 public:
  ForecastBucketData(const ForecastBase* f, Date s, Date e, short i, bool d);

  ForecastBucketData(ForecastBucketData&& other)
      : fcstbkt(other.fcstbkt),
        fcst(other.fcst),
        index(other.index),
        dates(other.dates),
        measures(move(other.measures)) {}

  ForecastBucketData(const ForecastBucketData&) = delete;

  const MeasureList& getMeasures() const { return measures; }

  void sortMeasures() const {
    const_cast<ForecastBucketData*>(this)->measures.sort();
  }

  ForecastBucket* getForecastBucket() const { return fcstbkt; }

  ForecastBucket* getOrCreateForecastBucket() const;

  void deleteForecastBucket() const;

  double getForecastPlanned() const;

  double getOrdersPlanned() const;

  string toString(bool add_dates = false, bool sorted = true) const;

  double getValue(const ForecastMeasure& n) const {
    return measures.find(n.getHashedName(), n.getDefault());
  }

  pair<double, bool> getValueAndFound(const ForecastMeasure& n) const {
    return measures.findAndFound(n.getHashedName(), n.getDefault());
  }

  size_t getSize() const;

  void propagateValue(const ForecastMeasure* key, double val);

  template <typename... Args>
  void setValue(bool propagate, CommandManager*, const ForecastMeasure* key,
                double val, Args&&... args);

  template <typename... Args>
  void incValue(bool propagate, CommandManager*, const ForecastMeasure* key,
                double val, Args&&... args);

  template <typename... Args>
  void removeValue(bool propagate, CommandManager*, const ForecastMeasure* key,
                   Args&... args);

  Date getStart() const { return dates.getStart(); }

  Date getEnd() const { return dates.getEnd(); }

  DateRange getDates() const { return dates; }

  const ForecastBase* getForecast() const { return fcst; }

  short getIndex() const { return index; }

  void clearDirty() const {
    const_cast<ForecastBucketData*>(this)->dirty = false;
  }

  void markDirty();

  bool isDirty() const { return dirty; }

 private:
  /* Special case for overrides: if the override is incremented
   * to be 0, it could mean two different things:
   * - Either all overrides have been removed.
   * - Either the sum of all overrides is 0.
   * Only this method can make the difference.
   */
  void validateOverride(const ForecastMeasure*);

  ForecastBucket* fcstbkt = nullptr;
  ForecastBase* fcst;
  DateRange dates;
  short index;
  bool dirty = false;
  MeasureList measures;
};

inline double ForecastMeasure::getValue(const ForecastBucketData& f) const {
  return f.getValue(*this);
}

inline pair<double, bool> ForecastMeasure::getValueAndFound(
    const ForecastBucketData& f) const {
  return f.getValueAndFound(*this);
}

template <>
void ForecastBucketData::setValue(bool propagate, CommandManager* mgr,
                                  const ForecastMeasure* key, const double val);

template <typename... Args>
void ForecastBucketData::setValue(bool propagate, CommandManager* mgr,
                                  const ForecastMeasure* key, double val,
                                  Args&&... args) {
  // Recursive template that finally will call the above specialization
  setValue(propagate, mgr, key, val);
  setValue(propagate, mgr, args...);
}

template <>
void ForecastBucketData::incValue(bool propagate, CommandManager* mgr,
                                  const ForecastMeasure* key, const double val);

template <typename... Args>
void ForecastBucketData::incValue(bool propagate, CommandManager* mgr,
                                  const ForecastMeasure* key, double val,
                                  Args&&... args) {
  // Recursive template that finally will call the above specialization
  incValue(propagate, mgr, key, val);
  incValue(propagate, mgr, args...);
}

template <>
void ForecastBucketData::removeValue(bool propagate, CommandManager* mgr,
                                     const ForecastMeasure* key);

template <typename... Args>
void ForecastBucketData::removeValue(bool propagate, CommandManager* mgr,
                                     const ForecastMeasure* key,
                                     Args&... args) {
  // Recursive template that finally will call the above specialization
  removeValue(propagate, mgr, key);
  removeValue(propagate, mgr, args...);
}

class ForecastData {
 public:
  ForecastData(const ForecastBase*);

  /* Return a json representation of all buckets. */
  string toString() const;

  vector<ForecastBucketData>& getBuckets() { return buckets; }

  void flush();

  void clearDirty() const;

  size_t getSize() const;

  recursive_mutex* getLock() { return &lock; }

  recursive_mutex lock;

 private:
  vector<ForecastBucketData> buckets;
};

class CommandSetForecastData : public Command {
 public:
  CommandSetForecastData(ForecastBucketData*, const ForecastMeasure*, double);

  void commit() {
    if (fcstbucket) {
      fcstbucket = nullptr;
      owner = nullptr;
    }
  }

  virtual void rollback() {
    if (fcstbucket) key->update(*fcstbucket, oldvalue);
    fcstbucket = nullptr;
    owner = nullptr;
  }

  virtual ~CommandSetForecastData() {
    if (fcstbucket) rollback();
  }

  virtual short getType() const { return 8; }

 private:
  // This forecastdata pointer is needed to increase its reference count
  shared_ptr<ForecastData> owner;

  ForecastBucketData* fcstbucket = nullptr;

  const ForecastMeasure* key = nullptr;
  double oldvalue;
};

/** This class represents a forecast value in a time bucket. */
class ForecastBucket : public Demand {
 public:
  static const Keyword tag_forecast;
  static const Keyword tag_weight;
  static const Keyword tag_forecast_total;
  static const Keyword tag_forecast_consumed;
  static const Keyword tag_forecast_baseline;
  static const Keyword tag_forecast_override;
  static const Keyword tag_orders_total;
  static const Keyword tag_orders_adjustment;
  static const Keyword tag_orders_adjustment_1;
  static const Keyword tag_orders_adjustment_2;
  static const Keyword tag_orders_adjustment_3;
  static const Keyword tag_orders_open;
  static const Keyword tag_orders_planned;
  static const Keyword tag_outlier;
  static const Keyword tag_forecast_planned;

  // Forward declaration of inner class
  class bucketiterator;

  /* Constructor. */
  ForecastBucket(Forecast*, const DateRange&, short index);

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static const MetaCategory* metacategory;

  Forecast* getForecast() const;

  void setForecast(Forecast*);

  /* Returns the total, gross forecast. */
  double getForecastTotal() const;

  double getForecastNet() const;

  /* Returns the consumed forecast. */
  double getForecastConsumed() const;

  /* Update the priority of the forecast. */
  void setForecastPriority(int i) { getOwner()->setPriority(i); }

  double getForecastBaseline() const;

  void setForecastBaseline(double);

  virtual void writeProperties(Serializer&) const;

  double getForecastOverride() const;

  void setForecastOverride(double);

  double getOrdersOpen() const;

  double getOrdersTotal() const;

  void setOrdersTotal(double);

  double getOrdersAdjustment() const;

  void setOrdersAdjustment(double);

  double getOrdersAdjustmentMinus1() const;

  void setOrdersAdjustmentMinus1(double v);

  double getOrdersAdjustmentMinus2() const;

  void setOrdersAdjustmentMinus2(double v);

  double getOrdersAdjustmentMinus3() const;

  void setOrdersAdjustmentMinus3(double v);

  /* Returns the planned delivery quantity of sales orders within this
   * bucket. */
  double getOrdersPlanned() const;

  /* Returns the total deliveries for the net forecast.
   *
   * Note that net forecast of previous buckets can be planned in this one
   * bucket. Similary some of the net forecast due in this bucket could be
   * planned in a later bucket.
   * This method returns the planned quantities becoming available within
   * this time bucket, regardless of their original forecast date.
   */
  double getForecastPlanned() const;

  /* Return the start of the due date range for this bucket. */
  Date getStartDate() const { return timebucket.getStart(); }

  /* Update the start of the due date range for this bucket. */
  void setStartDate(Date d) { timebucket.setStart(d); }

  /* Return the end of the due date range for this bucket. */
  Date getEndDate() const { return timebucket.getEnd(); }

  /* Update the end of the due date range for this bucket. */
  void setEndDate(Date d) { timebucket.setEnd(d); }

  /* Return the date range for this bucket. */
  DateRange getDueRange() const { return timebucket; }

  short getBucketIndex() const { return bucketindex; }

  void setBucketIndex(short i) { bucketindex = i; }

  void reduceDeliveries(double, CommandManager* = nullptr);

  /* A flag to mark at which date with a forecasting bucket the forecast
   * is due.
   * Possible values are:
   *  - "start"
   *    Start of the bucket, which is a conservative setting.
   *    This is the default.
   *  - "middle"
   *    Middle of the bucket, rounded towards the nearest start of day.
   *  - "end"
   *    End of the bucket, which is a very relaxed setting.
   */
  static void setDueWithinBucket(const string& v) {
    if (v == DUEATSTART)
      DueWithinBucket = 0;
    else if (v == DUEATMIDDLE)
      DueWithinBucket = 1;
    else if (v == DUEATEND)
      DueWithinBucket = 2;
    else
      logger << "Warning: Invalid value for DueWithinBucket" << endl;
  }

  static const string& getDueWithinBucket() {
    switch (DueWithinBucket) {
      case 0:
        return DUEATSTART;
      case 1:
        return DUEATMIDDLE;
      case 2:
        return DUEATEND;
    }
    throw LogicException("Unreachable code reached");
  }

  static int initialize();

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::name, &Cls::getName, nullptr, "",
                              MANDATORY);
    m->addPointerField<Cls, Demand>(Tags::owner, &Cls::getOwner, nullptr,
                                    DONT_SERIALIZE);
    m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation,
                                       nullptr, DONT_SERIALIZE);
    m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation,
                                      nullptr, PLAN);
    m->addPointerField<Cls, Customer>(Tags::customer, &Cls::getCustomer,
                                      nullptr, PLAN + WRITE_OBJECT_SVC);
    m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity,
                           0, BASE);
    m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, nullptr,
                                  PLAN + WRITE_OBJECT_SVC);
    m->addDateField<Cls>(Tags::due, &Cls::getDue, &Cls::setDue,
                         Date::infinitePast, PLAN);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority,
                        &Cls::setForecastPriority, 0, DONT_SERIALIZE);
    m->addDurationField<Cls>(Tags::maxlateness, &Cls::getMaxLateness, 0,
                             Duration::MAX, DONT_SERIALIZE);
    m->addDoubleField<Cls>(Tags::minshipment, &Cls::getMinShipment, 0, 1,
                           DONT_SERIALIZE);
    m->addDateField<Cls>(Tags::start, &Cls::getStartDate, &Cls::setStartDate,
                         Date::infinitePast, MANDATORY);
    m->addDateField<Cls>(Tags::end, &Cls::getEndDate, &Cls::setEndDate,
                         Date::infiniteFuture, MANDATORY);
    m->addStringField<Cls>(Tags::status, &Cls::getStatusString,
                           &Cls::setStatusString, "open");
    m->addPointerField<Cls, Operation>(Tags::delivery_operation,
                                       &Cls::getDeliveryOperation, nullptr,
                                       DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_forecast_total,
                           &Cls::getForecastTotal, nullptr, 0.0,
                           DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_forecast_consumed,
                           &Cls::getForecastConsumed, nullptr, 0.0,
                           DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_forecast_baseline,
                           &Cls::getForecastBaseline, &Cls::setForecastBaseline,
                           0.0, DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_forecast_override,
                           &Cls::getForecastOverride, &Cls::setForecastOverride,
                           -1.0, DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_orders_total,
                           &Cls::getOrdersTotal, &Cls::setOrdersTotal, 0.0,
                           DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_orders_adjustment,
                           &Cls::getOrdersAdjustment, &Cls::setOrdersAdjustment,
                           0.0, DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_orders_open, &Cls::getOrdersOpen,
                           &Cls::dummySink, 0.0, DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_orders_planned,
                           &Cls::getOrdersPlanned, &Cls::dummySink, 0.0,
                           DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_forecast_planned,
                           &Cls::getForecastPlanned, &Cls::dummySink, 0.0,
                           DONT_SERIALIZE);
    m->addPointerField<Cls, Forecast>(ForecastBucket::tag_forecast,
                                      &Cls::getForecast, &Cls::setForecast,
                                      MANDATORY + PARENT + WRITE_REFERENCE);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    m->addIteratorClassField<Cls, PeggingIterator>(
        Tags::pegging, Tags::pegging, &Cls::getPegging, DETAIL + WRITE_OBJECT);
    m->addIteratorField<Cls, DeliveryIterator, OperationPlan>(
        Tags::operationplans, Tags::operationplan, &Cls::getOperationPlans,
        DETAIL + WRITE_OBJECT);
    m->addIteratorField<Cls, Problem::List::iterator, Problem>(
        Tags::constraints, Tags::problem, &Cls::getConstraintIterator, DETAIL);
    m->addDoubleField<Cls>(ForecastBucket::tag_orders_adjustment_1,
                           &Cls::getOrdersAdjustmentMinus1,
                           &Cls::setOrdersAdjustmentMinus1, 0.0,
                           DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_orders_adjustment_2,
                           &Cls::getOrdersAdjustmentMinus2,
                           &Cls::setOrdersAdjustmentMinus2, 0.0,
                           DONT_SERIALIZE);
    m->addDoubleField<Cls>(ForecastBucket::tag_orders_adjustment_3,
                           &Cls::getOrdersAdjustmentMinus3,
                           &Cls::setOrdersAdjustmentMinus3, 0.0,
                           DONT_SERIALIZE);
    m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, nullptr, 0,
                        DONT_SERIALIZE);
    m->addDurationField<Cls>(Tags::delay, &Cls::getDelay, nullptr, -999L, PLAN);
    m->addDateField<Cls>(Tags::delivery, &Cls::getDeliveryDate, nullptr,
                         Date::infiniteFuture, PLAN);
    m->addDoubleField<Cls>(Tags::planned_quantity, &Cls::getPlannedQuantity,
                           nullptr, -1.0, PLAN);
  }

  short getIndex() const { return bucketindex; }

 private:
  DateRange timebucket;
  short bucketindex = -1;

  // double orders_open; computed
  // double orders_open_value; computed

  static PyObject* setMeasurePython(PyObject*, PyObject*, PyObject*);
  static PyObject* getMeasurePython(PyObject*, PyObject*, PyObject*);

  /* Note this is a static field, and all forecastbuckets thus automatically
   * use the same value.
   */
  static short DueWithinBucket;
  static const string DUEATSTART;
  static const string DUEATMIDDLE;
  static const string DUEATEND;

  /* Reader function to create the forecastbucket objects.
   * This method is quite different from the other reader functions, since
   * it doesn't directly find or create an object. Instead it calls
   * special methods on the forecast model to manipulate the forecast
   * buckets.
   */
  static Object* reader(const MetaClass*, const DataValueDict&,
                        CommandManager* = nullptr);

  /* Reader function to create the forecastbucket objects.
   * This method is quite different from the other create functions, since
   * it doesn't directly create the object. Instead it calls the instantiate
   * methods on the forecast model to generate the buckets, and then finds
   * the one with the correct dates.
   */
  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

  /* This method doesn't do anything.
   * It is used as a dummy handler when some read-only fields are updated.
   */
  void dummySink(double d) {}
};

class ForecastBase {
 private:
  struct Comparator {
   public:
    bool operator()(ForecastBase* a, ForecastBase* b) const;
  };

  typedef set<ForecastBase*, Comparator> HashTable;

  static HashTable table;

  /* Define the time horizon for which to create calendar buckets.
   * Both parameters are expressed as a number of days.
   */
  static long horizon_future;
  static long horizon_history;
  static long forecast_partition;

  typedef CacheEntry<ForecastData, ForecastBase> CachedForecastData;

  /* Cached data measures. */
  CachedForecastData data;

 protected:
  static void insertInHash(ForecastBase* f);

  static void eraseFromHash(ForecastBase* f);

 public:
  static ForecastBase* findForecast(Item*, Customer*, Location*, bool = false);

  static HashTable& getForecasts() { return table; }

  virtual bool isAggregate() const { return true; }

  virtual bool isLeaf() const { return false; }

  virtual bool getDiscrete() const { return false; }

  virtual bool getPlanned() const { return false; }

  virtual unsigned long getMethods() const { return 0; }

  virtual const string& getForecastName() const {
    return PooledString::nullstring;
  }

  virtual Item* getForecastItem() const = 0;

  virtual Location* getForecastLocation() const = 0;

  virtual Customer* getForecastCustomer() const = 0;

  inline shared_ptr<ForecastData> getData() const;

  void markDirty() const { const_cast<ForecastBase*>(this)->data.markDirty(); }

  int getHorizonFuture() const {
    return horizon_future;  // This is a static variable!
  }

  static int getHorizonFutureStatic() { return horizon_future; }

  void setHorizonFuture(int i) {
    horizon_future = i;  // This is a static variable!
  }

  int getHorizonHistory() const {
    return horizon_history;  // This is a static variable!
  }

  static int getHorizonHistoryStatic() { return horizon_history; }

  void setHorizonHistory(int i) {
    horizon_history = i;  // This is a static variable!
  }

  int getForecastPartition() const {
    return forecast_partition;  // This is a static variable!
  }

  static int getForecastPartitionStatic() { return forecast_partition; }

  void setForecastPartition(int i) {
    forecast_partition = i;  // This is a static variable!
  }

  /** Debugging function. */
  void inspect(const string& = "") const;

  /* Update the forecast quantity.
   * The forecast quantity will be distributed equally among the buckets
   * available between the two dates, taking into account also the bucket
   * weights.
   * The logic applied is briefly summarized as follows:
   *  - If the daterange has its start and end dates equal, we find the
   *    matching forecast bucket and update the quantity.
   *  - Otherwise the quantity is distributed among all intersecting
   *    forecast buckets. This distribution is considering the weigth of
   *    the bucket and the time duration of the bucket.
   *    The bucket weight is the value specified on the calendar.
   *    If a forecast bucket only partially overlaps with the daterange
   *    only the overlapping time is used as the duration.
   *  - If only buckets with zero weight are found in the daterange a
   *    dataexception is thrown. It indicates a situation where forecast
   *    is specified for a date where no values are allowed.
   * The last argument specifies whether we overwrite the current value
   * or whether we add to it.
   */
  void setFields(DateRange&, const DataValueDict&, CommandManager* = nullptr,
                 bool = false);

  /* An iterator to walk over the forecasts of a certain item. */
  class ItemIterator {
   public:
    ItemIterator(Item* it = nullptr);

    ForecastBase* operator*() const { return forecast; }

    ForecastBase* operator->() const { return forecast; }

    operator bool() const { return iter != ub; }

    ItemIterator& operator++() {
      ++iter;
      forecast = (iter != ub) ? *iter : nullptr;
      return *this;
    }

   private:
    HashTable::iterator iter;
    HashTable::iterator ub;
    ForecastBase* forecast = nullptr;
  };

  /* An iterator to walk over all parent forecasts, across all levels. */
  class ParentIterator {
   private:
    /* Define the time horizon for which to create calendar buckets.
     * Both parameters are expressed as a number of days.
     */
    static long horizon_future;
    static long horizon_history;
    static long forecast_partition;

    /* Cached data measures. */
    CachedForecastData data;

   public:
    ParentIterator(const ForecastBase* fcst = nullptr)
        : rootforecast(const_cast<ForecastBase*>(fcst)) {
      if (fcst) {
        item = fcst->getForecastItem();
        location = fcst->getForecastLocation();
        customer = fcst->getForecastCustomer();
      }
      increment();
    }

    ForecastBase* operator*() const { return forecast; }

    ForecastBase* operator->() const { return forecast; }

    operator bool() const { return forecast != nullptr; }

    ParentIterator& operator++() {
      increment();
      return *this;
    }

    /* Post-increment operator which moves the pointer to the next member. */
    ParentIterator operator++(int) {
      ParentIterator tmp = *this;
      increment();
      return tmp;
    }

   private:
    Item* item = nullptr;
    Location* location = nullptr;
    Customer* customer = nullptr;
    ForecastBase* forecast = nullptr;
    ForecastBase* rootforecast = nullptr;

    void increment();
  };

  ParentIterator getParents() const { return this; }

  /* An iterator to walk over the leave forecast, across all levels.
   * The argument determines whether the starting node is also included
   * if it's a leaf.
   */
  class LeafIterator {
   public:
    LeafIterator(const ForecastBase* fcst, bool inclus,
                 const ForecastMeasure* m = nullptr)
        : item(fcst ? fcst->getForecastItem() : nullptr),
          inclusive(inclus),
          itmfcst(fcst ? fcst->getForecastItem() : nullptr),
          measure(m),
          rootforecast(fcst) {
      increment(true);
    }

    LeafIterator() {}

    ForecastBase* operator*() const { return *itmfcst; }

    ForecastBase* operator->() const { return *itmfcst; }

    operator bool() const { return itmfcst; }

    LeafIterator& operator++() {
      increment(false);
      return *this;
    }

   private:
    Item::memberRecursiveIterator item;
    bool inclusive = true;
    ItemIterator itmfcst;
    const ForecastMeasure* measure = nullptr;
    const ForecastBase* rootforecast = nullptr;
    void increment(bool);
  };

  LeafIterator getLeaves(bool inclusive,
                         const ForecastMeasure* m = nullptr) const {
    return LeafIterator(this, inclusive, m);
  }
};

/* This class represents a bucketized demand signal.
 *
 * The forecast object defines the item and priority of the demands.
 * A calendar (of type void, double, integer or boolean) divides the time
 * horizon in individual time buckets. The calendar value is used to assign
 * priorities to the time buckets. The class basically works as an interface
 * for a hierarchy of demands, where the lower level demands represent
 * forecasting time buckets.
 */
class Forecast : public Demand, public ForecastBase {
  friend class ForecastSolver;

 public:
  static const Keyword tag_methods;
  static const Keyword tag_method;
  static const Keyword tag_planned;
  static const Keyword tag_smape_error;
  static const Keyword tag_deviation;
  static const Keyword tag_horizon_future;
  static const Keyword tag_horizon_history;
  static const Keyword tag_forecast_partition;

 public:
  /* Constants for each forecast method. */
  static const unsigned long METHOD_CONSTANT = 1;
  static const unsigned long METHOD_TREND = 2;
  static const unsigned long METHOD_SEASONAL = 4;
  static const unsigned long METHOD_CROSTON = 8;
  static const unsigned long METHOD_MOVINGAVERAGE = 16;
  static const unsigned long METHOD_MANUAL = 32;
  static const unsigned long METHOD_ALL = 31;

  virtual bool isAggregate() const { return false; }

  virtual Item* getForecastItem() const { return getItem(); }

  virtual Location* getForecastLocation() const { return getLocation(); }

  virtual Customer* getForecastCustomer() const { return getCustomer(); }

  virtual const string& getForecastName() const { return getName(); }

  static void parse(Object* o, const DataValueDict& in, CommandManager* cmdmgr);

  /* Default constructor. */
  explicit Forecast() { initType(metadata); }

  /* Destructor. */
  ~Forecast();

  /* Updates the quantity of the forecast. This method is empty. */
  virtual void setQuantity(double f) {
    throw DataException("Can't set quantity of a forecast");
  }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    // Regiser a special parsing not
    const_cast<MetaCategory*>(Plan::metacategory)
        ->addFunctionField<Plan>(ForecastBucket::tag_forecast, &parse,
                                 DONT_SERIALIZE);

    // Re-registering the Location, Item and Customer fields to make sure the
    // overriden set-method is getting called.
    m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation,
                                      &Cls::setLocation, DONT_SERIALIZE);
    m->addPointerField<Cls, Item>(Tags::location, &Cls::getItem, &Cls::setItem,
                                  DONT_SERIALIZE);
    m->addPointerField<Cls, Customer>(Tags::customer, &Cls::getCustomer,
                                      &Cls::setCustomer, DONT_SERIALIZE);
    m->addPointerField<Cls, Calendar>(Tags::calendar, &Cls::getCalendar,
                                      &Cls::setCalendar);
    m->addBoolField<Cls>(Tags::discrete, &Cls::getDiscrete, &Cls::setDiscrete,
                         BOOL_TRUE);
    m->addBoolField<Cls>(Tags::planned, &Cls::getPlanned, &Cls::setPlanned,
                         BOOL_TRUE);
    m->addStringField<Cls>(Tags::status, &Cls::getStatusString,
                           &Cls::setStatusString, "open");
    // m->addUnsignedLongField<Cls>(tag_methods, &Cls::getMethods,
    // &Cls::setMethods, METHOD_ALL);
    m->addStringField<Cls>(tag_methods, &Cls::getMethodsString,
                           &Cls::setMethodsString, "automatic");
    m->addStringRefField<Cls>(tag_method, &Cls::getMethod, nullptr, "",
                              DONT_SERIALIZE);
    m->addDoubleField<Cls>(tag_deviation, &Cls::getDeviation,
                           &Cls::setDeviation, 0.0, DONT_SERIALIZE);
    m->addDoubleField<Cls>(tag_smape_error, &Cls::getSMAPEerror, nullptr, 0.0,
                           DONT_SERIALIZE);
    m->addIntField<Cls>(Forecast::tag_horizon_future, &Cls::getHorizonFuture,
                        &Cls::setHorizonFuture, 365 * 3, DONT_SERIALIZE);
    m->addIntField<Cls>(Forecast::tag_horizon_history, &Cls::getHorizonHistory,
                        &Cls::setHorizonHistory, 365 * 10, DONT_SERIALIZE);
    m->addIntField<Cls>(Forecast::tag_forecast_partition,
                        &Cls::getForecastPartition, &Cls::setForecastPartition,
                        -1, DONT_SERIALIZE);
    m->addIteratorField<Cls, ForecastBucket::bucketiterator, ForecastBucket>(
        Tags::buckets, Tags::bucket, &Cls::getBuckets,
        BASE + WRITE_OBJECT + WRITE_HIDDEN);
    m->addDoubleField<Cls>(Tags::minshipment, &Cls::getMinShipment,
                           &Cls::setMinShipment, 0, DONT_SERIALIZE);
  }

  static int initialize();

  /* Returns which statistical forecast methods are allowed.
   * The following bit values can be added to enable forecasting methods:
   *   - 1: Constant forecast, single exponential
   *   - 2: Trending forecast, double exponential
   *   - 4: Seasonal forecast, holt-winter's multiplicative
   *   - 8: Intermittent demand, croston
   *   - 16: Moving average
   *   - 32: Manual
   * If no flag is set (ie value is 0), then no statistical forecast will be
   * computed at all.
   * If multiple flags are set, the algorithm automatically selects the
   * forecast method which returns the lowest forecast error.
   * The default value is 31, which enables all forecast methods.
   */
  unsigned long getMethods() const { return methods; }

  /* Updates computed flag. */
  void setMethods(unsigned long b) {
    methods = b & (METHOD_ALL + METHOD_MANUAL);
  }

  /* Update the list of allowed forecast methods from input string.
   * The input string can have multiple values separated by one of the
   * following delimiters:
   *     ! " # % & ' ( ) ; < = > ? [ \ ] * + , - . / : ^ _ { | } ~
   */
  void setMethodsString(const string&);

  /* Returns the list of allowed forecast methods as a string. */
  string getMethodsString() const;

  /* Return the forecast method applied to compute the forecast. */
  const string& getMethod() const {
    static string constant("constant");
    static string trend("trend");
    static string seasonal("seasonal");
    static string intermittent("intermittent");
    static string movingaverage("moving average");
    static string manual("manual");
    static string none("none");
    if (method == METHOD_CONSTANT)
      return constant;
    else if (method == METHOD_TREND)
      return trend;
    else if (method == METHOD_SEASONAL)
      return seasonal;
    else if (method == METHOD_CROSTON)
      return intermittent;
    else if (method == METHOD_MOVINGAVERAGE)
      return movingaverage;
    else if (method == METHOD_MANUAL)
      return manual;
    else if (method == 0)
      return none;
    else {
      logger << "method" << method << endl;
      throw LogicException("Unknown forecast method");
    }
  }

  /* Store the selected forecast method. This method is not exposed publicly. */
  void setMethod(unsigned int n) { method = n; }

  /* Returns whether forecast instance is a leaf node. */
  bool isLeaf() const;

  /* Normally, we compute what is a leaf and what's not.
   * In some cases we already know in advance and can set it explicitly already.
   */
  void setLeaf(bool b) { leaf = b ? 1 : 0; }

  /** Returns whether fractional forecasts are allowed or not.<br>
   * The default is true.
   */
  virtual bool getDiscrete() const { return discrete; }

  /* Updates forecast discreteness flag. */
  void setDiscrete(const bool b) { discrete = b; }

  /* Returns whether This forecast should be planned.
   * The default is true.
   * This field should be set correctly before any calculations are done.
   */
  bool getPlanned() const { return planned; }

  /* Updates forecast planned flag. */
  void setPlanned(const bool b);

  /* Update the item to be planned. */
  virtual void setItem(Item*);

  /* Update the location to be planned. */
  virtual void setLocation(Location*);

  /* Update the customer. */
  virtual void setCustomer(Customer*);

  /* Update the maximum allowed lateness for planning. */
  void setMaxLateness(Duration);

  /* Update the minumum allowed shipment quantity for planning. */
  void setMinShipment(double);

  /* Specify a bucket calendar for the forecast. Once forecasted
   * quantities have been entered for the forecast, the calendar
   * can't be updated any more. */
  static void setCalendar_static(Calendar* c) {
    if (calptr && c != calptr)
      logger << "Warning: Forecasting buckets can't be changed once specified"
             << endl;
    else
      calptr = c;
  }

  void setCalendar(Calendar* c) {
    if (calptr && c != calptr)
      logger << "Warning: Forecasting buckets can't be changed once specified"
             << endl;
    else
      calptr = c;
  }

  /* Returns a reference to the calendar used for this forecast.
   * This is a static method: all forecast use the exact same
   * forecasting buckets.
   */
  static Calendar* getCalendar_static() { return calptr; }

  Calendar* getCalendar() const { return calptr; }

  /* Updates the due date of the demand. Lower numbers indicate a
   * higher priority level. The method also updates the priority
   * in all buckets.
   */
  virtual void setPriority(int);

  /* Updates the due date of the demand. */
  virtual void setDue(const Date& d) {
    throw DataException("Can't set due date of a forecast");
  }

  double getDeviation() const { return deviation; }

  void setDeviation(double e) { deviation = e; }

  double getSMAPEerror() const { return smape_error; }

  void setSMAPEerror(double e) { smape_error = e; }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  /* Return the memory size. */
  size_t getSize() const {
    return Demand::getSize() +
           sizeof(Forecast*) * 3;  // overhead of forecast tree
  }

  /* Iterator over all forecasting buckets. */
  ForecastBucket::bucketiterator getBuckets() const;

  /* Callback function, used for prevent a calendar from being deleted when it
   * is used for an uninitialized forecast. */
  static bool callback(Calendar*, const Signal);

 private:
  static PyObject* inspectPython(PyObject*, PyObject*);
  static PyObject* setValuePython(PyObject*, PyObject*, PyObject*);
  static PyObject* setValuePython2(PyObject*, PyObject*, PyObject*);
  static PyObject* getValuePython(PyObject*, PyObject*, PyObject*);
  static PyObject* saveForecast(PyObject*, PyObject*);

  /* A calendar to define the time buckets. */
  static Calendar* calptr;

  /* Flags whether this forecast instance is associated to a leaf node.
   *  -1 : unititialized value
   *  0 : non-leaf forecast
   *  1 : leaf forecast
   */
  short leaf = -1;

  /* Flags whether fractional forecasts are allowed. */
  bool discrete = true;

  /* Flags whether this forecast should be planned. */
  bool planned = true;

  /* Allowed forecasting methods. */
  unsigned int methods = METHOD_ALL;

  /* Applied forecast method. */
  unsigned int method = 0;

  /* SMAPE forecast error. */
  double smape_error = 0.0;

  /* Demand standard deviation. */
  double deviation = 0.0;
};

class ForecastKey : public ForecastBase {
 public:
  ForecastKey(Item* i = nullptr, Location* l = nullptr, Customer* c = nullptr)
      : it(i), loc(l), cust(c) {}

  Item* getForecastItem() const { return it; }

  Location* getForecastLocation() const { return loc; }

  Customer* getForecastCustomer() const { return cust; }

 private:
  Item* it = nullptr;
  Location* loc = nullptr;
  Customer* cust = nullptr;
};

class ForecastAggregated : public ForecastBase, public Object {
 private:
  Item* it = nullptr;
  Location* loc = nullptr;
  Customer* cust = nullptr;

 public:
  ForecastAggregated(Item* i, Location* l = nullptr, Customer* c = nullptr)
      : it(i), loc(l), cust(c) {
    insertInHash(this);
    if (c) c->incNumberOfDemands();
  }

  Item* getForecastItem() const { return it; }

  Location* getForecastLocation() const { return loc; }

  Customer* getForecastCustomer() const { return cust; }
};

inline Forecast* ForecastBucket::getForecast() const {
  return static_cast<Forecast*>(getOwner());
}

inline void ForecastBase::insertInHash(ForecastBase* f) { table.insert(f); }

inline void ForecastBase::eraseFromHash(ForecastBase* f) { table.erase(f); }

inline void ForecastBucket::setForecast(Forecast* f) { setOwner(f); }

class ForecastBucket::bucketiterator {
 private:
  Demand::memberIterator iter;

 public:
  // Constructor
  bucketiterator(const Forecast* f) : iter(f) {}

  // Return current value and advance the iterator
  ForecastBucket* next() { return static_cast<ForecastBucket*>(iter.next()); }
};

inline ForecastBucket::bucketiterator Forecast::getBuckets() const {
  auto fcstdata = getData();
  lock_guard<recursive_mutex> exclusive(fcstdata->lock);
  for (auto& b : fcstdata->getBuckets()) b.getOrCreateForecastBucket();
  sortMembers();
  return ForecastBucket::bucketiterator(this);
}

inline ostream& operator<<(ostream& os, const ForecastBucketData& o) {
  os << o.getForecast()->getForecastItem() << " @ "
     << o.getForecast()->getForecastLocation() << " @ "
     << o.getForecast()->getForecastCustomer() << " : " << o.toString(true);
  return os;
}

/* Implementation of a forecast netting algorithm, and a proxy
 * for any configuration setting on the forecasting module.
 *
 * As customer orders are being received they need to be deducted from
 * the forecast to avoid double-counting demand.
 *
 * The netting solver will process each order as follows:
 * - <b>First search for a matching forecast.</b>
 *   A matching forecast has the same item and customer as the order.
 *   If no match is found at this level, a match is tried at higher levels
 *   of the customer and item.
 *   Ultimately a match is tried with a empty customer or item field.
 * - <b>Next, the remaining net quantity of the forecast is decreased.</b>
 *   The forecast bucket to be reduced is the one where the order is due.
 *   If the net quantity is already completely depleted in that bucket
 *   the solver will look in earlier and later buckets. The parameters
 *   Net_Early and Net_Late control the limits for the search in the
 *   time dimension.
 *
 * The logging levels have the following meaning:
 * - 0: Silent operation. Default logging level.
 * - 1: Log demands being netted and the matching forecast.
 * - 2: Same as 1, plus details on forecast buckets being netted.
 */
class ForecastSolver : public Solver {
  friend class Forecast;

 public:
  /* An auxiliary method to return metrics from a forecast methods. */
  struct Metrics {
    double smape;
    double standarddeviation;
    bool force;

    Metrics(double a, double b, bool c)
        : smape(a), standarddeviation(b), force(c) {};
  };

  /* Abstract base class for all forecasting methods. */
  class ForecastMethod {
   public:
    /* Forecast evaluation. */
    virtual Metrics generateForecast(const Forecast*,
                                     vector<ForecastBucketData>&, short,
                                     vector<double>&, unsigned int,
                                     ForecastSolver*) = 0;

    /* This method is called when this forecast method has generated the
     * lowest forecast error and now needs to set the forecast values.
     */
    virtual void applyForecast(Forecast*, vector<ForecastBucketData>&, short,
                               CommandManager*) = 0;

    virtual unsigned int getCode() = 0;
  };

  /* A class to calculate a forecast based on a moving average. */
  class MovingAverage : public ForecastMethod {
   private:
    /* Default number of averaged buckets.
     * The default is 5.
     */
    static unsigned int defaultorder;

    /* Number of buckets to average. */
    unsigned int order;

    /* Calculated average.
     * Used to carry results between the evaluation and applying of the
     * forecast.
     */
    double avg;

   public:
    /* Constructor. */
    MovingAverage(int i = defaultorder) : order(i), avg(0) {
      if (i < 1) {
        logger
            << "Warning: Moving average needs to smooth over at least 1 bucket"
            << endl;
        i = 1;
      }
    }

    /* Forecast evaluation. */
    Metrics generateForecast(const Forecast*, vector<ForecastBucketData>&,
                             short, vector<double>&, unsigned int,
                             ForecastSolver*);

    /* Forecast value updating. */
    void applyForecast(Forecast*, vector<ForecastBucketData>&, short,
                       CommandManager*);

    /* Update the initial value for the alfa parameter. */
    static void setDefaultOrder(int x) {
      if (x < 1)
        logger
            << "Warning: Parameter MovingAverage.order needs to be at least 1"
            << endl;
      else
        defaultorder = x;
    }

    static int getDefaultOrder() { return defaultorder; }

    unsigned int getCode() { return Forecast::METHOD_MOVINGAVERAGE; }
  };

  /* A class to perform single exponential smoothing on a time series.
   */
  class SingleExponential : public ForecastMethod {
   private:
    /* Smoothing constant. */
    double alfa;

    /* Default initial alfa value.
     * The default value is 0.2.
     */
    static double initial_alfa;

    /* Lower limit on the alfa parameter.
     * The default value is 0.
     **/
    static double min_alfa;

    /* Upper limit on the alfa parameter.
     * The default value is 1.
     **/
    static double max_alfa;

    /* Smoothed result.
     * Used to carry results between the evaluation and applying of the
     * forecast.
     */
    double f_i;

   public:
    /* Constructor. */
    SingleExponential(double a = initial_alfa) : alfa(a), f_i(0) {
      if (alfa < min_alfa) alfa = min_alfa;
      if (alfa > max_alfa) alfa = max_alfa;
    }

    /* Forecast evaluation. */
    Metrics generateForecast(const Forecast*, vector<ForecastBucketData>&,
                             short, vector<double>&, unsigned int,
                             ForecastSolver*);

    /* Forecast value updating. */
    void applyForecast(Forecast*, vector<ForecastBucketData>&, short,
                       CommandManager*);

    /* Update the initial value for the alfa parameter. */
    static void setInitialAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter SingleExponential.initialAlfa must be "
                  "between 0 and 1"
               << endl;
      else
        initial_alfa = x;
    }

    static double getInitialAlfa() { return initial_alfa; }

    /* Update the minimum value for the alfa parameter. */
    static void setMinAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter SingleExponential.minAlfa must be "
                  "between 0 and 1"
               << endl;
      else
        min_alfa = x;
    }

    static double getMinAlfa() { return min_alfa; }

    /* Update the maximum value for the alfa parameter. */
    static void setMaxAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter SingleExponential.maxAlfa must be "
                  "between 0 and 1"
               << endl;
      else
        max_alfa = x;
    }

    static double getMaxAlfa() { return max_alfa; }

    unsigned int getCode() { return Forecast::METHOD_CONSTANT; }
  };

  /* A class to perform double exponential smoothing on a time
   * series.
   */
  class DoubleExponential : public ForecastMethod {
   private:
    /* Smoothing constant. */
    double alfa;

    /* Default initial alfa value.
     * The default value is 0.2.
     */
    static double initial_alfa;

    /* Lower limit on the alfa parameter.
     * The default value is 0.
     **/
    static double min_alfa;

    /* Upper limit on the alfa parameter.
     * The default value is 1.
     **/
    static double max_alfa;

    /* Trend smoothing constant. */
    double gamma;

    /* Default initial gamma value.
     * The default value is 0.05.
     */
    static double initial_gamma;

    /* Lower limit on the gamma parameter.
     * The default value is 0.05.
     **/
    static double min_gamma;

    /* Upper limit on the gamma parameter.
     * The default value is 1.
     **/
    static double max_gamma;

    /* Smoothed result.
     * Used to carry results between the evaluation and applying of the
     * forecast.
     */
    double trend_i;

    /* Smoothed result.
     * Used to carry results between the evaluation and applying of the
     * forecast.
     */
    double constant_i;

    /* Factor used to smoothen the trend in the future buckets.
     * The default value is 0.8.
     */
    static double dampenTrend;

   public:
    /* Constructor. */
    DoubleExponential(double a = initial_alfa, double g = initial_gamma)
        : alfa(a), gamma(g), trend_i(0), constant_i(0) {}

    /* Forecast evaluation. */
    Metrics generateForecast(const Forecast*, vector<ForecastBucketData>&,
                             short, vector<double>&, unsigned int,
                             ForecastSolver*);

    /* Forecast value updating. */
    void applyForecast(Forecast*, vector<ForecastBucketData>&, short,
                       CommandManager*);

    /* Update the initial value for the alfa parameter. */
    static void setInitialAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter DoubleExponential.initialAlfa must be "
                  "between 0 and 1"
               << endl;
      else
        initial_alfa = x;
    }

    static double getInitialAlfa() { return initial_alfa; }

    /* Update the minimum value for the alfa parameter. */
    static void setMinAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter DoubleExponential.minAlfa must be "
                  "between 0 and 1"
               << endl;
      else
        min_alfa = x;
    }

    static double getMinAlfa() { return min_alfa; }

    /* Update the maximum value for the alfa parameter. */
    static void setMaxAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter DoubleExponential.maxAlfa must be "
                  "between 0 and 1"
               << endl;
      else
        max_alfa = x;
    }

    static double getMaxAlfa() { return max_alfa; }

    /* Update the initial value for the alfa parameter.
     * The default value is 0.05.
     * Setting this parameter to too low a value can create false
     * positives: the double exponential method is selected for a time
     * series without a real trend. A single exponential is better for
     * such cases.
     */
    static void setInitialGamma(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter DoubleExponential.initialGamma must be "
                  "between 0 and 1"
               << endl;
      else
        initial_gamma = x;
    }

    static double getInitialGamma() { return initial_gamma; }

    /* Update the minimum value for the alfa parameter. */
    static void setMinGamma(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter DoubleExponential.minGamma must be "
                  "between 0 and 1"
               << endl;
      else
        min_gamma = x;
    }

    static double getMinGamma() { return min_gamma; }

    /* Update the maximum value for the alfa parameter. */
    static void setMaxGamma(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter DoubleExponential.maxGamma must be "
                  "between 0 and 1"
               << endl;
      else
        max_gamma = x;
    }

    static double getMaxGamma() { return max_gamma; }

    /* Update the dampening factor for the trend. */
    static void setDampenTrend(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter DoubleExponential.dampenTrend must be "
                  "between 0 and 1"
               << endl;
      else
        dampenTrend = x;
    }

    static double getDampenTrend() { return dampenTrend; }

    unsigned int getCode() { return Forecast::METHOD_TREND; }
  };

  /* A class to perform seasonal forecasting on a time
   * series.
   */
  class Seasonal : public ForecastMethod {
   private:
    /* Smoothing constant. */
    double alfa;

    /* Trend smoothing constant. */
    double beta;

    /* Seasonality smoothing constant.
     * The default value is 0.05.
     */
    static double gamma;

    /* Default initial alfa value.
     * The default value is 0.2.
     */
    static double initial_alfa;

    /* Lower limit on the alfa parameter.
     * The default value is 0.
     **/
    static double min_alfa;

    /* Upper limit on the alfa parameter.
     * The default value is 1.
     **/
    static double max_alfa;

    /* Default initial beta value.
     * The default value is 0.05.
     */
    static double initial_beta;

    /* Lower limit on the beta parameter.
     * The default value is 0.05.
     **/
    static double min_beta;

    /* Upper limit on the beta parameter.
     * The default value is 1.
     **/
    static double max_beta;

    /* Used to dampen a trend in the future. */
    static double dampenTrend;

    /* Minimum cycle to be check for.
     * The interval of cycles we try to detect should be broad enough.
     * If eg we normally expect a yearly cycle use a minimum cycle of 10.
     */
    static unsigned int min_period;

    /* Maximum cycle to be check for.
     * The interval of cycles we try to detect should be broad enough.
     * If eg we normally expect a yearly cycle use a maximum cycle of 14.
     */
    static unsigned int max_period;

    /* Minimum required autocorrelation factor below which a seasonal
     * forecast is never used.
     */
    static double min_autocorrelation;

    /* Maximum required autocorrelation factor beyond which a seasonal
     * forecast is always used.
     */
    static double max_autocorrelation;

    /* Period of the cycle. */
    unsigned short period;

    /* Computed autocorrelation. */
    double autocorrelation;

    /* Smoothed result - constant component.
     * Used to carry results between the evaluation and applying of the
     * forecast.
     */
    double L_i;

    /* Smoothed result - trend component.
     * Used to carry results between the evaluation and applying of the
     * forecast.
     */
    double T_i;

    /* Smoothed result - seasonal component.
     * Used to carry results between the evaluation and applying of the
     * forecast.
     */
    double S_i[80];

    /* Remember where in the cycle we are. */
    unsigned int cycleindex;

    /* A check for seasonality.
     * The cycle period is returned if seasonality is detected. Zero is
     * returned in case no seasonality is present.
     */
    void detectCycle(vector<double>&, unsigned int);

   public:
    /* Constructor. */
    Seasonal(double a = initial_alfa, double b = initial_beta)
        : alfa(a), beta(b), period(0), autocorrelation(0.0), L_i(0), T_i(0) {}

    /* Forecast evaluation. */
    Metrics generateForecast(const Forecast*, vector<ForecastBucketData>&,
                             short, vector<double>&, unsigned int,
                             ForecastSolver*);

    /* Forecast value updating. */
    void applyForecast(Forecast*, vector<ForecastBucketData>&, short,
                       CommandManager*);

    /* Update the minimum period that can be detected. */
    static void setMinPeriod(int x) {
      if (x <= 1)
        logger << "Warning: Parameter Seasonal.minPeriod must be greater than 1"
               << endl;
      else
        min_period = x;
    }

    static int getMinPeriod() { return min_period; }

    /* Update the maximum period that can be detected. */
    static void setMaxPeriod(int x) {
      if (x <= 1 || x > 80)
        logger
            << "Warning: Parameter Seasonal.maxPeriod must be between 1 and 80"
            << endl;
      else
        max_period = x;
    }

    static int getMaxPeriod() { return max_period; }

    /* Update the autocorrelation value below which a seasonal forecast
     * is NEVER used.
     */
    static void setMinAutocorrelation(double d) {
      if (d <= 0.0 || d > 1.0)
        logger << "Warning: Parameter Seasonal.minAutocorrelation must be "
                  "between 0.0 and 1.0"
               << endl;
      else
        min_autocorrelation = d;
    }

    static double getMinAutocorrelation() { return min_autocorrelation; }

    /* Update the autocorrelation value above which a seasonal forecast
     * is ALWAYS used.
     * For lower autocorrelation values a seasonal forecast can still
     * be used, but only if it produces a lower SMAPE.
     */
    static void setMaxAutocorrelation(double d) {
      if (d <= 0.0 || d > 1.0)
        logger << "Warning: Parameter Seasonal.maxAutocorrelation must be "
                  "between 0.0 and 1.0"
               << endl;
      else
        max_autocorrelation = d;
    }

    static double getMaxAutocorrelation() { return max_autocorrelation; }

    /* Update the initial value for the alfa parameter. */
    static void setInitialAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger
            << "Warning: Parameter Seasonal.initialAlfa must be between 0 and 1"
            << endl;
      else
        initial_alfa = x;
    }

    static double getInitialAlfa() { return initial_alfa; }

    /* Update the minimum value for the alfa parameter. */
    static void setMinAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter Seasonal.minAlfa must be between 0 and 1"
               << endl;
      else
        min_alfa = x;
    }

    static double getMinAlfa() { return min_alfa; }

    /* Update the maximum value for the alfa parameter. */
    static void setMaxAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter Seasonal.maxAlfa must be between 0 and 1"
               << endl;
      else
        max_alfa = x;
    }

    static double getMaxAlfa() { return max_alfa; }

    /* Update the initial value for the beta parameter. */
    static void setInitialBeta(double x) {
      if (x < 0 || x > 1.0)
        logger
            << "Warning: Parameter Seasonal.initialBeta must be between 0 and 1"
            << endl;
      else
        initial_beta = x;
    }

    static double getInitialBeta() { return initial_beta; }

    /* Update the minimum value for the beta parameter. */
    static void setMinBeta(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter Seasonal.minBeta must be between 0 and 1"
               << endl;
      else
        min_beta = x;
    }

    static double getMinBeta() { return min_beta; }

    /* Update the maximum value for the beta parameter. */
    static void setMaxBeta(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter Seasonal.maxBeta must be between 0 and 1"
               << endl;
      else
        max_beta = x;
    }

    static double getMaxBeta() { return max_beta; }

    /* Update the value for the gamma parameter.
     * The default value is 0.05.
     */
    static void setGamma(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter Seasonal.gamma must be between 0 and 1"
               << endl;
      else
        gamma = x;
    }

    static double getGamma() { return gamma; }

    /* Update the dampening factor for the trend. */
    static void setDampenTrend(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter Seasonal.dampenTrend must be between 0 "
                  "and 1";
      else
        dampenTrend = x;
    }

    static double getDampenTrend() { return dampenTrend; }

    unsigned int getCode() { return Forecast::METHOD_SEASONAL; }
  };

  /* A class to calculate a forecast with Croston's method. */
  class Croston : public ForecastMethod {
   private:
    /* Smoothing constant. */
    double alfa;

    /* Default initial alfa value.
     * The default value is 0.2.
     */
    static double initial_alfa;

    /* Lower limit on the alfa parameter.
     * The default value is 0.
     **/
    static double min_alfa;

    /* Upper limit on the alfa parameter.
     * The default value is 1.
     **/
    static double max_alfa;

    /* Minimum intermittence before this method is applicable. */
    static double min_intermittence;

    /* Decay rate for dying forecasts (ie no hits since 2 * average time
     * between demand hits. */
    static double decay_rate;

    /* Smoothed forecast.
     * Used to carry results between the evaluation and applying of the
     * forecast.
     */
    double f_i;

   public:
    /* Constructor. */
    Croston(double a = initial_alfa) : alfa(a), f_i(0) {
      if (alfa < min_alfa) alfa = min_alfa;
      if (alfa > max_alfa) alfa = max_alfa;
    }

    /* Forecast evaluation. */
    Metrics generateForecast(const Forecast*, vector<ForecastBucketData>&,
                             short, vector<double>&, unsigned int,
                             ForecastSolver*);

    /* Forecast value updating. */
    void applyForecast(Forecast*, vector<ForecastBucketData>&, short,
                       CommandManager*);

    /* Update the initial value for the alfa parameter. */
    static void setInitialAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger
            << "Warning: Parameter Croston.initialAlfa must be between 0 and 1"
            << endl;
      else
        initial_alfa = x;
    }

    static double getInitialAlfa() { return initial_alfa; }

    /* Update the minimum value for the alfa parameter. */
    static void setMinAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter Croston.minAlfa must be between 0 and 1"
               << endl;
      else
        min_alfa = x;
    }

    static double getMinAlfa() { return min_alfa; }

    /* Decay rate for dying items. */
    static void setDecayRate(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter Croston.decayRate must be between 0 and 1"
               << endl;
      else
        decay_rate = x;
    }

    static double getDecayRate() { return decay_rate; }

    /* Update the maximum value for the alfa parameter. */
    static void setMaxAlfa(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter Croston.maxAlfa must be between 0 and 1"
               << endl;
      else
        max_alfa = x;
    }

    static double getMaxAlfa() { return max_alfa; }

    /* Update the minimum intermittence before applying this method. */
    static void setMinIntermittence(double x) {
      if (x < 0 || x > 1.0)
        logger << "Warning: Parameter Croston.minIntermittence must be between "
                  "0 and 1"
               << endl;
      else
        min_intermittence = x;
    }

    /* Return the minimum intermittence before applying this method. */
    static double getMinIntermittence() { return min_intermittence; }

    unsigned int getCode() { return Forecast::METHOD_CROSTON; }
  };

  /* A dummy forecast class that generates baseline forecast of 0. */
  class Manual : public ForecastMethod {
   public:
    /* Constructor. */
    Manual() {}

    /* Forecast evaluation. */
    Metrics generateForecast(const Forecast*, vector<ForecastBucketData>&,
                             short, vector<double>&, unsigned int,
                             ForecastSolver*);

    /* Forecast value updating. */
    void applyForecast(Forecast*, vector<ForecastBucketData>&, short,
                       CommandManager*);

    unsigned int getCode() { return Forecast::METHOD_MANUAL; }
  };

  /* Default constructor. */
  explicit ForecastSolver() {
    initType(metadata);
    commands = &default_commands;
  }

  ~ForecastSolver() {
    if (commands) commands->commit();
  }

  /* There are two different calculations implemented in this method.
   *  1) When called for a forecast, we first compute the statistical
   *     baseline forecast and then apply the overrides on it.
   *  2) When called on another demand type, we net the order from the
   *     forecast. The method searches for a matching forecast, and then
   *     decreasing the net forecast.
   */
  void solve(const Demand*, void* = nullptr);

  /* This is the main solver method. */
  void solve(void* v = nullptr) { solve(true, true, -1); }
  void solve(bool run_fcst = true, bool run_netting = true, int cluster = -1);

  /* Python interface for the solve method. */
  static PyObject* solve(PyObject*, PyObject*, PyObject*);

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  virtual size_t getSize() const { return sizeof(ForecastSolver); }
  static int initialize();
  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

  void setCalendar(Calendar* c) { Forecast::setCalendar_static(c); }

  Calendar* getCalendar() const { return Forecast::getCalendar_static(); }

  const string& getDueWithinBucket() const {
    return ForecastBucket::getDueWithinBucket();
  }

  void setDueWithinBucket(const string& s) {
    ForecastBucket::setDueWithinBucket(s);
  }

  void setCustomerThenItemHierarchy(bool b) {
    Customer_Then_Item_Hierarchy = b;
  }

  bool getCustomerThenItemHierarchy() const {
    return Customer_Then_Item_Hierarchy;
  }

  void setMatchUsingDeliveryOperation(bool b) {
    Match_Using_Delivery_Operation = b;
  }

  bool getMatchUsingDeliveryOperation() const {
    return Match_Using_Delivery_Operation;
  }

  void setNetEarly(Duration t) { Net_Early = t; }

  Duration getNetEarly() const { return Net_Early; }

  void setNetLate(Duration t) { Net_Late = t; }

  Duration getNetLate() const { return Net_Late; }

  void setNetPastDemand(bool b) { Net_PastDemand = b; }

  bool getNetPastDemand() const { return Net_PastDemand; }

  void setAverageNoDataDays(bool b) { AverageNoDataDays = b; }

  bool getAverageNoDataDays() const { return AverageNoDataDays; }

  void setNetIgnoreLocation(bool b) { Net_Ignore_Location = b; }

  bool getNetIgnoreLocation() const { return Net_Ignore_Location; }

  /* Updates the value of the Forecast.smapeAlfa module parameter. */
  void setForecastSmapeAlfa(double t) {
    if (t <= 0.5 || t > 1.0) {
      logger
          << "Warning: Parameter Forecast.smapeAlfa must be between 0.5 and 1.0"
          << endl;
      return;
    }
    Forecast_SmapeAlfa = t;

    // Initialize the smape weight array
    weight[0] = 1.0;
    for (int i = 0; i < 299; ++i)
      weight[i + 1] = weight[i] * Forecast_SmapeAlfa;
  }

  /* Returns the value of the Forecast_Iterations module parameter. */
  double getForecastSmapeAlfa() const { return Forecast_SmapeAlfa; }

  /* Updates the value of the Forecast_Iterations module parameter. */
  void setForecastIterations(unsigned long t) {
    if (t <= 0)
      logger << "Warning: Parameter Forecast.Iterations must be bigger than 0"
             << endl;
    else
      Forecast_Iterations = t;
  }

  /* Returns the value of the Forecast_Iterations module parameter. */
  unsigned long getForecastIterations() const { return Forecast_Iterations; }

  /* Updates the value of the Forecast_Skip module parameter. */
  void setForecastSkip(unsigned long t) {
    if (t < 0)
      logger << "Warning: Parameter Forecast.Skip must be bigger than or equal "
                "to 0"
             << endl;
    else
      Forecast_Skip = t;
  }

  /* Return the number of timeseries values used to initialize the
   * algorithm. The forecast error is not counted for these buckets.
   */
  unsigned long getForecastSkip() const { return Forecast_Skip; }

  /* Update the multiplier of the standard deviation used for detecting
   * outlier demands.
   */
  void setForecastMaxDeviation(double d) {
    if (d <= 0)
      logger << "Warning: Parameter Forecast.maxDeviation must be bigger than 0"
             << endl;
    else
      Forecast_maxDeviation = d;
  }

  /* Return the multiplier of the standard deviation used for detecting
   * outlier demands.
   */
  double getForecastMaxDeviation() const { return Forecast_maxDeviation; }

  void setForecastDeadAfterInactivity(int d) {
    if (d <= 0)
      logger
          << "Warning: Parameter Forecast.deadAfterInactivity must be positive"
          << endl;
    else
      Forecast_DeadAfterInactivity = d;
  }

  int getForecastDeadAfterInactivity() const {
    return Forecast_DeadAfterInactivity;
  }

  int getMovingAverageDefaultOrder() const {
    return MovingAverage::getDefaultOrder();
  }

  void setMovingAverageDefaultOrder(int i) {
    MovingAverage::setDefaultOrder(i);
  }

  double getSingleExponentialInitialAlfa() const {
    return SingleExponential::getInitialAlfa();
  }

  void setSingleExponentialInitialAlfa(double i) {
    SingleExponential::setInitialAlfa(i);
  }

  double getSingleExponentialMinAlfa() const {
    return SingleExponential::getMinAlfa();
  }

  void setSingleExponentialMinAlfa(double i) {
    SingleExponential::setMinAlfa(i);
  }

  double getSingleExponentialMaxAlfa() const {
    return SingleExponential::getMaxAlfa();
  }

  void setSingleExponentialMaxAlfa(double i) {
    SingleExponential::setMaxAlfa(i);
  }

  double getDoubleExponentialInitialAlfa() const {
    return DoubleExponential::getInitialAlfa();
  }

  void setDoubleExponentialInitialAlfa(double i) {
    DoubleExponential::setInitialAlfa(i);
  }

  double getDoubleExponentialMinAlfa() const {
    return DoubleExponential::getMinAlfa();
  }

  void setDoubleExponentialMinAlfa(double i) {
    DoubleExponential::setMinAlfa(i);
  }

  double getDoubleExponentialMaxAlfa() const {
    return DoubleExponential::getMaxAlfa();
  }

  void setDoubleExponentialMaxAlfa(double i) {
    DoubleExponential::setMaxAlfa(i);
  }

  double getDoubleExponentialInitialGamma() const {
    return DoubleExponential::getInitialGamma();
  }

  void setDoubleExponentialInitialGamma(double i) {
    DoubleExponential::setInitialGamma(i);
  }

  double getDoubleExponentialMinGamma() const {
    return DoubleExponential::getMinGamma();
  }

  void setDoubleExponentialMinGamma(double i) {
    DoubleExponential::setMinGamma(i);
  }

  double getDoubleExponentialMaxGamma() const {
    return DoubleExponential::getMaxGamma();
  }

  void setDoubleExponentialMaxGamma(double i) {
    DoubleExponential::setMaxGamma(i);
  }

  double getDoubleExponentialDampenTrend() const {
    return DoubleExponential::getDampenTrend();
  }

  void setDoubleExponentialDampenTrend(double i) {
    DoubleExponential::setDampenTrend(i);
  }

  double getSeasonalInitialAlfa() const { return Seasonal::getInitialAlfa(); }

  void setSeasonalInitialAlfa(double i) { Seasonal::setInitialAlfa(i); }

  double getSeasonalMinAlfa() const { return Seasonal::getMinAlfa(); }

  void setSeasonalMinAlfa(double i) { Seasonal::setMinAlfa(i); }

  double getSeasonalMaxAlfa() const { return Seasonal::getMaxAlfa(); }

  void setSeasonalMaxAlfa(double i) { Seasonal::setMaxAlfa(i); }

  double getSeasonalInitialBeta() const { return Seasonal::getInitialBeta(); }

  void setSeasonalInitialBeta(double i) { Seasonal::setInitialBeta(i); }

  double getSeasonalMinBeta() const { return Seasonal::getMinBeta(); }

  void setSeasonalMinBeta(double i) { Seasonal::setMinBeta(i); }

  double getSeasonalMaxBeta() const { return Seasonal::getMaxBeta(); }

  void setSeasonalMaxBeta(double i) { Seasonal::setMaxBeta(i); }

  double getSeasonalGamma() const { return Seasonal::getGamma(); }

  void setSeasonalGamma(double i) { Seasonal::setGamma(i); }

  double getSeasonalDampenTrend() const { return Seasonal::getDampenTrend(); }

  void setSeasonalDampenTrend(double i) { Seasonal::setDampenTrend(i); }

  int getSeasonalMinPeriod() const { return Seasonal::getMinPeriod(); }

  void setSeasonalMinPeriod(int i) { Seasonal::setMinPeriod(i); }

  int getSeasonalMaxPeriod() const { return Seasonal::getMaxPeriod(); }

  void setSeasonalMaxPeriod(int i) { Seasonal::setMaxPeriod(i); }

  double getSeasonalMinAutocorrelation() const {
    return Seasonal::getMinAutocorrelation();
  }

  void setSeasonalMinAutocorrelation(double i) {
    Seasonal::setMinAutocorrelation(i);
  }

  double getSeasonalMaxAutocorrelation() const {
    return Seasonal::getMaxAutocorrelation();
  }

  void setSeasonalMaxAutocorrelation(double i) {
    Seasonal::setMaxAutocorrelation(i);
  }

  double getCrostonInitialAlfa() const { return Croston::getInitialAlfa(); }

  void setCrostonInitialAlfa(double i) { Croston::setInitialAlfa(i); }

  double getCrostonMinAlfa() const { return Croston::getMinAlfa(); }

  void setCrostonMinAlfa(double i) { Croston::setMinAlfa(i); }

  double getCrostonMaxAlfa() const { return Croston::getMaxAlfa(); }

  void setCrostonMaxAlfa(double i) { Croston::setMaxAlfa(i); }

  double getCrostonMinIntermittence() const {
    return Croston::getMinIntermittence();
  }

  void setCrostonMinIntermittence(double i) { Croston::setMinIntermittence(i); }

  double getCrostonDecayRate() const { return Croston::getDecayRate(); }

  void setCrostonDecayRate(double i) { Croston::setDecayRate(i); }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    // Forecast buckets
    m->addStringRefField<Cls>(ForecastSolver::tag_DueWithinBucket,
                              &Cls::getDueWithinBucket,
                              &Cls::setDueWithinBucket);
    m->addPointerField<Cls, Calendar>(Tags::calendar, &Cls::getCalendar,
                                      &Cls::setCalendar);
    // Netting
    m->addBoolField<Cls>(ForecastSolver::tag_Net_CustomerThenItemHierarchy,
                         &Cls::getCustomerThenItemHierarchy,
                         &Cls::setCustomerThenItemHierarchy);
    m->addBoolField<Cls>(ForecastSolver::tag_Net_MatchUsingDeliveryOperation,
                         &Cls::getMatchUsingDeliveryOperation,
                         &Cls::setMatchUsingDeliveryOperation);
    m->addDurationField<Cls>(ForecastSolver::tag_Net_NetEarly,
                             &Cls::getNetEarly, &Cls::setNetEarly);
    m->addDurationField<Cls>(ForecastSolver::tag_Net_NetLate, &Cls::getNetLate,
                             &Cls::setNetLate);
    m->addBoolField<Cls>(ForecastSolver::tag_Net_PastDemand,
                         &Cls::getNetPastDemand, &Cls::setNetPastDemand);
    m->addBoolField<Cls>(ForecastSolver::tag_AverageNoDataDays,
                         &Cls::getAverageNoDataDays,
                         &Cls::setAverageNoDataDays);
    m->addBoolField<Cls>(ForecastSolver::tag_Net_IgnoreLocation,
                         &Cls::getNetIgnoreLocation,
                         &Cls::setNetIgnoreLocation);
    // Forecasting
    m->addUnsignedLongField<Cls>(ForecastSolver::tag_Iterations,
                                 &Cls::getForecastIterations,
                                 &Cls::setForecastIterations);
    m->addDoubleField<Cls>(ForecastSolver::tag_SmapeAlfa,
                           &Cls::getForecastSmapeAlfa,
                           &Cls::setForecastSmapeAlfa);
    m->addUnsignedLongField<Cls>(ForecastSolver::tag_Skip,
                                 &Cls::getForecastSkip, &Cls::setForecastSkip);
    m->addDoubleField<Cls>(ForecastSolver::tag_Outlier_maxDeviation,
                           &Cls::getForecastMaxDeviation,
                           &Cls::setForecastMaxDeviation);
    m->addIntField<Cls>(ForecastSolver::tag_DeadAfterInactivity,
                        &Cls::getForecastDeadAfterInactivity,
                        &Cls::setForecastDeadAfterInactivity);
    // Moving average forecast method
    m->addIntField<Cls>(ForecastSolver::tag_MovingAverage_order,
                        &Cls::getMovingAverageDefaultOrder,
                        &Cls::setMovingAverageDefaultOrder);
    // Single exponential forecast method
    m->addDoubleField<Cls>(ForecastSolver::tag_SingleExponential_initialAlfa,
                           &Cls::getSingleExponentialInitialAlfa,
                           &Cls::setSingleExponentialInitialAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_SingleExponential_minAlfa,
                           &Cls::getSingleExponentialMinAlfa,
                           &Cls::setSingleExponentialMinAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_SingleExponential_maxAlfa,
                           &Cls::getSingleExponentialMaxAlfa,
                           &Cls::setSingleExponentialMaxAlfa);
    // Double exponential forecast method
    m->addDoubleField<Cls>(ForecastSolver::tag_DoubleExponential_initialAlfa,
                           &Cls::getDoubleExponentialInitialAlfa,
                           &Cls::setDoubleExponentialInitialAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_DoubleExponential_minAlfa,
                           &Cls::getDoubleExponentialMinAlfa,
                           &Cls::setDoubleExponentialMinAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_DoubleExponential_maxAlfa,
                           &Cls::getDoubleExponentialMaxAlfa,
                           &Cls::setDoubleExponentialMaxAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_DoubleExponential_initialGamma,
                           &Cls::getDoubleExponentialInitialGamma,
                           &Cls::setDoubleExponentialInitialGamma);
    m->addDoubleField<Cls>(ForecastSolver::tag_DoubleExponential_minGamma,
                           &Cls::getDoubleExponentialMinGamma,
                           &Cls::setDoubleExponentialMinGamma);
    m->addDoubleField<Cls>(ForecastSolver::tag_DoubleExponential_maxGamma,
                           &Cls::getDoubleExponentialMaxGamma,
                           &Cls::setDoubleExponentialMaxGamma);
    m->addDoubleField<Cls>(ForecastSolver::tag_DoubleExponential_dampenTrend,
                           &Cls::getDoubleExponentialDampenTrend,
                           &Cls::setDoubleExponentialDampenTrend);
    // Seasonal forecast method
    m->addDoubleField<Cls>(ForecastSolver::tag_Seasonal_initialAlfa,
                           &Cls::getSeasonalInitialAlfa,
                           &Cls::setSeasonalInitialAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_Seasonal_minAlfa,
                           &Cls::getSeasonalMinAlfa, &Cls::setSeasonalMinAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_Seasonal_maxAlfa,
                           &Cls::getSeasonalMaxAlfa, &Cls::setSeasonalMaxAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_Seasonal_initialBeta,
                           &Cls::getSeasonalInitialBeta,
                           &Cls::setSeasonalInitialBeta);
    m->addDoubleField<Cls>(ForecastSolver::tag_Seasonal_minBeta,
                           &Cls::getSeasonalMinBeta, &Cls::setSeasonalMinBeta);
    m->addDoubleField<Cls>(ForecastSolver::tag_Seasonal_maxBeta,
                           &Cls::getSeasonalMaxBeta, &Cls::setSeasonalMaxBeta);
    m->addDoubleField<Cls>(ForecastSolver::tag_Seasonal_gamma,
                           &Cls::getSeasonalGamma, &Cls::setSeasonalGamma);
    m->addDoubleField<Cls>(ForecastSolver::tag_Seasonal_dampenTrend,
                           &Cls::getSeasonalDampenTrend,
                           &Cls::setSeasonalDampenTrend);
    m->addIntField<Cls>(ForecastSolver::tag_Seasonal_minPeriod,
                        &Cls::getSeasonalMinPeriod, &Cls::setSeasonalMinPeriod);
    m->addIntField<Cls>(ForecastSolver::tag_Seasonal_maxPeriod,
                        &Cls::getSeasonalMaxPeriod, &Cls::setSeasonalMaxPeriod);
    m->addDoubleField<Cls>(ForecastSolver::tag_Seasonal_minAutocorrelation,
                           &Cls::getSeasonalMinAutocorrelation,
                           &Cls::setSeasonalMinAutocorrelation);
    m->addDoubleField<Cls>(ForecastSolver::tag_Seasonal_maxAutocorrelation,
                           &Cls::getSeasonalMaxAutocorrelation,
                           &Cls::setSeasonalMaxAutocorrelation);
    // Croston forecast method
    m->addDoubleField<Cls>(ForecastSolver::tag_Croston_initialAlfa,
                           &Cls::getCrostonInitialAlfa,
                           &Cls::setCrostonInitialAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_Croston_minAlfa,
                           &Cls::getCrostonMinAlfa, &Cls::setCrostonMinAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_Croston_maxAlfa,
                           &Cls::getCrostonMaxAlfa, &Cls::setCrostonMaxAlfa);
    m->addDoubleField<Cls>(ForecastSolver::tag_Croston_minIntermittence,
                           &Cls::getCrostonMinIntermittence,
                           &Cls::setCrostonMinIntermittence);
    m->addDoubleField<Cls>(ForecastSolver::tag_Croston_decayRate,
                           &Cls::getCrostonDecayRate,
                           &Cls::setCrostonDecayRate);

    // Command manager
    m->addPointerField<Cls, CommandManager>(
        Tags::manager, &Cls::getCommandManager, &Cls::setCommandManager);
  }

 private:
  /* Controls how we search the customer and item levels when looking for a
   * matching forecast for a demand.
   */
  static bool Customer_Then_Item_Hierarchy;

  /* Controls whether or not a matching delivery operation is required
   * between a matching order and its forecast.
   */
  static bool Match_Using_Delivery_Operation;

  /* Controls whether we ignore the location dimension when searching for
   * a matching forecast for a demand.
   */
  static bool Net_Ignore_Location;

  /* Store the maximum time difference between an order due date and a
   * forecast bucket to net from.
   * The default value is 0, meaning that only netting from the due
   * bucket is allowed.
   */
  static Duration Net_Late;

  /* Store the maximum time difference between an order due date and a
   * forecast bucket to net from.
   * The default value is 0, meaning that only netting from the due
   * bucket is allowed.
   */
  static Duration Net_Early;

  /* Default value of false: net only sales orders from the current and future.
   * When set to true we also consider older sales orders.
   */
  static bool Net_PastDemand;

  /* Default value is true: the forecast solver will compute an average value
   * for all no data points taking the mean between the last valid point before
   * a no data series and the first valid point after this no data series.
   * If set to false, the solver will ignore these days and remove them from the
   * time series.
   */
  static bool AverageNoDataDays;

  /* Specifies the maximum number of iterations allowed for a forecast
   * method to tune its parameters.
   * Only positive values are allowed and the default value is 10.
   * Set the parameter to 1 to disable the tuning and generate a
   * forecast based on the user-supplied parameters.
   */
  static unsigned long Forecast_Iterations;

  /* Specifies how the sMAPE forecast error is weighted for different time
   * buckets. The SMAPE value in the most recent bucket is 1.0, and the
   * weight decreases exponentially for earlier buckets.
   * Acceptable values are in the interval 0.5 and 1.0, and the default
   * is 0.95.
   */
  static double Forecast_SmapeAlfa;

  /* Inactivity during this period will mark the forecast as inactive,
   * resulting in a baseline forecast of 0. */
  static int Forecast_DeadAfterInactivity;

  const static short MAXBUCKETS = 500;

  /* An array with weights for history buckets. */
  static double weight[MAXBUCKETS];

  /* Number of warmup periods.
   * These periods are used for the initialization of the algorithm
   * and don't count towards measuring the forecast error.
   * The default value is 5.
   */
  static unsigned long Forecast_Skip;

  /* Threshold for detecting outliers. */
  static double Forecast_maxDeviation;

  // Used when autocommit is false
  CommandManager* commands;
  CommandManager default_commands;

  static PyObject* commit(PyObject*, PyObject*);

  static PyObject* rollback(PyObject*, PyObject*);

  /* Given a demand, this function will identify the forecast model it
   * links to.
   */
  Forecast* matchDemandToForecast(const Demand* l);

  /* Implements the netting of a customer order from a matching forecast
   * (and its delivery plan).
   */
  void netDemandFromForecast(const Demand*, Forecast*);

  /* Implements the timeseries forecasting algorithms. */
  void computeBaselineForecast(const Forecast*);

  /* Deletes all outliers found by a forecasting method that is not applied */
  static void deleteOutliers(
      const Forecast* forecast,
      ForecastSolver::ForecastMethod* appliedMethod = nullptr);

  /* Update the command manager used to track all changes. */
  void setCommandManager(CommandManager* c) { commands = c; }

  /* Return the command manager used to track all changes. */
  CommandManager* getCommandManager() const { return commands; }

  /* Used for sorting demands during netting. */
  struct sorter {
    bool operator()(const Demand* x, const Demand* y) const {
      return SolverCreate::demand_comparison(x, y);
    }
  };

 public:
  /* Used for sorting demands during netting. */
  typedef multiset<Demand*, sorter> sortedDemandList;

  static const Keyword tag_DueWithinBucket;
  static const Keyword tag_Net_CustomerThenItemHierarchy;
  static const Keyword tag_Net_MatchUsingDeliveryOperation;
  static const Keyword tag_Net_NetEarly;
  static const Keyword tag_Net_NetLate;
  static const Keyword tag_Net_PastDemand;
  static const Keyword tag_AverageNoDataDays;
  static const Keyword tag_Net_IgnoreLocation;
  static const Keyword tag_Iterations;
  static const Keyword tag_SmapeAlfa;
  static const Keyword tag_Skip;
  static const Keyword tag_MovingAverage_order;
  static const Keyword tag_SingleExponential_initialAlfa;
  static const Keyword tag_SingleExponential_minAlfa;
  static const Keyword tag_SingleExponential_maxAlfa;
  static const Keyword tag_DoubleExponential_initialAlfa;
  static const Keyword tag_DoubleExponential_minAlfa;
  static const Keyword tag_DoubleExponential_maxAlfa;
  static const Keyword tag_DoubleExponential_initialGamma;
  static const Keyword tag_DoubleExponential_minGamma;
  static const Keyword tag_DoubleExponential_maxGamma;
  static const Keyword tag_DoubleExponential_dampenTrend;
  static const Keyword tag_Seasonal_initialAlfa;
  static const Keyword tag_Seasonal_minAlfa;
  static const Keyword tag_Seasonal_maxAlfa;
  static const Keyword tag_Seasonal_initialBeta;
  static const Keyword tag_Seasonal_minBeta;
  static const Keyword tag_Seasonal_maxBeta;
  static const Keyword tag_Seasonal_gamma;
  static const Keyword tag_Seasonal_dampenTrend;
  static const Keyword tag_Seasonal_minPeriod;
  static const Keyword tag_Seasonal_maxPeriod;
  static const Keyword tag_Seasonal_minAutocorrelation;
  static const Keyword tag_Seasonal_maxAutocorrelation;
  static const Keyword tag_Croston_initialAlfa;
  static const Keyword tag_Croston_minAlfa;
  static const Keyword tag_Croston_maxAlfa;
  static const Keyword tag_Croston_minIntermittence;
  static const Keyword tag_Croston_decayRate;
  static const Keyword tag_Outlier_maxDeviation;
  static const Keyword tag_DeadAfterInactivity;
  static const Keyword tag_Horizon_future;
  static const Keyword tag_Horizon_history;
  static const Keyword tag_forecast_partition;
};

/* A problem of this class is created when an outlier is detected for a
 * ForecastBucket.
 */
class ProblemOutlier : public Problem {
 private:
  ForecastSolver::ForecastMethod* method;

 public:
  string getDescription() const {
    ostringstream ch;
    /* The format is expected as is by the widget. Changing this format needs
       adaptation at widget level
        and on the question marks to flag the ouliers in the reports*/
    ch << "Outlier detected for " << getForecastBucket()->getItem()->getName()
       << " @ " << getForecastBucket()->getLocation()->getName() << " @ "
       << getForecastBucket()->getCustomer()->getName() << " @ "
       << getForecastBucket()->getStartDate().toString("%Y-%m-%d");
    return ch.str();
  }

  bool isFeasible() const { return true; }

  double getWeight() const { return getForecastBucket()->getOrdersTotal(); }

  explicit ProblemOutlier(ForecastBucket* d, ForecastSolver::ForecastMethod* fm,
                          bool add = true)
      : Problem(d) {
    if (add) addProblem();
    method = fm;
  }

  ~ProblemOutlier() { removeProblem(); }

  string getEntity() const { return "demand"; }

  ForecastSolver::ForecastMethod* getForecastMethod() { return method; }

  void setForecastMethod(ForecastSolver::ForecastMethod* m) { method = m; }

  const DateRange getDates() const {
    return DateRange(getForecastBucket()->getStartDate(),
                     getForecastBucket()->getEndDate());
  }

  Object* getOwner() const { return static_cast<ForecastBucket*>(owner); }

  ForecastBucket* getForecastBucket() const {
    return static_cast<ForecastBucket*>(owner);
  }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;
};

shared_ptr<ForecastData> ForecastBase::getData() const {
  return data.getValue(this);
}

template <typename... Measures>
void ForecastMeasure::resetMeasure(short mode, Measures*... measures) {
  for (auto& f : Forecast::getForecasts()) {
    auto fcstdata = f->getData();
    lock_guard<recursive_mutex> exclusive(fcstdata->lock);
    for (auto bckt = fcstdata->getBuckets().begin();
         bckt != fcstdata->getBuckets().end(); ++bckt) {
      bool do_it = false;
      if (mode & PAST)
        do_it = bckt->getEnd() <= Plan::instance().getFcstCurrent();
      else if (mode & PAST_CURRENT)
        do_it = bckt->getStart() <= Plan::instance().getFcstCurrent();
      else if (mode & ALL)
        do_it = true;
      else if (mode & FUTURE_CURRENT)
        do_it = bckt->getEnd() > Plan::instance().getFcstCurrent();
      else if (mode & FUTURE)
        do_it = bckt->getStart() > Plan::instance().getFcstCurrent();
      if (do_it) bckt->removeValue(false, nullptr, measures...);
    }
  }
}

}  // namespace frepple
#endif
