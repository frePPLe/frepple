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

#ifndef TIMELINE
#define TIMELINE

#include "frepple/utils.h"
#include <cmath>

namespace frepple
{

/**
  * This class implements a "sorted list" data structure.
  * The data structure has slow insert scalability: O(n)
  * Moving data around in the structure is efficient though: O(1)
  * The class leverages the STL library and also follows its api.
  * The class used to instantiate a timeline must support the
  * "bool operator < (TYPE)".
  *
  * Note that the events store the quantity but NOT the date. We pick up
  * the date from the template type. The reasoning for this choice is that
  * the quantity requires more computation than the date and is worthwhile
  * caching. The date field can be read efficiently from the parent type.
  */
template <class type> class TimeLine
{
    friend class Event;
  public:
    class iterator;
    class const_iterator;
    class Event : public NonCopyable
    {
        friend class TimeLine<type>;
        friend class const_iterator;
        friend class iterator;
      protected:
        double oh;
        double cum_prod;
        Event* next;
        Event* prev;
        Event() : oh(0), cum_prod(0), next(NULL), prev(NULL) {};
      public:
        virtual ~Event() {};
        virtual float getQuantity() const {return 0.0f;}
        virtual void setQuantity(float q) {}

        /** Return the current onhand value. */
        double getOnhand() const {return oh;}

        /** Return the total produced quantity till the current date. */
        double getCumulativeProduced() const {return cum_prod;}

        /** Return the total consumed quantity till the current date. */
        double getCumulativeConsumed() const {return cum_prod - oh;}

        /** This functions returns the mimimum boundary valid at the time of
          * this event. */
        virtual float getMin() const
        {
          Event const *c = this;
          while (c && c->getType()!=3) c=c->prev;
          return c ? c->getMin() : 0.0f;
        }
        /** This functions returns the maximum boundary valid at the time of
          * this event. */
        virtual float getMax() const
        {
          Event const *c = this;
          while (c && c->getType()!=4) c=c->prev;
          return c ? c->getMax() : 0.0f;
        }
        virtual const Date & getDate() const = 0;
        virtual unsigned short getType() const = 0;
        /** First criterion is date: earlier Dates come first.
          * Second criterion is the size: big events come first.
          * As a third tie-breaking criterion, we use a pointer comparison.
          * This garantuees us a fixed and unambiguous ordering.
          * As a side effect, this makes sure that producers come before
          * consumers. This feature is required to avoid zero-time
          * material shortages.
          */
        bool operator < (Event const& fl2) const
        {
          assert (&fl2);
          if (getDate() != fl2.getDate())
            return getDate() < fl2.getDate();
          else if (fabs(getQuantity() - fl2.getQuantity()) > ROUNDING_ERROR)
            return getQuantity() > fl2.getQuantity();
          else
            return this < &fl2;
        }
    };
  class EventChangeOnhand : public Event
    {
    private:
      float quantity;
      public:
        float getQuantity() const {return quantity;}
        void setQuantity(float q) {quantity = q;}
        EventChangeOnhand(float qty) : quantity(qty) {}
        virtual unsigned short getType() const {return 1;}
    };
  class EventMinQuantity : public Event
    {
      private:
        Date dt;
        float newMin;
      public:
        EventMinQuantity(Date d, float f=0.0f) : Event(), dt(d), newMin(f) {}
        void setMin(float f) {newMin = f;}
        virtual float getMin() const {return newMin;}
        const Date & getDate() const {return dt;}
        virtual unsigned short getType() const {return 3;}
    };
  class EventMaxQuantity : public Event
    {
      private:
        Date dt;
        float newMax;
      public:
        EventMaxQuantity(Date d, float f=0.0f) : Event(), dt(d), newMax(f) {}
        void setMax(float f) {newMax = f;}
        virtual float getMax() const {return newMax;}
        const Date & getDate() const {return dt;}
        virtual unsigned short getType() const {return 4;}
    };
    /** This is bi-directional iterator through the timeline. It looks a bit
      * STL-compliant, but this is only superficially. The class doesn't meet
      * all requirements for a full STL-compliant iterator.
      * @todo Make the timeline iterators fully STL compliant.
      */
    class const_iterator
    {
      protected:
        const Event* cur;
      public:
        const_iterator() {}
        const_iterator(const Event* e) : cur(e) {};
        const_iterator(const iterator& c) : cur(c.cur) {}
        const Event& operator*() const {return *cur;}
        const Event* operator->() const {return cur;}
        const_iterator& operator++() {cur = cur->next; return *this;}
        const_iterator operator++(int)
          {iterator tmp = *this; ++*this; return tmp;}
        const_iterator& operator--() {cur = cur->prev; return *this; }
        const_iterator operator--(int)
          {iterator tmp = *this; --*this; return tmp;}
        bool operator==(const const_iterator& x) const {return cur == x.cur;}
        bool operator!=(const const_iterator& x) const {return cur != x.cur;}
    };
    class iterator : public const_iterator
    {
      public:
        iterator() {}
        iterator(Event* e) : const_iterator(e) {};
        Event& operator*() const {return *const_cast<Event*>(this->cur);}
        Event* operator->() const {return const_cast<Event*>(this->cur);}
        iterator& operator++() {this->cur = this->cur->next; return *this;}
        iterator operator++(int) {iterator tmp = *this; ++*this; return tmp;}
        iterator& operator--() {this->cur = this->cur->prev; return *this; }
        iterator operator--(int) {iterator tmp = *this; --*this; return tmp;}
        bool operator==(const iterator& x) const {return this->cur == x.cur;}
        bool operator!=(const iterator& x) const {return this->cur != x.cur;}
    };
    TimeLine() : first(NULL), last(NULL) {}
    int size() const
    {
      int cnt(0);
      for(Event* p=first; p; p=p->next) ++cnt;
      return cnt;
    }
    iterator begin() {return iterator(first);}
    iterator begin(Event* e) {return iterator(e);}
    iterator rbegin() {return iterator(last);}
    iterator end() {return iterator(NULL);}
    const_iterator begin() const {return const_iterator(first);}
    const_iterator begin(const Event* e) const {return const_iterator(e);}
    const_iterator rbegin() const {return const_iterator(last);}
    const_iterator end() const {return const_iterator(NULL);}
    bool empty() const {return first==NULL;}
    void insert(Event*);
    void erase(Event*);
    void setQuantity(Event*, float);

    /** This function is used for debugging purposes. It prints a header line,
      * followed by the date, quantity and on_hand of all events in the
      * timeline.
      */
    void inspect(string name) const
    {
      cout << "Inspecting  " << this << ": \"" << name << "\":" << endl;
      for(const_iterator oo=begin(); oo!=end(); ++oo)
        cout << "  " << oo->getDate() << "   "
          << oo->getQuantity() << "    " << oo->getOnhand()
          << "    " << oo->getCumulativeProduced()  << endl;
    }

    /** This function is used to trace the consistency of the data structure. */
    bool check() const;

  private:
    /** A pointer to the first event in the timeline. */
    Event* first;

    /** A pointer to the last event in the timeline. */
    Event* last;
};


template <class type> void TimeLine <type>::insert (Event* e)
{
  // Loop through all entities till we find the insertion point
  // While searching from the end, update the onhand and cumulative produced
  // quantity of all nodes passed
  iterator i = rbegin();
  float qty = e->getQuantity();
  if (qty > 0)
    for(; i!=end() && *e<*i; --i)
    {
      i->oh += qty;
      i->cum_prod += qty;
    }
  else
    for(; i!=end() && *e<*i; --i)
      i->oh += qty;

  // Insert
  if (i == end())
  {
    // Insert at the head
    if (first)
      first->prev = e;
    else
      // First element
      last = e;
    e->next = first;
    e->prev = NULL;
    first = e;
    e->oh = qty;
    if (qty>0) e->cum_prod = qty;
  }
  else
  {
    // Insert in the middle
    e->prev = &*i;
    e->next = i->next;
    if (i->next)
      i->next->prev = e;
    else
      // New last element
      last = e;
    i->next = e;
    e->oh = i->oh + qty;
    if (qty>0)
      e->cum_prod = i->cum_prod + qty;
    else
      e->cum_prod = i->cum_prod;
  }

  // Final debugging check
  assert(check());
}


template <class type> void TimeLine<type>::erase (Event* e)
{
  // Update later entries
  float qty = e->getQuantity();
  if (qty>0)
    for(iterator i = begin(e); i!=end(); ++i)
    {
      i->oh -= qty;
      i->cum_prod -= qty;
    }
  else
    for(iterator i = begin(e); i!=end(); ++i)
      i->oh -= qty;

  if (e->prev)
    e->prev->next = e->next;
  else
    // Erasing the head
    first = e->next;

  if (e->next)
    e->next->prev = e->prev;
  else
    // Erasing the tail
    last = e->prev;

  // Final debugging check
  assert(check());
}


template <class type> void TimeLine<type>::setQuantity(Event* e, float newqty)
{
  // Changing the quantity moves the event only slightly up or down the
  // timeline. The alogrithm below swaps the element with its predecessor or
  // successor for every position to move.
  // For 1-2 moves this is more efficient than removing it from the link and
  // reinserting it. For a large change in the date of an event the algorithm
  // is less efficient.

  // Compute the delta quantity
  float delta = e->getQuantity() - newqty;
  float oldqty = e->getQuantity();

  // Update the quantity
  e->setQuantity(newqty);

  // Update the position in the timeline.
  // Remember that the quantity is also used by the '<' operator! Changing the
  // quantity thus can affect the order of elements.
  while ( e->next && !(*e<*e->next) )
  {
    // Move to a later date
    Event *theNext = e->next, *theNextNext = theNext->next;
    if (e->prev) e->prev->next = theNext;
    theNext->prev = e->prev;
    theNext->next = e;
    e->prev = theNext;
    e->next = theNextNext;
    if (theNextNext)
      theNextNext->prev = e;
    else
      last = e;
    if (first == e) first = theNext;
    e->oh = theNext->oh;
    e->cum_prod = theNext->cum_prod;
    theNext->oh -= oldqty;
    if (oldqty > 0) theNext->cum_prod -= oldqty;
  }
  while ( e->prev && !(*e->prev<*e) )
  {
    // Move to an earlier date
    Event *thePrev = e->prev, *thePrevPrev = thePrev->prev;
    if (e->next) e->next->prev = thePrev;
    thePrev->next = e->next;
    thePrev->prev = e;
    e->next = thePrev;
    e->prev = thePrevPrev;
    if (thePrevPrev)
      thePrevPrev->next = e;
    else
      first = e;
    if (last == e) last = thePrev;
    thePrev->oh = e->oh;
    thePrev->cum_prod = e->cum_prod;
    e->oh -= thePrev->getQuantity();
    if (thePrev->getQuantity() > 0) e->cum_prod -= thePrev->getQuantity();
  }

  // Update the onhand for all later events
  if (fabs(delta) > ROUNDING_ERROR)
  {
    if (oldqty > 0)
      for (iterator i=begin(e); i!=end(); ++i)
      {
        i->oh -= delta;
        i->cum_prod -= delta;
      }
    else
      for (iterator i=begin(e); i!=end(); ++i)
        i->oh -= delta;
  }

  // Final debugging check commented out, since loadplans change in pairs.
  // After changing the first one the second is affected too but not
  // repositioned yet...
  // assert(check());
}


template <class type> bool TimeLine<type>::check() const
{
  double expectedOH = 0.0f;
  double expectedCumProd = 0.0f;
  const Event *prev = NULL;
  for (const_iterator i = begin(); i!=end(); ++i)
  {
    // Problem 1: The onhands don't add up properly
    expectedOH += i->getQuantity();
    if (i->getQuantity() > 0) expectedCumProd += i->getQuantity();
    if (fabs(expectedOH - i->oh) > ROUNDING_ERROR)
    {
      inspect("Error: timeline onhand value corrupted on "
        + string(i->getDate()));
      return false;
    }
    // Problem 2: The cumulative produced quantity isn't correct
    if (fabs(expectedCumProd - i->cum_prod) > ROUNDING_ERROR)
    {
      inspect("Error: timeline cumulative produced value corrupted on "
        + string(i->getDate()));
      return false;
    }
    // Problem 3: Timeline is not sorted correctly
    if (prev && !(*prev<*i)
      && fabs(prev->getQuantity() - i->getQuantity())>ROUNDING_ERROR)
    {
      inspect("Error: timeline sort corrupted on " + string(i->getDate()));
      return false;
    }
    prev = &*i;
  }
  return true;
}

}

#endif

