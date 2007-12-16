#!/usr/bin/python
#  file     : $URL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$

import frepple
import os

try:
	print "Initializing:"
	print frepple.FreppleInitialize(os.environ.get("FREPPLE_HOME"))
	print " OK"

	print "Reading base data:"
	frepple.FreppleReadXMLData('<?xml version="1.0" encoding="UTF-8" ?> \
		<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> \
			<NAME>actual plan</NAME> \
			<DESCRIPTION>Anything goes</DESCRIPTION> \
			<CURRENT>2007-01-01T00:00:01</CURRENT> \
			<OPERATIONS> \
				<OPERATION NAME="make end item" xsi:type="OPERATION_FIXED_TIME"> \
					<DURATION>24:00:00</DURATION> \
				</OPERATION> \
			</OPERATIONS> \
			<ITEMS> \
				<ITEM NAME="end item"> \
					<OPERATION NAME="delivery end item" xsi:type="OPERATION_FIXED_TIME"> \
						<DURATION>24:00:00</DURATION> \
					</OPERATION> \
				</ITEM> \
			</ITEMS> \
			<BUFFERS> \
				<BUFFER NAME="end item"> \
					<PRODUCING NAME="make end item"/> \
					<ITEM NAME="end item"/> \
				</BUFFER> \
			</BUFFERS> \
			<RESOURCES> \
				<RESOURCE NAME="Resource"> \
					<MAXIMUM NAME="Capacity" xsi:type="CALENDAR_FLOAT"> \
						<BUCKETS> \
							<BUCKET START="2007-01-01T00:00:01" VALUE="1"/> \
						</BUCKETS> \
					</MAXIMUM> \
					<LOADS> \
						<LOAD> \
							<OPERATION NAME="make end item" /> \
						</LOAD> \
					</LOADS> \
				</RESOURCE> \
			</RESOURCES> \
			<FLOWS> \
				<FLOW xsi:type="FLOW_START"> \
					<OPERATION NAME="delivery end item"/> \
					<BUFFER NAME="end item"/> \
					<QUANTITY>-1</QUANTITY> \
				</FLOW> \
				<FLOW xsi:type="FLOW_END"> \
					<OPERATION NAME="make end item"/> \
					<BUFFER NAME="end item"/> \
					<QUANTITY>1</QUANTITY> \
				</FLOW> \
			</FLOWS> \
			<DEMANDS> \
				<DEMAND NAME="order 1"> \
					<QUANTITY>10</QUANTITY> \
					<DUE>2007-01-04T09:00:00</DUE> \
					<PRIORITY>1</PRIORITY> \
					<ITEM NAME="end item"/> \
				</DEMAND> \
			</DEMANDS> \
		</PLAN> ', True, False)
	print " OK"

	print "Adding an item:"
	frepple.FreppleReadXMLData('<?xml version="1.0" encoding="UTF-8" ?> \
		<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> \
			<ITEMS> \
				<ITEM NAME="New Item"/> \
			</ITEMS> \
		</PLAN>', 1, 0)
	print " OK"

	print "Saving frepple model to a string:"
	print frepple.FreppleSaveString()
	print " OK"

	print "Saving frepple model to a file:"
	frepple.FreppleSaveFile("turbo.python.xml")
	print " OK"

	print "Passing invalid XML data to frepple:"
	frepple.FreppleReadXMLData('<?xml version="1.0" encoding="UTF-8" ?> \
		<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> \
			<XXDESCRIPTION>Dummy</XXDESCRIPTION> \
		</PLAN> ', 1, 0)
	print " OK"

	print "End of frepple commands"
except RuntimeError, inst:
	print "Runtime exception caught: " + str(inst)
except:
	print "Caught an unknown exception"
else:
	print "All commands passed without error"

print "Exiting..."
