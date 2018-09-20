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

#pragma once
#ifndef SOLVER_H
#define SOLVER_H

#include "frepple/model.h"
#ifndef DOXYGEN
#include <deque>
#include <cmath>
#endif

namespace frepple
{



/** @brief A solver class to remove excess material.
  *
  * The class works in a single thread only.
  */
class OperatorDelete : public Solver
{
  public:
    /** Constructor. */
    OperatorDelete(CommandManager* c = nullptr) : cmds(c)
    {
      initType(metadata);
    }

    /** Destructor. */
    virtual ~OperatorDelete() {}

    /** Python method for running the solver. */
    static PyObject* solve(PyObject*, PyObject*);

    /** Update the command manager */
    void setCommandManager(CommandManager* c)
    {
      cmds = c;
    }

    /** Return the command manager. */
    CommandManager* getCommandManager() const
    {
      return cmds;
    }

    /** Remove all entities for excess material that can be removed. */
    void solve(void *v = nullptr);

    /** Remove an operationplan and all its upstream supply.<br>
      * The argument operationplan is invalid when this function returns!
      */
    void solve(OperationPlan*, void* = nullptr);

    /** Remove excess from a buffer and all its upstream colleagues. */
    void solve(const Buffer*, void* = nullptr);

    /** Empty solve method for infinite buffers. */
    void solve(const BufferInfinite*, void* = nullptr) {}

    /** Remove excess starting from a single demand. */
     void solve(const Demand*, void* = nullptr);

    /** Remove excess operations on a resource. */
    void solve(const Resource*, void* = nullptr);

    static int initialize();
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;

    /** Auxilary function to push consuming or producing buffers of an
      * operationplan to the stack.
      */
    void pushBuffers(OperationPlan*, bool consuming, bool producing);

    bool getConstrained() const
    {
      return constrained;
    }

    void setConstrained(bool b)
    {
      constrained = b;
    }

  private:
	  /** A list of buffers still to scan for excess. */
	  vector<Buffer*> buffersToScan;   // TODO Use a different data structure to allow faster lookups and sorting?

	  /** A pointer to a command manager that takes care of the commit and
	    * rollback of all actions.
	    */
	  CommandManager* cmds;

    bool constrained = true;
};


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
class SolverCreate : public Solver
{
  protected:
    /** This variable stores the constraint which the solver should respect.
      * By default all constraints are enabled. */
    short constrts = 15;

    bool allowSplits = true;

    bool rotateResources = true;

    /** When set to false we solve only for the entity being called. This is
      * used when you want to control manual the sequence of the planning
      * loop.
      */
    bool propagate = true;

    /** Index of the cluster to replan selectively. */
    int cluster = -1;

    /** Copy the user exit functions from the custom dictionary into the
      * internal fields.
      */
    void update_user_exits();

    /** Behavior of this solver method is:
      *  - It will ask the consuming flows for the required quantity.
      *  - The quantity asked for takes into account the quantity_per of the
      *    producing flow.
      *  - The date asked for takes into account the post-operation time
      *    of the operation.
      */
    void solve(const Operation*, void* = nullptr);

    void solve(const OperationItemSupplier*, void* = nullptr);

    /** Behavior of this solver method is:
      *  - Asks each of the routing steps for the requested quantity, starting
      *    with the last routing step.<br>
      *    The time requested for the operation is based on the start date of
      *    the next routing step.
      */
    void solve(const OperationRouting*, void* = nullptr);

    /** Behavior of this solver method is:
      *  - The solver asks each alternate for the percentage of the requested
      *    quantity. We ask the operation with the highest percentage first,
      *    and only ask suboperations that are effective on the requested date.
      *  - The percentages don't need to add up to 100. We scale the proportiona
      *  - If an alternate replies more than requested (due to multiple and
      *    minimum size) this is considered when dividing the remaining
      *    quantity over the others.
      *  - If an alternate can't deliver the requested percentage of the
      *    quantity, we undo all previous alternates and retry planning
      *    for a rescaled total quantity.
      *    The split percentage is thus a hard constraint that must be
      *    respected - a constraint on a single alternate also constrains the
      *    planned quantity on all others.
      *    Obviously if an alternate replies 0 the total rescaled quantity
      *    remains 0.
      *  - A case not handled with this logic is when the split operations
      *    merge again upstream. If a shared upstream constraint is limiting
      *    the total quantity, the solver doesn't see this and can't react
      *    nicely to it. The solution would be that we a) detect this kind
      *    of situation and b) iteratively try to split an increasing total
      *    quantity. TODO...
      *  - For each effective alternate suboperation we create 1
      *    suboperationplan of the top operationplan.
      */
    void solve(const OperationSplit*,void* = nullptr);

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
    void solve(const OperationAlternate*,void* = nullptr);

