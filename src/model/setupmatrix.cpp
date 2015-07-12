/***************************************************************************
 *                                                                         *
 * Copyright (C) 2009-2015 by frePPLe bvba                                 *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            *
 * GNU Affero General Public License for more details.                     *
 *                                                                         *
 * You should have received a copy of the GNU Affero General Public        *
 * License along with this program.                                        *
 * If not, see <http://www.gnu.org/licenses/>.                             *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{

template<class SetupMatrix> DECLARE_EXPORT Tree utils::HasName<SetupMatrix>::st;
DECLARE_EXPORT const MetaCategory* SetupMatrix::metadata;
DECLARE_EXPORT const MetaClass* SetupMatrixDefault::metadata;
DECLARE_EXPORT const MetaClass* SetupMatrixRule::metadata;
DECLARE_EXPORT const MetaCategory* SetupMatrixRule::metacategory;


int SetupMatrix::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<SetupMatrix>("setupmatrix", "setupmatrices", reader, finder);
  registerFields<SetupMatrix>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  FreppleCategory<SetupMatrix>::getPythonType().addMethod("addRule",
    addPythonRule, METH_VARARGS | METH_KEYWORDS, "add a new setup rule");
  return FreppleCategory<SetupMatrix>::initialize();
}


int SetupMatrixRule::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<SetupMatrixRule>(
    "setupmatrixrule", "setupmatrixrules", MetaCategory::ControllerDefault
    );
  registerFields<SetupMatrixRule>(const_cast<MetaCategory*>(metacategory));
  metadata = MetaClass::registerClass<SetupMatrixRule>(
    "setupmatrixrule", "setupmatrixrule", Object::create<SetupMatrixRule>, true
    );

  // Initialize the Python class
  PythonType& x = PythonExtension<SetupMatrixRule>::getPythonType();
  x.setName("setupmatrixrule");
  x.setDoc("frePPLe setupmatrixrule");
  x.supportgetattro();
  x.supportsetattro();
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


int SetupMatrixDefault::initialize()
{
  // Initialize the metadata
  SetupMatrixDefault::metadata = MetaClass::registerClass<SetupMatrixDefault>(
    "setupmatrix",
    "setupmatrix_default",
    Object::create<SetupMatrixDefault>, true);

  // Initialize the Python class
  return FreppleClass<SetupMatrixDefault,SetupMatrix>::initialize();
}


DECLARE_EXPORT SetupMatrix::~SetupMatrix()
{
  // Destroy the rules.
  // Note that the rule destructor updates the firstRule field.
  while (firstRule) delete firstRule;

  // Remove all references to this setup matrix from resources
  for (Resource::iterator m = Resource::begin(); m != Resource::end(); ++m)
    if (m->getSetupMatrix() == this) m->setSetupMatrix(NULL);
}


/*
DECLARE_EXPORT SetupMatrixRule* SetupMatrix::createRule(const DataValueDict& atts)  TODO Review for use as read controller for rules
{
  // Pick up the priority attributes
  const DataValue *val = atts.get(Tags::priority);
  int priority = val ? val->getInt() : 0;

  // Check for existence of a rule with the same priority
  SetupMatrixRule* result = firstRule;
  while (result && priority > result->priority)
    result = result->nextRule;
  if (result && result->priority != priority)
    result = NULL;

  // Pick up the action attribute and update the rule accordingly
  switch (MetaClass::decodeAction(atts))
  {
    case ADD:
      // Only additions are allowed
      if (result)
      {
        ostringstream o;
        o << "Rule with priority "  << priority
          << " already exists in setup matrix '" << getName() << "'";
        throw DataException(o.str());
      }
      result = new SetupMatrixRule(this, priority);
      return result;
    case CHANGE:
      // Only changes are allowed
      if (!result)
      {
        ostringstream o;
        o << "No rule with priority " << priority
          << " exists in setup matrix '" << getName() << "'";
        throw DataException(o.str());
      }
      return result;
    case REMOVE:
      // Delete the entity
      if (!result)
      {
        ostringstream o;
        o << "No rule with priority " << priority
          << " exists in setup matrix '" << getName() << "'";
        throw DataException(o.str());
      }
      else
      {
        // Delete it
        delete result;
        return NULL;
      }
    case ADD_CHANGE:
      if (!result)
        // Adding a new rule
        result = new SetupMatrixRule(this, priority);
      return result;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}
*/

