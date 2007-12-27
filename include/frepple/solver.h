/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
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

#ifndef SOLVER_H
#define SOLVER_H

#include "frepple/model.h"
#include <deque>
#include <cmath>

namespace frepple
{

/** @brief This solver implements a heuristic algorithm for planning demands.
  *
  * One by one the demands are processed. The demand will consume step by step
  * any upstream materials, respecting all constraints on its path.<br>
  * The solver supports all planning constraints as defined in Solver
  * class.<br>
  * See the documentation of the different solve methods to understand the
  * functionality in more detail.
  *
  * The logging levels have the following meaning:
  * - 0: Silent operation. Default logging level.
  * - 1: Show solver progress for each demand.
  * - 2: Show the complete ask&reply communication of the solver.
  * - 3: Trace the status of all entities.
  */
class MRPSolver : public Solver
{
    TYPEDEF(MRPSolver);
  protected:
    /** This variable stores the constraint which the solver should respect.
      * By default no constraints are enabled. */
    short constrts;

    /** Behavior of this solver method is:
      *  - It will ask the consuming flows for the required quantity.
      *  - The quantity asked for takes into account the quantity_per of the
      *    producing flow.
      *  - The date asked for takes into account the post-operation time
      *    of the operation.
      */
    DECLARE_EXPORT void solve(const Operation*, void* = NULL);

    /** Behavior of this solver method is:
      *  - Asks each of the routing steps for the requested quantity, starting
      *    with the last routing step.<br>
      *    The time requested for the operation is based on the start date of
      *    the next routing step.
      */
    DECLARE_EXPORT void solve(const OperationRouting*, void* = NULL);

    /** Behavior of this solver method is:
      *  - @todo implementation and doc missing. */
    DECLARE_EXPORT void solve(const OperationEffective*, void* = NULL);

    /** Behavior of this solver method is:
      *  - The solver loops through each alternate operation in order of
      *    priority. On each alternate operation, the solver will try to plan
      *    the quantity that hasn't been planned on higher priority alternates.
      *  - As a special case, operations with zero priority are skipped in the
      *    loop. These operations are considered to be temporarily unavailable.
      *  - The requested operation can be planned over multiple alternates.
      *    We don't garantuee that a request is planned using a single alternate
      *    operation.
      *  - The solver properly considers the quantity_per of all flows producing
      *    into the requested buffer, if such a buffer is specified.
      */
    DECLARE_EXPORT void solve(const OperationAlternate*,void* = NULL);

    /** Behavior of this solver method:
      *  - No propagation to upstream buffers at all, even if a producing
      *    operation has been specified.
      *  - Always give an answer for the full quantity on the requested date.
      */
    DECLARE_EXPORT void solve(const BufferInfinite*,void* = NULL);

    /** Behavior of this solver method:
      *  - Consider 0 as the hard minimum limit. It is not possible
      *    to plan with a 'hard' safety stock reservation.
      *  - Minimum inventory is treated as a 'wish' inventory. When replenishing
      *    a buffer we try to satisfy the minimum target. If that turns out
      *    not to be possible we use whatever available supply for satisfying
      *    the demand first.
      *  - Planning for the minimum target is part of planning a demand. There
      *    is no planning run independent of demand to satisfy the minimum
      *    target.<br>
      *    E.g. If a buffer has no demand on it, the solver won't try to
      *    replenish to the minimum target.<br>
      *    E.g. If the minimum target increases after the latest date required
      *    for satisfying a certain demand that change will not be considered.
      *  - The solver completely ignores the maximum target.
      */
    DECLARE_EXPORT void solve(const Buffer*, void* = NULL);

    /** Behavior of this solver method:
      *  - When the inventory drops below the minimum inventory level, a new
      *    replenishment is triggered.
      *    The replenishment brings the inventory to the maximum level again.
      *  - The minimum and maximum inventory are soft-constraints. The actual
      *    inventory can go lower than the minimum or exceed the maximum.
      *  - The minimum, maximum and multiple size of the replenishment are
      *    hard constraints, and will always be respected.
      *  - A minimum and maximum interval between replenishment is also
      *    respected as a hard constraint.
      *  - No propagation to upstream buffers at all, even if a producing
      *    operation has been specified.
      *  - The minimum calendar isn't used by the solver.
      */
    DECLARE_EXPORT void solve(const BufferProcure*, void* = NULL);

    /** Behavior of this solver method:
      *  - This method simply passes on the request to the referenced buffer.
      *    It is called from a solve(Operation*) method and passes on the
      *    control to a solve(Buffer*) method.
      * @see checkOperationMaterial
      */
    DECLARE_EXPORT void solve(const Flow*, void* = NULL);

    /** Behavior of this solver method:
      *  - The operationplan is checked for a capacity overload. When detected
      *    it is moved to an earlier date.
      *  - This move can be repeated until no capacity is found till a suitable
      *    time slot is found. If the fence and/or leadtime constraints are
      *    enabled they can restrict the feasible moving time.<br>
      *    If a feasible timeslot is found, the method exits here.
      *  - If no suitable time slot can be found at all, the operation plan is
      *    put on its original date and we now try to move it to a feasible
      *    later date. Again, successive moves are possible till a suitable
      *    slot is found or till we reach the end of the horizon.
      *    The result of the search is returned as the answer-date to the
      *    solver.
      */
    DECLARE_EXPORT void solve(const Resource*, void* = NULL);

