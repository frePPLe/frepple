#!/usr/bin/perl
#  file     : $HeadURL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$
#  email    : jdetaeye@users.sourceforge.net

use strict;
use warnings;

use lib "..";
use TestLib;
use Time::HiRes qw ( gettimeofday tv_interval );
use Env qw(EXECUTABLE);
use threads;
use threads::shared;
use Time::HiRes qw ( gettimeofday tv_interval sleep );
use Thread::Semaphore;
use frepple;

my %name : shared;
my %delay : shared;
my %maxcount : shared;
my %sumtime : shared;
my %mintime : shared;
my %maxtime : shared;
my %count : shared;
my $maxthreads = new Thread::Semaphore;
my $totalstarttime = [gettimeofday];

#
# Creating the initial model
#
frepple::readXMLData('<?xml version="1.0" encoding="UTF-8" ?>' .
  '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' .
  '<NAME>actual plan</NAME>' .
  '<CURRENT>2007-01-01T00:00:01</CURRENT>' .
  '<DEFAULT_CALENDAR NAME="Weeks"/>' .
  '<OPERATIONS>' .
  '<OPERATION NAME="make end item" xsi:type="OPERATION_FIXED_TIME" ' .
  'DURATION="24:00:00"/>' .
  '</OPERATIONS><ITEMS>' .
  '<ITEM NAME="end item">' .
  '<OPERATION NAME="delivery end item" DURATION="24:00:00"/>' .
  '</ITEM>' .
  '</ITEMS> <BUFFERS>' .
  '<BUFFER NAME="end item">' .
  '<PRODUCING NAME="make end item"/> <ITEM NAME="end item"/>' .
  '</BUFFER>' .
  '</BUFFERS><RESOURCES>' .
  '<RESOURCE NAME="Resource">' .
  '<MAXIMUM NAME="Capacity" xsi:type="CALENDAR_FLOAT"><BUCKETS>' .
  '<BUCKET START="2007-01-01T00:00:01"> <VALUE>1</VALUE> </BUCKET>' .
  '</BUCKETS></MAXIMUM>' . 
  '<LOADS><LOAD><OPERATION NAME="make end item"/></LOAD></LOADS>' .
  '</RESOURCE>' .
  '</RESOURCES><FLOWS>' .
  '<FLOW xsi:type="FLOW_START"> <OPERATION NAME="delivery end item"/>' .
  '<BUFFER NAME="end item"/> <QUANTITY>-1</QUANTITY>' .
  '</FLOW>' . 
  '<FLOW xsi:type="FLOW_END"> <OPERATION NAME="make end item"/>' .
  '<BUFFER NAME="end item"/> <QUANTITY>1</QUANTITY>' .
  '</FLOW>' .
  '</FLOWS><DEMANDS>' .
  '<DEMAND NAME="order 1" QUANTITY="10" DUE="2007-01-04T09:00:00" ' .
  'PRIORITY="1" POLICY="PLANLATE> <ITEM NAME="end item"/></DEMAND>' .
  '</DEMANDS></PLAN>',1,0);

#
# Running the test threads
#
my $thread1 = threads->create("run", "thread1", 0, 100, \&funcAddDemand);
my $thread2 = threads->create("run", "thread2", 0, 100, \&funcAddDemand);
my $thread3 = threads->create("run", "thread3", 0, 20, \&funcSave);
my $thread4 = threads->create("run", "thread4", 0, 20, \&funcSave);
my $thread5 = threads->create("run", "thread5", 0, 20, \&funcSave);
my $thread6 = threads->create("run", "thread6", 0, 20, \&funcSave);
$SIG{INT} = \&interrupt;
$SIG{STOP} = \&interrupt;
$SIG{QUIT} = \&interrupt;
$SIG{PIPE} = \&interrupt;

foreach my $i (threads->list()) {
	$i->join();
}

# The final results
print "  THREAD    #execs  TotTime  Avg Time  Min Time  Max Time\n";
foreach my $id (sort keys %name)
{
	printf "%10s %6u %8.3f %9.3f %9.3f %9.3f \n", $name{$id}, $count{$id}, 
	  $sumtime{$id}, ($sumtime{$id}/$count{$id}), $mintime{$id}, $maxtime{$id};
}
printf "total time %.3f\n", tv_interval($totalstarttime);

