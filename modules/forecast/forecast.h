/***************************************************************************
  file : $URL$
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

/** @file forecast.h
  * @brief Header file for the module forecast.
  *
  * @namespace module_forecast
  * @brief Module for representing forecast.
  *
  * The forecast module provides the following functionality:
  *
  *  - A special demand type to model forecasts.<br>
  *    A forecast demand is bucketized. A demand is automatically
  *    created for each bucket.<br>
  * 
  *  - A solver for netting orders from the forecast.<br>
  *    As customer orders are being received they need to be deducted from
  *    the forecast to avoid double-counting it.<br>
  *    The netting solver will for each order search for a matching forecast
  *    and reduce the remaining net quantity of the forecast.
  *
  *  - Techniques to predict/forecast the future demand based on the demand
  *    history is NOT available in this module (yet).
  *
  * The XML schema extension enabled by this module is (see mod_forecast.xsd):
  * <PRE>
  * <xsd:complexType name="DEMAND_FORECAST">
  *   <xsd:complexContent>
  *     <xsd:extension base="DEMAND">
  *       <xsd:choice minOccurs="0" maxOccurs="unbounded">
  *         <xsd:element name="CALENDAR" type="CALENDAR" />
  *         <xsd:element name="BUCKETS">
  *           <xsd:complexType>
  *             <xsd:choice minOccurs="0" maxOccurs="unbounded">
  *               <xsd:element name="BUCKET">
  *                 <xsd:complexType>
  *                   <xsd:all>
  *                     <xsd:element name="QUANTITY" type="positiveFloat"
  *                       minOccurs="0" />
  *                     <xsd:element name="DUE" type="xsd:dateTime"
  *                       minOccurs="0"/>
  *                   </xsd:all>
  *                   <xsd:attribute name="QUANTITY" type="positiveFloat" />
  *                   <xsd:attribute name="DUE" type="xsd:dateTime" />
  *                 </xsd:complexType>
  *               </xsd:element>
  *             </xsd:choice>
  *           </xsd:complexType>
  *         </xsd:element>
  *       </xsd:choice>
  *     </xsd:extension>
  *   </xsd:complexContent>
  * </xsd:complexType>
  * </PRE>
  * 
  * The module support the following configuration parameters:
  *   - Customer_Then_Item_Hierarchy:<br>
  *     As part of the forecast netting a demand is assiociated with a certain
  *     forecast. When no matching forecast is found for the customer and item 
  *     of the demand, frepple looks for forecast at higher level customers 
  *     and items.<br>
  *     This flag allows us to control whether we first search the customer 
  *     hierarchy and then the item hierarchy, or the other way around.<br>
  *     The default value is true, ie search higher customer levels before 
  *     searching higher levels of the item.
  *   - Match_Using_Delivery_Operation:<br>
  *     Specifies whether or not a demand and a forecast require to have the 
  *     same delivery operation to be a match<br>
  *     The default value is true.
  */

#ifndef FORECAST_H
#define FORECAST_H

#include "frepple.h"
using namespace frepple;

namespace module_forecast
{


/** Initialization routine for the library. */
MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z);


/** @brief This class represents a bucketized demand signal.
  *
  * The forecast object defines the item and priority of the demands.
  * A void calendar then defines the buckets.
  * The class basically works as an interface for a hierarchy of demands.
  */
class Forecast : public Demand
{
    TYPEDEF(Forecast);
    friend class ForecastSolver;
  public:
    /** @brief 
      *
      */
    class ForecastBucket : public Demand
    {
      public:
        ForecastBucket(string n) : Demand(n), weight(0) {}
      private:
        float weight;
    };

    /** Constructor. */
    explicit Forecast(const string& nm) : Demand(nm), calptr(NULL) {}

    /** Destructor. */
    ~Forecast() 
    {
      // Update the dictionary
      for (MapOfForecasts::iterator x= 
        ForecastDictionary.lower_bound(make_pair(&*getItem(),&*getCustomer()));
        x != ForecastDictionary.end(); ++x)
        if (x->second == this) 
        {
          ForecastDictionary.erase(x); 
          return;
        }
    }

