#!/usr/bin/python
#  file     : $URL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$

import os, sys

runtimes = {}

def createdata(outfile,duplicates,header,body,footer,subst):
  # Print the header
  outfile.write(header)

  # Iteration
  if subst == 0:
    for cnt in range(duplicates):
      print >>outfile, body
  elif subst == 1:
   for cnt in range(duplicates):
      print >>outfile, body % (cnt)
  elif subst == 2:
   for cnt in range(duplicates):
      print >>outfile, body % (cnt,cnt)
  elif subst == 3:
   for cnt in range(duplicates):
      print >>outfile, body % (cnt,cnt,cnt)
  elif subst == 4:
   for cnt in range(duplicates):
      print >>outfile, body % (cnt,cnt,cnt,cnt)
  elif subst == 5:
   for cnt in range(duplicates):
      print >>outfile, body % (cnt,cnt,cnt,cnt,cnt)
  elif subst == 6:
   for cnt in range(duplicates):
      print >>outfile, body % (cnt,cnt,cnt,cnt,cnt,cnt)
  elif subst == 7:
   for cnt in range(duplicates):
      print >>outfile, body % (cnt,cnt,cnt,cnt,cnt,cnt,cnt)

  # Finalize
  outfile.write(footer)


# Initialize if not done already @todo need to do this more generic
if not 'EXECUTABLE' in os.environ:
  os.environ['EXECUTABLE'] = "../../libtool --mode=execute ../../src/frepple"
  testdir = os.path.dirname(os.path.abspath(sys.argv[0]))
  os.environ['FREPPLE_HOME'] = os.path.normpath(os.path.join(testdir, '..', '..', 'bin'))
  os.environ['LD_LIBRARY_PATH'] = os.environ['FREPPLE_HOME']

# Main loop
for counter in [5000, 10000, 15000, 20000, 25000]:
  print "\ncounter", counter
  outfile = open("input.xml","wt")

  createdata(
    outfile,
    counter,
    "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n" +
      "<CURRENT>2007-01-01T00:00:00</CURRENT>\n" +
      "<ITEMS>\n",
    "<ITEM NAME=\"ITEMNM_%d\" CATEGORY=\"cat1\" DESCRIPTION=\"DCRP_%d\" >" +
      "\n\t<OPERATION NAME=\"Delivery ITEMNM_%d\" " +
      "xsi:type=\"OPERATION_FIXED_TIME\" DURATION=\"P0D\"/>" +
      "\n</ITEM>",
    "</ITEMS>\n",
    3
    )
  createdata(
    outfile,
    counter,
    "<OPERATIONS>\n",
    "<OPERATION NAME=\"Make ITEMNM_%d\" xsi:type=\"OPERATION_FIXED_TIME\" "  +
      "DURATION=\"P1D\"/>",
    "</OPERATIONS>\n",
    1
    )
  createdata(
    outfile,
    counter,
    "<RESOURCES>\n",
    "<RESOURCE NAME=\"RESNM_%d\"><LOADS>" +
      "<LOAD><OPERATION NAME=\"Make ITEMNM_%d\"/></LOAD></LOADS></RESOURCE>",
    "</RESOURCES>\n",
    2
    )
  createdata(
    outfile,
    counter,
    "<FLOWS>\n",
    "<FLOW xsi:type=\"FLOW_START\"><OPERATION NAME=\"Delivery ITEMNM_%d\"/>" +
      "<BUFFER NAME=\"BUFNM_%d\" ONHAND=\"10\"/>" +
      "<QUANTITY>-1</QUANTITY></FLOW>\n" +
    "<FLOW xsi:type=\"FLOW_END\"><OPERATION NAME=\"Make ITEMNM_%d\"/>" +
      "<BUFFER NAME=\"BUFNM_%d\"/><QUANTITY>1</QUANTITY></FLOW>",
    "</FLOWS>\n",
    4
    )
  createdata(
    outfile,
    counter,
    "<DEMANDS>\n",
    "<DEMAND NAME=\"DEMANDNM1_%d\" QUANTITY=\"10\" DUE=\"2007-03-03T00:00:00\" " +
     "PRIORITY=\"1\"> <ITEM NAME=\"ITEMNM_%d\"/></DEMAND>\n" +
     "<DEMAND NAME=\"DEMANDNM2_%d\" QUANTITY=\"10\" DUE=\"2007-03-03T00:00:00\" " +
     "PRIORITY=\"2\"> <ITEM NAME=\"ITEMNM_%d\"/></DEMAND>\n" +
     "<DEMAND NAME=\"DEMANDNM3_%d\" QUANTITY=\"10\" DUE=\"2007-03-03T00:00:00\" " +
     "PRIORITY=\"1\"> <ITEM NAME=\"ITEMNM_%d\"/></DEMAND>",
    "</DEMANDS></PLAN>\n",
    6
    )

  outfile.close();

  # Run the execution
  starttime = os.times()
  out = os.popen(os.environ['EXECUTABLE'] + "  ./commands.xml")
  while True:
    i = out.readline()
    if not i: break
    print i.strip()
  if out.close() != None:
    print "Planner exited abnormally\n"
    sys.exit(1)

  # Measure the time
  endtime = os.times()
  runtimes[counter] = endtime[4]-starttime[4]
  print "time: %.3f" % (endtime[4]-starttime[4])

  # Clean up the input and the output
  os.remove("input.xml")
  os.remove("output.xml")
  #if os.path.isfile("input_%d.xml" % counter):
  #  os.remove("input_%d.xml" % counter)
  #os.rename("input.xml", "input_%d.xml" % counter)
  #if os.path.isfile("output_%d.xml" % counter):
  #  os.remove("output_%d.xml" % counter)
  #os.rename("output.xml", "output_%d.xml" % counter)

# Define failure criterium
if runtimes[25000] > runtimes[5000]*5*1.05:
  print "\nTest failed. Run time scales worse than linear with model size.\n"
  sys.exit(1)

print "\nTest passed\n"
