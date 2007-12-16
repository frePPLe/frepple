#!/usr/bin/python
#  file     : $URL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$

# In this test a number of threads are created that are simultaneously firing messages to
# a frepple server.
# Different message types can be sent, each with a specific delay between calls.
# The test results the min, max and average time taken by each message type, and the number
# of processed messages.
# The test has a predefined time duration.

import time, threading, random, sys


# Skip this test by default!!!
sys.exit(0)

def send2frepple(data):
  '''
  Posts the data to frepple.
  Not implemented yet!!!
  '''
  #print data
  time.sleep(1)


def funcSleep (id,cnt):
  '''
  A thread command to sleep for a second.
  '''
  send2frepple(
    '<?xml version="1.0" encoding="UTF-8" ?>' +
    '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
    '<COMMANDS>' +
    '<COMMAND xsi:type="COMMAND_SYSTEM" CMDLINE="sleep 1"/>' +
    '</COMMANDS></PLAN>')


def funcSolve(id,cnt):
  '''
  A thread command to solve the plan.
  '''
  send2frepple(
    '<?xml version="1.0" encoding="UTF-8" ?>' +
    '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
    '<COMMANDS>' +
    '<COMMAND xsi:type="COMMAND_SOLVE" VERBOSE="FALSE">' +
    '<SOLVER NAME="MRP" xsi:type="SOLVER_MRP" CONSTRAINTS="0"/>' +
    '</COMMAND>' +
    '</COMMANDS></PLAN>')


def funcSave(id,cnt):
  '''
  A thread command to save the model.
  '''
  send2frepple(
    ('<?xml version="1.0" encoding="UTF-8" ?>' +
    '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
    '<COMMANDS>' +
    '<COMMAND xsi:type="COMMAND_SAVE" FILENAME="output.%d.xml"/>' +
    '</COMMANDS></PLAN>') % id)


def funcAddDemand(id,cnt):
  '''
  A thread command to create a demand.
  '''
  send2frepple(
    ('<?xml version="1.0" encoding="UTF-8" ?>' +
    '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
    '<DEMANDS>' +
    '<DEMAND NAME="order_%d_%d" QUANTITY="10" ' +
    'DUE="2005-01-04T09:00:00" PRIORITY="1"> ' +
    '<ITEM NAME="end item"/></DEMAND>' +
    '</DEMANDS></PLAN>') % (id,cnt))


def funcDeleteDemand(id,cnt):
  '''
  A thread command to delete a demand.
  We assume the demand is created with funcAddDemand, which is executed by
  a preceding threadid.
  '''
  send2frepple(
    ('<?xml version="1.0" encoding="UTF-8" ?>' +
    '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
    '<DEMANDS>' +
    '<DEMAND NAME="DEMAND%d %cnt" ACTION="REMOVE"/>' +
    '</DEMANDS></PLAN>') % (id-1,cnt))


class Worker (threading.Thread):
  '''
  This is the routine executed by each of the threads.
  It will execute the specified function repeatedly with a delay between calls.
  Statistics about the timing are gathered.
  '''
  __threadid = 0

  def __init__(self, name, method, delay=0, maxcount=0):
    #global __threadid
    threading.Thread.__init__(self)
    Worker.__threadid += 1
    self.id = Worker.__threadid
    self.name = name
    self.setDaemon(1)
    self.delay = delay
    self.maxcount = maxcount
    self.method = method
    self.sumtime = 0
    self.mintime = 1e9
    self.maxtime = -1
    self.count = 0
    self.finished = False

  def run(self):
    while self.count<self.maxcount or self.maxcount <= 0:
      # Initialize timer
      starttime = time.clock()

      # Execute the command
      self.method(self.id,self.count)

      # Collect statistics
      timer = time.clock() - starttime
      self.sumtime += timer
      if (timer < self.mintime): self.mintime = timer
      if (timer > self.maxtime): self.maxtime = timer
      self.count += 1

      # Sleep a bit between 2 calls to the xml
      if self.delay > 0: time.sleep(self.delay * random.uniform(0.95,1.05))


# Creating the initial model
send2frepple(
  """<?xml version="1.0" encoding="UTF-8" ?>
  <PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NAME>actual plan</NAME>
  <CURRENT>2007-01-01T00:00:01</CURRENT>
  <DEFAULT_CALENDAR NAME="Weeks"/>
  <OPERATIONS>
  <OPERATION NAME="make end item" xsi:type="OPERATION_FIXED_TIME" DURATION="24:00:00"/>
  </OPERATIONS><ITEMS>
  <ITEM NAME="end item">
  <OPERATION NAME="delivery end item" DURATION="24:00:00"/>
  </ITEM>
  </ITEMS> <BUFFERS>
  <BUFFER NAME="end item">
  <PRODUCING NAME="make end item"/> <ITEM NAME="end item"/>
  </BUFFER>
  </BUFFERS><RESOURCES>
  <RESOURCE NAME="Resource">
  <MAXIMUM NAME="Capacity" xsi:type="CALENDAR_FLOAT"><BUCKETS>
  <BUCKET START="2007-01-01T00:00:01"> <VALUE>1</VALUE> </BUCKET>
  </BUCKETS></MAXIMUM>
  <LOADS><LOAD><OPERATION NAME="make end item"/></LOAD></LOADS>
  </RESOURCE>
  </RESOURCES><FLOWS>
  <FLOW xsi:type="FLOW_START"> <OPERATION NAME="delivery end item"/>
  <BUFFER NAME="end item"/> <QUANTITY>-1</QUANTITY>
  </FLOW>
  <FLOW xsi:type="FLOW_END"> <OPERATION NAME="make end item"/>
  <BUFFER NAME="end item"/> <QUANTITY>1</QUANTITY>
  </FLOW>
  </FLOWS><DEMANDS>
  <DEMAND NAME="order 1" QUANTITY="10" DUE="2007-01-04T09:00:00"
  PRIORITY="1"> <ITEM NAME="end item"/></DEMAND>
  </DEMANDS></PLAN>""")

# Define the test threads and the duration of the test
threads = [
     Worker("thread1", funcAddDemand, 0.25, 10),
     Worker("thread2", funcSleep, 0.25, 10),
     Worker("thread3", funcAddDemand, 0.1, 20),
     Worker("thread4", funcSave, 0.1, 20)
     ]
maxRunTime = 10

# Run the threads
starttime = time.clock()
try:
  for t in threads: t.start()
  # Wait for the total duration of the test
  time.sleep(maxRunTime)
  #Alternative: Wait for all threads to reach their message count
  #for t in threads: t.join()
except KeyboardInterrupt:
  # The test has been interupted, which counts as a failure
  print "Interrupted test"

totaltime = time.clock() - starttime

# The final results
print "\n  Thread    #execs  TotTime  Avg Time  Min Time  Max Time"
for t in threads:
  print "%10s %6u %8.3f %9.3f %9.3f %9.3f" % (t.name, t.count, t.sumtime, t.sumtime/t.count, t.mintime, t.maxtime)
print "total time %.3f" % totaltime

print "\nTest passed"


