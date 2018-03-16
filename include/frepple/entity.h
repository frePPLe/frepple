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


template <class T> inline ostream& operator << (ostream &o, const HasName<T> &n)
{
  return o << n.getName();
}


template <class T> inline ostream& operator << (ostream &o, const HasName<T> *n)
{
  return o << (n ? n->getName() : string("NULL"));
}


template <class T> void HasHierarchy<T>::setOwner (T* fam)
{
  // Check if already set to the same entity
  if (parent == fam) return;

  // Avoid loops in the hierarchy. For instance, HasHierarchy A points to B
  // as its owner, and B points to A.
  for (T *t = fam; t; t = t->parent)
    if (t == this)
      throw DataException("Invalid hierarchy relation between \""
          + this->getName() + "\" and \"" + fam->getName() + "\"");

  // Clean up previous owner, if any
  if (parent)
  {
    if (parent->first_child == this)
      // We are the first child of our parent
      parent->first_child = next_brother;
    else
    {
      // Removed somewhere in the middle of the list of children
      T *i = parent->first_child;
      while (i && i->next_brother!=this) i = i->next_brother;
      if (!i) throw LogicException("Invalid hierarchy data");
      i->next_brother = next_brother;
    }
    next_brother = NULL;
  }

  // Set new owner
  parent = fam;

  // Register the new member at the owner
  if (fam)
  {
    if (fam->first_child)
    {
      // We append it at the end of the list, preserving the insert order.
      T *i = fam->first_child;
      while (i->next_brother) i = i->next_brother;
      i->next_brother = static_cast<T*>(this);
    }
    else
      // I am the first child of my parent
      fam->first_child = static_cast<T*>(this);
  }
}


template <class T> HasHierarchy<T>::~HasHierarchy()
{
  // All my members now point to my parent.
  T* last_child = NULL;
  for (T *i = first_child; i; i=i->next_brother)
  {
    i->parent = parent;
    last_child = i;
  }

  if (parent && last_child)
  {
    // Extend the child list of my parent.
    // The new children are prepended to the list of existing children.
    last_child->next_brother = parent->first_child;
    parent->first_child = first_child;
  }
  if (!parent)
  {
    // If there is no new parent, we also clear the next-brother field of
    // the children.
    T* j;
    for (T *i = first_child; i; i=j)
    {
      j = i->next_brother;
      i->next_brother = NULL;
    }
  }
  else
    // A parent exists and I have to remove myself as a member
    setOwner(NULL);
}


template <class T> unsigned short HasHierarchy<T>::getHierarchyLevel() const
{
  unsigned short i(0);
  for (auto p = this; p->parent; p = p->parent) ++i;
  return i;
}
