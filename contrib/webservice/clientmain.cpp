/***************************************************************************
  file : $HeadURL: file:///develop/SVNrepository/frepple/trunk/contrib/webservice/clientmain.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : johan_de_taeye@yahoo.com
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

#include "planner.hpp"

int main()
{
  try
  {
    frepple p;
    int d = p.InputXML("C:/develop/frepple/bin/test.xml");
    printf("inputxml %i\n", d);
    string x = p.OutputXML();
    printf("outputxml %s\n", x);
  }
  catch (frepple_AxisClientException a)
  {
    printf("%s\n", a.what());
  }
  catch (AxisException& e)
  {
    printf("trouble %s\n", e.what());
  }
  catch (...)
  {
    printf("trouble\n");
  }
}