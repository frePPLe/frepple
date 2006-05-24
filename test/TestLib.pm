
package TestLib;

use strict;
use warnings;

BEGIN 
{
  use Exporter ();
  our @EXPORT = qw(createdata);
}


#
# FUNCTIONS TO CREATE DUMMY DATA FILES
#


sub createdata (*;$;$;$;$;$;@) 
{
  # Pick up the parameters
  my ($OUTFILE,$duplicates,$header,$body,$footer,@subst) = @_;
  my ($curbody, $new, $cnt);
    
  # Print the header
  printf $OUTFILE "$header";
  
  # Iteration
  for ($cnt=1; $cnt <= $duplicates; $cnt++) 
    {
    $_ = $body;
    for my $cursubst (@subst)
      { 
      $new = $cursubst . "_" . $cnt;
      s/$cursubst/$new/g; 
      }
    printf $OUTFILE "$_";
    }
  
  # Finalize
  printf $OUTFILE "$footer";
}

1;