    /** Behavior of this solver method:
      *  - No propagation to upstream buffers at all, even if a producing
      *    operation has been specified.
      *  - Always give an answer for the full quantity on the requested date.
      */
    void solve(const BufferInfinite*,void* = nullptr);

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
    void solve(const Buffer*, void* = nullptr);

    /** Called by the previous method to solve for safety stock only. */
    void solveSafetyStock(const Buffer*, void* = nullptr);

    /** Behavior of this solver method:
      *  - This method simply passes on the request to the referenced buffer.
      *    It is called from a solve(Operation*) method and passes on the
      *    control to a solve(Buffer*) method.
      * @see checkOperationMaterial
      */
    void solve(const Flow*, void* = nullptr);

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
    void solve(const Resource*, void* = nullptr);

    /** Behavior of this solver method:
      *  - Always return OK.
      */
    void solve(const ResourceInfinite*,void* = nullptr);

    /** Behavior of this solver method:
      *  - The operationplan is checked for a capacity in the time bucket
      *    where its start date falls.
      *  - If no capacity is found in that bucket, we check in the previous
      *    buckets (until we hit the limit defined by the maxearly field).
      *    We move the operationplan such that it starts one second before
      *    the end of the earlier bucket.
      *  - If no available time bucket is found in the allowed time fence,
      *    we scan for the first later bucket which still has capacity left.
      *    And we return the start date of that bucket as the answer-date to
      *    the solver.
      */
    void solve(const ResourceBuckets*,void* = nullptr);

    /** Behavior of this solver method:
      *  - This method simply passes on the request to the referenced resource.
      *    With the current model structure it could easily be avoided (and
      *    thus gain a bit in performance), but we wanted to include it anyway
      *    to make the solver as generic and future-proof as possible.
      * @see checkOperationCapacity
      */
    void solve(const Load*, void* = nullptr);

    /** Choose a resource.<br>
      * Normally the chosen resource is simply the resource specified on the
      * load.<br>
      * When the load specifies a certain skill and an aggregate resource, then
      * we search for appropriate child resources.
      */
    void chooseResource(const Load*, void*);

  public:
    /** Behavior of this solver method:
      *  - Respects the following demand planning policies:<br>
      *     1) Maximum allowed lateness
      *     2) Minimum shipment quantity
      * This method is normally called from within the main solve method, but
      * it can also be called independently to plan a certain demand.
      * @see solve
      */
    void solve(const Demand*, void* = nullptr);

    /** This is the main solver method that will appropriately call the other
      * solve methods.<br>
      * The demands in the model will all be sorted with the criteria defined in
      * the demand_comparison() method. For each of demand the solve(Demand*)
      * method is called to plan it.
      */
    void solve(void *v = nullptr);

    /** Constructor. */
    SolverCreate() : commands(this)
    {
      initType(metadata);
      commands.setCommandManager(&mgr);
    }

    /** Destructor. */
    virtual ~SolverCreate() {}

    static int initialize();
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;

    /** Static constant for the LEADTIME constraint type.<br>
      * The numeric value is 1.
      * @see MATERIAL
      * @see CAPACITY
      * @see FENCE
      */
    static const short LEADTIME = 1;

    /** Static constant for the MATERIAL constraint type.<br>
      * The numeric value is 2.
      * @see LEADTIME
      * @see CAPACITY
      * @see FENCE
      */
    static const short MATERIAL = 2;

