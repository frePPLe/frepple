/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/tags.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
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

#include "frepple/utils.h"
using namespace frepple;

namespace frepple
{

const XMLtag Tags::tag_unspecified ("UNSPECIFIED");
const XMLtag Tags::tag_name ("NAME");
const XMLtag Tags::tag_description ("DESCRIPTION");
const XMLtag Tags::tag_owner ("OWNER");
const XMLtag Tags::tag_members ("MEMBERS");
const XMLtag Tags::tag_plan ("PLAN");
const XMLtag Tags::tag_current ("CURRENT");
const XMLtag Tags::tag_logfile ("LOGFILE");
const XMLtag Tags::tag_operation ("OPERATION");
const XMLtag Tags::tag_buffer ("BUFFER");
const XMLtag Tags::tag_operations ("OPERATIONS");
const XMLtag Tags::tag_buffers ("BUFFERS");
const XMLtag Tags::tag_item ("ITEM");
const XMLtag Tags::tag_items ("ITEMS");
const XMLtag Tags::tag_flows ("FLOWS");
const XMLtag Tags::tag_flow ("FLOW");
const XMLtag Tags::tag_flow_plans ("FLOW_PLANS");
const XMLtag Tags::tag_flow_plan ("FLOW_PLAN");
const XMLtag Tags::tag_problems ("PROBLEMS");
const XMLtag Tags::tag_demands ("DEMANDS");
const XMLtag Tags::tag_producing ("PRODUCING");
const XMLtag Tags::tag_consuming ("CONSUMING");
const XMLtag Tags::tag_level ("LEVEL");
const XMLtag Tags::tag_cluster ("CLUSTER");
const XMLtag Tags::tag_due ("DUE");
const XMLtag Tags::tag_quantity ("QUANTITY");
const XMLtag Tags::tag_priority ("PRIORITY");
const XMLtag Tags::tag_problem ("PROBLEM");
const XMLtag Tags::tag_type ("xsi:type");  // @todo this assumes the definition of XSI namespace is present
const XMLtag Tags::tag_resource ("RESOURCE");
const XMLtag Tags::tag_resources ("RESOURCES");
const XMLtag Tags::tag_dates ("DATES");
const XMLtag Tags::tag_steps ("STEPS");
const XMLtag Tags::tag_duration ("DURATION");
const XMLtag Tags::tag_duration_per ("DURATION_PER");
const XMLtag Tags::tag_delay ("DELAY");
const XMLtag Tags::tag_loads ("LOADS");
const XMLtag Tags::tag_load ("LOAD");
const XMLtag Tags::tag_load_plans ("LOAD_PLANS");
const XMLtag Tags::tag_load_plan ("LOAD_PLAN");
const XMLtag Tags::tag_operation_plans ("OPERATION_PLANS");
const XMLtag Tags::tag_operation_plan ("OPERATION_PLAN");
const XMLtag Tags::tag_locked ("LOCKED");
const XMLtag Tags::tag_id ("ID");
const XMLtag Tags::tag_epst ("EPST");
const XMLtag Tags::tag_lpst ("LPST");
const XMLtag Tags::tag_before ("BEFORE");
const XMLtag Tags::tag_after ("AFTER");
const XMLtag Tags::tag_buckets ("BUCKETS");
const XMLtag Tags::tag_bucket ("BUCKET");
const XMLtag Tags::tag_start ("START");
const XMLtag Tags::tag_end ("END");
const XMLtag Tags::tag_calendar ("CALENDAR");
const XMLtag Tags::tag_calendars ("CALENDARS");
const XMLtag Tags::tag_date ("DATE");
const XMLtag Tags::tag_onhand ("ONHAND");
const XMLtag Tags::tag_locations ("LOCATIONS");
const XMLtag Tags::tag_location ("LOCATION");
const XMLtag Tags::tag_size_minimum ("SIZE_MINIMUM");
const XMLtag Tags::tag_size_multiple ("SIZE_MULTIPLE");
const XMLtag Tags::tag_default_calendar ("DEFAULT_CALENDAR");
const XMLtag Tags::tag_demand ("DEMAND");
const XMLtag Tags::tag_supply ("SUPPLY");
const XMLtag Tags::tag_start_onhand ("START_ONHAND");
const XMLtag Tags::tag_end_onhand ("END_ONHAND");
const XMLtag Tags::tag_policy ("POLICY");
const XMLtag Tags::tag_usage ("USAGE");
const XMLtag Tags::tag_command ("COMMAND");
const XMLtag Tags::tag_commands ("COMMANDS");
const XMLtag Tags::tag_filename ("FILENAME");
const XMLtag Tags::tag_constraints ("CONSTRAINTS");
const XMLtag Tags::tag_alternate ("ALTERNATE");
const XMLtag Tags::tag_alternates ("ALTERNATES");
const XMLtag Tags::tag_value ("VALUE");
const XMLtag Tags::tag_mode ("MODE");
const XMLtag Tags::tag_fence ("FENCE");
const XMLtag Tags::tag_detectproblems ("DETECTPROBLEMS");
const XMLtag Tags::tag_maximum ("MAXIMUM");
const XMLtag Tags::tag_minimum ("MINIMUM");
const XMLtag Tags::tag_solver ("SOLVER");
const XMLtag Tags::tag_solvers ("SOLVERS");
const XMLtag Tags::tag_customer ("CUSTOMER");
const XMLtag Tags::tag_customers ("CUSTOMERS");
const XMLtag Tags::tag_data ("DATA");
const XMLtag Tags::tag_startorend ("STARTOREND");
const XMLtag Tags::tag_category("CATEGORY");
const XMLtag Tags::tag_subcategory("SUBCATEGORY");
const XMLtag Tags::tag_cmdline("CMDLINE");
const XMLtag Tags::tag_verbose("VERBOSE");
const XMLtag Tags::tag_abortonerror("ABORTONERROR");
const XMLtag Tags::tag_maxparallel("MAXPARALLEL");
const XMLtag Tags::tag_action("ACTION");
const XMLtag Tags::tag_validate("VALIDATE");
const XMLtag Tags::tag_csv("CSV");
const XMLtag Tags::tag_parameter("PARAMETER");
const XMLtag Tags::tag_headerstart("HEADERSTART");
const XMLtag Tags::tag_headeratts("HEADERATTS");
const XMLtag Tags::tag_content("CONTENT");
const XMLtag Tags::tag_url("URL");
const XMLtag Tags::tag_pegging("PEGGING");

}
