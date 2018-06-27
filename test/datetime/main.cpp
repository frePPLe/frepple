/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by frePPLe bvba                                 *
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


#include "frepple.h"
using namespace frepple;


int main (int argc, char *argv[])
{

  Date d1;
  d1.parse("2009-02-01T01:02:03", "%Y-%m-%dT%H:%M:%S");
  DateDetail d1_detail(d1);

  Date d2;
  d2.parse("2009-02-03T01:02:03", "%Y-%m-%dT%H:%M:%S");
  DateDetail d2_detail(d2);

  Date d3;
  // The date d3 is chosen such that daylight saving time
  // is in effect at that date.
  d3.parse("2009-06-01T00:00:00", "%Y-%m-%dT%H:%M:%S");
  DateDetail d3_detail(d3);

  Duration t1 = 10L;

  logger << "d1 \"2009-02-01T01:02:03\" => " << d1 << " " << d1_detail.getSecondsDay()
     << " " << d1_detail.getSecondsWeek() << " " << d1_detail.getSecondsMonth()
     << " " << d1_detail.getSecondsYear() << endl;
  logger << "d2 \"2009-02-03T01:02:03\" => " << d2 << " " << d2_detail.getSecondsDay()
     << " " << d2_detail.getSecondsWeek() << " " << d2_detail.getSecondsMonth()
     << " " << d2_detail.getSecondsYear() << endl;
  logger << "d3 \"2009-06-01T00:00:00\" => " << d3 << " " << d3_detail.getSecondsDay()
     << " " << d3_detail.getSecondsWeek() << " " << d3_detail.getSecondsMonth()
     << " " << d3_detail.getSecondsYear() << endl;
  logger << "t1: " << t1 << endl;

  Duration t2 = d1 - d2;
  logger << "d1-d2: " << t2 << endl;

  t2 = d2 - d1;
  logger << "d2-d1: " << t2 << endl;

  d1 -= t1;
  logger << "d1-t1: " << d1 << endl;

  Duration t3;
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
  catch (const DataException& e)
  {
    logger << "Data exception caught: " << e.what() << endl;
  }
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
