/***************************************************************************
  file : $HeadURL: file:///develop/SVNrepository/frepple/trunk/test/sizeof/main.cpp $
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


#include "frepple/model.h"
using namespace frepple;


int main (int argc, char *argv[])
{

  cout << "Plan\t" << sizeof(Plan) << endl
  << "Calendar\t" << sizeof(Calendar) << endl
  << "Calendar::Bucket\t" << sizeof(Calendar::Bucket) << endl
  << "CalendarFloat\t" << sizeof(CalendarFloat) << endl
  << "CalendarFloat::Bucket\t" << sizeof(CalendarFloat::BucketValue) << endl
  << "Item\t" << sizeof(Item) << endl
  << "Location\t" << sizeof(Location) << endl
  << "Customer\t" << sizeof(Customer) << endl
  << "Buffer\t" << sizeof(Buffer) << endl
  << "Demand\t" << sizeof(Demand) << endl
  << "Resource\t" << sizeof(Resource) << endl
  << "Operation\t" << sizeof(Operation) << endl
  << "OperationFixedTime\t" << sizeof(OperationFixedTime) << endl
  << "OperationRouting\t" << sizeof(OperationRouting) << endl
  << "OperationTimePer\t" << sizeof(OperationTimePer) << endl
  << "Load\t" << sizeof(Load) << endl
  << "Flow\t" << sizeof(Flow) << endl;

  cout << "OperationPlan\t" << sizeof(OperationPlan) << endl
  << "FlowPlan\t" << sizeof(FlowPlan) << endl
  << "LoadPlan\t" << sizeof(LoadPlan) << endl;

  cout << "Problem\t" << sizeof(Problem) << endl
  << "ProblemBeforeCurrent\t" << sizeof(ProblemBeforeCurrent) << endl
  << "ProblemBeforeFence\t" << sizeof(ProblemBeforeFence) << endl
  << "ProblemLate\t" << sizeof(ProblemLate) << endl
  << "ProblemEarly\t" << sizeof(ProblemEarly) << endl
  << "ProblemExcess\t" << sizeof(ProblemExcess) << endl
  << "ProblemShort\t" << sizeof(ProblemShort) << endl
  << "ProblemDemandNotPlanned\t" << sizeof(ProblemDemandNotPlanned) << endl
  << "ProblemCapacityOverload\t" << sizeof(ProblemCapacityOverload) << endl
  << "ProblemPlannedEarly\t" << sizeof(ProblemPlannedEarly) << endl
  << "ProblemPlannedLate\t" << sizeof(ProblemPlannedLate) << endl
  << "ProblemPrecedence\t" << sizeof(ProblemPrecedence) << endl
  << "ProblemMaterialShortage\t" << sizeof(ProblemMaterialShortage) << endl
  << "ProblemMaterialExcess\t" << sizeof(ProblemMaterialExcess) << endl;

  cout << "Date\t" << sizeof(Date) << endl
  << "DateRange\t" << sizeof(DateRange) << endl
  << "TimePeriod\t" << sizeof(DateRange) << endl
  << "HasHierarchy<type>\t" << sizeof(HasHierarchy<Demand>) << endl
  << "HasName<type>\t" << sizeof(HasName<Demand>) << endl
  << "HasDescription\t" << sizeof(HasDescription) << endl
  << "TimeLine<type>\t" << sizeof(TimeLine<Demand>) << endl
  << "XMLtag\t" << sizeof(XMLtag) << endl
  << "XMLInput\t" << sizeof(XMLInput) << endl
  << "XMLInputFile\t" << sizeof(XMLInputFile) << endl
  << "XMLInputString\t" << sizeof(XMLInputString) << endl
  << "Object\t" << sizeof(Object) << endl
  << "Command\t" << sizeof(Command) << endl
  << "CommandList\t" << sizeof(CommandList) << endl;

  return EXIT_SUCCESS;
}
