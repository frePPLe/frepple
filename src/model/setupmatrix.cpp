/***************************************************************************
 *                                                                         *
 * Copyright (C) 2009-2015 by frePPLe bv                                   *
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

#include "frepple/model.h"

namespace frepple {

template <class SetupMatrix>
Tree utils::HasName<SetupMatrix>::st;
const MetaCategory* SetupMatrix::metadata;
const MetaClass* SetupMatrixDefault::metadata;
const MetaClass* SetupMatrixRuleDefault::metadata;
const MetaCategory* SetupMatrixRule::metadata;

int SetupMatrix::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<SetupMatrix>(
      "setupmatrix", "setupmatrices", reader, finder);
  registerFields<SetupMatrix>(const_cast<MetaCategory*>(metadata));
  FreppleCategory<SetupMatrix>::getPythonType().addMethod(
      "calculatesetup", &SetupMatrix::calculateSetupPython, METH_VARARGS,
      "Return the setup time between the 2 setups passed as argument");
  // Initialize the Python class
  return FreppleCategory<SetupMatrix>::initialize();
}

int SetupMatrixRule::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<SetupMatrixRule>(
      "setupmatrixrule", "setupmatrixrules", reader);
  registerFields<SetupMatrixRule>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<SetupMatrixRule>::initialize();
  ;
}

int SetupMatrixDefault::initialize() {
  // Initialize the metadata
  SetupMatrixDefault::metadata = MetaClass::registerClass<SetupMatrixDefault>(
      "setupmatrix", "setupmatrix_default", Object::create<SetupMatrixDefault>,
      true);

  // Initialize the Python class
  return FreppleClass<SetupMatrixDefault, SetupMatrix>::initialize();
}

int SetupMatrixRuleDefault::initialize() {
  // Initialize the metadata
  SetupMatrixRuleDefault::metadata =
      MetaClass::registerClass<SetupMatrixRuleDefault>(
          "setupmatrixrule", "setupmatrixrule_default",
          Object::create<SetupMatrixRuleDefault>, true);

  // Initialize the Python class
  return FreppleClass<SetupMatrixRuleDefault, SetupMatrixRule>::initialize();
}

SetupMatrix::~SetupMatrix() {
  // Destroy the rules.
  // Note that the rule destructor updates the firstRule field.
  while (firstRule) delete firstRule;

  // Remove all references to this setup matrix from resources
  for (auto& m : Resource::all())
    if (m.getSetupMatrix() == this) m.setSetupMatrix(nullptr);
}

Object* SetupMatrixRule::reader(const MetaClass*, const DataValueDict& atts,
                                CommandManager* mgr) {
  // Pick up the setupmatrix
  const DataValue* matrix_val = atts.get(Tags::setupmatrix);
  SetupMatrix* matrix =
      matrix_val ? static_cast<SetupMatrix*>(matrix_val->getObject()) : nullptr;

  // Pick up the priority.
  const DataValue* prio_val = atts.get(Tags::priority);
  int prio = 0;
  if (prio_val) prio = prio_val->getInt();

  // Check for existence of a bucket with the same start, end and priority
  SetupMatrixRule* result = nullptr;
  if (matrix) {
    auto i = matrix->getRules();
    while (SetupMatrixRule* j = i.next())
      if (j->priority == prio) {
        result = j;
        break;
      }
  }

  // Pick up the action attribute and update accordingly
  switch (MetaClass::decodeAction(atts)) {
    case Action::ADD:
      // Only additions are allowed
      if (result) {
        ostringstream o;
        o << "Rule already exists in setupmatrix '" << matrix << "'";
        throw DataException(o.str());
      }
      result = new SetupMatrixRuleDefault();
      result->setPriority(prio);
      if (matrix) result->setSetupMatrix(matrix);
      if (mgr) mgr->add(new CommandCreateObject(result));
      return result;
    case Action::CHANGE:
      // Only changes are allowed
      if (!result) throw DataException("Rule doesn't exist");
      return result;
    case Action::REMOVE:
      // Delete the entity
      if (!result)
        throw DataException("Rule doesn't exist");
      else {
        // Delete it
        delete result;
        return nullptr;
      }
    case Action::ADD_CHANGE:
      if (!result) {
        // Adding a new rule
        result = new SetupMatrixRuleDefault();
        result->setPriority(prio);
        if (matrix) result->setSetupMatrix(matrix);
        if (mgr) mgr->add(new CommandCreateObject(result));
      }
      return result;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}

void SetupMatrixRule::setSetupMatrix(SetupMatrix* s) {
  if (matrix == s) return;

  // Unlink from the previous matrix
  if (matrix) {
    if (prevRule)
      prevRule->nextRule = nextRule;
    else
      matrix->firstRule = nextRule;
    if (nextRule) nextRule->prevRule = prevRule;
  }

  // Assign the pointer
  matrix = s;

  // Link in the list of buckets of the new calendar
  if (matrix) {
    if (matrix->firstRule) {
      matrix->firstRule->prevRule = this;
      nextRule = matrix->firstRule;
    }
    matrix->firstRule = this;
    updateSort();
  }
}

SetupMatrixRule::~SetupMatrixRule() {
  // Maintain linked list
  if (nextRule) nextRule->prevRule = prevRule;
  if (prevRule)
    prevRule->nextRule = nextRule;
  else
    matrix->firstRule = nextRule;
}

void SetupMatrixRule::updateSort() {
  // Update the position in the list
  if (!matrix) return;
  bool ok = true;
  do {
    ok = true;
    if ((nextRule && nextRule->priority == priority) ||
        (prevRule && prevRule->priority == priority)) {
      ostringstream o;
      o << "Duplicate rules with priority " << priority << " in setup matrix '"
        << matrix << "'";
      throw DataException(o.str());
    } else if (nextRule && nextRule->priority < priority) {
      // Move a position later in the list
      if (nextRule->nextRule) nextRule->nextRule->prevRule = this;
      if (prevRule)
        prevRule->nextRule = nextRule;
      else
        matrix->firstRule = nextRule;
      nextRule->prevRule = prevRule;
      prevRule = nextRule;
      SetupMatrixRule* tmp = nextRule->nextRule;
      nextRule->nextRule = this;
      nextRule = tmp;
      ok = false;
    } else if (prevRule && prevRule->priority > priority) {
      // Move a position earlier in the list
      if (prevRule->prevRule) prevRule->prevRule->nextRule = this;
      if (nextRule) nextRule->prevRule = prevRule;
      prevRule->nextRule = nextRule;
      nextRule = prevRule;
      SetupMatrixRule* tmp = prevRule->prevRule;
      prevRule->prevRule = this;
      prevRule = tmp;
      ok = false;
    }
  } while (!ok);  // Repeat till in place
}

void SetupMatrixRule::setPriority(const int n) {
  if (n == priority) return;
  if (!matrix) {
    // As long as there is no matrix assigned, anything goes
    priority = n;
    return;
  }

  // Update the field
  priority = n;

  // Update the list
  updateSort();
}

void SetupMatrixRule::updateExpression() {
  string tmp(from);
  if (tmp.empty())
    tmp = ".* to ";
  else
    tmp.append(" to ");
  if (to.empty())
    tmp.append(".*");
  else
    tmp.append(to);
  try {
    expression = regex(tmp, regex::ECMAScript | regex::optimize);
  } catch (const regex_error&) {
    string msg("Invalid setup matrix rule \"" + tmp + "\" on setup matrix \"" +
               getSetupMatrix()->getName() + "\"");
    Resource* rsrc = nullptr;
    for (auto& r : Resource::all())
      if (r.getSetupMatrix() == getSetupMatrix()) {
        rsrc = &r;
        break;
      }
    if (rsrc)
      new ProblemInvalidData(rsrc, msg, "capacity", Date::infinitePast,
                             Date::infiniteFuture);
    throw DataException(msg);
  }
}

SetupMatrixRule* SetupMatrix::calculateSetup(const PooledString& oldsetup,
                                             const PooledString& newsetup,
                                             Resource* res) const {
  // No need to look
  if (oldsetup == newsetup) return nullptr;

  // Look up in the cache
  auto key = make_pair(oldsetup, newsetup);
  auto val = cachedChangeovers.find(key);
  if (val != cachedChangeovers.end()) return val->second;

  // Loop through all rules
  string from_to = (oldsetup);
  from_to.append(" to ");
  from_to.append(newsetup);
  for (auto curRule = firstRule; curRule; curRule = curRule->nextRule)
    if (curRule->matches(from_to)) {
      const_cast<cachedrules&>(cachedChangeovers)[key] = curRule;
      return curRule;
    }

  // No matching rule was found - create a invalid-data problem
  if (res) {
    stringstream o;
    o << "No conversion from '" << oldsetup << "' to '" << newsetup
      << "' defined in setup matrix '" << getName() << "'";
    new ProblemInvalidData(res, o.str(), "resource", Date::infinitePast,
                           Date::infiniteFuture, true);
  }
  auto norule = const_cast<SetupMatrixRuleDefault*>(&ChangeOverNotAllowed);
  const_cast<cachedrules&>(cachedChangeovers)[key] = norule;
  return norule;
}

PyObject* SetupMatrix::calculateSetupPython(PyObject* self, PyObject* args) {
  // Pick up the 2 setup arguments
  char* pysetup_1;
  char* pysetup_2;
  if (!PyArg_ParseTuple(args, "|ss:calculateSetup", &pysetup_1, &pysetup_2))
    return nullptr;

  try {
    PooledString setup_1(pysetup_1);
    PooledString setup_2(pysetup_2);
    return PythonData(
        static_cast<SetupMatrix*>(self)->calculateSetup(setup_1, setup_2));
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

}  // namespace frepple
