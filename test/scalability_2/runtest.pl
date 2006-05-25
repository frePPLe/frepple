#!/usr/bin/perl
#  file     : $HeadURL: file:///develop/SVNrepository/frepple/trunk/test/scalability_2/runtest.pl $
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$
#  email    : jdetaeye@users.sourceforge.net

# This script automatically creates a model using some parameters.
# Parameters:
#    - number of buffer levels
#    - possible choices for number of operations for each buffer, per level, 
#      includes choice of type
#    - possible choices for number of flows per operation, per level
#    - possible choices for number of loads per operation, per level
#    - number of demands per end item buffer, including demand type priority 
#      and due date
#    - Multiplication factor for the above...
# Fixed are:
#    - number of items (generated dynamically based on the above parameters
#    - time horizon
# Assumptions:
#   - each resource is used at 1 level only
#
# Generic model:
#   [ buffer -> Operation -> ] ...   [ buffer -> Operation -> ] 
#   [ buffer -> Operation -> ] ...   [ buffer -> Operation -> ] 
#   [ buffer -> Operation -> ] ...   [ buffer -> Operation -> ] 
#   [ buffer -> Operation -> ] ...   [ buffer -> Operation -> ] 
#   [ buffer -> Operation -> ] ...   [ buffer -> Operation -> ] 
#       ...                                  ...                     ...
#
# Algorithm:
#   Loop through multiplication values
#      Create an end item
#      Create all demands for the end item
#      Create a delivery operation for the item
#      Create a end item buffer
#      Choose an operation
#        Choose loads
#        Choose flows
#          Recurse on the buffer
#
#  Changes of the new "creator engine":
#    - supports multiple choices of created output, compared to a fixed one
#    - adds evaluation of the expressions, compared to a constant, pre-defined 
#      replacement
#

#use strict;
#use warnings;

use lib "..";
use TestLib;
use Env qw(EXECUTABLE);
use Time::HiRes qw ( gettimeofday tv_interval );
my %runtimes;

# Values of the multiplicator
@multiplicator = (1, 2);

# Header for the output file
$head = "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n" .
        "<CURRENT>2006-01-01T00:00:00</CURRENT>\n" .
        "<COMMANDS>\n" .
        " <COMMAND xsi:type=\"COMMAND_SOLVE\" VERBOSE=\"false\">" .
        "  <SOLVER NAME=\"MRP\" xsi:type=\"SOLVER_MRP\" CONSTRAINTS=\"0\"/>" . 
        " </COMMAND>\n" .
        " <COMMAND xsi:type=\"COMMAND_SAVEPLAN\" FILENAME=\"output.xml\"/>\n" .
        "</COMMANDS>\n" .
        "<ITEMS>\n";

# Tail of the output file
$tail = "</ITEMS>\n</PLAN>\n";

# Sequential list of replacements
@replace = (
     "BODY", [
    		[ "<ITEM name=\"end_item_CNT\">\nDEL_OPER</ITEM>\n", 
    		  's/CNT/$counter%2/ge']
     ],
     "DEL_OPER", [
     	 ["<OPERATION NAME=\"deliver_CNT\">\nDEL_FLOWS\n</OPERATION>",
     	  's/CNT/$counter/ge'],
       ["<OPERATION NAME=\"deliver_CNT\" DURATION=\"24:00:00\">\n" . 
        "DEL_FLOWS\n</OPERATION>",
        's/CNT/$counter/ge'],
       ["<OPERATION NAME=\"deliver_CNT\" DURATION=\"48:00:00\">\n" .
        "DEL_FLOWS\n</OPERATION>",
        's/CNT/$counter/ge']
     ],
     "DEL_FLOWS", [
     	 ["<FLOWS><FLOW xsi:type=\"FLOW_START\">\n" .
     	  "<QUANTITY>-1</QUANTITY>\nDEL_BUF\n</FLOW></FLOWS>\n",
     	  ""]
     ],
     "DEL_BUF", [
     	 ["<BUFFER NAME=\"end_item_CNT\">\n" .
     	  "<ITEM NAME=\"end_item_CNT\"/>\n" .
     	  "PROD_OP\n" .
     	  "</BUFFER>",
     	  's/CNT/$counter/ge']
     ],
     "PROD_OP", [
       ["<PRODUCING NAME=\"make_1_CNT\"/>",
        's/CNT/$counter/ge']
     ]
     );

# Loop over all model sizes
foreach $size (@multiplicator) {

  # Start creating model
  open(OUTFILE, ">input$size.xml");
  print "\nCreating model for size $size...\n";

  # Loop over the size
  print OUTFILE $head;
  for (my $counter=0; $counter<$size; $counter++) {

    # Set a starting string
    $_ = "BODY";

    # Loop through all replacements
    for (my $repcnt=0; $repcnt<$#replace; $repcnt+=2) {

    	# Find replacement data
    	$replacement = $replace[$repcnt];
      @pipo = @{$replace[$repcnt+1]};

    	# Do the next replacement
      $repl = @{$pipo[ $counter % ($#pipo+1) ]}[0];
    	print "Replacing $replacement\n";
    	s/$replacement/$repl/g;

    	# Process the counter replacements
    	eval @{$pipo[ $counter % ($#pipo+1) ]}[1];
    }

    # Write the output of all replacements
    print OUTFILE $_;
    }
  print OUTFILE $tail;

  # End creating model input file
  close(OUTFILE);

  # Run the model
  print "Running model for size $size...\n";
	my $starttime = [gettimeofday];
  # system("$EXECUTABLE ./input$size.xml");
  # die "Planner exited abnormally\n" if $? ne 0;
  unlink "output.xml";
  #rename "input.xml", "output_$size.xml";

  # Measure the time
  $runtimes{$size} = tv_interval($starttime);
  printf "time: %.3f\n", $runtimes{$counter};
}

# Define failure criterium
if ($runtimes{$multiplicator[$#multiplicator]} >
    ($runtimes{$multiplicator[0]}+1)
    * $multiplicator[0] / $multiplicator[$#multiplicator] * 1.1)
{
	die "\nTest failed. Run time is not linear with model size.\n";
}

print "\nTest passed\n";
exit;