    /** Updates the quantity of the forecast. This method is empty. */
    virtual void setQuantity(float f)
      {throw DataException("Can't set quantity of a forecast");}

    /** Update the forecast in a bucket, given any date in the bucket. */
    virtual void setQuantity(Date, float);

    void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, XMLElement& pElement);
    void beginElement(XMLInput& pIn, XMLElement& pElement);

    /** Update the item to be planned. */
    virtual void setItem(const Item*);

    /** Update the customer. */
    virtual void setCustomer(const Customer*);

    /** Specify a bucket calendar for the forecast. Once forecasted
      * quantities have been entered for the forecast, the calendar
      * can't be updated any more. */
    virtual void setCalendar(const Calendar* c);

    /** Returns a reference to the calendar used for this forecast. */
    Calendar::pointer getCalendar() const {return calptr;}

    /** Updates the due date of the demand. Lower numbers indicate a
      * higher priority level. The method also updates the priority
      * in all buckets.
      */
    virtual void setPriority(int);

    /** Updates the operation being used to plan the demands. */
    virtual void setOperation(const Operation *);

    /** Updates the due date of the demand. */
    virtual void setDue(Date d)
    {throw DataException("Can't set due date of a forecast");}

    /** Update the policy of the demand in all buckets. */
    virtual void setPolicy(const string&);

    /** Update the policy of the demand in all buckets. */
    virtual void addPolicy(const string&);

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(Forecast) + getName().size() + HasDescription::memsize();}

    /** Updates the value of the Customer_Then_Item_Hierarchy module
      * parameter. */
    static void setCustomerThenItemHierarchy(bool b) 
      {Customer_Then_Item_Hierarchy = b;}

    /** Returns the value of the Customer_Then_Item_Hierarchy module 
      * parameter. */
    bool getCustomerThenItemHierarchy() 
      {return Customer_Then_Item_Hierarchy;}

    /** Updates the value of the Match_Using_Delivery_Operation module
      * parameter. */
    static void setMatchUsingDeliveryOperation(bool b) 
      {Match_Using_Delivery_Operation = b;}

    /** Returns the value of the Match_Using_Delivery_Operation module 
      * parameter. */
    static bool getMatchUsingDeliveryOperation() 
      {return Match_Using_Delivery_Operation;}

    /** A data type to maintain a dictionary of all forecasts. */
    typedef multimap < pair<const Item*, const Customer*>, Forecast* > MapOfForecasts;

    /** Callback function, used for prevent a calendar from being deleted when it
      * is used for an uninitialized forecast. */
    static bool callback(Calendar*, const Signal);

  private:    
    /** Initializion of a forecast.<br>
      * It creates demands for each bucket of the calendar.
      */
    void initialize();

    /** A void calendar to define the time buckets. */
    const Calendar* calptr;

    /** Update the forecast in a bucket. */
    void setQuantity(const Calendar::Bucket&, float);

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
};


/** @brief Implementation of a forecast netting algorithm. 
  *
  * @todo
  */
class ForecastSolver : public Solver
{
    TYPEDEF(ForecastSolver);
    friend class Forecast;
  public:
    /** Constructor. */
    ForecastSolver(const string& n) : Solver(n), automatic(false) {}

    /** Behavior of this solver method:
      *  - <br>
      */
    void solve(const Demand*, void* = NULL);

    /** This is the main solver method that will appropriately call the other
      * solve methods.<br>
      */
    void solve(void *v = NULL);

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(ForecastSolver);}
    void endElement(XMLInput& pIn, XMLElement& pElement);
    void writeElement(XMLOutput*, const XMLtag&, mode) const;

    /** Updates the flag controlling incremental behavior. */
    void setAutomatic(bool); 

    /** Returns true when the solver is set up to run incrementally. */
    bool getAutomatic() const {return automatic;}

    /** Callback function, used for netting orders against the forecast. */
    bool callback(Demand* l, const Signal a);

  private:
    /** Given a demand, this function will identify the forecast model it 
      * links to. The demand will net from this forecast. 
      */
    Forecast* matchDemand2Forecast(const Demand* l);

    /** When set to true, this solver will automatically adjust the
      * netted forecast with every change in demand.
      */
    bool automatic;
};

}   // End namespace

#endif

