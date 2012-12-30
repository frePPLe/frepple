/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba                 *
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

template<class Skill> DECLARE_EXPORT Tree utils::HasName<Skill>::st;
DECLARE_EXPORT const MetaCategory* Skill::metadata;
DECLARE_EXPORT const MetaClass* SkillDefault::metadata;


int Skill::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("skill", "skills", reader, writer);

  // Initialize the Python class
  FreppleCategory<Skill>::getType().addMethod("addresource", addPythonResource, 
    METH_VARARGS, "add a new resource to the skill");
  return FreppleCategory<Skill>::initialize();
}


int SkillDefault::initialize()
{
  // Initialize the metadata
  SkillDefault::metadata = new MetaClass(
    "skill",
    "skill_default",
    Object::createString<SkillDefault>,
    true);

  // Initialize the Python class
  return FreppleClass<SkillDefault,Skill>::initialize()
    + SkillResourceIterator::initialize()
    + ResourceSkillIterator::initialize();
}


DECLARE_EXPORT void Skill::addResource(Resource* res)
{
  // Check if already assigned
  for (resourcelist::const_iterator i=resources.begin(); i!= resources.end(); ++i)
    if (*i == res) return;  // Silently ignore double assignment

  // Update data structure on the skill and resource
  resources.push_back(res);
  const_cast<Resource::skilllist&>(res->getSkills()).push_back(this);
}


DECLARE_EXPORT void Skill::deleteResource(Resource* res)
{
  // You're joking?
  if (!res) return;

  for (resourcelist::iterator i=resources.begin(); i!= resources.end(); ++i)
    if (*i == res) 
    {
      // Remove from resource list on the skill model
      resources.erase(i);
      for (Resource::skilllist::const_iterator j = res->getSkills().begin(); 
        j != res->getSkills().end(); ++j)
          if (*j == this) 
          {
            // Remove from the skill list on the resource model
            const_cast<Resource::skilllist&>(res->getSkills()).erase(j);
            // Done...
            return;
          }
      throw LogicException("Inconsistent skill data");
    }
  throw DataException("Resource doesn't have this skill");
}


PyObject* Skill::addPythonResource(PyObject* self, PyObject* args)
{
  try
  {
    // Pick up the calendar
    Skill *s = NULL;
    PythonObject c(self);
    if (c.check(SkillDefault::metadata))
      s = static_cast<SkillDefault*>(self);
    else
      throw LogicException("Invalid skill type");

    // Parse the arguments
    PyObject* pyresource = NULL;
    if (!PyArg_ParseTuple(args, "|O:addresource", &pyresource))
      return NULL;
    if (!PyObject_TypeCheck(pyresource, Resource::metadata->pythonClass))
      throw DataException("Expecting resource argument");
    else
      s->addResource(static_cast<Resource*>(pyresource));

    // Return value
    return Py_BuildValue("");
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
}


DECLARE_EXPORT void Skill::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
{
  // Write a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }

  // Write the complete object
  if (m != NOHEADER) o->BeginObject(tag, Tags::tag_name, XMLEscape(getName()));

  // Write the resources having this skill
  if (!resources.empty())
  {
    o->BeginObject(Tags::tag_resources);
    for (resourcelist::const_iterator i=resources.begin(); i!= resources.end(); i++)
      (*i)->writeElement(o, Tags::tag_resource, REFERENCE);
    o->EndObject(Tags::tag_resources);
  }

  // That was it
  o->EndObject(tag);
}


DECLARE_EXPORT void Skill::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(Tags::tag_resource)
      && pIn.getParentElement().first.isA(Tags::tag_resources))
    pIn.readto( Resource::reader(Resource::metadata,pIn.getAttributes()) );
}


DECLARE_EXPORT void Skill::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_resource))
  {
    Resource * r = dynamic_cast<Resource*>(pIn.getPreviousObject());
    if (r) addResource(r);
    else throw LogicException("Incorrect object type during read operation");
  }
}


DECLARE_EXPORT Skill::~Skill()
{
  // Clean up data structures on the resource models
  while (!resources.empty())
    deleteResource(resources.front());

  // Clean up the references on the load models
  for (Operation::iterator o = Operation::begin(); o != Operation::end(); ++o)
    for(Operation::loadlist::const_iterator l = o->getLoads().begin();
      l != o->getLoads().end(); ++l)
      if (l->getSkill() == this)
        const_cast<Load&>(*l).setSkill(NULL);
}


DECLARE_EXPORT PyObject* Skill::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_name))
    return PythonObject(getName());
  if (attr.isA(Tags::tag_resources))
    return new SkillResourceIterator(this);
  return NULL;
}


DECLARE_EXPORT int Skill::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    setName(field.getString());
  else
    return -1;  // Error
  return 0;  // OK
}


int SkillResourceIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<SkillResourceIterator>::getType();
  x.setName("skillResourceIterator");
  x.setDoc("frePPLe iterator for resources on skills");
  x.supportiter();
  return x.typeReady();
}


PyObject* SkillResourceIterator::iternext()
{
  if (cur == skill->getResources().end()) return NULL;
  PyObject *result = *(&*(cur++));
  Py_INCREF(result);
  return result;
}


int ResourceSkillIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<ResourceSkillIterator>::getType();
  x.setName("resourceSkillIterator");
  x.setDoc("frePPLe iterator for skills on resources");
  x.supportiter();
  return x.typeReady();
}


PyObject* ResourceSkillIterator::iternext()
{
  if (cur == resource->getSkills().end()) return NULL;
  PyObject *result = *(&*(cur++));
  Py_INCREF(result);
  return result;
}

}
