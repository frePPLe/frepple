/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by frePPLe bv                                   *
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

/** @brief This class holds a collection of all XML tags used by frepple.
 *
 * The class is a mere placeholder for a number of static instances of the
 * Keyword class.<br>
 * Nothing prevents you from creating static Keyword instances.
 */
class Tags {
 public:
  static const Keyword action;
  static const Keyword allmembers;
  static const Keyword alternate;
  static const Keyword alternates;
  static const Keyword alternate_name;
  static const Keyword approved;
  static const Keyword autocommit;
  static const Keyword autofence;
  static const Keyword available;
  static const Keyword batch;
  static const Keyword batchwindow;
  static const Keyword blockedby;
  static const Keyword blocking;
  static const Keyword booleanproperty;
  static const Keyword bucket;
  static const Keyword buckets;
  static const Keyword buffer;
  static const Keyword buffers;
  static const Keyword calendar;
  static const Keyword calendars;
  static const Keyword category;
  static const Keyword closed;
  static const Keyword cluster;
  static const Keyword completed;
  static const Keyword completed_allow_future;
  static const Keyword confirmed;
  static const Keyword constraints;
  static const Keyword constrained;
  static const Keyword consume_material;
  static const Keyword consume_capacity;
  static const Keyword consuming;
  static const Keyword consuming_date;
  static const Keyword content;
  static const Keyword cost;
  static const Keyword criticality;
  static const Keyword create;
  static const Keyword current;
  static const Keyword customer;
  static const Keyword customers;
  static const Keyword data;
  static const Keyword date;
  static const Keyword dateproperty;
  static const Keyword dates;
  static const Keyword days;
  static const Keyword dbconnection;
  static const Keyword deflt;
  static const Keyword delay;
  static const Keyword delivery;
  static const Keyword delivery_operation;
  static const Keyword deliveryduration;
  static const Keyword demand;
  static const Keyword demands;
  static const Keyword demand_deviation;
  static const Keyword dependencies;
  static const Keyword dependency;
  static const Keyword description;
  static const Keyword destination;
  static const Keyword detectproblems;
  static const Keyword discrete;
  static const Keyword doubleproperty;
  static const Keyword due;
  static const Keyword duration;
  static const Keyword duration_per;
  static const Keyword efficiency;
  static const Keyword efficiency_calendar;
  static const Keyword effective_start;
  static const Keyword effective_end;
  static const Keyword end;
  static const Keyword end_force;
  static const Keyword enddate;
  static const Keyword endtime;
  static const Keyword entity;
  static const Keyword erase;
  static const Keyword extra_safety_leadtime;
  static const Keyword factor;
  static const Keyword fcst_current;
  static const Keyword feasible;
  static const Keyword fence;
  static const Keyword filename;
  static const Keyword first;
  static const Keyword flow;
  static const Keyword flowplan;
  static const Keyword flowplans;
  static const Keyword flows;
  static const Keyword fromsetup;
  static const Keyword hard_safety_leadtime;
  static const Keyword hard_posttime;
  static const Keyword headeratts;
  static const Keyword headerstart;
  static const Keyword hidden;
  static const Keyword id;
  static const Keyword individualPoolResources;
  static const Keyword info;
  static const Keyword interruption;
  static const Keyword interruptions;
  static const Keyword ip_flag;
  static const Keyword item;
  static const Keyword itemdistribution;
  static const Keyword itemdistributions;
  static const Keyword items;
  static const Keyword itemsupplier;
  static const Keyword itemsuppliers;
  static const Keyword leadtime;
  static const Keyword level;
  static const Keyword load;
  static const Keyword loadplan;
  static const Keyword loadplans;
  static const Keyword loads;
  static const Keyword location;
  static const Keyword locations;
  static const Keyword locked;
  static const Keyword logfile;
  static const Keyword loglimit;
  static const Keyword loglevel;
  static const Keyword manager;
  static const Keyword maxearly;
  static const Keyword maximum;
  static const Keyword maximum_calendar;
  static const Keyword maxinventory;
  static const Keyword maxlateness;
  static const Keyword maxbucketcapacity;
  static const Keyword members;
  static const Keyword minimum;
  static const Keyword minimum_calendar;
  static const Keyword mininventory;
  static const Keyword minshipment;
  static const Keyword moveApprovedEarly;
  static const Keyword name;
  static const Keyword nolocationcalendar;
  static const Keyword offset;
  static const Keyword onhand;
  static const Keyword operation;
  static const Keyword operationplan;
  static const Keyword operationplans;
  static const Keyword operations;
  static const Keyword ordertype;
  static const Keyword origin;
  static const Keyword owner;
  static const Keyword pegging;
  static const Keyword pegging_first_level;
  static const Keyword pegging_demand;
  static const Keyword pegging_downstream;
  static const Keyword pegging_downstream_first_level;
  static const Keyword pegging_upstream;
  static const Keyword pegging_upstream_first_level;
  static const Keyword percent;
  static const Keyword period_of_cover;
  static const Keyword plan;
  static const Keyword planned;
  static const Keyword planned_quantity;
  static const Keyword plantype;
  static const Keyword policy;
  static const Keyword posttime;
  static const Keyword pretime;
  static const Keyword priority;
  static const Keyword problem;
  static const Keyword problems;
  static const Keyword produce_material;
  static const Keyword producing;
  static const Keyword property;
  static const Keyword proposed;
  static const Keyword quantity;
  static const Keyword quantity_fixed;
  static const Keyword quantity_completed;
  static const Keyword reference;
  static const Keyword remark;
  static const Keyword resource;
  static const Keyword resources;
  static const Keyword resourceskill;
  static const Keyword resourceskills;
  static const Keyword resource_qty;
  static const Keyword root;
  static const Keyword rule;
  static const Keyword rules;
  static const Keyword safety_leadtime;
  static const Keyword search;
  static const Keyword second;
  static const Keyword setup;
  static const Keyword setupend;
  static const Keyword setupmatrices;
  static const Keyword setupmatrix;
  static const Keyword setuponly;
  static const Keyword setupoverride;
  static const Keyword size_maximum;
  static const Keyword size_minimum;
  static const Keyword size_minimum_calendar;
  static const Keyword size_multiple;
  static const Keyword skill;
  static const Keyword skills;
  static const Keyword solver;
  static const Keyword solvers;
  static const Keyword source;
  static const Keyword start;
  static const Keyword start_force;
  static const Keyword startorend;
  static const Keyword startdate;
  static const Keyword starttime;
  static const Keyword status;
  static const Keyword statusNoPropagation;
  static const Keyword stringproperty;
  static const Keyword subcategory;
  static const Keyword suboperation;
  static const Keyword suboperations;
  static const Keyword supplier;
  static const Keyword suppliers;
  static const Keyword suppressFlowplanCreation;
  static const Keyword supply;
  static const Keyword timezone;
  static const Keyword tool;
  static const Keyword toolperpiece;
  static const Keyword tosetup;
  static const Keyword transferbatch;
  static const Keyword type;
  static const Keyword unavailable;
  static const Keyword uom;
  static const Keyword userexit_buffer;
  static const Keyword userexit_demand;
  static const Keyword userexit_flow;
  static const Keyword userexit_nextdemand;
  static const Keyword userexit_operation;
  static const Keyword userexit_resource;
  static const Keyword value;
  static const Keyword variable;
  static const Keyword verbose;
  static const Keyword volume;
  static const Keyword weight;
  static const Keyword wip_produce_full_quantity;
};
