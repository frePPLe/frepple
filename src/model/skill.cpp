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

template<class Skill> Tree<string> utils::HasName<Skill>::st;
const MetaCategory* Skill::metadata;
const MetaClass* SkillDefault::metadata;


int Skill::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Skill>("skill", "skills", reader, finder);
  registerFields<Skill>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<Skill>::initialize();
}


int SkillDefault::initialize()
{
  // Initialize the metadata
  SkillDefault::metadata = MetaClass::registerClass<SkillDefault>(
    "skill",
    "skill_default",
    Object::create<SkillDefault>,
    true);

  // Initialize the Python class
  return FreppleClass<SkillDefault,Skill>::initialize();
}


Skill::~Skill()
{
  // The ResourceSkill objects are automatically deleted by the destructor
  // of the Association list class.

  // Clean up the references on the load models
  for (Operation::iterator o = Operation::begin(); o != Operation::end(); ++o)
    for(Operation::loadlist::const_iterator l = o->getLoads().begin();
      l != o->getLoads().end(); ++l)
      if (l->getSkill() == this)
        const_cast<Load&>(*l).setSkill(nullptr);
}

}
