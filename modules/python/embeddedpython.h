/***************************************************************************
  file : $URL: https://frepple.svn.sourceforge.net/svnroot/frepple/trunk/modules/lp_solver/lpsolver.h $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
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

/** @file embeddedpython.h
  * @brief Header file for the module python.
  *
  * @namespace module_python
  * @brief An embedded interpreter for the Python language.
  *
  * xxx.
*/

#include "frepple.h"
using namespace frepple;

#include "Python.h"

namespace module_python
{


/** This class xxx.
  */
class CommandPython : public Command
{
  private:
    /** Command to be executed if the condition returns true. */
    string cmd;

    /** Command to be executed if the condition returns false. */
    string filename;

  public:
    /** Executes either the if- or the else-clause, depending on the 
      * condition. */
    void execute();

    /** Returns a descriptive string. */
    string getDescription() const {return "Command python interpreter";}

    /** Default constructor. */
    explicit CommandPython() {}

    /** Destructor. */
    virtual ~CommandPython() 
    {
    }

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const 
      {return sizeof(CommandPython) + cmd.size() + filename.size();}

    void beginElement(XMLInput&, XMLElement& pElement);
    void endElement(XMLInput& pIn, XMLElement& pElement);
};

}

