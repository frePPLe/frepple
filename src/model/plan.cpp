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
    Operation::writepointer(&*i)->setChanged();
}


DECLARE_EXPORT void Plan::writeElement (XMLOutput *o, const XMLtag& tag, mode m) const
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


DECLARE_EXPORT void Plan::endElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_current))
    setCurrent(pElement.getDate());
  else if (pElement.isA(Tags::tag_description))
    pElement >> descr;
  else if (pElement.isA(Tags::tag_name))
    pElement >> name;
  else if (pElement.isA(Tags::tag_logfile))
    Environment::setLogFile(pElement.getString());
  else
    Plannable::endElement(pIn, pElement);
}


DECLARE_EXPORT void Plan::beginElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_commands))
  {
    // Handling of commands, a category which doesn't have a category reader
    LockManager::getManager().obtainWriteLock(&(pIn.getCommands()));
    pIn.readto(&(pIn.getCommands()));
  }
  else
  {
    const MetaCategory *cat = MetaCategory::findCategoryByGroupTag(pIn.getParentElement().getTagHash());
    if (cat)
    {
      if (cat->readFunction)
        // Hand over control to a registered read controller
        pIn.readto(cat->readFunction(*cat,pIn));
      else
        // There is no controller available.
        // This piece of code will be used to skip pieces of the XML file that
        // Frepple doesn't need to be understand
        pIn.IgnoreElement();
    }
  }
}


}
