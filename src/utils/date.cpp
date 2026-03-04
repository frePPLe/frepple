/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
 *                                                                         *
 * Permission is hereby granted, free of charge, to any person obtaining   *
 * a copy of this software and associated documentation files (the         *
 * "Software"), to deal in the Software without restriction, including     *
 * without limitation the rights to use, copy, modify, merge, publish,     *
 * distribute, sublicense, and/or sell copies of the Software, and to      *
 * permit persons to whom the Software is furnished to do so, subject to   *
 * the following conditions:                                               *
 *                                                                         *
 * The above copyright notice and this permission notice shall be          *
 * included in all copies or substantial portions of the Software.         *
 *                                                                         *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,         *
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF      *
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                   *
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE  *
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION  *
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION   *
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.         *
 *                                                                         *
 ***************************************************************************/

#include <clocale>
#include <ctime>

#include "frepple/utils.h"

namespace frepple::utils {

string Date::format("%Y-%m-%dT%H:%M:%S");
bool Date::is_utc = false;
string DateRange::separator = " / ";
size_t DateRange::separatorlength = 3;

/* This is the earliest date that we can represent. This not the
 * traditional epoch start, but a year later. 1/1/1970 gave troubles
 * when using a timezone with positive offset to GMT.
 */
const Date Date::infinitePast("1971-01-01T00:00:00", true);

/* This is the latest date that we can represent. This is not the absolute
 * limit of the internal representation, but more a convenient end date. */
const Date Date::infiniteFuture("2030-12-31T00:00:00", true);

const Duration Duration::MAX(Date::infiniteFuture - Date::infinitePast);
const Duration Duration::MIN(Date::infinitePast - Date::infiniteFuture);

void Duration::toCharBuffer(char* t) const {
  if (!lval) {
    sprintf(t, "P0D");
    return;
  }
  long tmp = (lval > 0 ? lval : -lval);
  if (lval < 0) *(t++) = '-';
  *(t++) = 'P';
  if (tmp >= 31536000L) {
    long y = tmp / 31536000L;
    t += sprintf(t, "%liY", y);
    tmp %= 31536000L;
  }
  if (tmp >= 86400L) {
    long d = tmp / 86400L;
    t += sprintf(t, "%liD", d);
    tmp %= 86400L;
  }
  if (tmp > 0L) {
    *(t++) = 'T';
    if (tmp >= 3600L) {
      long h = tmp / 3600L;
      t += sprintf(t, "%liH", h);
      tmp %= 3600L;
    }
    if (tmp >= 60L) {
      long h = tmp / 60L;
      t += sprintf(t, "%liM", h);
      tmp %= 60L;
    }
    if (tmp > 0L) sprintf(t, "%liS", tmp);
  }
}

void Duration::double2CharBuffer(double val, char* t) {
  if (!val) {
    sprintf(t, "P0D");
    return;
  }
  double fractpart, intpart;
  fractpart = modf(val, &intpart);
  if (fractpart < 0) fractpart = -fractpart;
  long tmp = static_cast<long>(intpart > 0 ? intpart : -intpart);
  if (val < 0) *(t++) = '-';
  *(t++) = 'P';
  if (tmp >= 31536000L) {
    long y = tmp / 31536000L;
    t += sprintf(t, "%liY", y);
    tmp %= 31536000L;
  }
  if (tmp >= 86400L) {
    long d = tmp / 86400L;
    t += sprintf(t, "%liD", d);
    tmp %= 86400L;
  }
  if (tmp > 0L || fractpart) {
    *(t++) = 'T';
    if (tmp >= 3600L) {
      long h = tmp / 3600L;
      t += sprintf(t, "%liH", h);
      tmp %= 3600L;
    }
    if (tmp >= 60L) {
      long h = tmp / 60L;
      t += sprintf(t, "%liM", h);
      tmp %= 60L;
    }
    if (tmp > 0L || fractpart) {
      if (fractpart)
        sprintf(t, "%.3fS", fractpart + tmp);
      else
        sprintf(t, "%liS", tmp);
    }
  }
}

DateRange::operator string() const {
  // Start date
  char r[65];
  char* pos = r + start.toCharBuffer(r);

  // Append the separator
  strcat(pos, separator.c_str());
  pos += separatorlength;

  // Append the end date
  end.toCharBuffer(pos);
  return r;
}

void Duration::parse(const char* s) {
  long totalvalue = 0;
  long value = 0;
  bool negative = false;
  const char* c = s;

  // Optional minus sign
  if (*c == '-') {
    negative = true;
    ++c;
  }

  // Compulsary 'P'
  if (*c != 'P') throw DataException("Invalid time string '" + string(s) + "'");
  ++c;

  // Parse the date part
  for (; *c && *c != 'T'; ++c) {
    switch (*c) {
      case '0':
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
      case '6':
      case '7':
      case '8':
      case '9':
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
  if (*c == 'T') {
    for (++c; *c; ++c) {
      switch (*c) {
        case '0':
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
        case '7':
        case '8':
        case '9':
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

double Duration::parse2double(const char* s) {
  double totalvalue = 0.0;
  long value = 0;
  double milliseconds = 0.0;
  bool negative = false;
  bool subseconds = false;
  const char* c = s;

  // Optional minus sign
  if (*c == '-') {
    negative = true;
    ++c;
  }

  // Compulsary 'P' if the string is formatted as an XML duration, but
  // the string can also be formatted as a numeric value
  if (*c != 'P') {
    char* endptr;
    double value = strtod(s, &endptr);
    if (*endptr) throw DataException("Invalid time string '" + string(s) + "'");
    return value;
  }
  ++c;

  // Parse the date part
  for (; *c && *c != 'T'; ++c) {
    switch (*c) {
      case '0':
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
      case '6':
      case '7':
      case '8':
      case '9':
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
  if (*c == 'T') {
    for (++c; *c; ++c) {
      switch (*c) {
        case '0':
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
        case '7':
        case '8':
        case '9':
          if (subseconds) {
            milliseconds = milliseconds + static_cast<double>(*c - '0') / value;
            value *= 10;
          } else
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

void Date::parse(const char* s, const char* fmt) {
  if (!s) {
    // Null string passed - default value is infinite past
    lval = infinitePast.lval;
    return;
  }
  struct tm p;
  memset(&p, 0, sizeof(struct tm));
  auto ok = strptime(s, fmt, &p);
  if (!ok) throw DataException("Error parsing date");
  // No clue whether daylight saving time is in effect...
  if (is_utc) {
    p.tm_isdst = 0;
    lval = timegm(&p);
  } else {
    p.tm_isdst = -1;
    lval = mktime(&p);
  }
}

}  // namespace frepple::utils