    /** Static constant for the CAPACITY constraint type.<br>
      * The numeric value is 4.
      * @see MATERIAL
      * @see LEADTIME
      * @see FENCE
      */
    static const short CAPACITY = 4;

    /** Static constant for the FENCE constraint type.<br>
      * The numeric value is 8.
      * @see MATERIAL
      * @see CAPACITY
      * @see LEADTIME
      */
    static const short FENCE = 8;

    /** Used internally to avoid inefficient loops. */
    static const unsigned short MAX_LOOP = 500;

    int getCluster() const
    {
      return cluster;
    }

    void setCluster(int i)
    {
      cluster = i;
    }

    /** Update the constraints to be considered by this solver. This field may
      * not be applicable for all solvers. */
    void setConstraints(short i)
    {
      constrts = i;
    }

    /** Returns the constraints considered by the solve. */
    short getConstraints() const
    {
      return constrts;
    }

    /** Returns true if this solver respects the operation release fences.
      * The solver isn't allowed to create any operation plans within the
      * release fence.
      */
    bool isFenceConstrained() const
    {
      return (constrts & FENCE)>0;
    }

    /** Returns true if the solver respects the current time of the plan.
      * The solver isn't allowed to create any operation plans in the past.
      */
    bool isLeadTimeConstrained() const
    {
      return (constrts & LEADTIME)>0;
    }

    /** Returns true if the solver respects the material procurement
      * constraints on procurement buffers.
      */
    bool isMaterialConstrained() const
    {
      return (constrts & MATERIAL)>0;
    }

    /** Returns true if the solver respects capacity constraints. */
    bool isCapacityConstrained() const
    {
      return (constrts & CAPACITY)>0;
    }

    /** Returns true if any constraint is relevant for the solver. */
    bool isConstrained() const
    {
      return constrts>0;
    }

    /** Returns the plan type:
      *  - 1: Constrained plan.<br>
      *       This plan doesn't not violate any constraints.<br>
      *       In case of material or capacity shortages the demand is delayed
      *       or planned short.
      *  - 2: Unconstrained plan with alternate search.<br>
      *       This unconstrained plan leaves material, capacity and operation
      *       problems when shortages are found. Availability is searched across
      *       alternates and the remaining shortage is shown on the primary
      *       alternate.<br>
      *       The demand is always fully met on time.
      *  - 3: Unconstrained plan without alternate search.<br>
      *       This unconstrained plan leaves material, capacity and operation
      *       problems when shortages are found. It doesn't evaluate availability
      *       on alternates.<br>
      *       The demand is always fully met on time.
      * The default is 1.
      */
    short getPlanType() const
    {
      return plantype;
    }

    void setPlanType(short b)
    {
      if (b < 1 || b > 3)
        throw DataException("Invalid plan type");
      plantype = b;
    }

    /** This function defines the order in which the demands are being
      * planned.<br>
      * The following sorting criteria are applied in order:
      *  - demand priority: smaller priorities first
      *  - demand due date: earlier due dates first
      *  - demand quantity: smaller quantities first
      */
    static bool demand_comparison(const Demand*, const Demand*);

    /** Return the time increment between requests when the answered reply
      * date isn't usable. */
    Duration getLazyDelay() const
    {
      return lazydelay;
    }

    /** Update the time increment between requests when the answered reply
      * date isn't usable. */
    void setLazyDelay(Duration l)
    {
      if (l <= 0L) throw DataException("Invalid lazy delay");
      lazydelay = l;
    }

    /** Return the minimum time increment between ask cycles. */
    Duration getMinimumDelay() const
    {
      return minimumdelay;
    }

    /** Update the time increment between requests when the answered reply
      * date isn't usable. */
    void setMinimumDelay(Duration l)
    {
      if (l < 0L) throw DataException("Invalid minimum delay");
      minimumdelay = l;
    }


    /** Return the time we wait for existing confirmed supply before 
      * triggering a new replenishment.
      * Default: 0
      */
    Duration getAutoFence() const
    {
      return autofence;
    }

    /** the time we wait for existing confirmed supply before 
      * triggering a new replenishment.
      * Default: 0
      */
    void setAutoFence(Duration l)
    {
      if (l < 0L)
        throw DataException("Invalid autofence");
      autofence = l;
    }

