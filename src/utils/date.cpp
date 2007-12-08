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
#include "frepple/utils.h"
#include <ctime>
#include <clocale>


namespace frepple
{

DECLARE_EXPORT string Date::format("%Y-%m-%dT%H:%M:%S");
DECLARE_EXPORT string DateRange::separator = " / ";

/* This is the earliest date that we can represent. This not the
 * traditional epcoh start, but a year later. 1/1/1970 gave troubles
 * when using a timezone with positive offset to GMT.
 */
DECLARE_EXPORT const Date Date::infinitePast("1971-01-01T00:00:00",true);

/* This is the latest date that we can represent. This is not the absolute
 * limit of the internal representation, but more a convenient end date. */
DECLARE_EXPORT const Date Date::infiniteFuture("2030-12-31T00:00:00",true);

DECLARE_EXPORT const TimePeriod TimePeriod::MAX(Date::infiniteFuture - Date::infinitePast);
DECLARE_EXPORT const TimePeriod TimePeriod::MIN(Date::infinitePast - Date::infiniteFuture);


DECLARE_EXPORT void Date::checkFinite(long long i)
{
  if (i > infiniteFuture.lval) lval = infiniteFuture.lval;
  else if (i < infinitePast.lval) lval = infinitePast.lval;
  else lval = static_cast<long>(i);
}


DECLARE_EXPORT void TimePeriod::toCharBuffer(char* t) const
{
  long tmp = (lval>0 ? lval : -lval);
  if (lval<0) *(t++) = '-';
  if (tmp >= 3600)
  {
    // Format: "HH:MM:SS"
    long minsec = tmp % 3600;
    sprintf(t,"%li:%02li:%02li", tmp/3600, minsec/60, minsec%60);
  }
  else if (tmp >= 60)
    // Format: "MM:SS"
    sprintf(t,"%li:%02li", tmp/60, tmp%60);
  else
    // Format: "SS"
    sprintf(t,"%li", tmp);
}


DECLARE_EXPORT DateRange::operator string() const
{
  // Start date
  string r(start);

  // Append the separator
  r.append(separator);

  // Append the end date
  r.append(string(end));
  return r;
}


DECLARE_EXPORT void Date::toCharBuffer(char* str) const
{
  // The standard library function localtime() is not re-entrant: the same
  // static structure is used for all calls. In a multi-threaded environment
  // the function is not to be used.
  // The POSIX standard defines a re-entrant version of the function:
  // localtime_r.
  // Visual C++ 6.0 and Borland 5.5 are missing it, but provide a thread-safe
  // variant without changing the function semantics.
#ifdef HAVE_LOCALTIME_R
  struct tm timeStruct;
  localtime_r(&lval, &timeStruct);
#else
  struct tm timeStruct = *localtime(&lval);
#endif
  strftime(str, 30,  format.c_str(), &timeStruct);
}


DECLARE_EXPORT void TimePeriod::parse (const char* s)
{
  lval = 0;
  long t = 0;
  int colons = 2;
  bool minus = false;
  for (const char *chr = s; *chr; ++chr)
  {
    if (*chr>='0' && *chr<='9')
      t = t * 10 + (*chr - '0');
    else if (*chr == ':' && colons)
    {
      lval = (lval + t) * 60;
      t = 0;
      --colons;
    }
    else if (*chr == '-' && !minus)
      minus = true;
    else
    {
      lval = 0;
      throw DataException("Invalid time string '" + string(s) + "'");
    }
  }
  lval += t;
  if (minus) lval = -lval;
}


DECLARE_EXPORT void Date::parse (const char* s, const string& fmt)
{
  struct tm p;
  strptime(s, fmt.c_str(), &p);
  // No clue whether daylight saving time is in effect...
  p.tm_isdst = -1;
  lval = mktime(&p);
}


// The next method is only compiled if the function strptime
// isn't available in your standard library.
#ifndef HAVE_STRPTIME

DECLARE_EXPORT char* Date::strptime(const char *buf, const char *fmt, struct tm *tm)
{
  struct dtconv
  {
    char    *abbrev_month_names[12];
    size_t  len_abbrev_month_names[12];
    char    *month_names[12];
    size_t  len_month_names[12];
    char    *abbrev_weekday_names[7];
    size_t  len_abbrev_weekday_names[7];
    char    *weekday_names[7];
    size_t  len_weekday_names[7];
    char    *time_format;
    char    *sDate_format;
    char    *dtime_format;
    char    *am_string;
    size_t  len_am_string;
    char    *pm_string;
    size_t  len_pm_string;
    char    *lDate_format;
    unsigned short  numWeekdays;
    unsigned short  numMonths;
  };

  // The "length" fields in this structure MUST match the values in the strings.
  static struct dtconv En_US =
    {
      { "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
      },
      {   3,     3,     3,     3,     3,     3,
          3,     3,     3,     3,     3,     3},
      { "January", "February", "March", "April", "May", "June", "July", "August",
        "September", "October", "November", "December" },
      {     8,         8,         5,       5,      3,     4,       4,      6,
          9,          7,          8,          8},
      { "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" },
      {   3,     3,     3,     3,     3,     3,     3},
      { "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday" },
      {   6,        6,         7,          9,           8,        6,
          8},
      "%H:%M:%S",
      "%m/%d/%y",
      "%a %b %e %T %Z %Y",
      "AM",
      2,
      "PM",
      2,
      "%A, %B, %e, %Y",
      7,
      12
    };

  char c, *ptr;
  short i, len = 0;

  // No clude whether daylight saving time is in effect...
  tm->tm_isdst = -1;

  ptr = (char*) fmt;
  while (*ptr != 0)
  {

    if (*buf == 0) break;
    c = *ptr++;
    if (c != '%')
    {
      if (isspace(c))
        while (*buf != 0 && isspace(*buf)) buf++;
      else if (c != *buf++) return 0;
      continue;
    }

    c = *ptr++;
    switch (c)
    {
      case 0:
      case '%':
        if (*buf++ != '%') return 0;
        break;

      case 'C':
        buf = strptime(buf, En_US.lDate_format, tm);
        if (buf == 0) return 0;
        break;

      case 'c':
        buf = strptime(buf, "%x %X", tm);
        if (buf == 0) return 0;
        break;

      case 'D':
        buf = strptime(buf, "%m/%d/%y", tm);
        if (buf == 0) return 0;
        break;

      case 'R':
        buf = strptime(buf, "%H:%M", tm);
        if (buf == 0) return 0;
        break;

      case 'r':
        buf = strptime(buf, "%I:%M:%S %p", tm);
        if (buf == 0) return 0;
        break;

      case 'T':
        buf = strptime(buf, "%H:%M:%S", tm);
        if (buf == 0) return 0;
        break;

      case 'X':
        buf = strptime(buf, En_US.time_format, tm);
        if (buf == 0) return 0;
        break;

      case 'x':
        buf = strptime(buf, En_US.sDate_format, tm);
        if (buf == 0) return 0;
        break;

      case 'j':
        if (!isdigit(*buf)) return 0;
        for (i = 0; *buf != 0 && isdigit(*buf); ++buf)
        {
          i *= 10;
          i += *buf - '0';
        }
        if (i > 365) return 0;
        tm->tm_yday = i;
        break;

      case 'M':
      case 'S':
        if (*buf == 0 || isspace(*buf)) break;
        if (!isdigit(*buf)) return 0;
        for (i = 0; *buf != 0 && isdigit(*buf); ++buf)
        {
          i *= 10;
          i += *buf - '0';
        }
        if (i > 59) return 0;
        if (c == 'M')
          tm->tm_min = i;
        else
          tm->tm_sec = i;
        if (*buf != 0 && isspace(*buf))
          while (*ptr != 0 && !isspace(*ptr)) ++ptr;
        break;

      case 'H':
      case 'I':
      case 'k':
      case 'l':
        if (!isdigit(*buf)) return 0;
        for (i = 0; *buf != 0 && isdigit(*buf); ++buf)
        {
          i *= 10;
          i += *buf - '0';
        }
        if (c == 'H' || c == 'k')
        {if (i > 23) return 0;}
        else if (i > 11) return 0;
        tm->tm_hour = i;
        if (*buf != 0 && isspace(*buf))
          while (*ptr != 0 && !isspace(*ptr)) ++ptr;
        break;

      case 'p':
        if (strncasecmp(buf, En_US.am_string, En_US.len_am_string) == 0)
        {
          if (tm->tm_hour > 12) return 0;
          if (tm->tm_hour == 12) tm->tm_hour = 0;
          buf += len;
          break;
        }
        if (strncasecmp(buf, En_US.pm_string, En_US.len_pm_string) == 0)
        {
          if (tm->tm_hour > 12) return 0;
          if (tm->tm_hour != 12) tm->tm_hour += 12;
          buf += len;
          break;
        }
        return 0;

      case 'A':
      case 'a':
        for (i = 0; i < En_US.numWeekdays; ++i)
        {
          if (strncasecmp(buf, En_US.weekday_names[i],
              En_US.len_weekday_names[i]) == 0) break;
          if (strncasecmp(buf, En_US.abbrev_weekday_names[i],
              En_US.len_abbrev_weekday_names[i]) == 0) break;
        }
        if (i == En_US.numWeekdays) return 0;
        tm->tm_wday = i;
        buf += len;
        break;

      case 'd':
      case 'e':
        if (!isdigit(*buf)) return 0;
        for (i = 0; *buf != 0 && isdigit(*buf); ++buf)
        {
          i *= 10;
          i += *buf - '0';
        }
        if (i > 31) return 0;
        tm->tm_mday = i;
        if (*buf != 0 && isspace(*buf))
          while (*ptr != 0 && !isspace(*ptr)) ++ptr;
        break;

      case 'B':
      case 'b':
      case 'h':
        for (i = 0; i < En_US.numMonths; ++i)
        {
          if (strncasecmp(buf, En_US.month_names[i],
              En_US.len_month_names[i]) == 0) break;
          if (strncasecmp(buf, En_US.abbrev_month_names[i],
              En_US.len_abbrev_month_names[i]) == 0) break;
        }
        if (i == En_US.numMonths) return 0;
        tm->tm_mon = i;
        buf += len;
        break;

      case 'm':
        if (!isdigit(*buf)) return 0;
        for (i = 0; *buf != 0 && isdigit(*buf); ++buf)
        {
          i *= 10;
          i += *buf - '0';
        }
        if (i < 1 || i > 12) return 0;
        tm->tm_mon = i - 1;
        if (*buf != 0 && isspace(*buf))
          while (*ptr != 0 && !isspace(*ptr)) ++ptr;
        break;

      case 'Y':
      case 'y':
        if (*buf == 0 || isspace(*buf)) break;
        if (!isdigit(*buf)) return 0;
        for (i = 0; *buf != 0 && isdigit(*buf); ++buf)
        {
          i *= 10;
          i += *buf - '0';
        }
        if (c == 'Y') i -= 1900;
        if (i < 0) return 0;
        tm->tm_year = i;
        if (*buf != 0 && isspace(*buf))
          while (*ptr != 0 && !isspace(*ptr)) ++ptr;
        break;
    }
  }

  return const_cast<char*>(buf);
}

#endif

}
