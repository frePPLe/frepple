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


/** @file pythonutils.cpp
  * @brief Reusable functions for python functionality.
  *
  * Include this file in modules which require these functions. 
  * 
  * Alternatively, we could import the functions from the mod_python module.
  * But this creates a hard dependency between the modules, which we try to 
  * avoid.
  */

PyObject* PythonDateTime(const Date& d)  // @todo to be removed... We have a better class for this
{
  // The standard library function localtime() is not re-entrant: the same
  // static structure is used for all calls. In a multi-threaded environment
  // the function is not to be used.
  // The POSIX standard defines a re-entrant version of the function:
  // localtime_r.
  // Visual C++ 6.0 and Borland 5.5 are missing it, but provide a thread-safe
  // variant without changing the function semantics.
  time_t ticks = d.getTicks();
#ifdef HAVE_LOCALTIME_R
  struct tm t;
  localtime_r(&ticks, &t);
#else
  struct tm t = *localtime(&ticks);
#endif
  return PyDateTime_FromDateAndTime(t.tm_year+1900, t.tm_mon+1, t.tm_mday,
      t.tm_hour, t.tm_min, t.tm_sec, 0);
}
