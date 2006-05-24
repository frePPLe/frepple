/***************************************************************************
  file : $HeadURL: file:///develop/SVNrepository/frepple/trunk/test/datetime/main.cpp $
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


#include "frepple/utils.h"
using namespace frepple;


int main (int argc, char *argv[])
{

  Date d1;
  d1.parse("2006-02-01T01:02:03", "%Y-%m-%dT%H:%M:%S");

  Date d2;
  d2.parse("2006-02-03T01:02:03", "%Y-%m-%dT%H:%M:%S");

  Date d3;
  // The date d3 is chosen such that daylight saving time
  // is in effect at that date.
  d3.parse("2006-06-01T00:00:00", "%Y-%m-%dT%H:%M:%S");

  TimePeriod t1 = 10;

  cout << "d1 \"2006-02-01T01:02:03\" => " << d1 << endl;
  cout << "d2 \"2006-02-03T01:02:03\" => " << d2 << endl;
  cout << "d3 \"2006-06-01T00:00:00\" => " << d3 << endl;
  cout << "t1: " << t1 << endl;

  TimePeriod t2 = d1 - d2;
  cout << "d1-d2: " << t2 << endl;

  t2 = d2 - d1;
  cout << "d2-d1: " << t2 << endl;

  d1 -= t1;
  cout << "d1-t1: " << d1 << endl;

  TimePeriod t3;
  t3.parse("24:00:00");
  cout << "time \"24:00:00\" => " << t3 << "    " 
    << static_cast<long>(t3) << endl;
  t3.parse("9:00");
  cout << "time \"9:00\" => " << t3 << "    " 
    << static_cast<long>(t3) << endl;
  try
  {
  	t3.parse("00:0a:00");
  }
  catch (DataException e)
  	{ cout << "Data exception caught: " << e.what() << endl; }
  cout << "time \"00:0a:00\" => " << t3 << "    " 
    << static_cast<long>(t3) << endl;
  t3.parse("79:00");
  cout << "time \"79:00\" => " << t3 << "    " 
    << static_cast<long>(t3) << endl;
  t3.parse("3600");
  cout << "time \"3600\" => " << t3 << "    " 
    << static_cast<long>(t3) << endl;
  t3.parse("00:00:00");
  cout << "time \"00:00:00\" => " << t3 << "    " 
    << static_cast<long>(t3) << endl;
  t3.parse("-01:01");
  cout << "time \"-01:01\" => " << t3 << "    " 
    << static_cast<long>(t3) << endl;

  cout << "infinite past: " << Date::infinitePast << endl;
  cout << "infinite future: " << Date::infiniteFuture << endl;

  return EXIT_SUCCESS;

}
