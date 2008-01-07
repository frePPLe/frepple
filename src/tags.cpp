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

DECLARE_EXPORT const XMLtag Tags::tag_abortonerror("abortonerror");
DECLARE_EXPORT const XMLtag Tags::tag_action("action");
DECLARE_EXPORT const XMLtag Tags::tag_after("after");
DECLARE_EXPORT const XMLtag Tags::tag_alternate("alternate");
DECLARE_EXPORT const XMLtag Tags::tag_alternates("alternates");
DECLARE_EXPORT const XMLtag Tags::tag_before("before");
DECLARE_EXPORT const XMLtag Tags::tag_bucket("bucket");
DECLARE_EXPORT const XMLtag Tags::tag_buckets("buckets");
DECLARE_EXPORT const XMLtag Tags::tag_buffer("buffer");
DECLARE_EXPORT const XMLtag Tags::tag_buffers("buffers");
DECLARE_EXPORT const XMLtag Tags::tag_calendar("calendar");
DECLARE_EXPORT const XMLtag Tags::tag_calendars("calendars");
DECLARE_EXPORT const XMLtag Tags::tag_category("category");
DECLARE_EXPORT const XMLtag Tags::tag_cluster("cluster");
DECLARE_EXPORT const XMLtag Tags::tag_cmdline("cmdline");
DECLARE_EXPORT const XMLtag Tags::tag_command("command");
DECLARE_EXPORT const XMLtag Tags::tag_commands("commands");
DECLARE_EXPORT const XMLtag Tags::tag_condition("condition");
DECLARE_EXPORT const XMLtag Tags::tag_constraints("constraints");
DECLARE_EXPORT const XMLtag Tags::tag_consuming("consuming");
DECLARE_EXPORT const XMLtag Tags::tag_content("content");
DECLARE_EXPORT const XMLtag Tags::tag_current("current");
DECLARE_EXPORT const XMLtag Tags::tag_customer("customer");
DECLARE_EXPORT const XMLtag Tags::tag_customers("customers");
DECLARE_EXPORT const XMLtag Tags::tag_data("data");
DECLARE_EXPORT const XMLtag Tags::tag_date("date");
DECLARE_EXPORT const XMLtag Tags::tag_dates("dates");
DECLARE_EXPORT const XMLtag Tags::tag_demand("demand");
DECLARE_EXPORT const XMLtag Tags::tag_demands("demands");
DECLARE_EXPORT const XMLtag Tags::tag_description("description");
DECLARE_EXPORT const XMLtag Tags::tag_detectproblems("detectproblems");
DECLARE_EXPORT const XMLtag Tags::tag_discrete("discrete");
DECLARE_EXPORT const XMLtag Tags::tag_due("due");
DECLARE_EXPORT const XMLtag Tags::tag_duration("duration");
DECLARE_EXPORT const XMLtag Tags::tag_duration_per("duration_per");
DECLARE_EXPORT const XMLtag Tags::tag_effective_start("effective_start");
DECLARE_EXPORT const XMLtag Tags::tag_effective_end("effective_end");
DECLARE_EXPORT const XMLtag Tags::tag_else("else");
DECLARE_EXPORT const XMLtag Tags::tag_end("end");
DECLARE_EXPORT const XMLtag Tags::tag_epst("epst");
DECLARE_EXPORT const XMLtag Tags::tag_fence("fence");
DECLARE_EXPORT const XMLtag Tags::tag_factor("factor");
DECLARE_EXPORT const XMLtag Tags::tag_filename("filename");
DECLARE_EXPORT const XMLtag Tags::tag_flow("flow");
DECLARE_EXPORT const XMLtag Tags::tag_flow_plan("flow_plan");
DECLARE_EXPORT const XMLtag Tags::tag_flow_plans("flow_plans");
DECLARE_EXPORT const XMLtag Tags::tag_flows("flows");
DECLARE_EXPORT const XMLtag Tags::tag_headeratts("headeratts");
DECLARE_EXPORT const XMLtag Tags::tag_headerstart("headerstart");
DECLARE_EXPORT const XMLtag Tags::tag_id("id");
DECLARE_EXPORT const XMLtag Tags::tag_item("item");
DECLARE_EXPORT const XMLtag Tags::tag_items("items");
DECLARE_EXPORT const XMLtag Tags::tag_leadtime("leadtime");
DECLARE_EXPORT const XMLtag Tags::tag_level("level");
DECLARE_EXPORT const XMLtag Tags::tag_load("load");
DECLARE_EXPORT const XMLtag Tags::tag_load_plan("load_plan");
DECLARE_EXPORT const XMLtag Tags::tag_load_plans("load_plans");
DECLARE_EXPORT const XMLtag Tags::tag_loads("loads");
DECLARE_EXPORT const XMLtag Tags::tag_location("location");
DECLARE_EXPORT const XMLtag Tags::tag_locations("locations");
DECLARE_EXPORT const XMLtag Tags::tag_locked("locked");
DECLARE_EXPORT const XMLtag Tags::tag_logfile("logfile");
DECLARE_EXPORT const XMLtag Tags::tag_loglevel("loglevel");
DECLARE_EXPORT const XMLtag Tags::tag_lpst("lpst");
DECLARE_EXPORT const XMLtag Tags::tag_maximum("maximum");
DECLARE_EXPORT const XMLtag Tags::tag_maxinterval("maxinterval");
DECLARE_EXPORT const XMLtag Tags::tag_maxinventory("maxinventory");
DECLARE_EXPORT const XMLtag Tags::tag_maxlateness("maxlateness");
DECLARE_EXPORT const XMLtag Tags::tag_maxparallel("maxparallel");
DECLARE_EXPORT const XMLtag Tags::tag_members("members");
DECLARE_EXPORT const XMLtag Tags::tag_minimum("minimum");
DECLARE_EXPORT const XMLtag Tags::tag_mininterval("mininterval");
DECLARE_EXPORT const XMLtag Tags::tag_mininventory("mininventory");
DECLARE_EXPORT const XMLtag Tags::tag_minshipment("minshipment");
DECLARE_EXPORT const XMLtag Tags::tag_mode("mode");
DECLARE_EXPORT const XMLtag Tags::tag_name("name");
DECLARE_EXPORT const XMLtag Tags::tag_onhand("onhand");
DECLARE_EXPORT const XMLtag Tags::tag_operation("operation");
DECLARE_EXPORT const XMLtag Tags::tag_operation_plan("operation_plan");
DECLARE_EXPORT const XMLtag Tags::tag_operation_plans("operation_plans");
DECLARE_EXPORT const XMLtag Tags::tag_operations("operations");
DECLARE_EXPORT const XMLtag Tags::tag_owner("owner");
DECLARE_EXPORT const XMLtag Tags::tag_parameter("parameter");
DECLARE_EXPORT const XMLtag Tags::tag_pegging("pegging");
DECLARE_EXPORT const XMLtag Tags::tag_plan("plan");
DECLARE_EXPORT const XMLtag Tags::tag_posttime("posttime");
DECLARE_EXPORT const XMLtag Tags::tag_pretime("pretime");
DECLARE_EXPORT const XMLtag Tags::tag_priority("priority");
DECLARE_EXPORT const XMLtag Tags::tag_problem("problem");
DECLARE_EXPORT const XMLtag Tags::tag_problems("problems");
DECLARE_EXPORT const XMLtag Tags::tag_producing("producing");
DECLARE_EXPORT const XMLtag Tags::tag_quantity("quantity");
DECLARE_EXPORT const XMLtag Tags::tag_resource("resource");
DECLARE_EXPORT const XMLtag Tags::tag_resources("resources");
DECLARE_EXPORT const XMLtag Tags::tag_size_maximum("size_maximum");
DECLARE_EXPORT const XMLtag Tags::tag_size_minimum("size_minimum");
DECLARE_EXPORT const XMLtag Tags::tag_size_multiple("size_multiple");
DECLARE_EXPORT const XMLtag Tags::tag_solver("solver");
DECLARE_EXPORT const XMLtag Tags::tag_solvers("solvers");
DECLARE_EXPORT const XMLtag Tags::tag_start("start");
DECLARE_EXPORT const XMLtag Tags::tag_startorend("startorend");
DECLARE_EXPORT const XMLtag Tags::tag_steps("steps");
DECLARE_EXPORT const XMLtag Tags::tag_subcategory("subcategory");
DECLARE_EXPORT const XMLtag Tags::tag_supply("supply");
DECLARE_EXPORT const XMLtag Tags::tag_then("then");
DECLARE_EXPORT const XMLtag Tags::tag_type("xsi:type");  // @todo this assumes the definition of XSI namespace is present
DECLARE_EXPORT const XMLtag Tags::tag_url("url");
DECLARE_EXPORT const XMLtag Tags::tag_usage("usage");
DECLARE_EXPORT const XMLtag Tags::tag_validate("validate");
DECLARE_EXPORT const XMLtag Tags::tag_value("value");
DECLARE_EXPORT const XMLtag Tags::tag_variable("variable");
DECLARE_EXPORT const XMLtag Tags::tag_verbose("verbose");
DECLARE_EXPORT const XMLtag Tags::tag_weight("weight");

}
