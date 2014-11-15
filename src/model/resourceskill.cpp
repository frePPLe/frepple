/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
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

DECLARE_EXPORT const MetaCategory* ResourceSkill::metadata;


int ResourceSkill::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("resourceskill", "resourceskills", MetaCategory::ControllerDefault, writer);
  const_cast<MetaCategory*>(metadata)->registerClass(
    "resourceskill","resourceskill",true,Object::createDefault<ResourceSkill>
  );

  // Initialize the Python class
  PythonType& x = FreppleCategory<ResourceSkill>::getType();
  x.setName("resourceskill");
  x.setDoc("frePPLe resourceskill");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaCategory*>(ResourceSkill::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT ResourceSkill::ResourceSkill(Skill* s, Resource* r, int u)
{
  setSkill(s);
  setResource(r);
  setPriority(u);
  initType(metadata);
  try { validate(ADD); }
  catch (...)
  {
    if (getSkill()) getSkill()->resources.erase(this);
    if (getResource()) getResource()->skills.erase(this);
    resetReferenceCount();
    throw;
  }
}


DECLARE_EXPORT ResourceSkill::ResourceSkill(Skill* s, Resource* r, int u, DateRange e)
{
  setSkill(s);
  setResource(r);
  setPriority(u);
  setEffective(e);
  initType(metadata);
  try { validate(ADD); }
  catch (...)
  {
    if (getSkill()) getSkill()->resources.erase(this);
    if (getResource()) getResource()->skills.erase(this);
    resetReferenceCount();
    throw;
  }
}


void ResourceSkill::writer(const MetaCategory* c, XMLOutput* o)
{
  bool first = true;
  for (Resource::iterator i = Resource::begin(); i != Resource::end(); ++i)
    for (Resource::skilllist::const_iterator j = i->getSkills().begin(); j != i->getSkills().end(); ++j)
    {
      if (first)
      {
        o->BeginObject(Tags::tag_resourceskills);
        first = false;
      }
      // We use the FULL mode, to force the flows being written regardless
      // of the depth in the XML tree.
      o->writeElement(Tags::tag_resourceskill, &*j, FULL);
    }
  if (!first) o->EndObject(Tags::tag_resourceskills);
}


DECLARE_EXPORT void ResourceSkill::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
{
  // If the resourceskill has already been saved, no need to repeat it again
  // A 'reference' to a load is not useful to be saved.
  if (m == REFERENCE) return;
  assert(m != NOHEAD && m != NOHEADTAIL);

  o->BeginObject(tag);

  // If the resourceskill is defined inside of a resource tag, we don't need to save
  // the resource. Otherwise we do save it...
  if (!dynamic_cast<Resource*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_resource, getResource());

  // If the resourceskill is defined inside of a skill tag, we don't need to save
  // the skill. Otherwise we do save it...
  if (!dynamic_cast<Skill*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_skill, getSkill());

  // Write the priority and effective daterange
  if (getPriority()!=1) o->writeElement(Tags::tag_priority, getPriority());
  if (getEffective().getStart() != Date::infinitePast)
    o->writeElement(Tags::tag_effective_start, getEffective().getStart());
  if (getEffective().getEnd() != Date::infiniteFuture)
    o->writeElement(Tags::tag_effective_end, getEffective().getEnd());

  // Write source field
  o->writeElement(Tags::tag_source, getSource());

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void ResourceSkill::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_resource))
    pIn.readto( Resource::reader(Resource::metadata,pIn.getAttributes()) );
  else if (pAttr.isA (Tags::tag_skill))
    pIn.readto( Skill::reader(Skill::metadata,pIn.getAttributes()) );
  else
    PythonDictionary::read(pIn, pAttr, getDict());
}


DECLARE_EXPORT void ResourceSkill::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA (Tags::tag_resource))
  {
    Resource *r = dynamic_cast<Resource*>(pIn.getPreviousObject());
    if (r) setResource(r);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA (Tags::tag_skill))
  {
    Skill *s = dynamic_cast<Skill*>(pIn.getPreviousObject());
    if (s) setSkill(s);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_priority))
    setPriority(pElement.getInt());
  else if (pAttr.isA(Tags::tag_effective_end))
    setEffectiveEnd(pElement.getDate());
  else if (pAttr.isA(Tags::tag_effective_start))
    setEffectiveStart(pElement.getDate());
  else if (pAttr.isA(Tags::tag_source))
    setSource(pElement.getString());
  else if (pAttr.isA(Tags::tag_action))
  {
    delete static_cast<Action*>(pIn.getUserArea());
    pIn.setUserArea(
      new Action(MetaClass::decodeAction(pElement.getString().c_str()))
    );
  }
  else if (pIn.isObjectEnd())
  {
    // The resourceskill data is now all read in. See if it makes sense now...
    Action a = pIn.getUserArea() ?
        *static_cast<Action*>(pIn.getUserArea()) :
        ADD_CHANGE;
    delete static_cast<Action*>(pIn.getUserArea());
    try { validate(a); }
    catch (...)
    {
      delete this;
      throw;
    }
  }
}


DECLARE_EXPORT PyObject* ResourceSkill::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_resource))
    return PythonObject(getResource());
  if (attr.isA(Tags::tag_skill))
    return PythonObject(getSkill());
  if (attr.isA(Tags::tag_priority))
    return PythonObject(getPriority());
  if (attr.isA(Tags::tag_effective_end))
    return PythonObject(getEffective().getEnd());
  if (attr.isA(Tags::tag_effective_start))
    return PythonObject(getEffective().getStart());
  if (attr.isA(Tags::tag_source))
    return PythonObject(getSource());
  return NULL;
}