    /** Get the threshold to stop iterating when the delta between iterations
      * is less than this absolute threshold.
      */
    double getIterationThreshold() const
    {
      return iteration_threshold;
    }

    /** Set the threshold to stop iterating when the delta between iterations
      * is less than this absolute threshold.<br>
      * The value must be greater than or equal to zero and the default is 1.
      */
    void setIterationThreshold(double d)
    {
      if (d<0.0)
        throw DataException("Invalid iteration threshold: must be >= 0");
      iteration_threshold = d;
    }

    /** Get the threshold to stop iterating when the delta between iterations
      * is less than this percentage threshold.
      */
    double getIterationAccuracy() const
    {
      return iteration_accuracy;
    }

    /** Set the threshold to stop iterating when the delta between iterations
      * is less than this percentage threshold.<br>
      * The value must be between 0 and 100 and the default is 1%.
      */
    void setIterationAccuracy(double d)
    {
      if (d<0.0 || d>100.0)
        throw DataException("Invalid iteration accuracy: must be >=0 and <= 100");
      iteration_accuracy = d;
    }

    /** Return the maximum number of asks allowed to plan a demand.
      * If the can't plan a demand within this limit, we consider it
      * unplannable.
      */
    unsigned long getIterationMax() const
    {
      return iteration_max;
    }

    /** Update the maximum number of asks allowed to plan a demand.
      * If the can't plan a demand within this limit, we consider it
      * unplannable.
      */
    void setIterationMax(unsigned long d)
    {
      iteration_max = d;
    }

    /** Specify a Python function that is called before solving a flow. */
    void setUserExitFlow(PythonFunction n)
    {
      userexit_flow = n;
    }

    /** Return the Python function that is called before solving a flow. */
    PythonFunction getUserExitFlow() const
    {
      return userexit_flow;
    }

    /** Specify a Python function that is called before solving a demand. */
    void setUserExitDemand(PythonFunction n)
    {
      userexit_demand = n;
    }

    /** Return the Python function that is called before solving a demand. */
    PythonFunction getUserExitDemand() const
    {
      return userexit_demand;
    }

    /** Specify a Python function that is called before solving a buffer. */
    void setUserExitBuffer(PythonFunction n)
    {
      userexit_buffer = n;
    }

    /** Return the Python function that is called before solving a buffer. */
    PythonFunction getUserExitBuffer() const
    {
      return userexit_buffer;
    }

    /** Specify a Python function that is called before solving a resource. */
    void setUserExitResource(PythonFunction n)
    {
      userexit_resource = n;
    }

    /** Return the Python function that is called before solving a resource. */
    PythonFunction getUserExitResource() const
    {
      return userexit_resource;
    }

    /** Specify a Python function that is called before solving a operation. */
    void setUserExitOperation(PythonFunction n)
    {
      userexit_operation = n;
    }

    /** Return the Python function that is called before solving a operation. */
    PythonFunction getUserExitOperation() const
    {
      return userexit_operation;
    }

    /** Python method for running the solver. */
    static PyObject* solve(PyObject*, PyObject*);

    /** Python method for committing the plan changes. */
    static PyObject* commit(PyObject*, PyObject*);

    /** Python method for undoing the plan changes. */
    static PyObject* rollback(PyObject*, PyObject*);

    bool getRotateResources() const
    {
      return rotateResources;
    }

    void setRotateResources(bool b)
    {
      rotateResources = b;
    }

    bool getAllowSplits() const
    {
      return allowSplits;
    }

    void setAllowSplits(bool b)
    {
      allowSplits = b;
    }

    bool getPropagate() const
    {
      return propagate;
    }

    void setPropagate(bool b)
    {
      propagate = b;
    }

    bool getPlanSafetyStockFirst() const
    {
      return planSafetyStockFirst;
    }

    void setPlanSafetyStockFirst(bool b)
    {
      planSafetyStockFirst = b;
    }

    Duration getAdministrativeLeadTime() const
    {
      return administrativeleadtime;
    }

