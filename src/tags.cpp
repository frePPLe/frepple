/***************************************************************************
 *                                                                         *
 * Copyright(C) 2007-2013 by Johan De Taeye, frePPLe bvba                  *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 *(at your option) any later version.                                     *
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

#define FREPPLE_CORE
#include "frepple/utils.h"
using namespace frepple;

namespace frepple
{
namespace utils
{

DECLARE_EXPORT const Keyword Tags::tag_action("action");
DECLARE_EXPORT const Keyword Tags::tag_alternate("alternate");
DECLARE_EXPORT const Keyword Tags::tag_alternates("alternates");
DECLARE_EXPORT const Keyword Tags::tag_autocommit("autocommit");
DECLARE_EXPORT const Keyword Tags::tag_available("available");
DECLARE_EXPORT const Keyword Tags::tag_booleanproperty("booleanproperty");
DECLARE_EXPORT const Keyword Tags::tag_bucket("bucket");
DECLARE_EXPORT const Keyword Tags::tag_buckets("buckets");
DECLARE_EXPORT const Keyword Tags::tag_buffer("buffer");
DECLARE_EXPORT const Keyword Tags::tag_buffers("buffers");
DECLARE_EXPORT const Keyword Tags::tag_calendar("calendar");
DECLARE_EXPORT const Keyword Tags::tag_calendars("calendars");
DECLARE_EXPORT const Keyword Tags::tag_carrying_cost("carrying_cost");
DECLARE_EXPORT const Keyword Tags::tag_category("category");
DECLARE_EXPORT const Keyword Tags::tag_cluster("cluster");
DECLARE_EXPORT const Keyword Tags::tag_constraints("constraints");
DECLARE_EXPORT const Keyword Tags::tag_consume_material("consume_material");
DECLARE_EXPORT const Keyword Tags::tag_consume_capacity("consume_capacity");
DECLARE_EXPORT const Keyword Tags::tag_consuming("consuming");
DECLARE_EXPORT const Keyword Tags::tag_consuming_date("consuming_date");
DECLARE_EXPORT const Keyword Tags::tag_content("content");
DECLARE_EXPORT const Keyword Tags::tag_cost("cost");
DECLARE_EXPORT const Keyword Tags::tag_criticality("criticality");
DECLARE_EXPORT const Keyword Tags::tag_current("current");
DECLARE_EXPORT const Keyword Tags::tag_customer("customer");
DECLARE_EXPORT const Keyword Tags::tag_customers("customers");
DECLARE_EXPORT const Keyword Tags::tag_data("data");
DECLARE_EXPORT const Keyword Tags::tag_date("date");
DECLARE_EXPORT const Keyword Tags::tag_dateproperty("dateproperty");
DECLARE_EXPORT const Keyword Tags::tag_dates("dates");
DECLARE_EXPORT const Keyword Tags::tag_days("days");
DECLARE_EXPORT const Keyword Tags::tag_default("default");
DECLARE_EXPORT const Keyword Tags::tag_demand("demand");
DECLARE_EXPORT const Keyword Tags::tag_demands("demands");
DECLARE_EXPORT const Keyword Tags::tag_description("description");
DECLARE_EXPORT const Keyword Tags::tag_detectproblems("detectproblems");
DECLARE_EXPORT const Keyword Tags::tag_discrete("discrete");
DECLARE_EXPORT const Keyword Tags::tag_doubleproperty("doubleproperty");
DECLARE_EXPORT const Keyword Tags::tag_due("due");
DECLARE_EXPORT const Keyword Tags::tag_duration("duration");
DECLARE_EXPORT const Keyword Tags::tag_duration_per("duration_per");
DECLARE_EXPORT const Keyword Tags::tag_effective_start("effective_start");
DECLARE_EXPORT const Keyword Tags::tag_effective_end("effective_end");
DECLARE_EXPORT const Keyword Tags::tag_end("end");
DECLARE_EXPORT const Keyword Tags::tag_enddate("enddate");
DECLARE_EXPORT const Keyword Tags::tag_endtime("endtime");
DECLARE_EXPORT const Keyword Tags::tag_entity("entity");
DECLARE_EXPORT const Keyword Tags::tag_fence("fence");
DECLARE_EXPORT const Keyword Tags::tag_factor("factor");
DECLARE_EXPORT const Keyword Tags::tag_filename("filename");
DECLARE_EXPORT const Keyword Tags::tag_flow("flow");
DECLARE_EXPORT const Keyword Tags::tag_flowplan("flowplan");
DECLARE_EXPORT const Keyword Tags::tag_flowplans("flowplans");
DECLARE_EXPORT const Keyword Tags::tag_flows("flows");
DECLARE_EXPORT const Keyword Tags::tag_fromsetup("fromsetup");
DECLARE_EXPORT const Keyword Tags::tag_headeratts("headeratts");
DECLARE_EXPORT const Keyword Tags::tag_headerstart("headerstart");
DECLARE_EXPORT const Keyword Tags::tag_hidden("hidden");
DECLARE_EXPORT const Keyword Tags::tag_id("id");
DECLARE_EXPORT const Keyword Tags::tag_item("item");
DECLARE_EXPORT const Keyword Tags::tag_items("items");
DECLARE_EXPORT const Keyword Tags::tag_leadtime("leadtime");
DECLARE_EXPORT const Keyword Tags::tag_level("level");
DECLARE_EXPORT const Keyword Tags::tag_load("load");
DECLARE_EXPORT const Keyword Tags::tag_loadplan("loadplan");
DECLARE_EXPORT const Keyword Tags::tag_loadplans("loadplans");
DECLARE_EXPORT const Keyword Tags::tag_loads("loads");
DECLARE_EXPORT const Keyword Tags::tag_location("location");
DECLARE_EXPORT const Keyword Tags::tag_locations("locations");
DECLARE_EXPORT const Keyword Tags::tag_locked("locked");
DECLARE_EXPORT const Keyword Tags::tag_logfile("logfile");
DECLARE_EXPORT const Keyword Tags::tag_loglevel("loglevel");
DECLARE_EXPORT const Keyword Tags::tag_maxearly("maxearly");
DECLARE_EXPORT const Keyword Tags::tag_maximum("maximum");
DECLARE_EXPORT const Keyword Tags::tag_maximum_calendar("maximum_calendar");
DECLARE_EXPORT const Keyword Tags::tag_maxinterval("maxinterval");
DECLARE_EXPORT const Keyword Tags::tag_maxinventory("maxinventory");
DECLARE_EXPORT const Keyword Tags::tag_maxlateness("maxlateness");
DECLARE_EXPORT const Keyword Tags::tag_members("members");
DECLARE_EXPORT const Keyword Tags::tag_minimum("minimum");
DECLARE_EXPORT const Keyword Tags::tag_minimum_calendar("minimum_calendar");
DECLARE_EXPORT const Keyword Tags::tag_mininterval("mininterval");
DECLARE_EXPORT const Keyword Tags::tag_mininventory("mininventory");
DECLARE_EXPORT const Keyword Tags::tag_minshipment("minshipment");
DECLARE_EXPORT const Keyword Tags::tag_motive("motive");
DECLARE_EXPORT const Keyword Tags::tag_name("name");
DECLARE_EXPORT const Keyword Tags::tag_onhand("onhand");
DECLARE_EXPORT const Keyword Tags::tag_operation("operation");
DECLARE_EXPORT const Keyword Tags::tag_operationplan("operationplan");
DECLARE_EXPORT const Keyword Tags::tag_operationplans("operationplans");
DECLARE_EXPORT const Keyword Tags::tag_operations("operations");
DECLARE_EXPORT const Keyword Tags::tag_owner("owner");
DECLARE_EXPORT const Keyword Tags::tag_parameter("parameter");
DECLARE_EXPORT const Keyword Tags::tag_pegged("pegged");
DECLARE_EXPORT const Keyword Tags::tag_pegging("pegging");
DECLARE_EXPORT const Keyword Tags::tag_percent("percent");
DECLARE_EXPORT const Keyword Tags::tag_plan("plan");
DECLARE_EXPORT const Keyword Tags::tag_plantype("plantype");
DECLARE_EXPORT const Keyword Tags::tag_posttime("posttime");
DECLARE_EXPORT const Keyword Tags::tag_price("price");
DECLARE_EXPORT const Keyword Tags::tag_priority("priority");
DECLARE_EXPORT const Keyword Tags::tag_problem("problem");
DECLARE_EXPORT const Keyword Tags::tag_problems("problems");
DECLARE_EXPORT const Keyword Tags::tag_produce_material("produce_material");
DECLARE_EXPORT const Keyword Tags::tag_producing("producing");
DECLARE_EXPORT const Keyword Tags::tag_producing_date("producing_date");
DECLARE_EXPORT const Keyword Tags::tag_property("property");
DECLARE_EXPORT const Keyword Tags::tag_quantity("quantity");
DECLARE_EXPORT const Keyword Tags::tag_quantity_buffer("quantity_buffer");
DECLARE_EXPORT const Keyword Tags::tag_quantity_demand("quantity_demand");
DECLARE_EXPORT const Keyword Tags::tag_resource("resource");
DECLARE_EXPORT const Keyword Tags::tag_resources("resources");
DECLARE_EXPORT const Keyword Tags::tag_resourceskill("resourceskill");
DECLARE_EXPORT const Keyword Tags::tag_resourceskills("resourceskills");
DECLARE_EXPORT const Keyword Tags::tag_rule("rule");
DECLARE_EXPORT const Keyword Tags::tag_rules("rules");
DECLARE_EXPORT const Keyword Tags::tag_search("search");
DECLARE_EXPORT const Keyword Tags::tag_setup("setup");
DECLARE_EXPORT const Keyword Tags::tag_setupmatrices("setupmatrices");
DECLARE_EXPORT const Keyword Tags::tag_setupmatrix("setupmatrix");
DECLARE_EXPORT const Keyword Tags::tag_size_maximum("size_maximum");
DECLARE_EXPORT const Keyword Tags::tag_size_minimum("size_minimum");
DECLARE_EXPORT const Keyword Tags::tag_size_multiple("size_multiple");
DECLARE_EXPORT const Keyword Tags::tag_skill("skill");
DECLARE_EXPORT const Keyword Tags::tag_skills("skills");
DECLARE_EXPORT const Keyword Tags::tag_solver("solver");
DECLARE_EXPORT const Keyword Tags::tag_solvers("solvers");
DECLARE_EXPORT const Keyword Tags::tag_source("source");
DECLARE_EXPORT const Keyword Tags::tag_start("start");
DECLARE_EXPORT const Keyword Tags::tag_startorend("startorend");
DECLARE_EXPORT const Keyword Tags::tag_startdate("startdate");
DECLARE_EXPORT const Keyword Tags::tag_starttime("starttime");
DECLARE_EXPORT const Keyword Tags::tag_steps("steps");
DECLARE_EXPORT const Keyword Tags::tag_stringproperty("stringproperty");
DECLARE_EXPORT const Keyword Tags::tag_subcategory("subcategory");
DECLARE_EXPORT const Keyword Tags::tag_supplier("supplier");
DECLARE_EXPORT const Keyword Tags::tag_suppliers("suppliers");
DECLARE_EXPORT const Keyword Tags::tag_supply("supply");
DECLARE_EXPORT const Keyword Tags::tag_tosetup("tosetup");
// The next line requires the namespace "xsi" to be defined.
// It must refer to "http://www.w3.org/2001/XMLSchema-instance"
// This is required to support subclassing in the XML schema.
DECLARE_EXPORT const Keyword Tags::tag_type("type","xsi");
DECLARE_EXPORT const Keyword Tags::tag_unavailable("unavailable");
DECLARE_EXPORT const Keyword Tags::tag_userexit_buffer("userexit_buffer");
DECLARE_EXPORT const Keyword Tags::tag_userexit_demand("userexit_demand");
DECLARE_EXPORT const Keyword Tags::tag_userexit_flow("userexit_flow");
DECLARE_EXPORT const Keyword Tags::tag_userexit_operation("userexit_operation");
DECLARE_EXPORT const Keyword Tags::tag_userexit_resource("userexit_resource");
DECLARE_EXPORT const Keyword Tags::tag_validate("validate");
DECLARE_EXPORT const Keyword Tags::tag_value("value");
DECLARE_EXPORT const Keyword Tags::tag_variable("variable");
DECLARE_EXPORT const Keyword Tags::tag_verbose("verbose");
DECLARE_EXPORT const Keyword Tags::tag_weight("weight");

} // end namespace
} // end namespace
