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

/** @file forecast.h
  * @brief Header file for the module forecast.
  *
  * @namespace module_forecast
  * @brief Module for representing forecast.
  *
  * The forecast module provides the following functionality:
  *
  *  - A <b>new demand type</b> to model forecasts.<br>
  *    A forecast demand is bucketized. A demand is automatically
  *    created for each time bucket.<br>
  *    A calendar is used to define the time buckets to be used.
  *
  *  - Functionality for <b>distributing / profiling</b> forecast numbers
  *    into time buckets used for planning.<br>
  *    This functionality is typically used to translate between the time
  *    granularity of the sales department (which creates a sales forecast
  *    per e.g. calendar month) and the manufacturing department (which
  *    creates manufacturing and procurement plans in weekly or daily buckets
  *    ).<br>
  *    Another usage is to model a delivery date profile of the customers.
  *    Each bucket has a weight that is used to model situations where the
  *    demand is not evenly spread across buckets: e.g. when more orders are
  *    expected due on a monday than on a friday, or when a peak of orders is
  *    expected for delivery near the end of a month.
  *
  *  - A solver for <b>netting orders from the forecast</b>.<br>
  *    As customer orders are being received they need to be deducted from
  *    the forecast to avoid double-counting demand.<br>
  *    The netting solver will for each order search for a matching forecast
  *    and reduce the remaining net quantity of the forecast.
  *
  *  - A forecasting algorithm to <b>extrapolate historical demand data 
  *    to the future</b>.<br>
  *    The classical single exponential and double exponential smoothing 
  *    forecasting methods are both implemented. The forecast method giving
  *    the smallest mean absolute deviation (aka "mad"-error) will be 
  *    automatically picked to produce the forecast.<br>
  *    The parameters for the forecasting method (i.e. alfa for the single
  *    exponential smoothing, or alfa and gamma for the double exponential
  *    smoothing) are specified by the user. Optionally, the algorithm
  *    can automatically tune this parameters to their optimal value.
  *
  * The XML schema extension enabled by this module is (see mod_forecast.xsd):
  * <PRE>
  * <!-- Define the forecast type -->
  * <xsd:complexType name="demand_forecast">
  *   <xsd:complexContent>
  *     <xsd:extension base="demand">
  *       <xsd:choice minOccurs="0" maxOccurs="unbounded">
  *         <xsd:element name="calendar" type="calendar" />
  *         <xsd:element name="discrete" type="xsd:boolean" />
  *         <xsd:element name="buckets">
  *           <xsd:complexType>
  *             <xsd:choice minOccurs="0" maxOccurs="unbounded">
  *               <xsd:element name="bucket">
  *                 <xsd:complexType>
  *                   <xsd:all>
  *                     <xsd:element name="total" type="positiveDouble"
  *                       minOccurs="0" />
  *                     <xsd:element name="net" type="positiveDouble"
  *                       minOccurs="0" />
  *                     <xsd:element name="consumed" type="positiveDouble"
  *                       minOccurs="0" />
  *                     <xsd:element name="start" type="xsd:dateTime"
  *                       minOccurs="0"/>
  *                     <xsd:element name="end" type="xsd:dateTime"
  *                       minOccurs="0"/>
  *                   </xsd:all>
  *                   <xsd:attribute name="total" type="positiveDouble" />
  *                   <xsd:attribute name="net" type="positiveDouble" />
  *                   <xsd:attribute name="consumed" type="positiveDouble" />
  *                   <xsd:attribute name="start" type="xsd:dateTime" />
  *                   <xsd:attribute name="end" type="xsd:dateTime" />
  *                 </xsd:complexType>
  *               </xsd:element>
  *             </xsd:choice>
  *           </xsd:complexType>
  *         </xsd:element>
  *       </xsd:choice>
  *       <xsd:attribute name="discrete" type="xsd:boolean" />
  *     </xsd:extension>
  *   </xsd:complexContent>
  * </xsd:complexType>
  *
  * <!-- Define the netting solver. -->
	* <xsd:complexType name="solver_forecast">
	*	<xsd:complexContent>
	*		<xsd:extension base="solver">
	*			<xsd:choice minOccurs="0" maxOccurs="unbounded">
	*				<xsd:element name="loglevel" type="loglevel" />
	*			</xsd:choice>
	*		</xsd:extension>
	*	</xsd:complexContent>
	* </xsd:complexType>
  * </PRE>
  *
  * The module support the following configuration parameters:
  *
  *   - <b>Customer_Then_Item_Hierarchy</b>:<br>
  *     As part of the forecast netting a demand is assiociated with a certain
  *     forecast. When no matching forecast is found for the customer and item
  *     of the demand, frePPLe looks for forecast at higher level customers
  *     and items.<br>
  *     This flag allows us to control whether we first search the customer
  *     hierarchy and then the item hierarchy, or the other way around.<br>
  *     The default value is true, ie search higher customer levels before
  *     searching higher levels of the item.
  *
  *   - <b>Match_Using_Delivery_Operation</b>:<br>
  *     Specifies whether or not a demand and a forecast require to have the
  *     same delivery operation to be a match.<br>
  *     The default value is true.
  *
  *   - <b>Net_Early</b>:<br>
  *     Defines how much time before the due date of an order we are allowed
  *     to search for a forecast bucket to net from.<br>
  *     The default value is 0, meaning that we can net only from the bucket
  *     where the demand is due.
  *
  *   - <b>Net_Late</b>:<br>
  *     Defines how much time after the due date of an order we are allowed
  *     to search for a forecast bucket to net from.<br>
  *     The default value is 0, meaning that we can net only from the bucket
  *     where the demand is due.
  *
  *   - <b>Forecast_Iterations</b><br>
  *     Specifies the maximum number of iterations allowed for a forecast
  *     method to tune its parameters.<br>
  *     Only positive values are allowed and the default value is 10.<br>
  *     Set the parameter to 1 to disable the tuning and generate a forecast 
  *     based on the user-supplied parameters.
  */

