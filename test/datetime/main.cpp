/***************************************************************************
  file : $HeadURL$
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


#include "frepple/utils.h"
using namespace frepple;


int main (int argc, char *argv[])
{

  Date d1;
  d1.parse("2007-02-01T01:02:03", "%Y-%m-%dT%H:%M:%S");

  Date d2;
  d2.parse("2007-02-03T01:02:03", "%Y-%m-%dT%H:%M:%S");

  Date d3;
  // The date d3 is chosen such that daylight saving time
  // is in effect at that date.
  d3.parse("2007-06-01T00:00:00", "%Y-%m-%dT%H:%M:%S");

  TimePeriod t1 = 10;

  logger << "d1 \"2007-02-01T01:02:03\" => " << d1 << endl;
  logger << "d2 \"2007-02-03T01:02:03\" => " << d2 << endl;
  logger << "d3 \"2007-06-01T00:00:00\" => " << d3 << endl;
  logger << "t1: " << t1 << endl;

  TimePeriod t2 = d1 - d2;
  logger << "d1-d2: " << t2 << endl;

  t2 = d2 - d1;
  logger << "d2-d1: " << t2 << endl;

  d1 -= t1;
  logger << "d1-t1: " << d1 << endl;

  TimePeriod t3;
  t3.parse("P1D");
  logger << "time \"P1D\" => " << t3 << "    "
  << static_cast<long>(t3) << endl;
  t3.parse("PT9M");
  logger << "time \"PT9M\" => " << t3 << "    "
  << static_cast<long>(t3) << endl;
  try
  {
    t3.parse("Pwrong");
  }
  catch (DataException e)
  { logger << "Data exception caught: " << e.what() << endl; }
  logger << "time \"Pwrong\" => " << t3 << "    "
  << static_cast<long>(t3) << endl;
  t3.parse("PT79M");
  logger << "time \"PT79M\" => " << t3 << "    "
  << static_cast<long>(t3) << endl;
  t3.parse("P1W1DT1H");
  logger << "time \"P1W1DT1H\" => " << t3 << "    "
  << static_cast<long>(t3) << endl;
  t3.parse("PT0S");
  logger << "time \"PT0S\" => " << t3 << "    "
  << static_cast<long>(t3) << endl;
  t3.parse("-PT1M1S");
  logger << "time \"-PT1M1S\" => " << t3 << "    "
  << static_cast<long>(t3) << endl;

  logger << "infinite past: " << Date::infinitePast << endl;
  logger << "infinite future: " << Date::infiniteFuture << endl;

  return EXIT_SUCCESS;

}
