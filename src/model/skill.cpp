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

template<class Skill> DECLARE_EXPORT Tree utils::HasName<Skill>::st;
DECLARE_EXPORT const MetaCategory* Skill::metadata;
DECLARE_EXPORT const MetaClass* SkillDefault::metadata;


int Skill::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("skill", "skills", reader, writer);

  // Initialize the Python class
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
  return FreppleClass<SkillDefault,Skill>::initialize();
}


DECLARE_EXPORT void Skill::writeElement(Serializer* o, const Keyword& tag, mode m) const
{
  // Write a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL)
    o->BeginObject(tag, Tags::tag_name, getName());

  // Write source field
  o->writeElement(Tags::tag_source, getSource());

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void Skill::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(Tags::tag_resourceskill)
      && pIn.getParentElement().first.isA(Tags::tag_resourceskills))
  {
    ResourceSkill *s =
      dynamic_cast<ResourceSkill*>(MetaCategory::ControllerDefault(ResourceSkill::metadata,pIn.getAttributes()));
    if (s) s->setSkill(this);
    pIn.readto(s);
  }
  else
    PythonDictionary::read(pIn, pAttr, getDict());
}


DECLARE_EXPORT void Skill::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_source))
    setSource(pElement.getString());
}


DECLARE_EXPORT Skill::~Skill()
{
  // The ResourceSkill objects are automatically deleted by the destructor
  // of the Association list class.

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
  if (attr.isA(Tags::tag_resourceskills))
    return new ResourceSkillIterator(this);
  if (attr.isA(Tags::tag_source))
    return PythonObject(getSource());
  return NULL;
}


DECLARE_EXPORT int Skill::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    setName(field.getString());
  else if (attr.isA(Tags::tag_source))
    setSource(field.getString());
  else
    return -1;  // Error
  return 0;  // OK
}


}