#ifndef FORECAST_H
#define FORECAST_H

#include "frepple.h"
using namespace frepple;

namespace module_forecast
{


/** Initialization routine for the library. */
MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList&);


/** Initializes python extensions enabled by the module. */
void initializePython();

struct PythonForecastBucket;

/** @brief This class represents a bucketized demand signal.
  *
  * The forecast object defines the item and priority of the demands.<br>
  * A calendar (of type void, double, integer or boolean) divides the time horizon
  * in individual time buckets. The calendar value is used to assign priorities
  * to the time buckets.<br>
  * The class basically works as an interface for a hierarchy of demands, where the
  * lower level demands represent forecasting time buckets.
  */
class Forecast : public Demand
{
    friend class ForecastSolver;
    friend struct PythonForecastBucket;
  private:

    /** @brief A class to perform single exponential smoothing on a time series. */
    class SingleExponential
    {
      private:
        /** Smoothing constant. */
        double alfa;

        /** Smoothed result.<br>
          * Used to carry results between the evaluation and applying of the forecast.
          */
        double f_i;

        /** Default initial alfa value.<br>
          * The default value is 0.2.
          */
        static double initial_alfa;

        /** Lower limit on the alfa parameter.<br>
          * The default value is 0.
          **/
        static double min_alfa;

        /** Upper limit on the alfa parameter.<br>
          * The default value is 1.
          **/
        static double max_alfa;

        /** Number of warmup periods.<br>
          * These periods are used for the initialization of the algorithm
          * and don't count towards measuring the forecast error.<br>
          * The default value is 7.
          **/
        static unsigned int skip;

      public:
        /** Constructor. */
        SingleExponential(double a = initial_alfa) : alfa(a) {}

        /** Forecast evaluation. */
        double generateForecast(const double history[], 
          unsigned int count, bool debug);

        /** @todo need also a applyForecast() method. it is called when this forecast
          * method has won and now needs to update the forecast values.
          */
    };

    /** @brief A class to perform single exponential smoothing on a time series. */
    class DoubleExponential
    {
      private:
        /** Smoothing constant. */
        double alfa;

