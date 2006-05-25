#!/usr/bin/perl
#  file     : $HeadURL: file:///develop/SVNrepository/frepple/trunk/test/scalability_1/runtest.pl $
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$
#  email    : jdetaeye@users.sourceforge.net

use strict;
use warnings;

use lib "..";
use TestLib;
use Time::HiRes qw ( gettimeofday tv_interval );
use Env qw(EXECUTABLE);

my %runtimes;

# Warning message
print "\nWarning: This test will take 10 minutes or more to complete.\n";
print "Go get a coffee or hit ctrl-c to abort this testcase...\n";

for (my $counter=5000; $counter < 30000; $counter+=5000)
  {
  print "\ncounter $counter\n";
  ## Open a pipe to which all output is sent.
  ## This is an alternative to the flat file proces... The performance of
  ## the program isn't any different.
  # open(OUTFILE, '| time -p $EXECUTABLE');
  open(OUTFILE, ">input.xml");

  my $fh = \*OUTFILE;
  TestLib::createdata(
    $fh,
    $counter,
    "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n" .
      "<CURRENT>2006-01-01T00:00:00</CURRENT>\n" .
      "<ITEMS>\n",
    "<ITEM NAME=\"ITEMNM\" CATEGORY=\"cat1\" DESCRIPTION=\"DCRP\" >" .
      "\n\t<OPERATION NAME=\"Delivery ITEMNM\" " .
      "xsi:type=\"OPERATION_FIXED_TIME\" DURATION=\"0\"/>" .
      "\n</ITEM>\n",
    "</ITEMS>\n",
    "ITEMNM","DCRP"
    );
  TestLib::createdata(
    $fh,
    $counter,
    "<OPERATIONS>\n",
    "<OPERATION NAME=\"Make ITEMNM\" xsi:type=\"OPERATION_FIXED_TIME\" " .
      "DURATION=\"24:00:00\"/>\n",
    "</OPERATIONS>\n",
    "ITEMNM",
    );
  TestLib::createdata(
    $fh,
    $counter,
    "<RESOURCES>\n",
    "<RESOURCE NAME=\"RESNM\"><LOADS>" .
      "<LOAD><OPERATION NAME=\"Make ITEMNM\"/></LOAD></LOADS></RESOURCE>\n",
    "</RESOURCES>\n",
    "RESNM","ITEMNM"
    );
  TestLib::createdata(
    $fh,
    $counter,
    "<FLOWS>\n",
    "<FLOW xsi:type=\"FLOW_START\"><OPERATION NAME=\"Delivery ITEMNM\"/>" .
      "<BUFFER NAME=\"BUFNM\" ONHAND=\"10\"/>" .
      "<QUANTITY>-1</QUANTITY></FLOW>\n" .
    "<FLOW xsi:type=\"FLOW_START\"><OPERATION NAME=\"Make ITEMNM\"/>" .
      "<BUFFER NAME=\"BUFNM\"/><QUANTITY>1</QUANTITY></FLOW>\n",
    "</FLOWS>\n",
    "ITEMNM","BUFNM"
    );
  TestLib::createdata(
    $fh,
    $counter,
    "<DEMANDS>\n",
    "<DEMAND NAME=\"DEMANDNM1\" QUANTITY=\"10\" DUE=\"2006-03-03T00:00:00\" " .
     "PRIORITY=\"1\"> <ITEM NAME=\"ITEMNM\"/></DEMAND>\n" .
     "<DEMAND NAME=\"DEMANDNM2\" QUANTITY=\"10\" DUE=\"2006-03-03T00:00:00\" " .
     "PRIORITY=\"2\"> <ITEM NAME=\"ITEMNM\"/></DEMAND>\n" .
     "<DEMAND NAME=\"DEMANDNM3\" QUANTITY=\"10\" DUE=\"2006-03-03T00:00:00\" " .
     "PRIORITY=\"1\"> <ITEM NAME=\"ITEMNM\"/></DEMAND>\n",
    "</DEMANDS></PLAN>\n",
    "DEMANDNM1","DEMANDNM2","DEMANDNM3","ITEMNM"
    );

  close(OUTFILE);

  # Run the execution
  my $starttime = [gettimeofday];
  system("$EXECUTABLE ./commands.xml");
  die "Planner exited abnormally\n" if $? > 0;

  # Measure the time
  $runtimes{$counter} = tv_interval($starttime);
  printf "time: %.3f\n", $runtimes{$counter};

  # Clean up the input and the output
  unlink "input.xml";
  unlink "output.xml";
  #rename "input.xml", "input_$counter.xml";
  #rename "output.xml", "output_$counter.xml";
  }

# Define failure criterium
if ($runtimes{25000} > ($runtimes{5000}+1)*5*1.05)
{
  die "\nTest failed. Run time scales worse than linear with model size.\n";
}

print "\nTest passed\n";
exit;
