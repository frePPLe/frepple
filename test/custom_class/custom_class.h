/***************************************************************************
  file : $HeadURL: file:///develop/SVNrepository/frepple/trunk/test/sizeof/main.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
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


#ifndef CUSTOM_CLASS_H
#define CUSTOM_CLASS_H
#include "frepple/model.h"
using namespace frepple;


class OperationTransport : public OperationFixedTime
{
  private:
    Buffer* fromBuf;
    Buffer* toBuf;
  public:
    /** Constructor. */
    explicit OperationTransport(const string& s)
      : OperationFixedTime(s), fromBuf(NULL), toBuf(NULL) {}

    Buffer* getFromBuffer() const {return fromBuf;}

    /** Update the source buffer of the transport.<br>
      * If operationplans already exist for the operation the update will
      * fail.
      */
    void setFromBuffer(Buffer *l);

    Buffer* getToBuffer() const {return toBuf;}

    /** Update the destination buffer of the transport.<br>
      * If operationplans already exist for the operation the update will
      * fail.
      */
    void setToBuffer(Buffer *l);

    void beginElement(XMLInput& , XMLElement&  );
    void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);

    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;

    static bool callback(Buffer*, Signal);
};

#endif   // endif CUSTOM_CLASS_H
