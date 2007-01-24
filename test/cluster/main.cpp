/***************************************************************************
  file : $HeadURL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007 by Johan De Taeye                                    *
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


#include "freppleinterface.h"
#include "frepple.h"
using namespace frepple;


// We can't garantuee that a cluster number is always the same.
// We can only check to see that all entities that everything
// which is supposed to belong to a single cluster is doing so...
map<int,int> actual_to_expected;
map<int,int> expected_to_actual;

// This variable will be switched to EXIT_FAILURE when at least one of the
// objects has a different level or cluster than expected.
int exitcode = EXIT_SUCCESS;


void check(char* entity, string name, int cluster, int level)
{
	// Decode the entity name
	// The pattern for the name string is "NAME : LEVEL : CLUSTER"
	int first_colon = name.find(':') + 1;
	int last_colon = name.rfind(':') + 1;
	string expectedlevelstring(name, first_colon, last_colon - first_colon - 1);
	string expectedclusterstring(name,last_colon);

	// Compare the level with the expected value
	int expectedlevel = atoi(expectedlevelstring.c_str());
	if (expectedlevel != level)
	{
		cout << " Error for " << entity << " '" << name << "': Level "
		  << level << ", expected level " << expectedlevel << endl;
		exitcode = EXIT_FAILURE;
	}

	// Compare the cluster with the expected value
	int expectedcluster = atoi(expectedclusterstring.c_str());
	map<int,int>::iterator i = actual_to_expected.find(cluster);
	if (i == actual_to_expected.end())
	{
		map<int,int>::iterator j = expected_to_actual.find(expectedcluster);
		if (j == expected_to_actual.end())
		{
			// New cluster
			expected_to_actual.insert(make_pair(expectedcluster,cluster));
			actual_to_expected.insert(make_pair(cluster,expectedcluster));
		}
		else
		{
			// This entity has a new cluster number, but another cluster number
	    // from the actual output maps to the same input cluster.
	    // This condition will result in a test failure.
			exitcode = EXIT_FAILURE;
			actual_to_expected.insert
			  (make_pair(cluster,expected_to_actual[expectedcluster]));
		}
	}
	else
	{
		int mapped_cluster = i->second;
		if (expectedcluster != mapped_cluster)
		{
			cout << " Error for " << entity << " '" << name << "': Cluster "
			  << mapped_cluster << ", expected cluster " << expectedcluster << endl;
			exitcode = EXIT_FAILURE;
		}
	}
}


int main (int argc, char *argv[])
{
  try
  {
    // 0: Initialize
    FreppleInitialize(NULL);

    // 1: Read the model
    FreppleReadXMLFile("input.xml",true,false);

    // 2: Verify the operations
	  for (Operation::iterator goper = Operation::begin();
     goper != Operation::end(); ++goper)
	    check("Operation",
	          goper->getName(),
	          goper->getCluster(),
	          goper->getLevel());

    // 3: Verify the resources
	  for (Resource::iterator gres = Resource::begin();
     gres != Resource::end(); ++gres)
	    check("Resource",
	          gres->getName(),
	          gres->getCluster(),
	          gres->getLevel());

    // 4: Verify the buffers
	  for (Buffer::iterator gbuf = Buffer::begin();
     gbuf != Buffer::end(); ++gbuf)
	    check("Buffer",
	          gbuf->getName(),
	          gbuf->getCluster(),
	          gbuf->getLevel());

	  // 5: Finalize
	  FreppleExit();
  }
  catch (...)
  {
    cout << "Error: Caught an exception in main routine:" <<  endl;
    try { throw; }
    catch (exception& e) {cout << "  " << e.what() << endl;}
    catch (...) {cout << "  Unknown type" << endl;}
    FreppleExit();
    return EXIT_FAILURE;
  }
  return exitcode;
}