    /** Behavior of this solver method:
      *  - Always return OK.
      */
    DECLARE_EXPORT void solve(const ResourceInfinite*,void* = NULL);

    /** Behavior of this solver method:
      *  - This method simply passes on the request to the referenced resource.
      *    With the current model structure it could easily be avoided (and
      *    thus gain a bit in performance), but we wanted to include it anyway
      *    to make the solver as generic and future-proof as possible.
      * @see checkOperationCapacity
      */
    void solve(const Load* l, void* d = NULL) {l->getResource()->solve(*this,d);}

    /** Behavior of this solver method:
      *  - Respects the following demand planning policies:<br>
      *     1) Maximum allowed lateness
      *     2) Minimum shipment quantity
      * This method is normally called from within the main solve method, but
      * it can also be called independently to plan a certain demand.
      * @see solve
      */
    DECLARE_EXPORT void solve(const Demand*, void* = NULL);

  public:
    /** This is the main solver method that will appropriately call the other
      * solve methods.<br>
      * The demands in the model will all be sorted with the criteria defined in
      * the demand_comparison() method. For each of demand the solve(Demand*)
      * method is called to plan it.
      */
    DECLARE_EXPORT void solve(void *v = NULL);

    /** Constructor. */
    MRPSolver(const string& n) : 
      Solver(n), constrts(0), maxparallel(0), lazydelay(86400L) {}

    /** Destructor. */
    virtual ~MRPSolver() {}

    DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(MRPSolver);}

    /** Static constant for the LEADTIME constraint type.<br>
      * The numeric value is 1.
      * @see MATERIAL
      * @see CAPACITY
      * @see FENCE
      */
    static const short LEADTIME;

    /** Static constant for the MATERIAL constraint type.<br>
      * The numeric value is 2.
      * @see LEADTIME
      * @see CAPACITY
      * @see FENCE
      */
    static const short MATERIAL;

    /** Static constant for the CAPACITY constraint type.<br>
      * The numeric value is 4.
      * @see MATERIAL
      * @see LEADTIME
      * @see FENCE
      */
    static const short CAPACITY;

    /** Static constant for the FENCE constraint type.<br>
      * The numeric value is 8.
      * @see MATERIAL
      * @see CAPACITY
      * @see LEADTIME
      */
    static const short FENCE;

    /** Update the constraints to be considered by this solver. This field may
      * not be applicable for all solvers. */
    void setConstraints(short i) {constrts = i;}

    /** Returns the constraints considered by the solve. */
    short getConstraints() const {return constrts;}

    /** Returns true if this solver respects the operation release fences.
      * The solver isn't allowed to create any operation plans within the
      * release fence.
      */
    bool isFenceConstrained() const {return (constrts & FENCE)>0;}

    /** Returns true if this solver respects the current time of the plan.
      * The solver isn't allowed to create any operation plans in the past.
      */
    bool isLeadtimeConstrained() const {return (constrts & LEADTIME)>0;}
    bool isMaterialConstrained() const {return (constrts & MATERIAL)>0;}
    bool isCapacityConstrained() const {return (constrts & CAPACITY)>0;}

    /** Returns true if any constraint is relevant for the solver. */
    bool isConstrained() const {return constrts>0;}

    /** This function defines the order in which the demands are being
      * planned.<br>
      * The following sorting criteria are appplied in order:
      *  - demand priority: smaller priorities first
      *  - demand due date: earlier due dates first
      *  - demand quantity: smaller quantities first
      */
    static DECLARE_EXPORT bool demand_comparison(const Demand*, const Demand*);

    /** Update the number of parallel solver threads.<br>
      * The default value depends on whether the solver is run in verbose mode
      * or not:
      *  - In normal mode the solver uses as many threads as specified by
      *    the environment variable NUMBER_OF_PROCESSORS.
      *  - In verbose mode the solver runs in a single thread to avoid
      *    mangling the debugging output of different threads.
      */
    void setMaxParallel(int i)
    {
      if (i >= 1) maxparallel = i;
      else throw DataException("Invalid number of parallel solver threads");
    }

    /** Return the number of threads used for planning. */
    int getMaxParallel() const
    {
      // Or: Explicitly specified number of threads
      if (maxparallel) return maxparallel;
      // Or: Default number of threads
      else return getLogLevel()>0 ? 1 : Environment::getProcessors();
    }

    /** Return the time increment between requests when the answered reply
      * date isn't usable. */
    TimePeriod getLazyDelay() const {return lazydelay;}

    /** Update the time increment between requests when the answered reply
      * date isn't usable. */
    void setLazyDelay(TimePeriod l) 
    {
      if (l > 0L) lazydelay = l;
      else throw DataException("Invalid lazy delay");      
    }

