#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

r'''
Exports frePPLe information to a flat file usable as a data file for
a LP formulation.

This file is only an example. A different LP formulation will obviously
require a different data file. Given the easy structure of this
Python code this will remain a clean and simple piece of code.
'''

import frepple
def exportfrepple():

  output = open('lpsolver.dat',"wt")

  print >>output, "param timerate := 0.97;\n"

  print >>output, "param : demands : reqqty  prio  due :="
  for b in frepple.demands():
    if b.quantity > 0:
      print >>output, b.name.replace(' ','').replace(':',''), b.quantity, b.priority, b.due.month
  print >>output, ";\n"

  print >>output, "param numbuckets := 12;"
  print >>output, "set buckets := 1 2 3 4 5 6 7 8 9 10 11 12;"

  print >>output, "set resources := "
  for b in frepple.resources():
    print >>output, b.name.replace(' ','').replace(':','')
  print >>output, ";\n"

  print >>output, "param availablecapacity"
  print >>output, ": 1 2 3 4 5 6 7 8 9 10 11 12 := "
  res = []
  for b in frepple.resources():
    res.append(b.name.replace(' ','').replace(':',''))
    print >>output, b.name.replace(' ','').replace(':',''), "120 120 120 120 120 120 120 120 120 120 120 120"
  print >>output, ";\n"

  print >>output, "param : loads : loadfactor :="
  import random
  for b in frepple.demands():
    if b.quantity > 0:
      # @todo the next line arbitrarily associates a demand with a resource. We need code to search the supply path instead...
      print >>output, b.name.replace(' ','').replace(':',''), random.choice(res), 1
  print >>output, ";\n"
  print >>output, "end;\n"
