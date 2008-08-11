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


# Main loop
for counter in [5000, 10000, 15000, 20000, 25000]:
  print "\ncounter", counter
  outfile = open("input.xml","wt")

  createdata(
    outfile,
    counter,
    "<plan xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n" +
      "<current>2007-01-01T00:00:00</current>\n" +
      "<items>\n",
    "<item name=\"ITEMNM_%d\" category=\"cat1\" description=\"DCRP_%d\" >" +
      "\n\t<operation name=\"Delivery ITEMNM_%d\" " +
      "xsi:type=\"operation_fixed_time\" duration=\"P0D\"/>" +
      "\n</item>",
    "</items>\n",
    3
    )
  createdata(
    outfile,
    counter,
    "<operations>\n",
    "<operation name=\"Make ITEMNM_%d\" xsi:type=\"operation_fixed_time\" "  +
      "duration=\"P1D\"/>",
    "</operations>\n",
    1
    )
  createdata(
    outfile,
    counter,
    "<resources>\n",
    "<resource name=\"RESNM_%d\"><loads>" +
      "<load><operation name=\"Make ITEMNM_%d\"/></load></loads></resource>",
    "</resources>\n",
    2
    )
  createdata(
    outfile,
    counter,
    "<flows>\n",
    "<flow xsi:type=\"flow_start\"><operation name=\"Delivery ITEMNM_%d\"/>" +
      "<buffer name=\"BUFNM_%d\" onhand=\"10\"/>" +
      "<quantity>-1</quantity></flow>\n" +
    "<flow xsi:type=\"flow_end\"><operation name=\"Make ITEMNM_%d\"/>" +
      "<buffer name=\"BUFNM_%d\"/><quantity>1</quantity></flow>",
    "</flows>\n",
    4
    )
  createdata(
    outfile,
    counter,
    "<demands>\n",
    "<demand name=\"DEMANDNM1_%d\" quantity=\"10\" due=\"2007-03-03T00:00:00\" " +
     "priority=\"1\"> <item name=\"ITEMNM_%d\"/></demand>\n" +
     "<demand name=\"DEMANDNM2_%d\" quantity=\"10\" due=\"2007-03-03T00:00:00\" " +
     "priority=\"2\"> <item name=\"ITEMNM_%d\"/></demand>\n" +
     "<demand name=\"DEMANDNM3_%d\" quantity=\"10\" due=\"2007-03-03T00:00:00\" " +
     "priority=\"1\"> <item name=\"ITEMNM_%d\"/></demand>",
    "</demands></plan>\n",
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
