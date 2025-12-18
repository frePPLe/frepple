/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
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

template <class Skill>
Tree utils::HasName<Skill>::st;
const MetaCategory* Skill::metadata;
const MetaClass* SkillDefault::metadata;

int Skill::initialize() {
  // Initialize the metadata
  metadata =
      MetaCategory::registerCategory<Skill>("skill", "skills", reader, finder);
  registerFields<Skill>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<Skill>::initialize();
}

int SkillDefault::initialize() {
  // Initialize the metadata
  SkillDefault::metadata = MetaClass::registerClass<SkillDefault>(
      "skill", "skill_default", Object::create<SkillDefault>, true);

  // Initialize the Python class
  return FreppleClass<SkillDefault, Skill>::initialize();
}

Skill::~Skill() {
  // The ResourceSkill objects are automatically deleted by the destructor
  // of the Association list class.

  // Clean up the references on the load models
  for (auto& o : Operation::all())
    for (auto& l : o.getLoads())
      if (l.getSkill() == this) const_cast<Load&>(l).setSkill(nullptr);
}

}  // namespace frepple