    void setAdministrativeLeadTime(Duration l)
    {
      if (l < 0L) throw DataException("Administrative Lead Time must be a positive value");
      administrativeleadtime = l;
    }

    bool getErasePreviousFirst() const
    {
      return erasePreviousFirst;
    }

    void setErasePreviousFirst(bool b)
    {
      erasePreviousFirst= b;
    }

    void setCommandManager(CommandManager* a = nullptr)
    {
      commands.setCommandManager(a);
    }

    CommandManager* getCommandManager() const
    {
      return commands.getCommandManager();
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addShortField<Cls>(Tags::constraints, &Cls::getConstraints, &Cls::setConstraints);
      m->addShortField<Cls>(Tags::plantype, &Cls::getPlanType, &Cls::setPlanType);
      m->addDoubleField<Cls>(SolverCreate::tag_iterationthreshold, &Cls::getIterationThreshold, &Cls::setIterationThreshold);
      m->addDoubleField<Cls>(SolverCreate::tag_iterationaccuracy, &Cls::getIterationAccuracy, &Cls::setIterationAccuracy);
      m->addDurationField<Cls>(SolverCreate::tag_lazydelay, &Cls::getLazyDelay, &Cls::setLazyDelay);
      m->addDurationField<Cls>(SolverCreate::tag_administrativeleadtime, &Cls::getAdministrativeLeadTime, &Cls::setAdministrativeLeadTime);
      m->addDurationField<Cls>(SolverCreate::tag_minimumdelay, &Cls::getMinimumDelay, &Cls::setMinimumDelay);
      m->addDurationField<Cls>(SolverCreate::tag_autofence, &Cls::getAutoFence, &Cls::setAutoFence);
      m->addBoolField<Cls>(SolverCreate::tag_allowsplits, &Cls::getAllowSplits, &Cls::setAllowSplits);
      m->addBoolField<Cls>(SolverCreate::tag_rotateresources, &Cls::getRotateResources, &Cls::setRotateResources);
      m->addBoolField<Cls>(SolverCreate::tag_planSafetyStockFirst, &Cls::getPlanSafetyStockFirst, &Cls::setPlanSafetyStockFirst);
      m->addUnsignedLongField<Cls>(SolverCreate::tag_iterationmax, &Cls::getIterationMax, &Cls::setIterationMax);
      m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, &Cls::setCluster);
    }

  private:
    typedef vector< deque<Demand*> > classified_demand;
    typedef classified_demand::iterator cluster_iterator;
    classified_demand demands_per_cluster;

    static const Keyword tag_iterationthreshold;
    static const Keyword tag_iterationaccuracy;
    static const Keyword tag_lazydelay;
    static const Keyword tag_minimumdelay;
    static const Keyword tag_autofence;
    static const Keyword tag_allowsplits;
    static const Keyword tag_rotateresources;
    static const Keyword tag_planSafetyStockFirst;
    static const Keyword tag_administrativeleadtime;
    static const Keyword tag_iterationmax;

    /** Type of plan to be created. */
    short plantype = 1;

    /** Time increments for a lazy replan.<br>
      * The solver is expected to return always a next-feasible date when the
      * request can't be met. The solver can then retry the request with an
      * updated request date. In some corner cases and in case of a bug it is
      * possible that no valid date is returned. The solver will then try the
      * request with a request date incremented by this value.<br>
      * The default value is 1 day.
      */
    Duration lazydelay = 86400L;

    /** Administrative lead time, demand should therefore be planned ahead 
      * by the solver at due minus administrative leadtime
    */
    Duration administrativeleadtime = 0L;

    /** Minimum acceptable time increment between ask cycles. 
      * By default a delay of 1 seconds is sufficient to trigger a new ask cycle.
      * This can indicate an inefficient search of the planning algorithm.      
      * Increasing this value avoids this inefficiency, but can reduce the quality
      * of the plan - we can leave "holes" in the schedule.
      */
    Duration minimumdelay;

    /** Time we wait for existing confirmed supply before triggering a new replenishment. */
    Duration autofence;

    /** Threshold to stop iterating when the delta between iterations is
      * less than this absolute limit.
      */
    double iteration_threshold = 1;

