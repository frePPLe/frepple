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
    '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
    '<COMMANDS>' +
    '<COMMAND xsi:type="COMMAND_SAVE" FILENAME="output.%d.xml"/>' +
    '</COMMANDS></plan>') % id)


def funcAddDemand(id,cnt):
  '''
  A thread command to create a demand.
  '''
  send2frepple(
    ('<?xml version="1.0" encoding="UTF-8" ?>' +
    '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
    '<demands>' +
    '<demand name="order_%d_%d" quantity="10" ' +
    'due="2005-01-04T09:00:00" priority="1"> ' +
    '<item name="end item"/></demand>' +
    '</demands></plan>') % (id,cnt))


def funcDeleteDemand(id,cnt):
  '''
  A thread command to delete a demand.
  We assume the demand is created with funcAddDemand, which is executed by
  a preceding threadid.
  '''
  send2frepple(
    ('<?xml version="1.0" encoding="UTF-8" ?>' +
    '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
    '<demands>' +
    '<demand name="DEMAND%d %cnt" action="REMOVE"/>' +
    '</demands></plan>') % (id-1,cnt))


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
  <plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <name>actual plan</name>
  <current>2007-01-01T00:00:01</current>
  <operations>
  <operation name="make end item" xsi:type="operation_fixed_time" duration="24:00:00"/>
  </operations><items>
  <item name="end item">
  <operation name="delivery end item" duration="24:00:00"/>
  </item>
  </items> <buffers>
  <buffer name="end item">
  <producing name="make end item"/> <item name="end item"/>
  </buffer>
  </buffers><resources>
  <resource name="Resource">
  <maximum name="Capacity" xsi:type="calendar_float"><buckets>
  <bucket start="2007-01-01T00:00:01"> <value>1</value> </bucket>
  </buckets></maximum>
  <loads><load><operation name="make end item"/></load></loads>
  </resource>
  </resources><flows>
  <flow xsi:type="flow_start"> <operation name="delivery end item"/>
  <buffer name="end item"/> <quantity>-1</quantity>
  </flow>
  <flow xsi:type="flow_end"> <operation name="make end item"/>
  <buffer name="end item"/> <quantity>1</quantity>
  </flow>
  </flows><demands>
  <demand name="order 1" quantity="10" due="2007-01-04T09:00:00"
  priority="1"> <item name="end item"/></demand>
  </demands></plan>""")

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