        /** Default initial alfa value.<br>
          * The default value is 0.2.
          */
        static double initial_alfa;

        /** Lower limit on the alfa parameter.<br>
          * The default value is 0.
          **/
        static double min_alfa;

        /** Upper limit on the alfa parameter.<br>
          * The default value is 1.
          **/
        static double max_alfa;

        /** Trend smoothing constant. */
        double gamma;

        /** Default initial gamma value.<br>
          * The default value is 0.0.
          */
        static double initial_gamma;

        /** Lower limit on the gamma parameter.<br>
          * The default value is 0.
          **/
        static double min_gamma;

        /** Upper limit on the gamma parameter.<br>
          * The default value is 1.
          **/
        static double max_gamma;

        /** Number of warmup periods.<br>
          * These periods are used for the initialization of the algorithm
          * and don't count towards measuring the forecast error.<br>
          * The default value is 7.
          **/
        static unsigned int skip;

      public:
        /** Constructor. */
        DoubleExponential(double a = initial_alfa, double g = initial_gamma) 
          : alfa(a), gamma(g) {}

        /** Forecast evaluation. */
        double generateForecast(const double history[], 
          unsigned int count, bool debug);
    };


    /** @brief This class represents a forecast value in a time bucket.
      *
      * A forecast bucket is never manipulated or created directly. Instead,
      * the owning forecast manages the buckets.
      */
    class ForecastBucket : public Demand
    {

      public:
        ForecastBucket(Forecast* f, Date d, Date e, double w, ForecastBucket* p)
          : Demand(f->getName() + " - " + string(d)), weight(w), consumed(0.0),
            total(0.0), timebucket(d,e), prev(p), next(NULL)
        {
          if (p) p->next = this;
          setOwner(f);
          setHidden(true);  // Avoid the subdemands show up in the output
          setItem(&*(f->getItem()));
          setDue(d);
          setPriority(f->getPriority());
          setMaxLateness(f->getMaxLateness());
          setMinShipment(f->getMinShipment());
          setOperation(&*(f->getOperation()));
        }
        double weight;
        double consumed;
        double total;
        DateRange timebucket;
        ForecastBucket* prev;
        ForecastBucket* next;
        virtual size_t getSize() const 
        {
          return sizeof(ForecastBucket) + Demand::extrasize();
        }
    };

  public:
    /** Constructor. */
    explicit Forecast(const string& nm)
      : Demand(nm), calptr(NULL), discrete(true) {}

    /** Destructor. */
    ~Forecast();

    /** Updates the quantity of the forecast. This method is empty. */
    virtual void setQuantity(double f)
      {throw DataException("Can't set quantity of a forecast");}

    /** Update the forecast quantity.<br>
      * The forecast quantity will be distributed equally among the buckets
      * available between the two dates, taking into account also the bucket
      * weights.<br>
      * The logic applied is briefly summarized as follows:
      *  - If the daterange has its start and end dates equal, we find the
      *    matching forecast bucket and update the quantity.
      *  - Otherwise the quantity is distributed among all intersecting
      *    forecast buckets. This distribution is considering the weigth of
      *    the bucket and the time duration of the bucket.<br>
      *    The bucket weight is the value specified on the calendar.<br>
      *    If a forecast bucket only partially overlaps with the daterange
      *    only the overlapping time is used as the duration.
      *  - If only buckets with zero weigth are found in the daterange a
      *    dataexception is thrown. It indicates a situation where forecast
      *    is specified for a date where no values are allowed.
      */
    virtual void setTotalQuantity(const DateRange& , double);