    /** Threshold to stop iterating when the delta between iterations is
      * less than this percentage limit.
      */
    double iteration_accuracy = 0.01;

    /** Maximum number of asks allowed to plan a demand.
      * If the can't plan a demand within this limit, we consider it
      * unplannable.
      */
    unsigned long iteration_max = 0;

    /** A Python callback function that is called for each alternate
      * flow. If the callback function returns false, that alternate
      * flow is an invalid choice.
      */
    PythonFunction userexit_flow;

    /** A Python callback function that is called for each demand. The return
      * value is not used.
      */
    PythonFunction userexit_demand;

    /** A Python callback function that is called for each buffer. The return
      * value is not used.
      */
    PythonFunction userexit_buffer;

    /** A Python callback function that is called for each resource. The return
      * value is not used.
      */
    PythonFunction userexit_resource;

    /** A Python callback function that is called for each operation. The return
      * value is not used.
      */
    PythonFunction userexit_operation;

    /** A flag that determines how we plan safety stock.<br/>
      *
      * By default the flag is FALSE and we get the following behavior:
      *  - When planning demands, we already try to replenish towards the
      *    safety stock level.
      *  - After planning all demands, we do another loop over all buffers
      *    to replenish to the safety stock level. This will replenish eg
      *    buffers without any (direct or indirect) demand on them.
      *
      * If the flag is set to TRUE, replenishing to the safety stock level
      * is more important than planning the demand on time. We get the
      * following behavior:
      *  - Before planning any demand, we try to replenish any buffer to its
      *    safety stock level.
      *    Buffers closer to the end item demand are replenished first.
      *  - When planning demands, we try to replenish towards the safety
      *    stock level.
      */
    bool planSafetyStockFirst = false;

    /** Flag to specify whether we erase the previous plan first or not. */
    bool erasePreviousFirst = true;

  protected:
    /** @brief This class is used to store the solver status during the
      * ask-reply calls of the solver.
      */
    struct State
    {
      /** Points to the demand being planned.<br>
        * This field is only non-null when planning the delivery operation.
        */
      Demand* curDemand;

      /** Points to the current owner operationplan. This is used when
        * operations are nested. */
      OperationPlan* curOwnerOpplan;

      /** Points to the current buffer. */
      Buffer* curBuffer;

      /** A flag to force the resource solver to move the operationplan to
        * a later date where it is feasible.
        */
      bool forceLate;

      /** This is the quantity we are asking for. */
      double q_qty;

      /** This is the date we are asking for. */
      Date q_date;

      /** This is the maximum date we are asking for.<br>
        * In case of a post-operation time there is a difference between
        * q_date and q_date_max.
        */
      Date q_date_max;

      /** This is the quantity we can get by the requested Date. */
      double a_qty;

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

      /** Cost of the reply.<br>
        * Only the direct cost should be returned in this field.
        */
      double a_cost;

      /** Penalty associated with the reply.<br>
        * This field contains indirect costs and other penalties that are
        * not strictly related to the request. Examples are setup costs,
        * inventory carrying costs, ...
        */
      double a_penalty;

      /** Defines a minimum quantity that we expect the answer to cover. */
      double q_qty_min;
    };

    /** @brief This class is a helper class of the SolverCreate class.
      *
      * It stores the solver state maintained by each solver thread.
      * @see SolverCreate
      */
    class SolverData
    {
        friend class SolverCreate;
      public:
        static void runme(void *args)
        {
          CommandManager mgr;
          SolverCreate::SolverData* x = static_cast<SolverCreate::SolverData*>(args);
          x->setCommandManager(&mgr);
          x->commit();
          delete x;
        }

        /** Return the solver. */
        SolverCreate* getSolver() const
        {
          return sol;
        }

        /** Constructor. */
        SolverData(SolverCreate* s=nullptr, int c=0, deque<Demand*>* d=nullptr);

        /** Destructor. */
        ~SolverData();

        /** Verbose mode is inherited from the solver. */
        unsigned short getLogLevel() const
        {
          return sol ? sol->getLogLevel() : 0;
        }

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
        void commit();

        void setCommandManager(CommandManager* a = nullptr);

