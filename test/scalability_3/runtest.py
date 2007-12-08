#!/usr/bin/python
#  file     : $URL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$

import os, sys, random

runtimes = {}

for counter in [500,1000,1500,2000]:
  print "\ncounter", counter
  out = open("input.xml","wt")

  # Print a header
  print >>out, ('<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n' +
    '<DESCRIPTION>Single buffer plan with $counter demands</DESCRIPTION>\n' +
    '<CURRENT>2007-01-01T00:00:00</CURRENT>\n' +
    '<COMMANDS>\n' +
    '<COMMAND xsi:type="COMMAND_SOLVE" VERBOSE="false">' +
    '  <SOLVER NAME="MRP" xsi:type="SOLVER_MRP" CONSTRAINTS="0"/>' +
    '</COMMAND>\n' +
    '<COMMAND xsi:type="COMMAND_SAVE" FILENAME="output.xml"/>\n' +
    '</COMMANDS>\n' +
    '<ITEMS>\n' +
      '\t<ITEM NAME="ITEM">' +
      '<OPERATION NAME="Delivery ITEM" xsi:type="OPERATION_FIXED_TIME"/>' +
      '</ITEM>\n' +
    '</ITEMS>\n' +
    '<OPERATIONS>\n' +
      '\t<OPERATION NAME="Make ITEM" xsi:type="OPERATION_FIXED_TIME"/>\n' +
    '</OPERATIONS>\n' +
    '<BUFFERS>\n' +
      '\t<BUFFER NAME="BUFFER"><ONHAND>10</ONHAND>' +
      '<PRODUCING NAME="Make ITEM"/>' +
      '</BUFFER>\n' +
    '</BUFFERS>\n' +
    '<FLOWS>\n' +
      '\t<FLOW xsi:type="FLOW_START"><OPERATION NAME="Delivery ITEM"/>' +
      '<BUFFER NAME="BUFFER"/>' +
      '<QUANTITY>-1</QUANTITY></FLOW>\n' +
      '\t<FLOW xsi:type="FLOW_END"><OPERATION NAME="Make ITEM"/>' +
      '<BUFFER NAME="BUFFER"/>' +
      '<QUANTITY>1</QUANTITY></FLOW>\n' +
    '</FLOWS>\n' +
    '<DEMANDS>')

  # A loop to print all demand
  for cnt in range(counter):
    month = "%02d" % (int(random.uniform(0,12))+1)
    day = "%02d" % (int(random.uniform(0,28))+1)
    print >>out, ("<DEMAND NAME=\"DEMAND $cnt\" QUANTITY=\"10\" " +
      "DUE=\"2005-%s-%sT00:00:00\" " +
      "PRIORITY=\"1\">" +
      "<ITEM NAME=\"ITEM\"/>" +
      "</DEMAND>") % (month,day)

  # Finalize the input
  print >>out, "</DEMANDS></PLAN>"
  out.close()

  # Run the executable
  starttime = os.times()
  out = os.popen(os.environ['EXECUTABLE'] + "  ./input.xml")
  while True:
    i = out.readline()
    if not i: break
    print i.strip()
  if out.close() != None:
    print "Planner exited abnormally"
    sys.exit(1)

  # Measure the time
  endtime = os.times()
  runtimes[counter] = endtime[4]-starttime[4]
  print "time: %.3f" % runtimes[counter]

# Define failure criterium
if runtimes[2000] > runtimes[500]*4*1.2:
  print "\nTest failed. Run time is not linear with model size."
  sys.exit(1)

print "\nTest passed"
