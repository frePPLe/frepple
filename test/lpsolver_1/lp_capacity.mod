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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$


#
# Simple capacity allocation Linear Programming formulation for frePPLe.
#
# This file is written in the GNU MathProg modeling language, as implemented
# in the GLPK library.
#
# The problem input:
#   - a set of time buckets
#   - a set of demands, each with a due bucket, a quantity and a priority
#   - a set of resources, each with an available capacity per time bucket
#   - a set of loads, ie demands requiring some time on one or more resources
#
# The problem is subject to the following constraints:
#   - for each time bucket and each resource:
#        sum of capacity used by each demand <= capacity available in the resource bucket
#   - for each demand:
#        sum of planned quantities <= requested demand quantity
#
# The LP problem solves for a hierarchy of goals.
#   - minimize the shortness of demand of priorities 1, 2 and 3
#   - minimize the lateness of demand of priorities 1, 2 and 3
#   - minimize the early use of capacity (ie use capacity before the due date)
#


set demands;

set resources;

param numbuckets;

set buckets;

param timerate;

set priority, default {1..3} ;

param due{demands};

# Available capacity per resource, per time bucket
param availablecapacity{resources,buckets};

# Load on the resources by each demand
set loads, within demands cross resources;
param loadfactor{(i,j) in loads};

# Requested quantity of each demand
param reqqty{demands};

# Priority of each demand
param prio{demands};

# -2: two buckets early, -1: 1 bucket early, 0: in due bucket, ...
set delta, default {-2..2};

# Quantity satisfied per demand
var bucketplannedqty{d in demands, dl in delta}, >= 0, <= reqqty[d];
subject to constrtpast{d in demands, dl in delta: due[d] + dl < 1 or due[d] + dl > numbuckets}:
  bucketplannedqty[d,dl] = 0;
var plannedqty{d in demands}, >=0, <= reqqty[d];
subject to constrtplanned{d in demands}:
  sum{dl in delta} bucketplannedqty[d,dl] = plannedqty[d];

# Do not consume more than available
subject to capacityconsumption{r in resources,b in buckets}:
  sum{(d,r2) in loads, dl in delta}
    if b = due[d] + dl and r = r2 then bucketplannedqty[d,dl] * loadfactor[d,r2]
  <= availablecapacity[r,b];

# Summary row for the total planned quantity of a priority layer
var goalshortage{p in priority}, >= 0;
subject to shortage{p in priority}:
  sum{f in demands} if prio[f] = p then (timerate ** (due[f]-1) * (reqqty[f] - plannedqty[f])), = goalshortage[p];

# Summary row for the total earliness of a priority layer
var goalearly{p in priority}, >= 0;
subject to early{p in priority}:
  sum{d in demands, dl in delta} if prio[d] = p and dl < 0 then - dl * timerate ** (due[d]-1) * bucketplannedqty[d,dl], = goalearly[p];

# Summary row for the total planned quantity of a priority layer
var goallate{p in priority}, >= 0;
subject to late{p in priority}:
  sum{d in demands, dl in delta} if prio[d] = p and dl > 0 then dl * timerate ** (due[d]-1) * bucketplannedqty[d,dl], = goallate[p];

# Summary row for the total load of a resource
var goalresload{r in resources}, >= 0;
#subject to resload{r in resources}:
#  sum{(d,r2) in loads} if r = r2 then (timerate ** (due[d]-1) * plannedqty[d] * loadfactor[d,r2]), = goalresload[r];
subject to resload{r in resources}:
  sum{(d,r2) in loads} if r = r2 then (plannedqty[d] * loadfactor[d,r2]), = goalresload[r];

# A hierarhical sequence of goals is controlled in the C++ code of the module

data;

# This data section is ignored: the solver uses a seperate datafile instead.

param timerate := 0.97;

param : demands : reqqty  prio  due :=
  o1   10   1  1
  o2   10   2  2
  o3   20   1  2
;

param numbuckets := 4;

set buckets := 1 2 3 4 ;

set resources := resourceA resourceB ;

param availablecapacity
:      1   2   3   4   :=
resourceA   15     15        15        15
resourceB   15     15        15        15
;

param : loads : loadfactor :=
o1     resourceA 1
o2     resourceA 1
o3     resourceB 1
;

end;
