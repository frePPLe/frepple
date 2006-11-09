#!/usr/bin/perl
#  file     : $HeadURL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$
#  email    : jdetaeye@users.sourceforge.net

use strict;
use warnings;
use Env qw(EXECUTABLE);
use Time::HiRes qw ( gettimeofday tv_interval );

my %runtimes;

for (my $counter=500; $counter <= 2000; $counter+=500)
  {
  print "\ncounter $counter\n";
  open(OUTFILE, ">input.xml");

  # Print a header
  printf OUTFILE
    "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n" .
    "<DESCRIPTION>Single buffer plan with $counter demands</DESCRIPTION>\n" .
    "<CURRENT>2006-01-01T00:00:00</CURRENT>\n" .
    "<COMMANDS>\n" .
    "<COMMAND xsi:type=\"COMMAND_SOLVE\" VERBOSE=\"false\">" .
    "  <SOLVER NAME=\"MRP\" xsi:type=\"SOLVER_MRP\" CONSTRAINTS=\"0\"/>" .
    "</COMMAND>\n" .
    "<COMMAND xsi:type=\"COMMAND_SAVE\" FILENAME=\"output.xml\"/>\n" .
    "</COMMANDS>\n" .
    "<ITEMS>\n" .
      "\t<ITEM NAME=\"ITEM\">" .
      "<OPERATION NAME=\"Delivery ITEM\" xsi:type=\"OPERATION_FIXED_TIME\"/>" .
      "</ITEM>\n" .
    "</ITEMS>\n" .
    "<OPERATIONS>\n" .
      "\t<OPERATION NAME=\"Make ITEM\" xsi:type=\"OPERATION_FIXED_TIME\"/>\n" .
    "</OPERATIONS>\n" .
    "<BUFFERS>\n" .
      "\t<BUFFER NAME=\"BUFFER\"><ONHAND>10</ONHAND>" .
      "<PRODUCING NAME=\"Make ITEM\"/>" .
      "</BUFFER>\n" .
    "</BUFFERS>\n" .
    "<FLOWS>\n" .
      "\t<FLOW xsi:type=\"FLOW_START\"><OPERATION NAME=\"Delivery ITEM\"/>" .
      "<BUFFER NAME=\"BUFFER\"/>" .
      "<QUANTITY>-1</QUANTITY></FLOW>\n" .
      "\t<FLOW xsi:type=\"FLOW_END\"><OPERATION NAME=\"Make ITEM\"/>" .
      "<BUFFER NAME=\"BUFFER\"/>" .
      "<QUANTITY>1</QUANTITY></FLOW>\n" .
    "</FLOWS>\n" .
    "<DEMANDS>\n";

  # A loop to print all demand
  for (my $cnt = 0; ++$cnt < $counter; )
  {
  	my $month = int(rand 12)+1;
  	my $day = int(rand 28)+1;
  	if ($month<10) {$month = "0" . $month;}
  	if ($day<10) {$day = "0" . $day;}
    printf OUTFILE
      "<DEMAND NAME=\"DEMAND $cnt\" QUANTITY=\"10\" " .
      "DUE=\"2005-${month}-${day}T00:00:00\" " .
      "PRIORITY=\"1\">" .
      "<ITEM NAME=\"ITEM\"/>" .
      "</DEMAND>\n";
  }

  # Finalize the input
  printf OUTFILE "</DEMANDS></PLAN>\n";
  close(OUTFILE);

	my $starttime = [gettimeofday];
  system("$EXECUTABLE ./input.xml");
  die "Planner exited abnormally\n" if $? > 0;

  # Measure the time
  $runtimes{$counter} = tv_interval($starttime);
  printf "time: %.3f\n", $runtimes{$counter};
  }

# Define failure criterium
if ($runtimes{2000} > $runtimes{500}*4*1.1)
{
	die "\nTest failed. Run time is not linear with model size.\n";
}

print "\nTest passed\n";
exit;