DECLARE_EXPORT PyObject* SetupMatrix::addPythonRule(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the setup matrix
    SetupMatrix *matrix = static_cast<SetupMatrix*>(self);
    if (!matrix) throw LogicException("Can't add a rule to a NULL setupmatrix");

    // Parse the arguments
    int prio = 0;
    PyObject *pyfrom = NULL;
    PyObject *pyto = NULL;
    long duration = 0;
    double cost = 0;
    static const char *kwlist[] = {"priority", "fromsetup", "tosetup", "duration", "cost", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwdict,
        "i|ssld:addRule",
        const_cast<char**>(kwlist), &prio, &pyfrom, &pyto, &duration, &cost))
      return NULL;

    // Add the new rule
    SetupMatrixRule *r = new SetupMatrixRule();
    r->setPriority(prio);
    r->setSetupMatrix(matrix);
    if (pyfrom) r->setFromSetup(PythonData(pyfrom).getString());
    if (pyto) r->setToSetup(PythonData(pyfrom).getString());
    r->setDuration(duration);
    r->setCost(cost);
    return PythonData(r);
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
}


DECLARE_EXPORT void SetupMatrixRule::setSetupMatrix(SetupMatrix *s)
{
  // Validate the arguments
  if (matrix)
    throw DataException("Can't reassign setup matrix matrix once assigned");
  if (!s)
    throw DataException("Can't update setup matrix to NULL");

  // Assign the pointer
  matrix = s;

  // Find the right place in the list
  SetupMatrixRule *next = matrix->firstRule, *prev = NULL;
  while (next && priority > next->priority)
  {
    prev = next;
    next = next->nextRule;
  }

  // Duplicate priority
  if (next && next->priority == priority)
    throw DataException("Multiple rules with identical priority in setup matrix");

  // Maintain linked list
  nextRule = next;
  prevRule = prev;
  if (prev)
    prev->nextRule = this;
  else
    matrix->firstRule = this;
  if (next)
    next->prevRule = this;
}


DECLARE_EXPORT SetupMatrixRule::~SetupMatrixRule()
{
  // Maintain linked list
  if (nextRule) nextRule->prevRule = prevRule;
  if (prevRule) prevRule->nextRule = nextRule;
  else matrix->firstRule = nextRule;
}


DECLARE_EXPORT void SetupMatrixRule::setPriority(const int n)
{
  if (n == priority)
    return;
  if (!matrix)
  {
    // As long as there is no matrix assigned, anything goes
    priority = n;
    return;
  }

  // Check for duplicate priorities, before making any changes
  for (SetupMatrixRule *i = matrix->firstRule; i; i = i->nextRule)
    if (i->priority == n)
    {
      ostringstream o;
      o << "Rule with priority " << priority << " in setup matrix '"
        << matrix->getName() << "' already exists";
      throw DataException(o.str());
    }
    else if (i->priority > n)
      break;

  // Update the field
  priority = n;

  // Check ordering on the left
  while (prevRule && priority < prevRule->priority)
  {
    SetupMatrixRule* next = nextRule;
    SetupMatrixRule* prev = prevRule;
    if (prev->prevRule)
      prev->prevRule->nextRule = this;
    else
      matrix->firstRule = this;
    prev->nextRule = nextRule;
    nextRule = prev;
    prevRule = prev->prevRule;
    if (next)
      next->prevRule = prev;
    prev->prevRule = this;
  }

  // Check ordering on the right
  while (nextRule && priority > nextRule->priority)
  {
    SetupMatrixRule* next = nextRule;
    SetupMatrixRule* prev = prevRule;
    nextRule = next->nextRule;
    if (next->nextRule)
      next->nextRule->prevRule = this;
    if (prev)
      prev->nextRule = next;
    else
      matrix->firstRule = next;
    next->nextRule = this;
    next->prevRule = prev;
    prevRule = next;
  }
}


DECLARE_EXPORT SetupMatrixRule* SetupMatrix::calculateSetup
(const string oldsetup, const string newsetup) const
{
  // No need to look
  if (oldsetup == newsetup) return NULL;

  // Loop through all rules
  for (SetupMatrixRule *curRule = firstRule; curRule; curRule = curRule->nextRule)
  {
    // Need a match on the fromsetup
    if (!curRule->getFromSetup().empty()
        && !matchWildcard(curRule->getFromSetup().c_str(), oldsetup.c_str()))
      continue;
    // Need a match on the tosetup
    if (!curRule->getToSetup().empty()
        && !matchWildcard(curRule->getToSetup().c_str(), newsetup.c_str()))
      continue;
    // Found a match
    return curRule;
  }

  // No matching rule was found
  logger << "Warning: Conversion from '" << oldsetup << "' to '" << newsetup
      << "' undefined in setup matrix '" << getName() << endl;
  return NULL;
}

} // end namespace