  private:
    typedef map < int, deque<Demand*>, less<int> > classified_demand;
    typedef classified_demand::iterator cluster_iterator;
    classified_demand demands_per_cluster;

    /** Number of parallel solver threads.<br>
      * The default value depends on whether the solver is run in verbose mode
      * or not:
      *  - In normal mode the solver uses NUMBER_OF_PROCESSORS threads.
      *  - In verbose mode the solver runs in a single thread to avoid
      *    mangling the debugging output of different threads.
      */
    int maxparallel;

    /** Time increments for a lazy replan.<br>
      * The solver is expected to return always a next-feasible date when the 
      * request can't be met. The solver can then retry the request with an 
      * updated request date. In some corner cases and in case of a bug it is
      * possible that no valid date is returned. The solver will then try the
      * request with a request date incremented by this value.<br>
      * The default value is 1 day.
      */
    TimePeriod lazydelay;      

  protected:
    /** @brief This class is a helper class of the MRPSolver class.
      *
      * It stores the solver state maintained by each solver thread.
      * @see MRPSolver
      */
    class MRPSolverdata : public CommandList
    {
        friend class MRPSolver;
      public:
        MRPSolver* getSolver() const {return sol;}
        MRPSolverdata(MRPSolver* s, int c, deque<Demand*>& d)
            : sol(s), curOwnerOpplan(NULL), q_loadplan(NULL), q_flowplan(NULL),
            q_operationplan(NULL), cluster(c), demands(d) {}

        /** Verbose mode is inherited from the solver. */
        unsigned short getLogLevel() const {return sol ? sol->getLogLevel() : 0;}

        /** This function runs a single planning thread. Such a thread will loop
          * through the following steps:
          *    - Use the method next_cluster() to find another unplanned cluster.
          *    - Exit the thread if no more cluster is found.
          *    - Sort all demands in the cluster, using the demand_comparison()
          *      method.
          *    - Loop through the sorted list of demands and plan each of them.
          *      During planning the demands exceptions are caught, and the
          *      planning loop will simply move on to the next demand.
          *      In this way, an error in a part of the model doesn't ruin the
          *      complete plan.
          * @see demand_comparison
          * @see next_cluster
          */
        virtual DECLARE_EXPORT void execute();

        virtual const MetaClass& getType() const {return MRPSolver::metadata;}
        virtual size_t getSize() const {return sizeof(MRPSolverdata);}

        bool getVerbose() const 
        {
          throw LogicException("Use the method MRPSolverdata::getLogLevel() instead of MRPSolverdata::getVerbose()");
        }

      private:
        /** Points to the solver. */
        MRPSolver* sol;

        /** Points to the demand being planned. */
        const Demand* curDemand;

        /** Points to the current owner operationplan. This is used when
          * operations are nested. */
        OperationPlan* curOwnerOpplan;

        /** Points to the current buffer. */
        const Buffer* curBuffer;

        /** A flag to force the resource solver to move the operationplan to
          * a later date where it is feasible.<br>
          * Admittedly this is an ugly hack...
          * @todo avoid the need for the forceLate variable
          */
        bool forceLate;

        /** This is the quantity we are asking for. */
        float q_qty;

        /** This is the date we are asking for. */
        Date q_date;

        /** This is the maximum date we are asking for.<br>
          * In case of a post-operation time there is a difference between
          * q_date and q_date_max.
          */
        Date q_date_max;

        /** This is the quantity we can get by the requested Date. */
        float a_qty;

        /** This is the Date when we can get extra availability. */
        Date a_date;

        /** This is a pointer to a LoadPlan. It is used for communication
          * between the Operation-Solver and the Resource-Solver. */
        LoadPlan* q_loadplan;

        /** This is a pointer to a FlowPlan. It is used for communication
          * between the Operation-Solver and the Buffer-Solver. */
        FlowPlan* q_flowplan;

        /** A pointer to an operationplan currently being solved. */
        OperationPlan* q_operationplan;

        /** An identifier of the cluster being replanned. Note that it isn't
          * always the complete cluster that is being planned.
          */
        int cluster;

        /** A deque containing all demands to be (re-)planned. */
        deque<Demand*>& demands;
    };

    /** This function will check all constraints for an operationplan
      * and propagate it upstream. The check does NOT check eventual
      * sub operationplans.
      * The return value is a flag whether the operationplan is
      * acceptable (sometimes in reduced quantity) or not.
      */
    DECLARE_EXPORT bool checkOperation(OperationPlan*, MRPSolverdata& data);

    /** Verifies whether this operationplan violates the leadtime
      * constraints. */
    DECLARE_EXPORT bool checkOperationLeadtime(OperationPlan*, MRPSolverdata&, bool);

    /** Verifies whether this operationplan violates the capacity constraint.
      * In case it does the operationplan is moved to an earlier or later
      * feasible date.
      */
    DECLARE_EXPORT void checkOperationCapacity(OperationPlan*, MRPSolverdata&);
};


/** @brief This class holds functions that used for maintenance of the solver
  * code.
  */
class LibrarySolver
{
  public:
    static void initialize();
    static void finalize() {}
};


} // end namespace


#endif
