/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007 by Johan De Taeye                                    *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Lesser General Public License as published   *
 * by the Free Software Foundation; either version 2.1 of the License, or  *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser *
 * General Public License for more details.                                *
 *                                                                         *
 * You should have received a copy of the GNU Lesser General Public        *
 * License along with this library; if not, write to the Free Software     *
 * Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{


DECLARE_EXPORT Plan* Plan::thePlan;


DECLARE_EXPORT Plan::~Plan()
{
  // Closing the logfile
  Environment::setLogFile("");

  // Clear the pointer to this singleton object
  thePlan = NULL;
}


DECLARE_EXPORT void Plan::setCurrent (Date l)
{
  // Update the time
  cur_Date = l;

  // Let all operationplans check for new ProblemBeforeCurrent and
  // ProblemBeforeFence problems.
  for (Operation::iterator i = Operation::begin(); i != Operation::end(); ++i)
    i->setChanged();
}


DECLARE_EXPORT void Plan::writeElement (XMLOutput *o, const Keyword& tag, mode m) const
{
  // No references
  assert(m != REFERENCE);

  // Opening tag
  if (m!=NOHEADER) o->BeginObject(tag);

  // Write all own fields
  o->writeElement(Tags::tag_name, name);
  o->writeElement(Tags::tag_description, descr);
  o->writeElement(Tags::tag_current, cur_Date);
  o->writeElement(Tags::tag_logfile, Environment::getLogFile());
  Plannable::writeElement(o, tag);

  // Persist all categories
  MetaCategory::persist(o);

  o->EndObject(tag);
}


DECLARE_EXPORT void Plan::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_current))
    setCurrent(pElement.getDate());
  else if (pAttr.isA(Tags::tag_description))
    pElement >> descr;
  else if (pAttr.isA(Tags::tag_name))
    pElement >> name;
  else if (pAttr.isA(Tags::tag_logfile))
    Environment::setLogFile(pElement.getString());
  else
    Plannable::endElement(pIn, pAttr, pElement);
}


DECLARE_EXPORT void Plan::beginElement (XMLInput& pIn, const Attribute& pAttr)
{
  const MetaCategory *cat = MetaCategory::findCategoryByGroupTag(pIn.getParentElement().first.getHash());
  if (cat)
  {
    if (cat->readFunction)
      // Hand over control to a registered read controller
      pIn.readto(cat->readFunction(cat,pIn.getAttributes()));
    else
      // There is no controller available.
      // This piece of code will be used to skip pieces of the XML file that
      // Frepple doesn't need to be understand
      pIn.IgnoreElement();
  }
}


int PythonPlan::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = getType();
  x.setName("parameters");
  x.setDoc("frePPLe global settings");
  x.supportgetattro();
  x.supportsetattro();
  int tmp =x.typeReady(m);

  // Add access to the information with a global attribute.
  // A pythonplan object is leaking.
  return PyModule_AddObject(m, "settings", new PythonPlan) + tmp;
}


DECLARE_EXPORT PyObject* PythonPlan::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_name))
    return PythonObject(Plan::instance().getName());
  if (attr.isA(Tags::tag_description))
    return PythonObject(Plan::instance().getDescription());
  if (attr.isA(Tags::tag_current))
    return PythonObject(Plan::instance().getCurrent());
  if (attr.isA(Tags::tag_logfile))
    return PythonObject(Environment::getLogFile());
  return NULL;
}


DECLARE_EXPORT int PythonPlan::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    Plan::instance().setName(field.getString());  
  else if (attr.isA(Tags::tag_description))
    Plan::instance().setDescription(field.getString());
  else if (attr.isA(Tags::tag_current))
    Plan::instance().setCurrent(field.getDate()); 
  else if (attr.isA(Tags::tag_logfile))
    Environment::setLogFile(field.getString());
  else
    return -1; // Error
  return 0;  // OK
}

}
