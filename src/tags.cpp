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

DECLARE_EXPORT const Keyword Tags::action("action");
DECLARE_EXPORT const Keyword Tags::alternate("alternate");
DECLARE_EXPORT const Keyword Tags::alternate_name("alternate_name");
DECLARE_EXPORT const Keyword Tags::approved("approved");
DECLARE_EXPORT const Keyword Tags::autocommit("autocommit");
DECLARE_EXPORT const Keyword Tags::available("available");
DECLARE_EXPORT const Keyword Tags::booleanproperty("booleanproperty");
DECLARE_EXPORT const Keyword Tags::bucket("bucket");
DECLARE_EXPORT const Keyword Tags::buckets("buckets");
DECLARE_EXPORT const Keyword Tags::buffer("buffer");
DECLARE_EXPORT const Keyword Tags::buffers("buffers");
DECLARE_EXPORT const Keyword Tags::calendar("calendar");
DECLARE_EXPORT const Keyword Tags::calendars("calendars");
DECLARE_EXPORT const Keyword Tags::category("category");
DECLARE_EXPORT const Keyword Tags::cluster("cluster");
DECLARE_EXPORT const Keyword Tags::confirmed("confirmed");
DECLARE_EXPORT const Keyword Tags::constraints("constraints");
DECLARE_EXPORT const Keyword Tags::consume_material("consume_material");
DECLARE_EXPORT const Keyword Tags::consume_capacity("consume_capacity");
DECLARE_EXPORT const Keyword Tags::consuming("consuming");
DECLARE_EXPORT const Keyword Tags::consuming_date("consuming_date");
DECLARE_EXPORT const Keyword Tags::content("content");
DECLARE_EXPORT const Keyword Tags::cost("cost");
DECLARE_EXPORT const Keyword Tags::criticality("criticality");
DECLARE_EXPORT const Keyword Tags::current("current");
DECLARE_EXPORT const Keyword Tags::customer("customer");
DECLARE_EXPORT const Keyword Tags::customers("customers");
DECLARE_EXPORT const Keyword Tags::data("data");
DECLARE_EXPORT const Keyword Tags::date("date");
DECLARE_EXPORT const Keyword Tags::dateproperty("dateproperty");
DECLARE_EXPORT const Keyword Tags::dates("dates");
DECLARE_EXPORT const Keyword Tags::days("days");
DECLARE_EXPORT const Keyword Tags::deflt("default");
DECLARE_EXPORT const Keyword Tags::demand("demand");
DECLARE_EXPORT const Keyword Tags::demands("demands");
DECLARE_EXPORT const Keyword Tags::description("description");
DECLARE_EXPORT const Keyword Tags::destination("destination");
DECLARE_EXPORT const Keyword Tags::detectproblems("detectproblems");
DECLARE_EXPORT const Keyword Tags::discrete("discrete");
DECLARE_EXPORT const Keyword Tags::doubleproperty("doubleproperty");
DECLARE_EXPORT const Keyword Tags::due("due");
DECLARE_EXPORT const Keyword Tags::duration("duration");
DECLARE_EXPORT const Keyword Tags::duration_per("duration_per");
DECLARE_EXPORT const Keyword Tags::effective_start("effective_start");
DECLARE_EXPORT const Keyword Tags::effective_end("effective_end");
DECLARE_EXPORT const Keyword Tags::end("end");
DECLARE_EXPORT const Keyword Tags::enddate("enddate");
DECLARE_EXPORT const Keyword Tags::endtime("endtime");
DECLARE_EXPORT const Keyword Tags::entity("entity");
DECLARE_EXPORT const Keyword Tags::fence("fence");
DECLARE_EXPORT const Keyword Tags::factor("factor");
DECLARE_EXPORT const Keyword Tags::filename("filename");
DECLARE_EXPORT const Keyword Tags::flow("flow");
DECLARE_EXPORT const Keyword Tags::flowplan("flowplan");
DECLARE_EXPORT const Keyword Tags::flowplans("flowplans");
DECLARE_EXPORT const Keyword Tags::flows("flows");
DECLARE_EXPORT const Keyword Tags::fromsetup("fromsetup");
DECLARE_EXPORT const Keyword Tags::headeratts("headeratts");
DECLARE_EXPORT const Keyword Tags::headerstart("headerstart");
DECLARE_EXPORT const Keyword Tags::hidden("hidden");
DECLARE_EXPORT const Keyword Tags::id("id");
DECLARE_EXPORT const Keyword Tags::item("item");
DECLARE_EXPORT const Keyword Tags::itemdistribution("itemdistribution");
DECLARE_EXPORT const Keyword Tags::itemdistributions("itemdistributions");
DECLARE_EXPORT const Keyword Tags::items("items");
DECLARE_EXPORT const Keyword Tags::itemsupplier("itemsupplier");
DECLARE_EXPORT const Keyword Tags::itemsuppliers("itemsuppliers");
DECLARE_EXPORT const Keyword Tags::leadtime("leadtime");
DECLARE_EXPORT const Keyword Tags::level("level");
DECLARE_EXPORT const Keyword Tags::load("load");
DECLARE_EXPORT const Keyword Tags::loadplan("loadplan");
DECLARE_EXPORT const Keyword Tags::loadplans("loadplans");
DECLARE_EXPORT const Keyword Tags::loads("loads");
DECLARE_EXPORT const Keyword Tags::location("location");
DECLARE_EXPORT const Keyword Tags::locations("locations");
DECLARE_EXPORT const Keyword Tags::locked("locked");
DECLARE_EXPORT const Keyword Tags::logfile("logfile");
DECLARE_EXPORT const Keyword Tags::loglevel("loglevel");
DECLARE_EXPORT const Keyword Tags::maxearly("maxearly");
DECLARE_EXPORT const Keyword Tags::maximum("maximum");
DECLARE_EXPORT const Keyword Tags::maximum_calendar("maximum_calendar");
DECLARE_EXPORT const Keyword Tags::maxinterval("maxinterval");
DECLARE_EXPORT const Keyword Tags::maxinventory("maxinventory");
DECLARE_EXPORT const Keyword Tags::maxlateness("maxlateness");
DECLARE_EXPORT const Keyword Tags::members("members");
DECLARE_EXPORT const Keyword Tags::minimum("minimum");
DECLARE_EXPORT const Keyword Tags::minimum_calendar("minimum_calendar");
DECLARE_EXPORT const Keyword Tags::mininterval("mininterval");
DECLARE_EXPORT const Keyword Tags::mininventory("mininventory");
DECLARE_EXPORT const Keyword Tags::minshipment("minshipment");
DECLARE_EXPORT const Keyword Tags::name("name");
DECLARE_EXPORT const Keyword Tags::onhand("onhand");
DECLARE_EXPORT const Keyword Tags::operation("operation");
DECLARE_EXPORT const Keyword Tags::operationplan("operationplan");
DECLARE_EXPORT const Keyword Tags::operationplans("operationplans");
DECLARE_EXPORT const Keyword Tags::operations("operations");
DECLARE_EXPORT const Keyword Tags::origin("origin");
DECLARE_EXPORT const Keyword Tags::owner("owner");
DECLARE_EXPORT const Keyword Tags::pegging("pegging");
DECLARE_EXPORT const Keyword Tags::pegging_upstream("pegging_upstream");
DECLARE_EXPORT const Keyword Tags::pegging_downstream("pegging_downstream");
DECLARE_EXPORT const Keyword Tags::percent("percent");
DECLARE_EXPORT const Keyword Tags::plan("plan");
DECLARE_EXPORT const Keyword Tags::plantype("plantype");
DECLARE_EXPORT const Keyword Tags::posttime("posttime");
DECLARE_EXPORT const Keyword Tags::price("price");
DECLARE_EXPORT const Keyword Tags::priority("priority");
DECLARE_EXPORT const Keyword Tags::problem("problem");
DECLARE_EXPORT const Keyword Tags::problems("problems");
DECLARE_EXPORT const Keyword Tags::produce_material("produce_material");
DECLARE_EXPORT const Keyword Tags::producing("producing");
DECLARE_EXPORT const Keyword Tags::producing_date("producing_date");
DECLARE_EXPORT const Keyword Tags::property("property");
DECLARE_EXPORT const Keyword Tags::proposed("proposed");
DECLARE_EXPORT const Keyword Tags::quantity("quantity");
DECLARE_EXPORT const Keyword Tags::quantity_buffer("quantity_buffer");
DECLARE_EXPORT const Keyword Tags::quantity_demand("quantity_demand");
DECLARE_EXPORT const Keyword Tags::reference("reference");
DECLARE_EXPORT const Keyword Tags::resource("resource");
DECLARE_EXPORT const Keyword Tags::resources("resources");
DECLARE_EXPORT const Keyword Tags::resourceskill("resourceskill");
DECLARE_EXPORT const Keyword Tags::resourceskills("resourceskills");
DECLARE_EXPORT const Keyword Tags::rule("rule");
DECLARE_EXPORT const Keyword Tags::rules("rules");
DECLARE_EXPORT const Keyword Tags::search("search");
DECLARE_EXPORT const Keyword Tags::setup("setup");
DECLARE_EXPORT const Keyword Tags::setupmatrices("setupmatrices");
DECLARE_EXPORT const Keyword Tags::setupmatrix("setupmatrix");
DECLARE_EXPORT const Keyword Tags::size_maximum("size_maximum");
DECLARE_EXPORT const Keyword Tags::size_minimum("size_minimum");
DECLARE_EXPORT const Keyword Tags::size_minimum_calendar("size_minimum_calendar");
DECLARE_EXPORT const Keyword Tags::size_multiple("size_multiple");
DECLARE_EXPORT const Keyword Tags::skill("skill");
DECLARE_EXPORT const Keyword Tags::skills("skills");
DECLARE_EXPORT const Keyword Tags::solver("solver");
DECLARE_EXPORT const Keyword Tags::solvers("solvers");
DECLARE_EXPORT const Keyword Tags::source("source");
DECLARE_EXPORT const Keyword Tags::start("start");
DECLARE_EXPORT const Keyword Tags::startorend("startorend");
DECLARE_EXPORT const Keyword Tags::startdate("startdate");
DECLARE_EXPORT const Keyword Tags::starttime("starttime");
DECLARE_EXPORT const Keyword Tags::status("status");
DECLARE_EXPORT const Keyword Tags::stringproperty("stringproperty");
DECLARE_EXPORT const Keyword Tags::subcategory("subcategory");
DECLARE_EXPORT const Keyword Tags::suboperation("suboperation");
DECLARE_EXPORT const Keyword Tags::suboperations("suboperations");
DECLARE_EXPORT const Keyword Tags::supplier("supplier");
DECLARE_EXPORT const Keyword Tags::suppliers("suppliers");
DECLARE_EXPORT const Keyword Tags::supply("supply");
DECLARE_EXPORT const Keyword Tags::tool("tool");
DECLARE_EXPORT const Keyword Tags::tosetup("tosetup");
// The next line requires the namespace "xsi" to be defined.
// It must refer to "http://www.w3.org/2001/XMLSchema-instance"
// This is required to support subclassing in the XML schema.
DECLARE_EXPORT const Keyword Tags::type("type","xsi");
DECLARE_EXPORT const Keyword Tags::unavailable("unavailable");
DECLARE_EXPORT const Keyword Tags::userexit_buffer("userexit_buffer");
DECLARE_EXPORT const Keyword Tags::userexit_demand("userexit_demand");
DECLARE_EXPORT const Keyword Tags::userexit_flow("userexit_flow");
DECLARE_EXPORT const Keyword Tags::userexit_operation("userexit_operation");
DECLARE_EXPORT const Keyword Tags::userexit_resource("userexit_resource");
DECLARE_EXPORT const Keyword Tags::value("value");
DECLARE_EXPORT const Keyword Tags::variable("variable");
DECLARE_EXPORT const Keyword Tags::verbose("verbose");
DECLARE_EXPORT const Keyword Tags::weight("weight");

} // end namespace
} // end namespace
