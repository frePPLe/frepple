/***************************************************************************
  file : $HeadURL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
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


/** @brief This class holds a collection of all XML tags used by frepple.
  *
  * The class is a mere placeholder for a number of static instances of the
  * XMLtag class.<br>
  * Nothing prevents you from creating static XMLtag instances.
  */
class Tags
{
  public:
    static DECLARE_EXPORT const XMLtag tag_abortonerror;
    static DECLARE_EXPORT const XMLtag tag_action;
    static DECLARE_EXPORT const XMLtag tag_after;
    static DECLARE_EXPORT const XMLtag tag_alternate;
    static DECLARE_EXPORT const XMLtag tag_alternates;
    static DECLARE_EXPORT const XMLtag tag_before;
    static DECLARE_EXPORT const XMLtag tag_bucket;
    static DECLARE_EXPORT const XMLtag tag_buckets;
    static DECLARE_EXPORT const XMLtag tag_buffer;
    static DECLARE_EXPORT const XMLtag tag_buffers;
    static DECLARE_EXPORT const XMLtag tag_calendar;
    static DECLARE_EXPORT const XMLtag tag_calendars;
    static DECLARE_EXPORT const XMLtag tag_category;
    static DECLARE_EXPORT const XMLtag tag_cluster;
    static DECLARE_EXPORT const XMLtag tag_cmdline;
    static DECLARE_EXPORT const XMLtag tag_command;
    static DECLARE_EXPORT const XMLtag tag_commands;
    static DECLARE_EXPORT const XMLtag tag_condition;
    static DECLARE_EXPORT const XMLtag tag_constraints;
    static DECLARE_EXPORT const XMLtag tag_consuming;
    static DECLARE_EXPORT const XMLtag tag_content;
    static DECLARE_EXPORT const XMLtag tag_current;
    static DECLARE_EXPORT const XMLtag tag_customer;
    static DECLARE_EXPORT const XMLtag tag_customers;
    static DECLARE_EXPORT const XMLtag tag_data;
    static DECLARE_EXPORT const XMLtag tag_date;
    static DECLARE_EXPORT const XMLtag tag_dates;
    static DECLARE_EXPORT const XMLtag tag_default_calendar;
    static DECLARE_EXPORT const XMLtag tag_delivery;
    static DECLARE_EXPORT const XMLtag tag_demand;
    static DECLARE_EXPORT const XMLtag tag_demands;
    static DECLARE_EXPORT const XMLtag tag_description;
    static DECLARE_EXPORT const XMLtag tag_detectproblems;
    static DECLARE_EXPORT const XMLtag tag_due;
    static DECLARE_EXPORT const XMLtag tag_duration;
    static DECLARE_EXPORT const XMLtag tag_duration_per;
    static DECLARE_EXPORT const XMLtag tag_else;
    static DECLARE_EXPORT const XMLtag tag_end;
    static DECLARE_EXPORT const XMLtag tag_end_onhand;
    static DECLARE_EXPORT const XMLtag tag_epst;
    static DECLARE_EXPORT const XMLtag tag_fence;
    static DECLARE_EXPORT const XMLtag tag_filename;
    static DECLARE_EXPORT const XMLtag tag_flow;
    static DECLARE_EXPORT const XMLtag tag_flow_plan;
    static DECLARE_EXPORT const XMLtag tag_flow_plans;
    static DECLARE_EXPORT const XMLtag tag_flows;
    static DECLARE_EXPORT const XMLtag tag_flowtype;
    static DECLARE_EXPORT const XMLtag tag_headeratts;
    static DECLARE_EXPORT const XMLtag tag_headerstart;
    static DECLARE_EXPORT const XMLtag tag_id;
    static DECLARE_EXPORT const XMLtag tag_item;
    static DECLARE_EXPORT const XMLtag tag_items;
    static DECLARE_EXPORT const XMLtag tag_leadtime;
    static DECLARE_EXPORT const XMLtag tag_level;
    static DECLARE_EXPORT const XMLtag tag_load;
    static DECLARE_EXPORT const XMLtag tag_load_plan;
    static DECLARE_EXPORT const XMLtag tag_load_plans;
    static DECLARE_EXPORT const XMLtag tag_loads;
    static DECLARE_EXPORT const XMLtag tag_location;
    static DECLARE_EXPORT const XMLtag tag_locations;
    static DECLARE_EXPORT const XMLtag tag_locked;
    static DECLARE_EXPORT const XMLtag tag_logfile;
    static DECLARE_EXPORT const XMLtag tag_lpst;
    static DECLARE_EXPORT const XMLtag tag_maximum;
    static DECLARE_EXPORT const XMLtag tag_maxinterval;
    static DECLARE_EXPORT const XMLtag tag_maxinventory;
    static DECLARE_EXPORT const XMLtag tag_maxparallel;
    static DECLARE_EXPORT const XMLtag tag_members;
    static DECLARE_EXPORT const XMLtag tag_minimum;
    static DECLARE_EXPORT const XMLtag tag_mininterval;
    static DECLARE_EXPORT const XMLtag tag_mininventory;
    static DECLARE_EXPORT const XMLtag tag_mode;
    static DECLARE_EXPORT const XMLtag tag_name;
    static DECLARE_EXPORT const XMLtag tag_onhand;
    static DECLARE_EXPORT const XMLtag tag_operation;
    static DECLARE_EXPORT const XMLtag tag_operation_plan;
    static DECLARE_EXPORT const XMLtag tag_operation_plans;
    static DECLARE_EXPORT const XMLtag tag_operations;
    static DECLARE_EXPORT const XMLtag tag_owner;
    static DECLARE_EXPORT const XMLtag tag_parameter;
    static DECLARE_EXPORT const XMLtag tag_pegging;
    static DECLARE_EXPORT const XMLtag tag_plan;
    static DECLARE_EXPORT const XMLtag tag_plannable;
    static DECLARE_EXPORT const XMLtag tag_policy;
    static DECLARE_EXPORT const XMLtag tag_posttime;
    static DECLARE_EXPORT const XMLtag tag_pretime;
    static DECLARE_EXPORT const XMLtag tag_priority;
    static DECLARE_EXPORT const XMLtag tag_problem;
    static DECLARE_EXPORT const XMLtag tag_problems;
    static DECLARE_EXPORT const XMLtag tag_producing;
    static DECLARE_EXPORT const XMLtag tag_quantity;
    static DECLARE_EXPORT const XMLtag tag_resource;
    static DECLARE_EXPORT const XMLtag tag_resources;
    static DECLARE_EXPORT const XMLtag tag_size_maximum;
    static DECLARE_EXPORT const XMLtag tag_size_minimum;
    static DECLARE_EXPORT const XMLtag tag_size_multiple;
    static DECLARE_EXPORT const XMLtag tag_solver;
    static DECLARE_EXPORT const XMLtag tag_solvers;
    static DECLARE_EXPORT const XMLtag tag_start;
    static DECLARE_EXPORT const XMLtag tag_start_onhand;
    static DECLARE_EXPORT const XMLtag tag_startorend;
    static DECLARE_EXPORT const XMLtag tag_steps;
    static DECLARE_EXPORT const XMLtag tag_subcategory;
    static DECLARE_EXPORT const XMLtag tag_supply;
    static DECLARE_EXPORT const XMLtag tag_then;
    static DECLARE_EXPORT const XMLtag tag_type;
    static DECLARE_EXPORT const XMLtag tag_unspecified;
    static DECLARE_EXPORT const XMLtag tag_url;
    static DECLARE_EXPORT const XMLtag tag_usage;
    static DECLARE_EXPORT const XMLtag tag_validate;
    static DECLARE_EXPORT const XMLtag tag_value;
    static DECLARE_EXPORT const XMLtag tag_variable;
    static DECLARE_EXPORT const XMLtag tag_verbose;

};