    void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement);
    void beginElement(XMLInput& pIn, const Attribute& pAttr);

    /** Returns whether fractional forecasts are allowed or not.<br>
      * The default is true.
      */
    bool getDiscrete() const {return discrete;}

    /** Updates forecast discreteness flag. */
    void setDiscrete(const bool b);

    /** Update the item to be planned. */
    virtual void setItem(Item*);

    /** Update the customer. */
    virtual void setCustomer(Customer*);

    /* Update the maximum allowed lateness for planning. */
    void setMaxLateness(TimePeriod);

    /* Update the minumum allowed shipment quantity for planning. */
    void setMinShipment(double);

    /** Specify a bucket calendar for the forecast. Once forecasted
      * quantities have been entered for the forecast, the calendar
      * can't be updated any more. */
    virtual void setCalendar(Calendar*);

    /** Returns a reference to the calendar used for this forecast. */
    Calendar* getCalendar() const {return calptr;}

    /** Generate a forecast value based on historical demand data. */
    static double generateFutureValues(const double[], unsigned int, bool = false);

    /** Updates the due date of the demand. Lower numbers indicate a
      * higher priority level. The method also updates the priority
      * in all buckets.
      */
    virtual void setPriority(int);

    /** Updates the operation being used to plan the demands. */
    virtual void setOperation(Operation *);

    /** Updates the due date of the demand. */
    virtual void setDue(const Date& d)
    {throw DataException("Can't set due date of a forecast");}

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const
    {
      return sizeof(Forecast) + Demand::extrasize() 
        + 6 * sizeof(void*); // Approx. size of an entry in forecast dictionary
    }

    /** Updates the value of the Customer_Then_Item_Hierarchy module
      * parameter. */
    static void setCustomerThenItemHierarchy(bool b)
      {Customer_Then_Item_Hierarchy = b;}

    /** Returns the value of the Customer_Then_Item_Hierarchy module
      * parameter. */
    static bool getCustomerThenItemHierarchy()
      {return Customer_Then_Item_Hierarchy;}

    /** Updates the value of the Match_Using_Delivery_Operation module
      * parameter. */
    static void setMatchUsingDeliveryOperation(bool b)
      {Match_Using_Delivery_Operation = b;}

    /** Returns the value of the Match_Using_Delivery_Operation module
      * parameter. */
    static bool getMatchUsingDeliveryOperation()
      {return Match_Using_Delivery_Operation;}

    /** Updates the value of the Net_Early module parameter. */
    static void setNetEarly(TimePeriod t) {Net_Early = t;}

    /** Returns the value of the Net_Early module parameter. */
    static TimePeriod getNetEarly() {return Net_Early;}

    /** Updates the value of the Net_Late module parameter. */
    static void setNetLate(TimePeriod t) {Net_Late = t;}

    /** Returns the value of the Net_Late module parameter. */
    static TimePeriod getNetLate() {return Net_Late;}

    /** Updates the value of the Forecast_Iterations module parameter. */
    static void setForecastIterations(unsigned long t) 
    {
      if (t<=0) throw DataException(
        "Parameter Forecast_Iterations must be bigger than 0."
        );
      Forecast_Iterations = t;
    }

    /** Returns the value of the Forecast_Iterations module parameter. */
    static unsigned long getForecastIterations() {return Forecast_Iterations;}

    /** A data type to maintain a dictionary of all forecasts. */
    typedef multimap < pair<const Item*, const Customer*>, Forecast* > MapOfForecasts;

    /** Callback function, used for prevent a calendar from being deleted when it
      * is used for an uninitialized forecast. */
    static bool callback(Calendar*, const Signal);

    /** Return a reference to a dictionary with all forecast objects. */
    static const MapOfForecasts& getForecasts() {return ForecastDictionary;}

  private:
    /** Initializion of a forecast.<br>
      * It creates demands for each bucket of the calendar.
      */
    void initialize();

    /** A void calendar to define the time buckets. */
    Calendar* calptr;

    /** Flags whether fractional forecasts are allowed. */
    bool discrete;

    /** A dictionary of all forecasts. */
    static MapOfForecasts ForecastDictionary;

    /** Controls how we search the customer and item levels when looking for a
      * matching forecast for a demand.
      */
    static bool Customer_Then_Item_Hierarchy;

    /** Controls whether or not a matching delivery operation is required
      * between a matching order and its forecast.
      */
    static bool Match_Using_Delivery_Operation;

    /** Store the maximum time difference between an order due date and a
      * forecast bucket to net from.<br>
      * The default value is 0, meaning that only netting from the due
      * bucket is allowed.
      */
    static TimePeriod Net_Late;

    /** Store the maximum time difference between an order due date and a
      * forecast bucket to net from.<br>
      * The default value is 0, meaning that only netting from the due
      * bucket is allowed.
      */
    static TimePeriod Net_Early;

    /** Specifies the maximum number of iterations allowed for a forecast
      * method to tune its parameters.<br>
      * Only positive values are allowed and the default value is 10.<br>
      * Set the parameter to 1 to disable the tuning and generate a 
      * forecast based on the user-supplied parameters.
      */
    static unsigned long Forecast_Iterations;
};


