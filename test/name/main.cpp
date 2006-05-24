/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/test/name/main.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : johan_de_taeye@yahoo.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Lesser General Public License as published   *
 * by the Free Software Foundation; either version 2.1 of the License, or  *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser *
 * General Public License for more details.                                *
 *                                                                         *
 * You should have received a copy of the GNU Lesser General Public        *
 * License along with this library; if not, write to the Free Software     *
 * Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA *
 *                                                                         *
 ***************************************************************************/


#include "frepple.h"
using namespace frepple;

/** Print the content of the list, and also verify its integrity. */
void printlist(char* msg)
{
  clog << msg << ":";
  for (Customer::iterator i = Customer::begin(); i != Customer::end(); ++i)
    clog << "  " << *i;
  clog << endl;
  Customer::verify();
}


/** Runs a simple test of the functionality.
  * The integrity of the tree is verified after a number of simple operations:
  *   - insert
  *   - find
  *   - erase
  *   - clear
  */
void functionality_test()
{
  // Validate the empty list
  printlist("Start");

  // Inserting elements
  Customer::add(new Customer("alfa"));
  printlist("insert alfa");
  Customer::add(new Customer("beta"));
  printlist("insert beta");
  Customer::add(new Customer("alfa1"));
  printlist("insert alfa1");
  Customer::add(new Customer("gamma"));
  printlist("insert gamma");
  Customer::add(new Customer("delta"));
  printlist("insert delta");
  Customer::add(new Customer("omega"));
  printlist("insert omega");

  // Searching for some existing names
  string s("delta");
  clog << "Find " << s << ": " << (Customer::find(s) ? "OK" : "NOK") << endl;
  s = "omega";
  clog << "Find " << s << ": " << (Customer::find(s) ? "OK" : "NOK") << endl;

  // Searching for nonexistent name
  s = "hamburger";
  clog << "Find " << s << ": " << (Customer::find(s) ? "OK" : "NOK") << endl;
  printlist("searches");

  // Erasing some existing elements
  delete Customer::find("delta");
  printlist("erase delta");
  delete Customer::find("gamma");
  printlist("erase gamma");

  // Erasing some existing elements
  delete Customer::find("hamburger");
  printlist("erase hamburger");

  // Inserting a duplicate
  Customer::add(new Customer("alfa2"));
  printlist("insert alfa2");
  Customer::add(new Customer("alfa4"));
  printlist("insert alfa4");
  Customer::add(new Customer("alfa x"));
  printlist("insert alfa x");
  Customer::add(new Customer("alfa y"));
  printlist("insert alfa y");
  Customer::add(new Customer("alfa z"));
  printlist("insert alfa z");
  Customer::add(new Customer("delta"));
  printlist("insert delta");
  Customer::add(new Customer("phi"));
  printlist("insert phi");

  // Inserting an already existing element
  Customer * k = new Customer("alfa2");
  clog << Customer::add(k)->getName() << endl;
  printlist("duplicate insert alfa2");
  delete k;

  // Clearing the list
  Customer::clear();
  printlist("clear");
}


/** Creates a random string.
  * Since the random function doesn't garantuee uniqueness of the generated
  * numbers, it is possible that we create duplicate names.
  */
string generate_name()
{
  stringstream ch;
  ch << rand() << endl;
  return ch.str();
}


/** Runs a number of tree operations and estimates the performance.
  * It tries to compute the test time based on the size with the formula:
  *    time = A + B * log (number of elements)
  * The parameters are computed from 2 measuring points time1 with size1
  * and time2 with size2.
  * Some simple math then provides the following equations for estimating
  * the parameters A and B:
  *     B = (time1 - time2) / log (size1 / size2)
  *     A = time1 - B * log (size1)
  * The proof of this equations is left as an exercise to the reader.
  * Once two measurements are available, the remaining data points are
  * expected to fall within 5% of the expectations.
  */
void scalability_test()
{
  // Formatting of the output: We print only 1 decimal to garantuee that
  // test results are stable across runs and platforms.
  clog.precision(1);
  clog.setf(ios_base::fixed);

  // Repeat for different tree sizes, and compare the relative performance
  clog << "Elements   Time per operation"  << endl;
  double ref1=0.0f, ref2=0.0f, a=0.0f, b=0.0f, size1, size2;
  int testpoints[] = 
    {300000, 5000, 250000, 200000, 150000, 100000, 50000, 25000};
  int cnt=0;
  //for (int scale = 400000; scale >= 100; scale*=0.75)
  for (int scale=testpoints[0]; cnt<=7; scale=testpoints[++cnt])
  {
    // Generate some strings. This turns out to be a rather slow process, so
    // we want to exclude it from the timing.
    string names[scale];
    srand(1000);
    for(int i=0; i<scale; ++i)
      names[i] = generate_name();

    // Create a timer
    Timer m;

    // Insert elements in the list
    for(int i=0; i<scale; ++i) Customer::add(new Customer(names[i]));

    // Do a number of searches and deletes
    for(int i=0; i<scale; ++i) Customer::find(names[i]);

    // Do a number of deletes
    for(int i=0; i<scale; ++i) delete Customer::find(names[i]);

    // Clear the complete list
    if (Customer::size()) throw domain_error("Tree elements not all deleted");
    Customer::clear();

    // Measure the time
    float curtime = m.elapsed();

    // Estimate the performance parameters
    // Print the performance
    if (ref1 == 0.0f)
    {
      // First data point
      ref1 = curtime * 1000 / scale;
      size1 = scale;
      clog << scale << "   " << (curtime * 1000 / scale) / ref1 << endl;
    }
    else if (ref2 == 0.0f)
    {
      // Second data point
      ref2 = curtime * 1000 / scale;
      size2 = scale;
      b = (ref1-ref2) / log(size1/size2);
      a = ref1 - b*log(size1);
      clog << scale << "   " << (curtime * 1000 / scale) / ref1 << endl;
    }
    else
    {
      // Other data points
      float compare = (curtime * 1000 / scale) / (a+b*log(scale));
      clog << scale << "   " 
        <<  (curtime * 1000 / scale) / ref1 << "  " 
        << (fabs(compare-1) < 0.05 ? "OK" : "NOK") << endl;
    }
  }
  //clog.precision(3);
  //clog << " A: " << a << " B: " << b << endl;
}


int main (int argc, char *argv[])
{
  try
  {
    XMLPlatformUtils::Initialize();
    clog << endl << "FUNCTIONAL TEST:" << endl << endl;
    functionality_test();
    clog << endl << "SCALABILITY TEST:" << endl << endl;
    scalability_test();
    return EXIT_SUCCESS;
  }
  catch (exception& e)
  {
    clog << "Error: " << e.what() << endl;
    return EXIT_FAILURE;
  } catch (...)
  {
    clog << "Error: Exception thrown." << endl;
    return EXIT_FAILURE;
  }
}
