/***************************************************************************
 *                                                                         *
 * Copyright (C) 2009-2013 by Johan De Taeye, frePPLe bvba                 *
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
DECLARE_EXPORT const MetaCategory* SetupMatrix::Rule::metadata;


int SetupMatrix::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("setupmatrix", "setupmatrices", reader, writer);

  // Initialize the Python class
  FreppleCategory<SetupMatrix>::getType().addMethod("addRule",
    addPythonRule, METH_VARARGS | METH_KEYWORDS, "add a new setup rule");
  return FreppleCategory<SetupMatrix>::initialize()
      + Rule::initialize()
      + SetupMatrixRuleIterator::initialize();
}


int SetupMatrix::Rule::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("setupmatrixrule", "setupmatrixrules");

  // Initialize the Python class
  PythonType& x = PythonExtension<SetupMatrix::Rule>::getType();
  x.setName("setupmatrixrule");
  x.setDoc("frePPLe setupmatrixrule");
  x.supportgetattro();
  x.supportsetattro();
  const_cast<MetaCategory*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


int SetupMatrixDefault::initialize()
{
  // Initialize the metadata
  SetupMatrixDefault::metadata = new MetaClass(
    "setupmatrix",
    "setupmatrix_default",
    Object::createString<SetupMatrixDefault>, true);

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


DECLARE_EXPORT void SetupMatrix::writeElement(Serializer *o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write source field
  o->writeElement(Tags::tag_source, getSource());

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write all rules
  o->BeginList (Tags::tag_rules);
  for (RuleIterator i = beginRules(); i != endRules(); ++i)
    // We use the FULL mode, to force the rules being written regardless
    // of the depth in the XML tree.
    o->writeElement(Tags::tag_rule, *i, FULL);
  o->EndList(Tags::tag_rules);

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void SetupMatrix::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(Tags::tag_rule)
      && pIn.getParentElement().first.isA(Tags::tag_rules))
    // A new rule
    pIn.readto(createRule(pIn.getAttributes()));
  else
    PythonDictionary::read(pIn, pAttr, getDict());
}


DECLARE_EXPORT SetupMatrix::Rule* SetupMatrix::createRule(const AttributeList& atts)
{
  // Pick up the start, end and name attributes
  int priority = atts.get(Tags::tag_priority)->getInt();

  // Check for existence of a rule with the same priority
  Rule* result = firstRule;
  while (result && priority > result->priority)
    result = result->nextRule;
  if (result && result->priority != priority) result = NULL;

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
      result = new Rule(this, priority);
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
        result = new Rule(this, priority);
      return result;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}


DECLARE_EXPORT void SetupMatrix::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_source))
    setSource(pElement.getString());
}


DECLARE_EXPORT PyObject* SetupMatrix::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_name))
    return PythonObject(getName());
  if (attr.isA(Tags::tag_rules))
    return new SetupMatrixRuleIterator(this);
  if (attr.isA(Tags::tag_source))
    return PythonObject(getSource());
  return NULL;
}


DECLARE_EXPORT int SetupMatrix::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    setName(field.getString());
  else if (attr.isA(Tags::tag_source))
    setSource(field.getString());
  else
    return -1;  // Error
  return 0;
}


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
    Rule * r = new Rule(matrix, prio);
    if (pyfrom) r->setFromSetup(PythonObject(pyfrom).getString());
    if (pyto) r->setToSetup(PythonObject(pyfrom).getString());
    r->setDuration(duration);
    r->setCost(cost);
    return PythonObject(r);
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
}


DECLARE_EXPORT SetupMatrix::Rule::Rule(SetupMatrix *s, int p)
  : cost(0), priority(p), matrix(s), nextRule(NULL), prevRule(NULL)
{
  // Validate the arguments
  if (!matrix) throw DataException("Can't add a rule to NULL setup matrix");

  // Find the right place in the list
  Rule *next = matrix->firstRule, *prev = NULL;
  while (next && p > next->priority)
  {
    prev = next;
    next = next->nextRule;
  }

  // Duplicate priority
  if (next && next->priority == p)
    throw DataException("Multiple rules with identical priority in setup matrix");

  // Maintain linked list
  nextRule = next;
  prevRule = prev;
  if (prev) prev->nextRule = this;
  else matrix->firstRule = this;
  if (next) next->prevRule = this;

  // Initialize the Python type
  initType(metadata);
}


DECLARE_EXPORT SetupMatrix::Rule::~Rule()
{
  // Maintain linked list
  if (nextRule) nextRule->prevRule = prevRule;
  if (prevRule) prevRule->nextRule = nextRule;
  else matrix->firstRule = nextRule;
}


DECLARE_EXPORT void SetupMatrix::Rule::writeElement
(Serializer* o, const Keyword& tag, mode m) const
{
  o->BeginObject(tag, Tags::tag_priority, priority);
  if (!from.empty()) o->writeElement(Tags::tag_fromsetup, from);
  if (!to.empty()) o->writeElement(Tags::tag_tosetup, to);
  if (duration) o->writeElement(Tags::tag_duration, duration);
  if (cost) o->writeElement(Tags::tag_cost, cost);
  o->EndObject(tag);
}


DECLARE_EXPORT void SetupMatrix::Rule::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_priority))
    setPriority(pElement.getInt());
  else if (pAttr.isA(Tags::tag_fromsetup))
    setFromSetup(pElement.getString());
  else if (pAttr.isA(Tags::tag_tosetup))
    setToSetup(pElement.getString());
  else if (pAttr.isA(Tags::tag_duration))
    setDuration(pElement.getTimeperiod());
  else if (pAttr.isA(Tags::tag_cost))
    setCost(pElement.getDouble());
}


DECLARE_EXPORT PyObject* SetupMatrix::Rule::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_priority))
    return PythonObject(priority);
  if (attr.isA(Tags::tag_setupmatrix))
    return PythonObject(matrix);
  if (attr.isA(Tags::tag_fromsetup))
    return PythonObject(from);
  if (attr.isA(Tags::tag_tosetup))
    return PythonObject(to);
  if (attr.isA(Tags::tag_duration))
    return PythonObject(duration);
  if (attr.isA(Tags::tag_cost))
    return PythonObject(cost);
  return NULL;
}


DECLARE_EXPORT int SetupMatrix::Rule::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_priority))
    setPriority(field.getInt());
  else if (attr.isA(Tags::tag_fromsetup))
    setFromSetup(field.getString());
  else if (attr.isA(Tags::tag_tosetup))
    setToSetup(field.getString());
  else if (attr.isA(Tags::tag_duration))
    setDuration(field.getTimeperiod());
  else if (attr.isA(Tags::tag_cost))
    setCost(field.getDouble());
  else
    return -1;  // Error
  return 0;  // OK
}


DECLARE_EXPORT void SetupMatrix::Rule::setPriority(const int n)
{
  // Update the field
  priority = n;

  // Check ordering on the left
  while (prevRule && priority < prevRule->priority)
  {
    Rule* next = nextRule;
    Rule* prev = prevRule;
    if (prev && prev->prevRule) prev->prevRule->nextRule = this;
    else matrix->firstRule = this;
    if (prev) prev->nextRule = nextRule;
    nextRule = prev;
    prevRule = prev ? prev->prevRule : NULL;
    if (next && next->nextRule) next->nextRule->prevRule = prev;
    if (next) next->prevRule = prev;
    if (prev) prev->prevRule = this;
  }

  // Check ordering on the right
  while (nextRule && priority > nextRule->priority)
  {
    Rule* next = nextRule;
    Rule* prev = prevRule;
    nextRule = next->nextRule;
    if (next && next->nextRule) next->nextRule->prevRule = this;
    if (prev) prev->nextRule = next;
    if (next) next->nextRule = this;
    if (next) next->prevRule = prev;
    prevRule = next;
  }

  // Check for duplicate priorities
  if ((prevRule && prevRule->priority == priority)
      || (nextRule && nextRule->priority == priority))
  {
    ostringstream o;
    o << "Duplicate priority " << priority << " in setup matrix '"
      << matrix->getName() << "'";
    throw DataException(o.str());
  }
}


int SetupMatrixRuleIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<SetupMatrixRuleIterator>::getType();
  x.setName("setupmatrixRuleIterator");
  x.setDoc("frePPLe iterator for setupmatrix rules");
  x.supportiter();
  return x.typeReady();
}


PyObject* SetupMatrixRuleIterator::iternext()
{
  if (currule == matrix->endRules()) return NULL;
  PyObject *result = &*(currule++);
  Py_INCREF(result);
  return result;
}


DECLARE_EXPORT SetupMatrix::Rule* SetupMatrix::calculateSetup
(const string oldsetup, const string newsetup) const
{
  // No need to look
  if (oldsetup == newsetup) return NULL;

  // Loop through all rules
  for (Rule *curRule = firstRule; curRule; curRule = curRule->nextRule)
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
