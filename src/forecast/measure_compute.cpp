/***************************************************************************
 *                                                                         *
 * Copyright (C) 2019 by frePPLe bv                                        *
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

const Keyword ForecastMeasureComputed::tag_update_expression(
    "update_expression");
const Keyword ForecastMeasureComputed::tag_compute_expression(
    "compute_expression");
double ForecastMeasureComputed::newvalue = 0.0;

exprtk::symbol_table<double> ForecastMeasureComputed::symboltable;
double ForecastMeasureComputed::cost;
ForecastBucket* ForecastMeasureComputed::fcstbckt;

int ForecastMeasureComputed::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<ForecastMeasureLocal>(
      "measure", "measure_computed", Object::create<ForecastMeasureComputed>);
  registerFields<ForecastMeasureComputed>(const_cast<MetaClass*>(metadata));

  PythonInterpreter::registerGlobalMethod(
      "compileMeasures", compileMeasuresPython, METH_NOARGS,
      "Compiles all expressions on the measures.");

  // Initialize the Python class
  return FreppleClass<ForecastMeasureComputed, ForecastMeasure>::initialize();
}

int ForecastMeasureComputedPlanned::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<ForecastMeasureLocal>(
      "measure", "measure_computedplanned",
      Object::create<ForecastMeasureComputedPlanned>);
  registerFields<ForecastMeasureComputedPlanned>(
      const_cast<MetaClass*>(metadata));

  PythonInterpreter::registerGlobalMethod(
      "compileMeasures", compileMeasuresPython, METH_NOARGS,
      "Compiles all expressions on the measures.");

  // Initialize the Python class
  return FreppleClass<ForecastMeasureComputedPlanned,
                      ForecastMeasure>::initialize();
}

struct ForecastMeasureComputed::ItemAttribute final
    : public exprtk::igeneric_function<double> {
  typedef exprtk::igeneric_function<double> igenfunct_t;
  typedef typename igenfunct_t::parameter_list_t parameter_list_t;
  typedef typename igenfunct_t::generic_type::string_view string_t;

  ItemAttribute() : igenfunct_t("S") {}

  inline double operator()(parameter_list_t parameters) override {
    auto attr = to_str(string_t(parameters[0]));
    if (attr == "cost")
      return fcstbckt->getItem()->getCost();
    else if (attr == "volume")
      return fcstbckt->getItem()->getVolume();
    else if (attr == "weight")
      return fcstbckt->getItem()->getWeight();
    else
      return fcstbckt->getItem()->getDoubleProperty(attr, 0);
  }
};

ForecastMeasureComputed::ItemAttribute
    ForecastMeasureComputed::functionItemAttribute;

struct ForecastMeasureComputed::LocationAttribute final
    : public exprtk::igeneric_function<double> {
  typedef exprtk::igeneric_function<double> igenfunct_t;
  typedef typename igenfunct_t::parameter_list_t parameter_list_t;
  typedef typename igenfunct_t::generic_type::string_view string_t;

  LocationAttribute() : igenfunct_t("S") {}

  inline double operator()(parameter_list_t parameters) override {
    auto attr = to_str(string_t(parameters[0]));
    return fcstbckt->getLocation()->getDoubleProperty(attr, 0);
  }
};

ForecastMeasureComputed::LocationAttribute
    ForecastMeasureComputed::functionLocationAttribute;

struct ForecastMeasureComputed::CustomerAttribute final
    : public exprtk::igeneric_function<double> {
  typedef exprtk::igeneric_function<double> igenfunct_t;
  typedef typename igenfunct_t::parameter_list_t parameter_list_t;
  typedef typename igenfunct_t::generic_type::string_view string_t;

  CustomerAttribute() : igenfunct_t("S") {}

  inline double operator()(parameter_list_t parameters) override {
    auto attr = to_str(string_t(parameters[0]));
    return fcstbckt->getCustomer()->getDoubleProperty(attr, 0);
  }
};

ForecastMeasureComputed::CustomerAttribute
    ForecastMeasureComputed::functionCustomerAttribute;

void ForecastMeasureComputed::appendDependents(
    list<const ForecastMeasureComputed*>& l) const {
  l.push_back(this);
  for (auto& i : dependents)
    if (i != this) i->appendDependents(l);
}

PyObject* ForecastMeasureComputed::compileMeasuresPython(PyObject* self,
                                                         PyObject* args) {
  try {
    compileMeasures();
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
  return Py_BuildValue("");
}

void ForecastMeasureComputed::compileMeasures() {
  short errors = 0;
  static exprtk::parser<double> parser;
  parser.dec().collect_variables() = true;
  parser.dec().collect_assignments() = true;

  // Fill the symbol table and reset previous compilation results
  symboltable.clear();
  symboltable.add_variable("cost", cost);
  symboltable.add_function("item", functionItemAttribute);
  symboltable.add_function("location", functionLocationAttribute);
  symboltable.add_function("customer", functionCustomerAttribute);
  symboltable.add_variable("newvalue", newvalue);
  for (auto& m : all()) {
    if (!m.isTemporary())
      symboltable.add_variable(m.getName(), m.expressionvalue);
    m.alldependents.clear();
    m.dependents.clear();
    m.assignments.clear();
  }

  for (auto& m : all()) {
    if (m.isTemporary() || !m.hasType<ForecastMeasureComputed>()) continue;
    auto c = static_cast<ForecastMeasureComputed*>(&m);

    // Compile the compute-expression
    c->compute_expression.register_symbol_table(symboltable);
    if (!parser.compile(c->compute_expression_string, c->compute_expression)) {
      logger << c->getName() << " error compiling expression \""
             << c->compute_expression_string << "\"" << endl;
      ++errors;
    } else {
      // Get all dependent measures
      deque<exprtk::parser<double>::dependent_entity_collector::symbol_t>
          symbol_list;
      parser.dec().symbols(symbol_list);
      for (auto i : symbol_list) {
        if (i.second == exprtk::parser<double>::e_st_variable) {
          auto m = const_cast<ForecastMeasure*>(find(i.first));
          if (m) m->dependents.push_back(c);
        }
      }
    }

    // Compile the update-expression
    if (!c->update_expression_string.empty()) {
      c->update_expression.register_symbol_table(symboltable);
      if (!parser.compile(c->update_expression_string, c->update_expression)) {
        logger << c->getName() << " error compiling update expression \""
               << c->update_expression_string << "\"" << endl;
        ++errors;
      } else {
        // Get all assignments
        deque<exprtk::parser<double>::dependent_entity_collector::symbol_t>
            symbol_list;
        parser.dec().assignment_symbols(symbol_list);
        for (auto i : symbol_list) {
          if (i.second == exprtk::parser<double>::e_st_variable) {
            auto m = const_cast<ForecastMeasure*>(find(i.first));
            if (m) c->assignments.push_back(m);
          }
        }
      }
    }
  }

  for (auto& m : all()) {
    // Get all recursive dependents
    for (auto& i : m.dependents) i->appendDependents(m.alldependents);

    for (auto i = m.alldependents.begin(); i != m.alldependents.end(); ++i) {
      // Remove duplicate dependents
      auto j = i;
      for (++j; j != m.alldependents.end(); ++j) {
        if (*j == *i) {
          auto k = j++;
          m.alldependents.erase(k);
          if (j == m.alldependents.end()) break;
        }
      }
    }
  }

  if (errors) throw DataException("Errors when compiling expressions");
}

void ForecastMeasure::evalExpression(const string& formula, ForecastBase* fcst,
                                     Date startdate, Date enddate) {
  // Find the forecast if not specified
  if (!fcst)
    fcst = Forecast::findForecast(Item::getRoot(), Customer::getRoot(),
                                  Location::getRoot());

  // Compile the expression
  exprtk::parser<double> parser;
  exprtk::expression<double> expression;
  expression.register_symbol_table(ForecastMeasureComputed::symboltable);
  if (!parser.compile(formula, expression))
    throw DataException("Error compiling expression");

  // Evaluate the expression for all leaf forecast buckets
  // double remainder = 0.0;
  for (auto c = fcst->getLeaves(true, this); c; ++c) {
    auto fcstdata = c->getData();
    lock_guard<recursive_mutex> exclusive(fcstdata->lock);
    for (auto bckt = fcstdata->getBuckets().begin();
         bckt != fcstdata->getBuckets().end() && bckt->getStart() <= enddate;
         ++bckt) {
      if ((bckt->getStart() >= startdate && bckt->getStart() < enddate) ||
          (bckt->getDates().within(startdate) &&
           bckt->getDates().between(enddate))) {
        // Fill the symbol table
        for (auto& m : all()) m.expressionvalue = bckt->getValue(m);

        // Evaluate the expression
        auto result = expression.value();
        if (getDiscrete()) {
          // Note: We just round the numbers to discrete values.
          // We are not rolling forward remainders across buckets.
          auto qty = floor(result + ROUNDING_ERROR);
          // remainder = result - qty;
          result = qty;
        }

        // Store the results
        update(*bckt, result);
      }
    }
  }
}

}  // namespace frepple
