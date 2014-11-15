/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
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
    static DECLARE_EXPORT const Keyword tag_action;
    static DECLARE_EXPORT const Keyword tag_alternate;
    static DECLARE_EXPORT const Keyword tag_alternates;
    static DECLARE_EXPORT const Keyword tag_autocommit;
    static DECLARE_EXPORT const Keyword tag_available;
    static DECLARE_EXPORT const Keyword tag_booleanproperty;
    static DECLARE_EXPORT const Keyword tag_bucket;
    static DECLARE_EXPORT const Keyword tag_buckets;
    static DECLARE_EXPORT const Keyword tag_buffer;
    static DECLARE_EXPORT const Keyword tag_buffers;
    static DECLARE_EXPORT const Keyword tag_calendar;
    static DECLARE_EXPORT const Keyword tag_calendars;
    static DECLARE_EXPORT const Keyword tag_carrying_cost;
    static DECLARE_EXPORT const Keyword tag_category;
    static DECLARE_EXPORT const Keyword tag_cluster;
    static DECLARE_EXPORT const Keyword tag_constraints;
    static DECLARE_EXPORT const Keyword tag_consume_material;
    static DECLARE_EXPORT const Keyword tag_consume_capacity;
    static DECLARE_EXPORT const Keyword tag_consuming;
    static DECLARE_EXPORT const Keyword tag_consuming_date;
    static DECLARE_EXPORT const Keyword tag_content;
    static DECLARE_EXPORT const Keyword tag_cost;
    static DECLARE_EXPORT const Keyword tag_criticality;
    static DECLARE_EXPORT const Keyword tag_current;
    static DECLARE_EXPORT const Keyword tag_customer;
    static DECLARE_EXPORT const Keyword tag_customers;
    static DECLARE_EXPORT const Keyword tag_data;
    static DECLARE_EXPORT const Keyword tag_date;
    static DECLARE_EXPORT const Keyword tag_dateproperty;
    static DECLARE_EXPORT const Keyword tag_dates;
    static DECLARE_EXPORT const Keyword tag_days;
    static DECLARE_EXPORT const Keyword tag_default;
    static DECLARE_EXPORT const Keyword tag_demand;
    static DECLARE_EXPORT const Keyword tag_demands;
    static DECLARE_EXPORT const Keyword tag_description;
    static DECLARE_EXPORT const Keyword tag_detectproblems;
    static DECLARE_EXPORT const Keyword tag_discrete;
    static DECLARE_EXPORT const Keyword tag_doubleproperty;
    static DECLARE_EXPORT const Keyword tag_due;
    static DECLARE_EXPORT const Keyword tag_duration;
    static DECLARE_EXPORT const Keyword tag_duration_per;
    static DECLARE_EXPORT const Keyword tag_effective_start;
    static DECLARE_EXPORT const Keyword tag_effective_end;
    static DECLARE_EXPORT const Keyword tag_end;
    static DECLARE_EXPORT const Keyword tag_enddate;
    static DECLARE_EXPORT const Keyword tag_endtime;
    static DECLARE_EXPORT const Keyword tag_entity;
    static DECLARE_EXPORT const Keyword tag_fence;
    static DECLARE_EXPORT const Keyword tag_factor;
    static DECLARE_EXPORT const Keyword tag_filename;
    static DECLARE_EXPORT const Keyword tag_flow;
    static DECLARE_EXPORT const Keyword tag_flowplan;
    static DECLARE_EXPORT const Keyword tag_flowplans;
    static DECLARE_EXPORT const Keyword tag_flows;
    static DECLARE_EXPORT const Keyword tag_fromsetup;
    static DECLARE_EXPORT const Keyword tag_headeratts;
    static DECLARE_EXPORT const Keyword tag_headerstart;
    static DECLARE_EXPORT const Keyword tag_hidden;
    static DECLARE_EXPORT const Keyword tag_id;
    static DECLARE_EXPORT const Keyword tag_item;
    static DECLARE_EXPORT const Keyword tag_items;
    static DECLARE_EXPORT const Keyword tag_leadtime;
    static DECLARE_EXPORT const Keyword tag_level;
    static DECLARE_EXPORT const Keyword tag_load;
    static DECLARE_EXPORT const Keyword tag_loadplan;
    static DECLARE_EXPORT const Keyword tag_loadplans;
    static DECLARE_EXPORT const Keyword tag_loads;
    static DECLARE_EXPORT const Keyword tag_location;
    static DECLARE_EXPORT const Keyword tag_locations;
    static DECLARE_EXPORT const Keyword tag_locked;
    static DECLARE_EXPORT const Keyword tag_logfile;
    static DECLARE_EXPORT const Keyword tag_loglevel;
    static DECLARE_EXPORT const Keyword tag_maxearly;
    static DECLARE_EXPORT const Keyword tag_maximum;
    static DECLARE_EXPORT const Keyword tag_maximum_calendar;
    static DECLARE_EXPORT const Keyword tag_maxinterval;
    static DECLARE_EXPORT const Keyword tag_maxinventory;
    static DECLARE_EXPORT const Keyword tag_maxlateness;
    static DECLARE_EXPORT const Keyword tag_members;
    static DECLARE_EXPORT const Keyword tag_minimum;
    static DECLARE_EXPORT const Keyword tag_minimum_calendar;
    static DECLARE_EXPORT const Keyword tag_mininterval;
    static DECLARE_EXPORT const Keyword tag_mininventory;
    static DECLARE_EXPORT const Keyword tag_minshipment;
    static DECLARE_EXPORT const Keyword tag_motive;
    static DECLARE_EXPORT const Keyword tag_name;
    static DECLARE_EXPORT const Keyword tag_onhand;
    static DECLARE_EXPORT const Keyword tag_operation;
    static DECLARE_EXPORT const Keyword tag_operationplan;
    static DECLARE_EXPORT const Keyword tag_operationplans;
    static DECLARE_EXPORT const Keyword tag_operations;
    static DECLARE_EXPORT const Keyword tag_owner;
    static DECLARE_EXPORT const Keyword tag_parameter;
    static DECLARE_EXPORT const Keyword tag_pegged;
    static DECLARE_EXPORT const Keyword tag_pegging;
    static DECLARE_EXPORT const Keyword tag_percent;
    static DECLARE_EXPORT const Keyword tag_plan;
    static DECLARE_EXPORT const Keyword tag_plantype;
    static DECLARE_EXPORT const Keyword tag_posttime;
    static DECLARE_EXPORT const Keyword tag_pretime;
    static DECLARE_EXPORT const Keyword tag_price;
    static DECLARE_EXPORT const Keyword tag_priority;
    static DECLARE_EXPORT const Keyword tag_problem;
    static DECLARE_EXPORT const Keyword tag_problems;
    static DECLARE_EXPORT const Keyword tag_produce_material;
    static DECLARE_EXPORT const Keyword tag_producing;
    static DECLARE_EXPORT const Keyword tag_producing_date;
    static DECLARE_EXPORT const Keyword tag_property;
    static DECLARE_EXPORT const Keyword tag_quantity;
    static DECLARE_EXPORT const Keyword tag_quantity_buffer;
    static DECLARE_EXPORT const Keyword tag_quantity_demand;
    static DECLARE_EXPORT const Keyword tag_resource;
    static DECLARE_EXPORT const Keyword tag_resources;
    static DECLARE_EXPORT const Keyword tag_resourceskill;
    static DECLARE_EXPORT const Keyword tag_resourceskills;
    static DECLARE_EXPORT const Keyword tag_rule;
    static DECLARE_EXPORT const Keyword tag_rules;
    static DECLARE_EXPORT const Keyword tag_search;
    static DECLARE_EXPORT const Keyword tag_setup;
    static DECLARE_EXPORT const Keyword tag_setupmatrices;
    static DECLARE_EXPORT const Keyword tag_setupmatrix;
    static DECLARE_EXPORT const Keyword tag_size_maximum;
    static DECLARE_EXPORT const Keyword tag_size_minimum;
    static DECLARE_EXPORT const Keyword tag_size_multiple;
    static DECLARE_EXPORT const Keyword tag_skill;
    static DECLARE_EXPORT const Keyword tag_skills;
    static DECLARE_EXPORT const Keyword tag_solver;
    static DECLARE_EXPORT const Keyword tag_solvers;
    static DECLARE_EXPORT const Keyword tag_source;
    static DECLARE_EXPORT const Keyword tag_start;
    static DECLARE_EXPORT const Keyword tag_startorend;
    static DECLARE_EXPORT const Keyword tag_startdate;
    static DECLARE_EXPORT const Keyword tag_starttime;
    static DECLARE_EXPORT const Keyword tag_steps;
    static DECLARE_EXPORT const Keyword tag_stringproperty;
    static DECLARE_EXPORT const Keyword tag_subcategory;
    static DECLARE_EXPORT const Keyword tag_supplier;
    static DECLARE_EXPORT const Keyword tag_suppliers;
    static DECLARE_EXPORT const Keyword tag_supply;
    static DECLARE_EXPORT const Keyword tag_tosetup;
    static DECLARE_EXPORT const Keyword tag_type;
    static DECLARE_EXPORT const Keyword tag_unavailable;
    static DECLARE_EXPORT const Keyword tag_userexit_buffer;
    static DECLARE_EXPORT const Keyword tag_userexit_demand;
    static DECLARE_EXPORT const Keyword tag_userexit_flow;
    static DECLARE_EXPORT const Keyword tag_userexit_operation;
    static DECLARE_EXPORT const Keyword tag_userexit_resource;
    static DECLARE_EXPORT const Keyword tag_validate;
    static DECLARE_EXPORT const Keyword tag_value;
    static DECLARE_EXPORT const Keyword tag_variable;
    static DECLARE_EXPORT const Keyword tag_verbose;
    static DECLARE_EXPORT const Keyword tag_weight;
};

