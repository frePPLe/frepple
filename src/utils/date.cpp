/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bvba                                 *
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

#define FREPPLE_CORE
#include "frepple/utils.h"
#include <ctime>
#include <clocale>


namespace frepple
{
namespace utils
{

string Date::format("%Y-%m-%dT%H:%M:%S");
string DateRange::separator = " / ";
size_t DateRange::separatorlength = 3;

/* This is the earliest date that we can represent. This not the
 * traditional epoch start, but a year later. 1/1/1970 gave troubles
 * when using a timezone with positive offset to GMT.
 */
const Date Date::infinitePast("1971-01-01T00:00:00",true);

/* This is the latest date that we can represent. This is not the absolute
 * limit of the internal representation, but more a convenient end date. */
const Date Date::infiniteFuture("2030-12-31T00:00:00",true);

const Duration Duration::MAX(Date::infiniteFuture - Date::infinitePast);
const Duration Duration::MIN(Date::infinitePast - Date::infiniteFuture);


void Duration::toCharBuffer(char* t) const
{
  if (!lval)
  {
    sprintf(t,"P0D");
    return;
  }
  long tmp = (lval>0 ? lval : -lval);
  if (lval<0) *(t++) = '-';
  *(t++) = 'P';
  if (tmp >= 31536000L)
  {
    long y = tmp / 31536000L;
    t += sprintf(t,"%liY", y);
    tmp %= 31536000L;
  }
  if (tmp >= 86400L)
  {
    long d = tmp / 86400L;
    t += sprintf(t,"%liD", d);
    tmp %= 86400L;
  }
  if (tmp > 0L)
  {
    *(t++) = 'T';
    if (tmp >= 3600L)
    {
      long h = tmp / 3600L;
      t += sprintf(t,"%liH", h);
      tmp %= 3600L;
    }
    if (tmp >= 60L)
    {
      long h = tmp / 60L;
      t += sprintf(t,"%liM", h);
      tmp %= 60L;
    }
    if (tmp > 0L)
      sprintf(t,"%liS", tmp);
  }
}


void Duration::double2CharBuffer(double val, char* t)
{
  if (!val)
  {
    sprintf(t,"P0D");
    return;
  }
  double fractpart, intpart;
  fractpart = modf(val, &intpart);
  if (fractpart < 0) fractpart = - fractpart;
  long tmp = static_cast<long>(intpart>0 ? intpart : -intpart);
  if (val<0) *(t++) = '-';
  *(t++) = 'P';
  if (tmp >= 31536000L)
  {
    long y = tmp / 31536000L;
    t += sprintf(t,"%liY", y);
    tmp %= 31536000L;
  }
  if (tmp >= 86400L)
  {
    long d = tmp / 86400L;
    t += sprintf(t,"%liD", d);
    tmp %= 86400L;
  }
  if (tmp > 0L || fractpart)
  {
    *(t++) = 'T';
    if (tmp >= 3600L)
    {
      long h = tmp / 3600L;
      t += sprintf(t,"%liH", h);
      tmp %= 3600L;
    }
    if (tmp >= 60L)
    {
      long h = tmp / 60L;
      t += sprintf(t,"%liM", h);
      tmp %= 60L;
    }
    if (tmp > 0L || fractpart)
    {
      if (fractpart)
        sprintf(t,"%.3fS", fractpart + tmp);
      else
        sprintf(t,"%liS", tmp);
    }
  }
}


DateRange::operator string() const
{
  // Start date
  char r[65];
  char *pos = r + start.toCharBuffer(r);

  // Append the separator
  strcat(pos, separator.c_str());
  pos += separatorlength;

  // Append the end date
  end.toCharBuffer(pos);
  return r;
}


void Duration::parse (const char* s)
{
  long totalvalue = 0;
  long value = 0;
  bool negative = false;
  const char *c = s;

  // Optional minus sign
  if (*c == '-')
  {
    negative = true;
    ++c;
  }

  // Compulsary 'P'
  if (*c != 'P')
    throw DataException("Invalid time string '" + string(s) + "'");
  ++c;

  // Parse the date part
  for ( ; *c && *c != 'T'; ++c)
  {
    switch (*c)
    {
      case '0': case '1': case '2': case '3': case '4':
      case '5': case '6': case '7': case '8': case '9':
        value = value * 10 + (*c - '0');
        break;
      case 'Y':
        totalvalue += value * 31536000L;
        value = 0;
        break;
      case 'M':
        // 1 Month = 1 Year / 12 = 365 days / 12
        totalvalue += value * 2628000L;
        value = 0;
        break;
      case 'W':
        totalvalue += value * 604800L;
        value = 0;
        break;
      case 'D':
        totalvalue += value * 86400L;
        value = 0;
        break;
      default:
        throw DataException("Invalid time string '" + string(s) + "'");
    }
  }

  // Parse the time part
  if (*c == 'T')
  {
    for (++c ; *c; ++c)
    {
      switch (*c)
      {
        case '0': case '1': case '2': case '3': case '4':
        case '5': case '6': case '7': case '8': case '9':
          value = value * 10 + (*c - '0');
          break;
        case 'H':
          totalvalue += value * 3600L;
          value = 0;
          break;
        case 'M':
          totalvalue += value * 60L;
          value = 0;
          break;
        case 'S':
          totalvalue += value;
          value = 0;
          break;
        default:
          throw DataException("Invalid time string '" + string(s) + "'");
      }
    }
  }

  // Missing a time unit
  if (value) throw DataException("Invalid time string '" + string(s) + "'");

  // If no exceptions were thrown we can now store the value
  lval = negative ? -totalvalue : totalvalue;
}


double Duration::parse2double (const char* s)
{
  double totalvalue = 0.0;
  long value = 0;
  double milliseconds = 0.0;
  bool negative = false;
  bool subseconds = false;
  const char *c = s;

  // Optional minus sign
  if (*c == '-')
  {
    negative = true;
    ++c;
  }

  // Compulsary 'P' if the string is formatted as an XML duration, but
  // the string can also be formatted as a numeric value
  if (*c != 'P')
  {
    char* endptr;
    double value = strtod(s, &endptr);
    if (*endptr)
      throw DataException("Invalid time string '" + string(s) + "'");
    return value;
  }
  ++c;

  // Parse the date part
  for ( ; *c && *c != 'T'; ++c)
  {
    switch (*c)
    {
      case '0': case '1': case '2': case '3': case '4':
      case '5': case '6': case '7': case '8': case '9':
        value = value * 10 + (*c - '0');
        break;
      case 'Y':
        totalvalue += value * 31536000L;
        value = 0;
        break;
      case 'M':
        // 1 Month = 1 Year / 12 = 365 days / 12
        totalvalue += value * 2628000L;
        value = 0;
        break;
      case 'W':
        totalvalue += value * 604800L;
        value = 0;
        break;
      case 'D':
        totalvalue += value * 86400L;
        value = 0;
        break;
      default:
        throw DataException("Invalid time string '" + string(s) + "'");
    }
  }

  // Parse the time part
  if (*c == 'T')
  {
    for (++c ; *c; ++c)
    {
      switch (*c)
      {
        case '0': case '1': case '2': case '3': case '4':
        case '5': case '6': case '7': case '8': case '9':
          if (subseconds)
          {
            milliseconds = milliseconds + static_cast<double>(*c - '0') / value;
            value *= 10;
          }
          else
            value = value * 10 + (*c - '0');
          break;
        case 'H':
          totalvalue += value * 3600L;
          value = 0;
          break;
        case 'M':
          totalvalue += value * 60L;
          value = 0;
          break;
        case '.':
          totalvalue += value;
          value = 10;
          subseconds = true;
          break;
        case 'S':
          if (subseconds)
            totalvalue += milliseconds;
          else
            totalvalue += value;
          value = 0;
          break;
        default:
          throw DataException("Invalid time string '" + string(s) + "'");
      }
    }
  }

  // Missing a time unit
  if (value) throw DataException("Invalid time string '" + string(s) + "'");

  // If no exceptions were thrown we can now store the value
  return negative ? -totalvalue : totalvalue;
}


void Date::parse (const char* s, const char* fmt)
{
  if (!s)
  {
    // Null string passed - default value is infinite past
    lval = infinitePast.lval;
    return;
  }
  struct tm p;
  memset(&p, 0, sizeof(struct tm));
  strptime(s, fmt, &p);
  // No clue whether daylight saving time is in effect...
  p.tm_isdst = -1;
  lval = mktime(&p);
}


// The next method is only compiled if the function strptime
// isn't available in your standard library.
#ifndef HAVE_STRPTIME

char* Date::strptime(const char *buf, const char *fmt, struct tm *tm)
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
    {
      "Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    },
    {
      3,     3,     3,     3,     3,     3,
      3,     3,     3,     3,     3,     3
    },
    {
      "January", "February", "March", "April", "May", "June", "July", "August",
      "September", "October", "November", "December"
    },
    {
      8,         8,         5,       5,      3,     4,       4,      6,
      9,          7,          8,          8
    },
    { "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" },
    {   3,     3,     3,     3,     3,     3,     3},
    {
      "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
      "Saturday"
    },
    {
      6,        6,         7,          9,           8,        6,
      8
    },
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

  // No clue whether daylight saving time is in effect...
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

} // end namespace
} // end namespace