/** @brief Implementation of a forecast netting algorithm.
  *
  * As customer orders are being received they need to be deducted from
  * the forecast to avoid double-counting demand.
  *
  * The netting solver will process each order as follows:
  * - <b>First search for a matching forecast.</b><br>
  *   A matching forecast has the same item and customer as the order.<br>
  *   If no match is found at this level, a match is tried at higher levels
  *   of the customer and item.<br>
  *   Ultimately a match is tried with a empty customer or item field.
  * - <b>Next, the remaining net quantity of the forecast is decreased.</b><br>
  *   The forecast bucket to be reduced is the one where the order is due.<br>
  *   If the net quantity is already completely depleted in that bucket
  *   the solver will look in earlier and later buckets. The parameters
  *   Net_Early and Net_Late control the limits for the search in the
  *   time dimension.
  *
  * The logging levels have the following meaning:
  * - 0: Silent operation. Default logging level.
  * - 1: Log demands being netted and the matching forecast.
  * - 2: Same as 1, plus details on forecast buckets being netted.
  */
class ForecastSolver : public Solver
{
    friend class Forecast;
  public:
    /** Constructor. */
    ForecastSolver(const string& n) : Solver(n) {}

    /** This method handles the search for a matching forecast, followed
      * by decreasing the net forecast.
      */
    void solve(const Demand*, void* = NULL);

    /** This is the main solver method that will appropriately call the other
      * solve methods.<br>
      */
    void solve(void *v = NULL);

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(ForecastSolver);}
    void writeElement(XMLOutput*, const Keyword&, mode) const;

    /** Callback function, used for netting orders against the forecast. */
    bool callback(Demand* l, const Signal a);

  private:
    /** Given a demand, this function will identify the forecast model it
      * links to.
      */
    Forecast* matchDemandToForecast(const Demand* l);

    /** Implements the netting of a customer order from a matching forecast
      * (and its delivery plan).
      */
    void netDemandFromForecast(const Demand*, Forecast*);

    /** Used for sorting demands during netting. */
    struct sorter
    {
  	  bool operator()(const Demand* x, const Demand* y) const
		    { return SolverMRP::demand_comparison(x,y); }
	  };

    /** Used for sorting demands during netting. */
    typedef multiset < Demand*, sorter > sortedDemandList;
};


#if defined(Py_PYTHON_H) || defined(DOXYGEN)

extern "C"
{

  /** @brief This struct exports forecast information to Python. */
  struct PythonForecast
  {
    private:
      PyObject_HEAD
      Forecast::MapOfForecasts::const_iterator iter;
      static PyMethodDef methods[];
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonForecast*);
      static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
      static void destroy(PythonForecast* obj) {PyObject_Del(obj);}
      static PyObject* timeseries(PyObject *, PyObject *);
  };


  /** @brief This struct exports forecast bucket information to Python. */
  struct PythonForecastBucket
  {
    private:
      PyObject_HEAD
      Forecast::ForecastBucket *iter;
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonForecastBucket*);
      static PyObject* create(PyTypeObject*, PyObject*, PyObject*) {return NULL;}
      static void destroy(PythonForecastBucket* obj) {PyObject_Del(obj);}
      static PyObject* createFromForecast(Forecast*);
  };

}

#endif

}   // End namespace

#endif


