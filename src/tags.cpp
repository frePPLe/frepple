/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright(C) 2007 by Johan De Taeye                                    *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Lesser General Public License as published   *
 * by the Free Software Foundation; either version 2.1 of the License, or  *
 *(at your option) any later version.                                     *
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
using namespace frepple;

namespace frepple
{

DECLARE_EXPORT const XMLtag Tags::tag_abortonerror("ABORTONERROR");
DECLARE_EXPORT const XMLtag Tags::tag_action("ACTION");
DECLARE_EXPORT const XMLtag Tags::tag_after("AFTER");
DECLARE_EXPORT const XMLtag Tags::tag_alternate("ALTERNATE");
DECLARE_EXPORT const XMLtag Tags::tag_alternates("ALTERNATES");
DECLARE_EXPORT const XMLtag Tags::tag_before("BEFORE");
DECLARE_EXPORT const XMLtag Tags::tag_bucket("BUCKET");
DECLARE_EXPORT const XMLtag Tags::tag_buckets("BUCKETS");
DECLARE_EXPORT const XMLtag Tags::tag_buffer("BUFFER");
DECLARE_EXPORT const XMLtag Tags::tag_buffers("BUFFERS");
DECLARE_EXPORT const XMLtag Tags::tag_calendar("CALENDAR");
DECLARE_EXPORT const XMLtag Tags::tag_calendars("CALENDARS");
DECLARE_EXPORT const XMLtag Tags::tag_category("CATEGORY");
DECLARE_EXPORT const XMLtag Tags::tag_cluster("CLUSTER");
DECLARE_EXPORT const XMLtag Tags::tag_cmdline("CMDLINE");
DECLARE_EXPORT const XMLtag Tags::tag_command("COMMAND");
DECLARE_EXPORT const XMLtag Tags::tag_commands("COMMANDS");
DECLARE_EXPORT const XMLtag Tags::tag_condition("CONDITION");
DECLARE_EXPORT const XMLtag Tags::tag_constraints("CONSTRAINTS");
DECLARE_EXPORT const XMLtag Tags::tag_consuming("CONSUMING");
DECLARE_EXPORT const XMLtag Tags::tag_content("CONTENT");
DECLARE_EXPORT const XMLtag Tags::tag_current("CURRENT");
DECLARE_EXPORT const XMLtag Tags::tag_customer("CUSTOMER");
DECLARE_EXPORT const XMLtag Tags::tag_customers("CUSTOMERS");
DECLARE_EXPORT const XMLtag Tags::tag_data("DATA");
DECLARE_EXPORT const XMLtag Tags::tag_date("DATE");
DECLARE_EXPORT const XMLtag Tags::tag_dates("DATES");
DECLARE_EXPORT const XMLtag Tags::tag_demand("DEMAND");
DECLARE_EXPORT const XMLtag Tags::tag_demands("DEMANDS");
DECLARE_EXPORT const XMLtag Tags::tag_description("DESCRIPTION");
DECLARE_EXPORT const XMLtag Tags::tag_detectproblems("DETECTPROBLEMS");
DECLARE_EXPORT const XMLtag Tags::tag_discrete("DISCRETE");
DECLARE_EXPORT const XMLtag Tags::tag_due("DUE");
DECLARE_EXPORT const XMLtag Tags::tag_duration("DURATION");
DECLARE_EXPORT const XMLtag Tags::tag_duration_per("DURATION_PER");
DECLARE_EXPORT const XMLtag Tags::tag_else("ELSE");
DECLARE_EXPORT const XMLtag Tags::tag_end("END");
DECLARE_EXPORT const XMLtag Tags::tag_epst("EPST");
DECLARE_EXPORT const XMLtag Tags::tag_fence("FENCE");
DECLARE_EXPORT const XMLtag Tags::tag_factor("FACTOR");
DECLARE_EXPORT const XMLtag Tags::tag_filename("FILENAME");
DECLARE_EXPORT const XMLtag Tags::tag_flow("FLOW");
DECLARE_EXPORT const XMLtag Tags::tag_flow_plan("FLOW_PLAN");
DECLARE_EXPORT const XMLtag Tags::tag_flow_plans("FLOW_PLANS");
DECLARE_EXPORT const XMLtag Tags::tag_flows("FLOWS");
DECLARE_EXPORT const XMLtag Tags::tag_headeratts("HEADERATTS");
DECLARE_EXPORT const XMLtag Tags::tag_headerstart("HEADERSTART");
DECLARE_EXPORT const XMLtag Tags::tag_id("ID");
DECLARE_EXPORT const XMLtag Tags::tag_item("ITEM");
DECLARE_EXPORT const XMLtag Tags::tag_items("ITEMS");
DECLARE_EXPORT const XMLtag Tags::tag_leadtime("LEADTIME");
DECLARE_EXPORT const XMLtag Tags::tag_level("LEVEL");
DECLARE_EXPORT const XMLtag Tags::tag_load("LOAD");
DECLARE_EXPORT const XMLtag Tags::tag_load_plan("LOAD_PLAN");
DECLARE_EXPORT const XMLtag Tags::tag_load_plans("LOAD_PLANS");
DECLARE_EXPORT const XMLtag Tags::tag_loads("LOADS");
DECLARE_EXPORT const XMLtag Tags::tag_location("LOCATION");
DECLARE_EXPORT const XMLtag Tags::tag_locations("LOCATIONS");
DECLARE_EXPORT const XMLtag Tags::tag_locked("LOCKED");
DECLARE_EXPORT const XMLtag Tags::tag_logfile("LOGFILE");
DECLARE_EXPORT const XMLtag Tags::tag_loglevel("LOGLEVEL");
DECLARE_EXPORT const XMLtag Tags::tag_lpst("LPST");
DECLARE_EXPORT const XMLtag Tags::tag_maximum("MAXIMUM");
DECLARE_EXPORT const XMLtag Tags::tag_maxinterval("MAXINTERVAL");
DECLARE_EXPORT const XMLtag Tags::tag_maxinventory("MAXINVENTORY");
DECLARE_EXPORT const XMLtag Tags::tag_maxlateness("MAXLATENESS");
DECLARE_EXPORT const XMLtag Tags::tag_maxparallel("MAXPARALLEL");
DECLARE_EXPORT const XMLtag Tags::tag_members("MEMBERS");
DECLARE_EXPORT const XMLtag Tags::tag_minimum("MINIMUM");
DECLARE_EXPORT const XMLtag Tags::tag_mininterval("MININTERVAL");
DECLARE_EXPORT const XMLtag Tags::tag_mininventory("MININVENTORY");
DECLARE_EXPORT const XMLtag Tags::tag_mode("MODE");
DECLARE_EXPORT const XMLtag Tags::tag_name("NAME");
DECLARE_EXPORT const XMLtag Tags::tag_onhand("ONHAND");
DECLARE_EXPORT const XMLtag Tags::tag_operation("OPERATION");
DECLARE_EXPORT const XMLtag Tags::tag_operation_plan("OPERATION_PLAN");
DECLARE_EXPORT const XMLtag Tags::tag_operation_plans("OPERATION_PLANS");
DECLARE_EXPORT const XMLtag Tags::tag_operations("OPERATIONS");
DECLARE_EXPORT const XMLtag Tags::tag_owner("OWNER");
DECLARE_EXPORT const XMLtag Tags::tag_parameter("PARAMETER");
DECLARE_EXPORT const XMLtag Tags::tag_pegging("PEGGING");
DECLARE_EXPORT const XMLtag Tags::tag_plan("PLAN");
DECLARE_EXPORT const XMLtag Tags::tag_policy("POLICY");
DECLARE_EXPORT const XMLtag Tags::tag_posttime("POSTTIME");
DECLARE_EXPORT const XMLtag Tags::tag_pretime("PRETIME");
DECLARE_EXPORT const XMLtag Tags::tag_priority("PRIORITY");
DECLARE_EXPORT const XMLtag Tags::tag_problem("PROBLEM");
DECLARE_EXPORT const XMLtag Tags::tag_problems("PROBLEMS");
DECLARE_EXPORT const XMLtag Tags::tag_producing("PRODUCING");
DECLARE_EXPORT const XMLtag Tags::tag_quantity("QUANTITY");
DECLARE_EXPORT const XMLtag Tags::tag_resource("RESOURCE");
DECLARE_EXPORT const XMLtag Tags::tag_resources("RESOURCES");
DECLARE_EXPORT const XMLtag Tags::tag_size_maximum("SIZE_MAXIMUM");
DECLARE_EXPORT const XMLtag Tags::tag_size_minimum("SIZE_MINIMUM");
DECLARE_EXPORT const XMLtag Tags::tag_size_multiple("SIZE_MULTIPLE");
DECLARE_EXPORT const XMLtag Tags::tag_solver("SOLVER");
DECLARE_EXPORT const XMLtag Tags::tag_solvers("SOLVERS");
DECLARE_EXPORT const XMLtag Tags::tag_start("START");
DECLARE_EXPORT const XMLtag Tags::tag_startorend("STARTOREND");
DECLARE_EXPORT const XMLtag Tags::tag_steps("STEPS");
DECLARE_EXPORT const XMLtag Tags::tag_subcategory("SUBCATEGORY");
DECLARE_EXPORT const XMLtag Tags::tag_supply("SUPPLY");
DECLARE_EXPORT const XMLtag Tags::tag_then("THEN");
DECLARE_EXPORT const XMLtag Tags::tag_type("xsi:type");  // @todo this assumes the definition of XSI namespace is present
DECLARE_EXPORT const XMLtag Tags::tag_unspecified("UNSPECIFIED");
DECLARE_EXPORT const XMLtag Tags::tag_url("URL");
DECLARE_EXPORT const XMLtag Tags::tag_usage("USAGE");
DECLARE_EXPORT const XMLtag Tags::tag_validate("VALIDATE");
DECLARE_EXPORT const XMLtag Tags::tag_value("VALUE");
DECLARE_EXPORT const XMLtag Tags::tag_variable("VARIABLE");
DECLARE_EXPORT const XMLtag Tags::tag_verbose("VERBOSE");

}