DECLARE_EXPORT int ResourceSkill::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_resource))
  {
    if (!field.check(Resource::metadata))
    {
      PyErr_SetString(PythonDataException, "resourceskill resource must be of type resource");
      return -1;
    }
    Resource* y = static_cast<Resource*>(static_cast<PyObject*>(field));
    setResource(y);
  }
  else if (attr.isA(Tags::tag_skill))
  {
    if (!field.check(Skill::metadata))
    {
      PyErr_SetString(PythonDataException, "resourceskill skill must be of type skill");
      return -1;
    }
    Skill* y = static_cast<Skill*>(static_cast<PyObject*>(field));
    setSkill(y);
  }
  else if (attr.isA(Tags::tag_priority))
    setPriority(field.getInt());
  else if (attr.isA(Tags::tag_effective_end))
    setEffectiveEnd(field.getDate());
  else if (attr.isA(Tags::tag_effective_start))
    setEffectiveStart(field.getDate());
  else if (attr.isA(Tags::tag_source))
    setSource(field.getString());
  else
    return -1;
  return 0;
}


/** @todo this method implementation is not generic enough and not extendible by subclasses. */
PyObject* ResourceSkill::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Pick up the skill
    PyObject* skill = PyDict_GetItemString(kwds,"skill");
    if (!PyObject_TypeCheck(skill, Skill::metadata->pythonClass))
      throw DataException("resourceskill skill must be of type skill");

    // Pick up the resource
    PyObject* res = PyDict_GetItemString(kwds,"resource");
    if (!PyObject_TypeCheck(res, Resource::metadata->pythonClass))
      throw DataException("resourceskill resource must be of type resource");

    // Pick up the priority
    PyObject* q1 = PyDict_GetItemString(kwds,"priority");
    int q2 = q1 ? PythonObject(q1).getInt() : 1;

    // Pick up the effective dates
    DateRange eff;
    PyObject* eff_start = PyDict_GetItemString(kwds,"effective_start");
    if (eff_start)
    {
      PythonObject d(eff_start);
      eff.setStart(d.getDate());
    }
    PyObject* eff_end = PyDict_GetItemString(kwds,"effective_end");
    if (eff_end)
    {
      PythonObject d(eff_end);
      eff.setEnd(d.getDate());
    }

    // Create the resourceskill
    ResourceSkill *l = new ResourceSkill(
      static_cast<Skill*>(skill),
      static_cast<Resource*>(res),
      q2, eff
    );

    // Iterate over extra keywords, and set attributes.   @todo move this responsibility to the readers...
    if (l)
    {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value))
      {
        PythonObject field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        Attribute attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::tag_effective_end) && !attr.isA(Tags::tag_effective_start)
          && !attr.isA(Tags::tag_skill) && !attr.isA(Tags::tag_resource)
          && !attr.isA(Tags::tag_priority) && !attr.isA(Tags::tag_type)
          && !attr.isA(Tags::tag_action))
        {
          int result = l->setattro(attr, field);
          if (result && !PyErr_Occurred())
            PyErr_Format(PyExc_AttributeError,
                "attribute '%S' on '%s' can't be updated",
                key, Py_TYPE(l)->tp_name);
        }
      };
    }

    // Return the object
    Py_INCREF(l);
    return static_cast<PyObject*>(l);
  }
  catch (...)
  {
    PythonType::evalException();
    return NULL;
  }
}


DECLARE_EXPORT void ResourceSkill::validate(Action action)
{
  // Catch null operation and resource pointers
  Skill *skill = getSkill();
  Resource *res = getResource();
  if (!skill || !res)
  {
    // Invalid load model
    if (!skill && !res)
      throw DataException("Missing resource and kill on a resourceskill");
    else if (!skill)
      throw DataException("Missing skill on a resourceskill on resource '"
          + res->getName() + "'");
    else if (!res)
      throw DataException("Missing resource on a resourceskill on skill '"
          + skill->getName() + "'");
  }

  // Check if a resourceskill with 1) identical resource, 2) identical skill and
  // 3) overlapping effectivity dates already exists
  Skill::resourcelist::const_iterator i = skill->getResources().begin();
  for (; i != skill->getResources().end(); ++i)
    if (i->getResource() == res
        && i->getEffective().overlap(getEffective())
        && &*i != this)
      break;

  // Apply the appropriate action
  switch (action)
  {
    case ADD:
      if (i != skill->getResources().end())
      {
        throw DataException("Resourceskill of '" + res->getName() + "' and '"
            + skill->getName() + "' already exists");
      }
      break;
    case CHANGE:
      throw DataException("Can't update a resourceskill");
    case ADD_CHANGE:
      // ADD is handled in the code after the switch statement
      if (i == skill->getResources().end()) break;
      throw DataException("Can't update a resourceskill");
    case REMOVE:
      // This resourceskill was only used temporarily during the reading process
      delete this;
      if (i == skill->getResources().end())
        // Nothing to delete
        throw DataException("Can't remove nonexistent resourceskill of '"
            + res->getName() + "' and '" + skill->getName() + "'");
      delete &*i;
      return;
  }
}


int ResourceSkillIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<ResourceSkillIterator>::getType();
  x.setName("resourceSkillIterator");
  x.setDoc("frePPLe iterator for resource skills");
  x.supportiter();
  return x.typeReady();
}


PyObject* ResourceSkillIterator::iternext()
{
  PyObject* result;
  if (res)
  {
    // Iterate over skills on a resource
    if (ir == res->getSkills().end()) return NULL;
    result = const_cast<ResourceSkill*>(&*ir);
    ++ir;
  }
  else
  {
    // Iterate over resources having a skill
    if (is == skill->getResources().end()) return NULL;
    result = const_cast<ResourceSkill*>(&*is);
    ++is;
  }
  Py_INCREF(result);
  return result;
}

}
