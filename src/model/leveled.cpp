/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bvba                                 *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            *
 * GNU Affero General Public License for more details.                     *
 *                                                                         *
 * You should have received a copy of the GNU Affero General Public        *
 * License along with this program.                                        *
 * If not, see <http://www.gnu.org/licenses/>.                             *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"
#include <climits>


// Uncomment the following line to create debugging statements during the
// clustering and leveling algorithm.
//#define CLUSTERDEBUG


namespace frepple
{


bool HasLevel::recomputeLevels = false;
bool HasLevel::computationBusy = false;
int HasLevel::numberOfClusters = 0;
short HasLevel::numberOfLevels = 0;


void HasLevel::computeLevels()
{
  computationBusy = true;
  // Get exclusive access to this function in a multi-threaded environment.
  static mutex levelcomputationbusy;
  lock_guard<mutex> l(levelcomputationbusy);

  // Another thread may already have computed the levels while this thread was
  // waiting for the lock. In that case the while loop will be skipped.
  while (recomputeLevels)
  {
    // Reset the recomputation flag. Note that during the computation the flag
    // could be switched on again by some model change in a different thread.
    // In that case, the while loop will be rerun.
    recomputeLevels = false;

    // Force creation of all delivery operations
    for (auto gdem = Demand::begin(); gdem != Demand::end(); ++gdem)
      gdem->getDeliveryOperation();

    // Reset current levels on buffers, resources and operations.
    // Also force the creation of all producing operations on the buffers.
    size_t numbufs = Buffer::size();
    // Creating the producing operations of the buffers can cause new buffers
    // to be created. We repeat this loop until no new buffers are being added.
    // This isn't the most efficient loop, but it remains cheap and fast...
    while (true)
    {
      for (auto gbuf = Buffer::begin(); gbuf != Buffer::end(); ++gbuf)
      {
        gbuf->cluster = 0;
        gbuf->lvl = -1;
        gbuf->getProducingOperation();
      }
      size_t numbufs_after = Buffer::size();
      if (numbufs == numbufs_after)
        break;
      else
        numbufs = numbufs_after;
    }
    for (auto gres = Resource::begin(); gres != Resource::end(); ++gres)
    {
      gres->cluster = 0;
      gres->lvl = -1;
    }
    for (auto gop = Operation::begin(); gop != Operation::end(); ++gop)
    {
      gop->cluster = 0;
      gop->lvl = -1;
    }

    // Loop through all operations
    stack< pair<Operation*, int> > opstack;
    Operation* cur_oper;
    int cur_level;
    Buffer *cur_buf;
    const Flow* cur_Flow;
    bool search_level;
    int cur_cluster;
    numberOfLevels = 0;
    numberOfClusters = 0;
    map<Operation*,short> visited;
    for (auto g = Operation::begin(); g != Operation::end(); ++g)
    {
      // Select a new cluster number
      if (g->cluster)
        cur_cluster = g->cluster;
      else
      {
        // Detect hanging operations
        if (g->getFlows().empty() && g->getLoads().empty()
            && g->getSuperOperations().empty()
            && g->getSubOperations().empty()
           )
        {
          // Cluster 0 keeps all dangling operations
          g->lvl = 0;
          continue;
        }
        cur_cluster = ++numberOfClusters;
        if (numberOfClusters >= INT_MAX)
          throw LogicException("Too many clusters");
      }

#ifdef CLUSTERDEBUG
      logger << "Investigating operation '" << &*g
          << "' - current cluster " << g->cluster << endl;
#endif

      // Do we need to activate the level search?
      // Criterion are:
      //   - Not used in a super operation
      //   - Have a producing flow on the operation itself
      //     or on any of its sub operations
      search_level = false;
      if (g->getSuperOperations().empty())
      {
        search_level = true;
        // Does the operation itself have producing flows?
        for (auto fl = g->getFlows().begin();
            fl != g->getFlows().end() && search_level; ++fl)
          if (fl->isProducer()) search_level = false;
        if (search_level)
        {
          // Do suboperations have a producing flow?
          for (auto i = g->getSubOperations().rbegin();
              i != g->getSubOperations().rend() && search_level;
              ++i)
            for (auto fl = (*i)->getOperation()->getFlows().begin();
                fl != (*i)->getOperation()->getFlows().end() && search_level;
                ++fl)
              if (fl->isProducer()) search_level = false;
        }
      }

      // If both the level and the cluster are de-activated, then we can move on
      if (!search_level && g->cluster)
        continue;

      // Start recursing
      // Note that as soon as push an operation on the stack we set its
      // cluster and/or level. This is avoid that operations are needlessly
      // pushed a second time on the stack.
      opstack.push(make_pair(&*g, search_level ? 0 : -1));
      visited.clear();
      g->cluster = cur_cluster;
      if (search_level) g->lvl = 0;
      while (!opstack.empty())
      {
        // Take the top of the stack
        cur_oper = opstack.top().first;
        cur_level = opstack.top().second;
        opstack.pop();

        // Keep track of the maximum number of levels
        if (cur_level > numberOfLevels)
          numberOfLevels = cur_level;

#ifdef CLUSTERDEBUG
        logger << "    Recursing in Operation '" << *(cur_oper)
            << "' - current level " << cur_level << endl;
#endif
        // Detect loops in the supply chain
        auto detectloop = visited.find(cur_oper);
        if (detectloop == visited.end())
          // Keep track of operations already visited
          visited.insert(make_pair(cur_oper,0));
        else if (++(detectloop->second) > 1)
          // Already visited this operation enough times - don't repeat
          continue;

        // Push sub operations on the stack
        for (auto i = cur_oper->getSubOperations().rbegin();
            i != cur_oper->getSubOperations().rend();
            ++i)
        {
          if ((*i)->getOperation()->lvl < cur_level)
          {
            // Search level and cluster
            opstack.push(make_pair((*i)->getOperation(),cur_level));
            (*i)->getOperation()->lvl = cur_level;
            (*i)->getOperation()->cluster = cur_cluster;
          }
          else if (!(*i)->getOperation()->cluster)
          {
            // Search for clusters information only
            opstack.push(make_pair((*i)->getOperation(),-1));
            (*i)->getOperation()->cluster = cur_cluster;
          }
          // else: no search required
        }

        // Push super operations on the stack
        for (auto j = cur_oper->getSuperOperations().rbegin();
            j != cur_oper->getSuperOperations().rend();
            ++j)
        {
          if ((*j)->lvl < cur_level)
          {
            // Search level and cluster
            opstack.push(make_pair(*j,cur_level));
            (*j)->lvl = cur_level;
            (*j)->cluster = cur_cluster;
          }
          else if (!(*j)->cluster)
          {
            // Search for clusters information only
            opstack.push(make_pair(*j,-1));
            (*j)->cluster = cur_cluster;
          }
          // else: no search required
        }

        // Update level of resources linked to current operation
        for (auto gres = cur_oper->getLoads().begin();
            gres != cur_oper->getLoads().end(); ++gres)
        {
          stack<Resource*> rsrc;
          auto resptr = gres->getResource();
          while (resptr->getOwner())
            resptr = resptr->getOwner();
          rsrc.push(resptr);
          while (!rsrc.empty())
          {
            resptr = rsrc.top();
            rsrc.pop();

            // Update the level of the resource
            if (resptr->lvl < cur_level)
              resptr->lvl = cur_level;
            // Update the cluster of the resource and operations using it
            if (!resptr->cluster)
            {
              resptr->cluster = cur_cluster;
              // Find more operations connected to this cluster by the resource
              for (
                auto resops = resptr->getLoads().begin();
                resops != resptr->getLoads().end(); ++resops
                )
              {
                if (!resops->getOperation()->cluster)
                {
                  opstack.push(make_pair(resops->getOperation(), -1));
                  resops->getOperation()->cluster = cur_cluster;
                }
              }
            }

            // Add all child resources to the stack
            for (auto chld = resptr->getMembers(); chld != Resource::end(); ++chld)
              rsrc.push(&*chld);
          }
        }

        // Now loop through all flows of the operation
        for (auto gflow = cur_oper->getFlows().begin();
            gflow != cur_oper->getFlows().end();
            ++gflow)
        {
          cur_Flow = &*gflow;
          cur_buf = cur_Flow->getBuffer();

          // Check whether the level search needs to continue
          search_level = cur_level!=-1 && cur_buf->lvl<cur_level+1;

          // Check if the buffer needs processing
          if (search_level || !cur_buf->cluster)
          {
            // Update the cluster of the current buffer
            cur_buf->cluster = cur_cluster;

            // Loop through all flows of the buffer
            for (auto buffl = cur_buf->getFlows().begin();
                buffl != cur_buf->getFlows().end();
                ++buffl)
            {
              // Check level recursion
              if (cur_Flow->isConsumer() && search_level)
              {
                if (buffl->getOperation()->lvl < cur_level+1
                    && &*buffl != cur_Flow && buffl->isProducer())
                {
                  opstack.push(make_pair(buffl->getOperation(),cur_level+1));
                  buffl->getOperation()->lvl = cur_level+1;
                  buffl->getOperation()->cluster = cur_cluster;
                }
                else if (!buffl->getOperation()->cluster)
                {
                  opstack.push(make_pair(buffl->getOperation(),-1));
                  buffl->getOperation()->cluster = cur_cluster;
                }
                if (cur_level+1 > numberOfLevels)
                  numberOfLevels = cur_level+1;
                cur_buf->lvl = cur_level+1;
              }
              // Check cluster recursion
              else if (!buffl->getOperation()->cluster)
              {
                opstack.push(make_pair(buffl->getOperation(),-1));
                buffl->getOperation()->cluster = cur_cluster;
              }
            }
          }  // End of needs-procssing if statement

          // Add all buffers for this item to the same cluster
          Item::bufferIterator buf_iter(cur_Flow->getBuffer()->getItem());
          while (Buffer* tmpbuf = buf_iter.next())
            if (!tmpbuf->cluster)
            {
              tmpbuf->cluster = cur_cluster;
              for (auto buffl = tmpbuf->getFlows().begin();
                buffl != tmpbuf->getFlows().end();
                ++buffl)
              {
                if (!buffl->getOperation()->cluster)
                {
                  opstack.push(make_pair(buffl->getOperation(), -1));
                  buffl->getOperation()->cluster = cur_cluster;
                }
              }
            }
        } // End of flow loop

      } // End while stack not empty

    } // End of Operation loop
  } // End of while recomputeLevels. The loop will be repeated as long as model
  // changes are done during the recomputation.

  // Unlock the exclusive access to this function
  computationBusy = false;
}

} // End Namespace
