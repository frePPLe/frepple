/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bvba                                 *
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
DECLARE_EXPORT const MetaClass* ResourceSkillDefault::metadata;


int ResourceSkill::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<ResourceSkill>("resourceskill", "resourceskills", MetaCategory::ControllerDefault, writer);
  registerFields<ResourceSkill>(const_cast<MetaCategory*>(metadata));
  ResourceSkillDefault::metadata = MetaClass::registerClass<ResourceSkillDefault>(
    "resourceskill", "resourceskill", Object::create<ResourceSkillDefault>, true
    );

  // Initialize the Python class
  PythonType& x = FreppleCategory<ResourceSkill>::getPythonType();
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


DECLARE_EXPORT ResourceSkill::~ResourceSkill()
{
  // Delete the associated from the related objects
  if (getResource()) getResource()->skills.erase(this);
  if (getSkill()) getSkill()->resources.erase(this);
}


void ResourceSkill::writer(const MetaCategory* c, Serializer* o)
{
  bool first = true;
  for (Resource::iterator i = Resource::begin(); i != Resource::end(); ++i)
    for (Resource::skilllist::const_iterator j = i->getSkills().begin(); j != i->getSkills().end(); ++j)
    {
      if (first)
      {
        o->BeginList(Tags::resourceskills);
        first = false;
      }
      // We use the FULL mode, to force the resource skills being written regardless
      // of the depth in the XML tree.
      o->writeElement(Tags::resourceskill, &*j, FULL);
    }
  if (!first) o->EndList(Tags::resourceskills);
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
    int q2 = q1 ? PythonData(q1).getInt() : 1;

    // Pick up the effective dates
    DateRange eff;
    PyObject* eff_start = PyDict_GetItemString(kwds,"effective_start");
    if (eff_start)
    {
      PythonData d(eff_start);
      eff.setStart(d.getDate());
    }
    PyObject* eff_end = PyDict_GetItemString(kwds,"effective_end");
    if (eff_end)
    {
      PythonData d(eff_end);
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
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        Attribute attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::effective_end) && !attr.isA(Tags::effective_start)
          && !attr.isA(Tags::skill) && !attr.isA(Tags::resource)
          && !attr.isA(Tags::priority) && !attr.isA(Tags::type)
          && !attr.isA(Tags::action))
        {
          const MetaFieldBase* fmeta = l->getType().findField(attr.getHash());
          if (!fmeta && l->getType().category)
            fmeta = l->getType().category->findField(attr.getHash());
          if (fmeta)
            // Update the attribute
            fmeta->setField(l, field);
          else
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
  PythonType& x = PythonExtension<ResourceSkillIterator>::getPythonType();
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
