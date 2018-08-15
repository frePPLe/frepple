/***************************************************************************
 *                                                                         *
 * Copyright(C) 2007-2015 by frePPLe bvba                                  *
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

const Keyword Tags::action("action");
const Keyword Tags::alternate("alternate");
const Keyword Tags::alternates("alternates");
const Keyword Tags::alternate_name("alternate_name");
const Keyword Tags::approved("approved");
const Keyword Tags::autocommit("autocommit");
const Keyword Tags::available("available");
const Keyword Tags::booleanproperty("booleanproperty");
const Keyword Tags::bucket("bucket");
const Keyword Tags::buckets("buckets");
const Keyword Tags::buffer("buffer");
const Keyword Tags::buffers("buffers");
const Keyword Tags::calendar("calendar");
const Keyword Tags::calendars("calendars");
const Keyword Tags::category("category");
const Keyword Tags::cluster("cluster");
const Keyword Tags::confirmed("confirmed");
const Keyword Tags::constraints("constraints");
const Keyword Tags::consume_material("consume_material");
const Keyword Tags::consume_capacity("consume_capacity");
const Keyword Tags::consuming("consuming");
const Keyword Tags::consuming_date("consuming_date");
const Keyword Tags::content("content");
const Keyword Tags::cost("cost");
const Keyword Tags::criticality("criticality");
const Keyword Tags::create("create");
const Keyword Tags::current("current");
const Keyword Tags::customer("customer");
const Keyword Tags::customers("customers");
const Keyword Tags::data("data");
const Keyword Tags::date("date");
const Keyword Tags::dateproperty("dateproperty");
const Keyword Tags::dates("dates");
const Keyword Tags::days("days");
const Keyword Tags::deflt("default");
const Keyword Tags::delay("delay");
const Keyword Tags::delivery("delivery");
const Keyword Tags::delivery_operation("delivery_operation");
const Keyword Tags::demand("demand");
const Keyword Tags::demands("demands");
const Keyword Tags::description("description");
const Keyword Tags::destination("destination");
const Keyword Tags::detectproblems("detectproblems");
const Keyword Tags::discrete("discrete");
const Keyword Tags::doubleproperty("doubleproperty");
const Keyword Tags::due("due");
const Keyword Tags::duration("duration");
const Keyword Tags::duration_per("duration_per");
const Keyword Tags::efficiency("efficiency");
const Keyword Tags::efficiency_calendar("efficiency_calendar");
const Keyword Tags::effective_start("effective_start");
const Keyword Tags::effective_end("effective_end");
const Keyword Tags::end("end");
const Keyword Tags::end_force("end_force");
const Keyword Tags::enddate("enddate");
const Keyword Tags::endtime("endtime");
const Keyword Tags::entity("entity");
const Keyword Tags::factor("factor");
const Keyword Tags::feasible("feasible");
const Keyword Tags::fence("fence");
const Keyword Tags::filename("filename");
const Keyword Tags::flow("flow");
const Keyword Tags::flowplan("flowplan");
const Keyword Tags::flowplans("flowplans");
const Keyword Tags::flows("flows");
const Keyword Tags::fromsetup("fromsetup");
const Keyword Tags::hasSuperOperations("hasSuperOperations");
const Keyword Tags::headeratts("headeratts");
const Keyword Tags::headerstart("headerstart");
const Keyword Tags::hidden("hidden");
const Keyword Tags::id("id");
const Keyword Tags::interruption("interruption");
const Keyword Tags::interruptions("interruptions");
const Keyword Tags::item("item");
const Keyword Tags::itemdistribution("itemdistribution");
const Keyword Tags::itemdistributions("itemdistributions");
const Keyword Tags::items("items");
const Keyword Tags::itemsupplier("itemsupplier");
const Keyword Tags::itemsuppliers("itemsuppliers");
const Keyword Tags::leadtime("leadtime");
const Keyword Tags::level("level");
const Keyword Tags::load("load");
const Keyword Tags::loadplan("loadplan");
const Keyword Tags::loadplans("loadplans");
const Keyword Tags::loads("loads");
const Keyword Tags::location("location");
const Keyword Tags::locations("locations");
const Keyword Tags::locked("locked");
const Keyword Tags::logfile("logfile");
const Keyword Tags::loglevel("loglevel");
const Keyword Tags::maxearly("maxearly");
const Keyword Tags::maximum("maximum");
const Keyword Tags::maximum_calendar("maximum_calendar");
const Keyword Tags::maxinterval("maxinterval");
const Keyword Tags::maxinventory("maxinventory");
const Keyword Tags::maxlateness("maxlateness");
const Keyword Tags::members("members");
const Keyword Tags::minimum("minimum");
const Keyword Tags::minimum_calendar("minimum_calendar");
const Keyword Tags::mininterval("mininterval");
const Keyword Tags::mininventory("mininventory");
const Keyword Tags::minshipment("minshipment");
const Keyword Tags::name("name");
const Keyword Tags::offset("offset");
const Keyword Tags::onhand("onhand");
const Keyword Tags::operation("operation");
const Keyword Tags::operationplan("operationplan");
const Keyword Tags::operationplans("operationplans");
const Keyword Tags::operations("operations");
const Keyword Tags::ordertype("ordertype");
const Keyword Tags::origin("origin");
const Keyword Tags::owner("owner");
const Keyword Tags::pegging("pegging");
const Keyword Tags::pegging_demand("pegging_demand");
const Keyword Tags::pegging_downstream("pegging_downstream");
const Keyword Tags::pegging_upstream("pegging_upstream");
const Keyword Tags::percent("percent");
const Keyword Tags::period_of_cover("period_of_cover");
const Keyword Tags::plan("plan");
const Keyword Tags::planned_quantity("planned_quantity");
const Keyword Tags::plantype("plantype");
const Keyword Tags::posttime("posttime");
const Keyword Tags::priority("priority");
const Keyword Tags::problem("problem");
const Keyword Tags::problems("problems");
const Keyword Tags::produce_material("produce_material");
const Keyword Tags::producing("producing");
const Keyword Tags::property("property");
const Keyword Tags::proposed("proposed");
const Keyword Tags::quantity("quantity");
const Keyword Tags::quantity_fixed("quantity_fixed");
const Keyword Tags::reference("reference");
const Keyword Tags::resource("resource");
const Keyword Tags::resources("resources");
const Keyword Tags::resourceskill("resourceskill");
const Keyword Tags::resourceskills("resourceskills");
const Keyword Tags::resource_qty("resource_qty");
const Keyword Tags::rule("rule");
const Keyword Tags::rules("rules");
const Keyword Tags::search("search");
const Keyword Tags::setup("setup");
const Keyword Tags::setupend("setupend");
const Keyword Tags::setupmatrices("setupmatrices");
const Keyword Tags::setupmatrix("setupmatrix");
const Keyword Tags::size_maximum("size_maximum");
const Keyword Tags::size_minimum("size_minimum");
const Keyword Tags::size_minimum_calendar("size_minimum_calendar");
const Keyword Tags::size_multiple("size_multiple");
const Keyword Tags::skill("skill");
const Keyword Tags::skills("skills");
const Keyword Tags::solver("solver");
const Keyword Tags::solvers("solvers");
const Keyword Tags::source("source");
const Keyword Tags::start("start");
const Keyword Tags::start_force("start_force");
const Keyword Tags::startorend("startorend");
const Keyword Tags::startdate("startdate");
const Keyword Tags::starttime("starttime");
const Keyword Tags::status("status");
const Keyword Tags::stringproperty("stringproperty");
const Keyword Tags::subcategory("subcategory");
const Keyword Tags::suboperation("suboperation");
const Keyword Tags::suboperations("suboperations");
const Keyword Tags::supplier("supplier");
const Keyword Tags::suppliers("suppliers");
const Keyword Tags::supply("supply");
const Keyword Tags::tool("tool");
const Keyword Tags::tosetup("tosetup");
const Keyword Tags::transferbatch("transferbatch");
// The next line requires the namespace "xsi" to be defined.
// It must refer to "http://www.w3.org/2001/XMLSchema-instance"
// This is required to support subclassing in the XML schema.
const Keyword Tags::type("type","xsi");
const Keyword Tags::unavailable("unavailable");
const Keyword Tags::userexit_buffer("userexit_buffer");
const Keyword Tags::userexit_demand("userexit_demand");
const Keyword Tags::userexit_flow("userexit_flow");
const Keyword Tags::userexit_operation("userexit_operation");
const Keyword Tags::userexit_resource("userexit_resource");
const Keyword Tags::value("value");
const Keyword Tags::variable("variable");
const Keyword Tags::verbose("verbose");
const Keyword Tags::weight("weight");

} // end namespace
} // end namespace