print "\nTest passed\n";
exit;

sub interrupt
{
	print "fuck";
}

#
# This is the routine executed by each of the threads.
# It will execute the specified function repeatedly with a delay between calls.
# Statistics about the timing are gathered.
sub run
{
	my $id = threads->tid();
	$name{$id} = shift;
	my $func;
	($delay{$id}, $maxcount{$id}, $func) = @_;
	($sumtime{$id}, $mintime{$id}, $maxtime{$id}, $count{$id}) = 
	  (0.0, 1e9, -1, 0);

	while ($count{$id}<$maxcount{$id} || $maxcount{$id}<0)
	{
		# Increment the max thread counter
		#{lock($maxthreads); $maxthreads->up;}

		# Initialize timer
		#print "$xml{$id} $count{$id}\n";
		my $starttime = [gettimeofday];

		# Execute the command
		&{$func}($id,$count{$id});

		# Collect timing results
		my $thistime = tv_interval($starttime);
		#{lock($maxthreads); $maxthreads->down;}
		$sumtime{$id} += $thistime;
		$mintime{$id} = $thistime if ($thistime < $mintime{$id});
		$maxtime{$id} = $thistime if ($thistime > $maxtime{$id});
		$count{$id}++;

		# Sleep a bit between 2 calls to the xml
		sleep $delay{$id} * (0.95 + rand 0.1)  if ($delay{$id}>0);
	}
}

#
# A thread command to sleep for a second
#
sub funcSleep
{
	frepple::readXMLData(
	  '<?xml version="1.0" encoding="UTF-8" ?>' .
	  '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' .
	  '<COMMANDS>' .
	  '<COMMAND xsi:type="COMMAND_SYSTEM" CMDLINE="sleep 1"/>' .
	  '</COMMANDS></PLAN>',0,0);
}

#
# A thread command to solve the plan
#
sub funcSolve
{
	frepple::readXMLData(
	  '<?xml version="1.0" encoding="UTF-8" ?>' .
	  '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' .
	  '<COMMANDS>' .
	  '<COMMAND xsi:type="COMMAND_SOLVE" VERBOSE="FALSE">' .
	  '<SOLVER NAME="MRP" xsi:type="SOLVER_MRP" CONSTRAINTS="0"/>' .
	  '</COMMAND>' .
	  '</COMMANDS></PLAN>',0,0);
}

#
# A thread command to save the model
#
sub funcSave
{
	my ($id, $cnt)  = @_;
	frepple::readXMLData(
	  '<?xml version="1.0" encoding="UTF-8" ?>' .
	  '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' .
	  '<COMMANDS>' .
	  '<COMMAND xsi:type="COMMAND_SAVE" FILENAME="output.' . $id . '.xml"/>' .
	  '</COMMANDS></PLAN>',0,0);
}


#
# A thread command to create a demand
#
sub funcAddDemand
{
	my ($id, $cnt)  = @_;
	frepple::readXMLData(
	  '<?xml version="1.0" encoding="UTF-8" ?>' .
	  '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' .
	  '<DEMANDS>' .
	  '<DEMAND NAME="order_' . $id . '_' . $cnt . '" QUANTITY="10" '.
	  'DUE="2005-01-04T09:00:00" PRIORITY="1" POLICY="PLANLATE"> ' .
	  '<ITEM NAME="end item"/></DEMAND>' .
	  '</DEMANDS></PLAN> ',0,0);
}


#
# A thread command to delete a demand
# We assume the demand is created with funcAddDemand, which is executed by 
# a preceding threadid.
#
sub funcDeleteDemand
{
	my ($id, $cnt)  = @_;
	frepple::readXMLData(
	  '<?xml version="1.0" encoding="UTF-8" ?>' .
	  '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' .
	  '<DEMANDS>' .
	  '<DEMAND NAME="DEMAND' . ($id-1) . ' ' . $cnt . '" ACTION="REMOVE'/>' .
	  '</DEMANDS></PLAN> ',0,0);
}