        CommandManager* getCommandManager() const
        {
          return mgr;
        }

        bool getVerbose() const
        {
          throw LogicException("Use the method SolverData::getLogLevel() instead of SolverData::getVerbose()");
        }

        /** Add a new state to the status stack. */
        void push(double q = 0.0, Date d = Date::infiniteFuture, bool full = false);

        /** Removes a state from the status stack. */
        void pop(bool copy_answer = false);

      private:
        static const int MAXSTATES = 256;

        /** Auxilary method to replenish safety stock in all buffers of a
          * cluster. This method is only intended to be called from the
          * commit() method.
          * @see SolverCreate::planSafetyStockFirst
          * @see SolverCreate::SolverData::commit
          */
        void solveSafetyStock(SolverCreate*);

        /** Pointer to the command manager. */
        CommandManager* mgr = nullptr;

        /** Points to the solver. */
        SolverCreate* sol = nullptr;

        /** An identifier of the cluster being replanned. Note that it isn't
          * always the complete cluster that is being planned.
          */
        int cluster;

        /** Internal solver to remove material. */
        OperatorDelete *operator_delete = nullptr;

        /** Points to the demand being planned. */
        Demand* planningDemand = nullptr;

        /** A deque containing all demands to be (re-)planned. */
        deque<Demand*>* demands;

        /** Stack of solver status information. */
        State statestack[MAXSTATES];

        /** Count the number of asks. */
        unsigned long iteration_count;

        /** True when planning in constrained mode. */
        bool constrainedPlanning;

        /** Flags whether or not constraints are being tracked. */
        bool logConstraints;

        /** Internal flag that is set to true when solving for safety stock. */
        bool safety_stock_planning;

        /** Collect all purchase operations. */
        struct order_operationitemsuppliers
        {
          bool operator() (const OperationItemSupplier* const& lhs, const OperationItemSupplier* const& rhs) const
          {
            return lhs->getName() < rhs->getName();
          }
        };
        set<const OperationItemSupplier*, order_operationitemsuppliers> purchase_operations;

      public:
        /** Pointer to the current solver status. */
        State* state;

        /** Pointer to the solver status one level higher on the stack. */
        State* prevstate;
    };

    /** When autocommit is switched off, this command structure will contain
      * all plan changes.
      */
    SolverData commands;

    /** Command manager used when autocommit is switched off. */
    CommandManager mgr;

    /** An auxilary method that will create an extra operationplan to
      * supply the requested quantity.
      * It calls the checkOperation method to check the feasibility
      * of the new operationplan.
      */
    OperationPlan* createOperation(const Operation*, SolverData*, bool propagate = true, bool start_or_end = true);

    /** This function will check all constraints for an operationplan
      * and propagate it upstream. The check does NOT check eventual
      * sub operationplans.<br>
      * The return value is a flag whether the operationplan is
      * acceptable (sometimes in reduced quantity) or not.
      */
    bool checkOperation(OperationPlan*, SolverData& data);

    /** Verifies whether this operationplan violates the leadtime
      * constraints. */
    bool checkOperationLeadTime(OperationPlan*, SolverData&, bool);

    /** Verifies whether this operationplan violates the capacity constraint.<br>
      * In case it does the operationplan is moved to an earlier or later
      * feasible date.
      */
    void checkOperationCapacity(OperationPlan*, SolverData&);

  public:
    /** Scan the operationplans that are about to be committed to verify that
      * they are not creating any excess.
      */
    void scanExcess(CommandManager*);

    /** Scan the operationplans that are about to be committed to verify that
      * they are not creating any excess.
      */
    void scanExcess(CommandList*);

    /** Return true if there is at least one non-delivery operationplan in
      * the command list.
      */
    bool hasOperationPlans(CommandManager*);

    /** Return true if there is at least one non-delivery operationplan in
      * the command list.
      */
    bool hasOperationPlans(CommandList*);

    /** Get a reference to the command list. */
    SolverData& getCommands()
    {
      return commands;
    }

};


/** @brief This class holds functions that used for maintenance of the solver
  * code.
  */
class LibrarySolver
{
  public:
    static void initialize();
};


} // end namespace


#endif
