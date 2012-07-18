#!/usr/bin/perl

#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#  file     : $HeadURL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$

use frepple;
use Env qw(FREPPLE_HOME);

# The eval command is used to catch frepple exceptions
eval {
  print "Initializing:\n";
  $s = $FREPPLE_HOME;
  frepple::FreppleInitialize($s);
  print " OK\n";

	print "Reading base data:\n";
	frepple::FreppleReadXMLData('<?xml version="1.0" encoding="UTF-8" ?>
		<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
			<NAME>actual plan</NAME>
			<COMMANDS>
			 <COMMAND xsi:type="COMMAND_SIZE" />
      </COMMANDS>
			<DESCRIPTION>Anything goes</DESCRIPTION>
			<CURRENT>2007-01-01T00:00:01</CURRENT>
			<OPERATIONS>
				<OPERATION NAME="make end item" xsi:type="OPERATION_FIXED_TIME">
					<DURATION>24:00:00</DURATION>
				</OPERATION>
			</OPERATIONS>
			<ITEMS>
				<ITEM NAME="end item">
					<OPERATION NAME="delivery end item" xsi:type="OPERATION_FIXED_TIME">
						<DURATION>24:00:00</DURATION>
					</OPERATION>
				</ITEM>
			</ITEMS>
			<BUFFERS>
				<BUFFER NAME="end item">
					<PRODUCING NAME="make end item"/>
					<ITEM NAME="end item"/>
				</BUFFER>
			</BUFFERS>
			<RESOURCES>
				<RESOURCE NAME="Resource">
					<MAXIMUM NAME="Capacity" xsi:type="CALENDAR_FLOAT">
						<BUCKETS>
							<BUCKET START="2007-01-01T00:00:01">
								<VALUE>1</VALUE>
							</BUCKET>
						</BUCKETS>
					</MAXIMUM>
					<LOADS>
						<LOAD>
							<OPERATION NAME="make end item" />
						</LOAD>
					</LOADS>
				</RESOURCE>
			</RESOURCES>
			<FLOWS>
				<FLOW xsi:type="FLOW_START">
					<OPERATION NAME="delivery end item"/>
					<BUFFER NAME="end item"/>
					<QUANTITY>-1</QUANTITY>
				</FLOW>
				<FLOW xsi:type="FLOW_END">
					<OPERATION NAME="make end item"/>
					<BUFFER NAME="end item"/>
					<QUANTITY>1</QUANTITY>
				</FLOW>
			</FLOWS>
			<DEMANDS>
				<DEMAND NAME="order 1">
					<QUANTITY>10</QUANTITY>
					<DUE>2007-01-04T09:00:00</DUE>
					<PRIORITY>1</PRIORITY>
					<ITEM NAME="end item"/>
					<POLICY>PLANLATE</POLICY>
				</DEMAND>
			</DEMANDS>
		</PLAN>', true, false);
	print " OK\n";

	print "Adding an item:\n";
	frepple::FreppleReadXMLData('<?xml version="1.0" encoding="UTF-8" ?>
		<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
			<ITEMS>
				<ITEM NAME="New Item"/>
			</ITEMS>
		</PLAN>', true, false);
	print " OK\n";

	print "Saving frepple model to a string:\n";
	# @todo try this out for large strings. Memory consumption?
	print frepple::FreppleSaveString();
	print " OK\n";

	print "Saving frepple model to a file:\n";
	frepple::FreppleSaveFile("turbo.perl.xml");
	print " OK\n";

	print "Passing invalid XML data to frepple:\n";
	frepple::FreppleReadXMLData('<?xml version="1.0" encoding="UTF-8" ?>
		<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
			<XXDESCRIPTION>dummy</DESCRIPTION>
		</PLAN> ', true, false);
	print " OK\n";

	print "End of frepple commands\n";
};
if ($@) {
	# Processing the execeptions thrown by the above commands
	print "Exception caught: $@\n";
}
else {
	print "All commands passed without error\n";
}

print "Exiting...\n";
