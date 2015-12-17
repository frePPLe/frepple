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


/** @brief This class holds a collection of all XML tags used by frepple.
  *
  * The class is a mere placeholder for a number of static instances of the
  * Keyword class.<br>
  * Nothing prevents you from creating static Keyword instances.
  */
class Tags
{
  public:
    static DECLARE_EXPORT const Keyword action;
    static DECLARE_EXPORT const Keyword alternate;
    static DECLARE_EXPORT const Keyword alternate_name;
    static DECLARE_EXPORT const Keyword approved;
    static DECLARE_EXPORT const Keyword autocommit;
    static DECLARE_EXPORT const Keyword available;
    static DECLARE_EXPORT const Keyword booleanproperty;
    static DECLARE_EXPORT const Keyword bucket;
    static DECLARE_EXPORT const Keyword buckets;
    static DECLARE_EXPORT const Keyword buffer;
    static DECLARE_EXPORT const Keyword buffers;
    static DECLARE_EXPORT const Keyword calendar;
    static DECLARE_EXPORT const Keyword calendars;
    static DECLARE_EXPORT const Keyword category;
    static DECLARE_EXPORT const Keyword cluster;
    static DECLARE_EXPORT const Keyword confirmed;
    static DECLARE_EXPORT const Keyword constraints;
    static DECLARE_EXPORT const Keyword consume_material;
    static DECLARE_EXPORT const Keyword consume_capacity;
    static DECLARE_EXPORT const Keyword consuming;
    static DECLARE_EXPORT const Keyword consuming_date;
    static DECLARE_EXPORT const Keyword content;
    static DECLARE_EXPORT const Keyword cost;
    static DECLARE_EXPORT const Keyword criticality;
    static DECLARE_EXPORT const Keyword current;
    static DECLARE_EXPORT const Keyword customer;
    static DECLARE_EXPORT const Keyword customers;
    static DECLARE_EXPORT const Keyword data;
    static DECLARE_EXPORT const Keyword date;
    static DECLARE_EXPORT const Keyword dateproperty;
    static DECLARE_EXPORT const Keyword dates;
    static DECLARE_EXPORT const Keyword days;
    static DECLARE_EXPORT const Keyword deflt;
    static DECLARE_EXPORT const Keyword demand;
    static DECLARE_EXPORT const Keyword demands;
    static DECLARE_EXPORT const Keyword description;
    static DECLARE_EXPORT const Keyword destination;
    static DECLARE_EXPORT const Keyword detectproblems;
    static DECLARE_EXPORT const Keyword discrete;
    static DECLARE_EXPORT const Keyword doubleproperty;
    static DECLARE_EXPORT const Keyword due;
    static DECLARE_EXPORT const Keyword duration;
    static DECLARE_EXPORT const Keyword duration_per;
    static DECLARE_EXPORT const Keyword effective_start;
    static DECLARE_EXPORT const Keyword effective_end;
    static DECLARE_EXPORT const Keyword end;
    static DECLARE_EXPORT const Keyword enddate;
    static DECLARE_EXPORT const Keyword endtime;
    static DECLARE_EXPORT const Keyword entity;
    static DECLARE_EXPORT const Keyword fence;
    static DECLARE_EXPORT const Keyword factor;
    static DECLARE_EXPORT const Keyword filename;
    static DECLARE_EXPORT const Keyword flow;
    static DECLARE_EXPORT const Keyword flowplan;
    static DECLARE_EXPORT const Keyword flowplans;
    static DECLARE_EXPORT const Keyword flows;
    static DECLARE_EXPORT const Keyword fromsetup;
    static DECLARE_EXPORT const Keyword headeratts;
    static DECLARE_EXPORT const Keyword headerstart;
    static DECLARE_EXPORT const Keyword hidden;
    static DECLARE_EXPORT const Keyword id;
    static DECLARE_EXPORT const Keyword item;
    static DECLARE_EXPORT const Keyword itemdistribution;
    static DECLARE_EXPORT const Keyword itemdistributions;
    static DECLARE_EXPORT const Keyword items;
    static DECLARE_EXPORT const Keyword itemsupplier;
    static DECLARE_EXPORT const Keyword itemsuppliers;
    static DECLARE_EXPORT const Keyword leadtime;
    static DECLARE_EXPORT const Keyword level;
    static DECLARE_EXPORT const Keyword load;
    static DECLARE_EXPORT const Keyword loadplan;
    static DECLARE_EXPORT const Keyword loadplans;
    static DECLARE_EXPORT const Keyword loads;
    static DECLARE_EXPORT const Keyword location;
    static DECLARE_EXPORT const Keyword locations;
    static DECLARE_EXPORT const Keyword locked;
    static DECLARE_EXPORT const Keyword logfile;
    static DECLARE_EXPORT const Keyword loglevel;
    static DECLARE_EXPORT const Keyword maxearly;
    static DECLARE_EXPORT const Keyword maximum;
    static DECLARE_EXPORT const Keyword maximum_calendar;
    static DECLARE_EXPORT const Keyword maxinterval;
    static DECLARE_EXPORT const Keyword maxinventory;
    static DECLARE_EXPORT const Keyword maxlateness;
    static DECLARE_EXPORT const Keyword members;
    static DECLARE_EXPORT const Keyword minimum;
    static DECLARE_EXPORT const Keyword minimum_calendar;
    static DECLARE_EXPORT const Keyword mininterval;
    static DECLARE_EXPORT const Keyword mininventory;
    static DECLARE_EXPORT const Keyword minshipment;
    static DECLARE_EXPORT const Keyword motive;
    static DECLARE_EXPORT const Keyword name;
    static DECLARE_EXPORT const Keyword onhand;
    static DECLARE_EXPORT const Keyword operation;
    static DECLARE_EXPORT const Keyword operationplan;
    static DECLARE_EXPORT const Keyword operationplans;
    static DECLARE_EXPORT const Keyword operations;
    static DECLARE_EXPORT const Keyword origin;
    static DECLARE_EXPORT const Keyword owner;
    static DECLARE_EXPORT const Keyword pegging;
    static DECLARE_EXPORT const Keyword pegging_upstream;
    static DECLARE_EXPORT const Keyword pegging_downstream;
    static DECLARE_EXPORT const Keyword percent;
    static DECLARE_EXPORT const Keyword plan;
    static DECLARE_EXPORT const Keyword plantype;
    static DECLARE_EXPORT const Keyword posttime;
    static DECLARE_EXPORT const Keyword pretime;
    static DECLARE_EXPORT const Keyword price;
    static DECLARE_EXPORT const Keyword priority;
    static DECLARE_EXPORT const Keyword problem;
    static DECLARE_EXPORT const Keyword problems;
    static DECLARE_EXPORT const Keyword produce_material;
    static DECLARE_EXPORT const Keyword producing;
    static DECLARE_EXPORT const Keyword producing_date;
    static DECLARE_EXPORT const Keyword property;
    static DECLARE_EXPORT const Keyword proposed;
    static DECLARE_EXPORT const Keyword quantity;
    static DECLARE_EXPORT const Keyword quantity_buffer;
    static DECLARE_EXPORT const Keyword quantity_demand;
    static DECLARE_EXPORT const Keyword reference;
    static DECLARE_EXPORT const Keyword resource;
    static DECLARE_EXPORT const Keyword resources;
    static DECLARE_EXPORT const Keyword resourceskill;
    static DECLARE_EXPORT const Keyword resourceskills;
    static DECLARE_EXPORT const Keyword rule;
    static DECLARE_EXPORT const Keyword rules;
    static DECLARE_EXPORT const Keyword search;
    static DECLARE_EXPORT const Keyword setup;
    static DECLARE_EXPORT const Keyword setupmatrices;
    static DECLARE_EXPORT const Keyword setupmatrix;
    static DECLARE_EXPORT const Keyword size_maximum;
    static DECLARE_EXPORT const Keyword size_minimum;
    static DECLARE_EXPORT const Keyword size_minimum_calendar;
    static DECLARE_EXPORT const Keyword size_multiple;
    static DECLARE_EXPORT const Keyword skill;
    static DECLARE_EXPORT const Keyword skills;
    static DECLARE_EXPORT const Keyword solver;
    static DECLARE_EXPORT const Keyword solvers;
    static DECLARE_EXPORT const Keyword source;
    static DECLARE_EXPORT const Keyword start;
    static DECLARE_EXPORT const Keyword startorend;
    static DECLARE_EXPORT const Keyword startdate;
    static DECLARE_EXPORT const Keyword starttime;
    static DECLARE_EXPORT const Keyword status;
    static DECLARE_EXPORT const Keyword stringproperty;
    static DECLARE_EXPORT const Keyword subcategory;
    static DECLARE_EXPORT const Keyword suboperation;
    static DECLARE_EXPORT const Keyword suboperations;
    static DECLARE_EXPORT const Keyword supplier;
    static DECLARE_EXPORT const Keyword suppliers;
    static DECLARE_EXPORT const Keyword supply;
    static DECLARE_EXPORT const Keyword tool;
    static DECLARE_EXPORT const Keyword tosetup;
    static DECLARE_EXPORT const Keyword type;
    static DECLARE_EXPORT const Keyword unavailable;
    static DECLARE_EXPORT const Keyword userexit_buffer;
    static DECLARE_EXPORT const Keyword userexit_demand;
    static DECLARE_EXPORT const Keyword userexit_flow;
    static DECLARE_EXPORT const Keyword userexit_operation;
    static DECLARE_EXPORT const Keyword userexit_resource;
    static DECLARE_EXPORT const Keyword value;
    static DECLARE_EXPORT const Keyword variable;
    static DECLARE_EXPORT const Keyword verbose;
    static DECLARE_EXPORT const Keyword weight;
};

