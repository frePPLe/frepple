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

template<class SetupMatrix> Tree<string> utils::HasName<SetupMatrix>::st;
const MetaCategory* SetupMatrix::metadata;
const MetaClass* SetupMatrixDefault::metadata;
const MetaClass* SetupMatrixRuleDefault::metadata;
const MetaCategory* SetupMatrixRule::metadata;


int SetupMatrix::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<SetupMatrix>("setupmatrix", "setupmatrices", reader, finder);
  registerFields<SetupMatrix>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<SetupMatrix>::initialize();
}


int SetupMatrixRule::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<SetupMatrixRule>(
    "setupmatrixrule", "setupmatrixrules", reader
    );
  registerFields<SetupMatrixRule>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<SetupMatrixRule>::initialize();;
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


int SetupMatrixRuleDefault::initialize()
{
  // Initialize the metadata
  SetupMatrixRuleDefault::metadata = MetaClass::registerClass<SetupMatrixRuleDefault>(
    "setupmatrixrule", "setupmatrixrule_default",
    Object::create<SetupMatrixRuleDefault>, true
    );

  // Initialize the Python class
  return FreppleClass<SetupMatrixRuleDefault, SetupMatrixRule>::initialize();
}


SetupMatrix::~SetupMatrix()
{
  // Destroy the rules.
  // Note that the rule destructor updates the firstRule field.
  while (firstRule) delete firstRule;

  // Remove all references to this setup matrix from resources
  for (Resource::iterator m = Resource::begin(); m != Resource::end(); ++m)
    if (m->getSetupMatrix() == this) m->setSetupMatrix(nullptr);
}


Object* SetupMatrixRule::reader(
  const MetaClass* cat, const DataValueDict& atts, CommandManager* mgr
)
{
  // Pick up the setupmatrix
  const DataValue* matrix_val = atts.get(Tags::setupmatrix);
  SetupMatrix *matrix = matrix_val ? static_cast<SetupMatrix*>(matrix_val->getObject()) : nullptr;

  // Pick up the priority.
  const DataValue* prio_val = atts.get(Tags::priority);
  int prio = 0;
  if (prio_val)
    prio = prio_val->getInt();

  // Check for existence of a bucket with the same start, end and priority
  SetupMatrixRule* result = nullptr;
  if (matrix)
  {
    auto i = matrix->getRules();
    while (SetupMatrixRule* j = i.next())
      if (j->priority == prio)
      {
        result = j;
        break;
      }
  }

  // Pick up the action attribute and update the bucket accordingly
  switch (MetaClass::decodeAction(atts))
  {
  case ADD:
    // Only additions are allowed
    if (result)
    {
      ostringstream o;
      o << "Rule already exists in setupmatrix '" << matrix << "'";
      throw DataException(o.str());
    }
    result = new SetupMatrixRuleDefault();
    result->setPriority(prio);
    if (matrix)
      result->setSetupMatrix(matrix);
    if (mgr)
      mgr->add(new CommandCreateObject(result));
    return result;
  case CHANGE:
    // Only changes are allowed
    if (!result)
      throw DataException("Rule doesn't exist");
    return result;
  case REMOVE:
    // Delete the entity
    if (!result)
      throw DataException("Rule doesn't exist");
    else
    {
      // Delete it
      delete result;
      return nullptr;
    }
  case ADD_CHANGE:
    if (!result)
    {
      // Adding a new rule
      result = new SetupMatrixRuleDefault();
      result->setPriority(prio);
      if (matrix)
        result->setSetupMatrix(matrix);
      if (mgr)
        mgr->add(new CommandCreateObject(result));
    }
    return result;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}


void SetupMatrixRule::setSetupMatrix(SetupMatrix *s)
{
  if (matrix == s)
    return;

  // Unlink from the previous matrix
  if (matrix)
  {
    if (prevRule)
      prevRule->nextRule = nextRule;
    else
      matrix->firstRule = nextRule;
    if (nextRule)
      nextRule->prevRule = prevRule;
  }

  // Assign the pointer
  matrix = s;

  // Link in the list of buckets of the new calendar
  if (matrix)
  {
    if (matrix->firstRule)
    {
      matrix->firstRule->prevRule = this;
      nextRule = matrix->firstRule;
    }
    matrix->firstRule = this;
    updateSort();
  }
}


SetupMatrixRule::~SetupMatrixRule()
{
  // Maintain linked list
  if (nextRule)
    nextRule->prevRule = prevRule;
  if (prevRule)
    prevRule->nextRule = nextRule;
  else 
    matrix->firstRule = nextRule;
}


void SetupMatrixRule::updateSort()
{
  // Update the position in the list
  if (!matrix) return;
  bool ok = true;
  do
  {
    ok = true;
    if ((nextRule && nextRule->priority == priority)
      || (prevRule && prevRule->priority == priority))
    {
      ostringstream o;
      o << "Duplicate rules with priority " << priority << " in setup matrix '"
        << matrix->getName() << "'";
      throw DataException(o.str());
    }
    else if (nextRule && nextRule->priority < priority)
    {
      // Move a position later in the list
      if (nextRule->nextRule)
        nextRule->nextRule->prevRule = this;
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
    }
    else if (prevRule && prevRule->priority > priority)
    {
      // Move a position earlier in the list
      if (prevRule->prevRule)
        prevRule->prevRule->nextRule = this;
      if (nextRule)
        nextRule->prevRule = prevRule;
      prevRule->nextRule = nextRule;
      nextRule = prevRule;
      SetupMatrixRule* tmp = prevRule->prevRule;
      prevRule->prevRule = this;
      prevRule = tmp;
      ok = false;
    }
  } while (!ok); // Repeat till in place
}


void SetupMatrixRule::setPriority(const int n)
{
  if (n == priority)
    return;
  if (!matrix)
  {
    // As long as there is no matrix assigned, anything goes
    priority = n;
    return;
  }

  // Update the field
  priority = n;

  // Update the list
  updateSort();
}


SetupMatrixRule* SetupMatrix::calculateSetup
(PooledString oldsetup, PooledString newsetup, Resource* res) const
{
  // No need to look
  if (oldsetup == newsetup)
    return nullptr;
  
  // Loop through all rules
  for (SetupMatrixRule *curRule = firstRule; curRule; curRule = curRule->nextRule)
  {
    // Need a match on the fromsetup
    if (!curRule->getFromSetup().empty()
        && !matchWildcard(curRule->getFromSetup(), oldsetup))
      continue;
    // Need a match on the tosetup
    if (!curRule->getToSetup().empty()
        && !matchWildcard(curRule->getToSetup(), newsetup))
      continue;
    // Found a match
    return curRule;
  }

  // No matching rule was found - create a invalid-data problem
  stringstream o;
  o << "No conversion from '" << oldsetup << "' to '" << newsetup
    << "' defined in setup matrix '" << getName() << "'";
  auto probiter = Problem::iterator(res);
  while (Problem* prob = probiter.next())
  {
    if (typeid(*prob) == typeid(ProblemInvalidData) && prob->getDescription() == o.str())
      // Problem already exists
      return const_cast<SetupMatrixRuleDefault*>(&ChangeOverNotAllowed);
  }
  new ProblemInvalidData(
    res, o.str(), "resource", Date::infinitePast, Date::infiniteFuture, 1, true
  );
  return const_cast<SetupMatrixRuleDefault*>(&ChangeOverNotAllowed);
}

} // end namespace
