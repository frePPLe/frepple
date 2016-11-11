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
#include "frepple/utils.h"

namespace frepple
{
namespace utils
{

void Tree::clear()
{
  // Tree is already empty
  if (empty()) return;

  // Erase all elements
  for (TreeNode* x = begin(); x != end(); x = begin())
  {
    Object *o = dynamic_cast<Object*>(x);
    if (o && o->getType().raiseEvent(o, SIG_REMOVE))
      delete(x);  // The destructor calls the erase method
    else
      throw DataException("Can't delete object");
  }
}


Tree::TreeNode* Tree::insert(TreeNode* z, TreeNode *hint)
{
  if (!z) throw LogicException("Inserting null pointer in tree");

  // Use the hint to create the proper starting point in the tree
  int comp;
  TreeNode* y;
  if (!hint)
  {
    // Effectively no hint given
    hint = header.parent;
    y = &header;
  }
  else
  {
    // Check if the hint is a good starting point to descend
    while (hint->parent)
    {
      comp = z->nm.compare(hint->parent->nm);
      if ((comp>0 && hint == hint->parent->left)
          || (comp<0 && hint == hint->parent->right))
        // Move the hint up to the parent node
        // If I'm left child of my parent && new node needs right insert
        // or I'm right child of my parent && new node needs left insert
        hint = hint->parent;
      else
        break;
    }
    y = hint->parent;
  }

  // Step down the tree till we found a proper empty leaf node in the tree
  for (; hint; hint = comp<0 ? hint->left : hint->right)
  {
    y = hint;
    // Exit the function if the key is already found
    comp = z->nm.compare(hint->nm);
    if (!comp) return hint;
  }

  if (y == &header || z->nm < y->nm)
  {
    // Inserting as a new left child
    y->left = z;  // also makes leftmost() = z when y == header
    if (y == &header)
    {
      // Inserting a first element in the list
      header.parent = z;
      header.right = z;
    }
    // maintain leftmost() pointing to min node
    else if (y == header.left) header.left = z;
  }
  else
  {
    // Inserting as a new right child
    y->right = z;
    // Maintain rightmost() pointing to max node.
    if (y == header.right) header.right = z;
  }

  // Set parent and child pointers of the new node
  z->parent = y;
  z->left = nullptr;
  z->right = nullptr;

  // Increase the node count
  ++count;

  // Rebalance the tree
  rebalance(z);
  return z;
}


void Tree::rebalance(TreeNode* x)
{
  x->color = red;

  while (x != header.parent && x->parent->color == red)
  {
    if (x->parent == x->parent->parent->left)
    {
      TreeNode* y = x->parent->parent->right;
      if (y && y->color == red)
      {
        x->parent->color = black;
        y->color = black;
        x->parent->parent->color = red;
        x = x->parent->parent;
      }
      else
      {
        if (x == x->parent->right)
        {
          x = x->parent;
          rotateLeft(x);
        }
        x->parent->color = black;
        x->parent->parent->color = red;
        rotateRight(x->parent->parent);
      }
    }
    else
    {
      TreeNode* y = x->parent->parent->left;
      if (y && y->color == red)
      {
        x->parent->color = black;
        y->color = black;
        x->parent->parent->color = red;
        x = x->parent->parent;
      }
      else
      {
        if (x == x->parent->left)
        {
          x = x->parent;
          rotateRight(x);
        }
        x->parent->color = black;
        x->parent->parent->color = red;
        rotateLeft(x->parent->parent);
      }
    }
  }
  header.parent->color = black;
}


void Tree::erase(TreeNode* z)
{
  // A colorless node was never inserted in the tree, and shouldn't be
  // removed from it either...
  if (!z || z->color == none) return;

  TreeNode* y = z;
  TreeNode* x = nullptr;
  TreeNode* x_parent = nullptr;
  --count;
  if (y->left == nullptr)     // z has at most one non-null child. y == z.
    x = y->right;     // x might be null.
  else if (y->right == nullptr) // z has exactly one non-null child. y == z.
    x = y->left;    // x is not null.
  else
  {
    // z has two non-null children.  Set y to
    y = y->right;   //   z's successor.  x might be null.
    while (y->left != nullptr) y = y->left;
    x = y->right;
  }
  if (y != z)
  {
    // relink y in place of z.  y is z's successor
    z->left->parent = y;
    y->left = z->left;
    if (y != z->right)
    {
      x_parent = y->parent;
      if (x) x->parent = y->parent;
      y->parent->left = x;   // y must be a child of left
      y->right = z->right;
      z->right->parent = y;
    }
    else
      x_parent = y;
    if (header.parent == z) header.parent = y;
    else if (z->parent->left == z) z->parent->left = y;
    else z->parent->right = y;
    y->parent = z->parent;
    std::swap(y->color, z->color);
    y = z;
    // y now points to node to be actually deleted
  }
  else
  {
    // y == z
    x_parent = y->parent;
    if (x) x->parent = y->parent;
    if (header.parent == z) header.parent = x;
    else if (z->parent->left == z) z->parent->left = x;
    else z->parent->right = x;
    if (header.left == z)
    {
      if (z->right == nullptr)    // z->left must be null also
        header.left = z->parent;
      // makes leftmost == header if z == root
      else
        header.left = minimum(x);
    }
    if (header.right == z)
    {
      if (z->left == nullptr)     // z->right must be null also
        header.right = z->parent;
      // makes rightmost == header if z == root
      else                      // x == z->left
        header.right = maximum(x);
    }
  }
  if (y->color != red)
  {
    while (x != header.parent && (x == nullptr || x->color == black))
      if (x == x_parent->left)
      {
        TreeNode* w = x_parent->right;
        if (w->color == red)
        {
          w->color = black;
          x_parent->color = red;
          rotateLeft(x_parent);
          w = x_parent->right;
        }
        if ((w->left == nullptr || w->left->color == black) &&
            (w->right == nullptr || w->right->color == black))
        {
          w->color = red;
          x = x_parent;
          x_parent = x_parent->parent;
        }
        else
        {
          if (w->right == nullptr || w->right->color == black)
          {
            w->left->color = black;
            w->color = red;
            rotateRight(w);
            w = x_parent->right;
          }
          w->color = x_parent->color;
          x_parent->color = black;
          if (w->right) w->right->color = black;
          rotateLeft(x_parent);
          break;
        }
      }
      else
      {
        // same as above, with right <-> left.
        TreeNode* w = x_parent->left;
        if (w->color == red)
        {
          w->color = black;
          x_parent->color = red;
          rotateRight(x_parent);
          w = x_parent->left;
        }
        if ((w->right == nullptr || w->right->color == black) &&
            (w->left == nullptr || w->left->color == black))
        {
          w->color = red;
          x = x_parent;
          x_parent = x_parent->parent;
        }
        else
        {
          if (w->left == nullptr || w->left->color == black)
          {
            w->right->color = black;
            w->color = red;
            rotateLeft(w);
            w = x_parent->left;
          }
          w->color = x_parent->color;
          x_parent->color = black;
          if (w->left) w->left->color = black;
          rotateRight(x_parent);
          break;
        }
      }
    if (x) x->color = black;
  }
}


void Tree::rotateLeft(TreeNode* x)
{
  TreeNode* y = x->right;
  x->right = y->left;
  if (y->left != nullptr) y->left->parent = x;
  y->parent = x->parent;

  if (x == header.parent)
    // x was the root
    header.parent = y;
  else if (x == x->parent->left)
    // x was on the left of its parent
    x->parent->left = y;
  else
    // x was on the right of its parent
    x->parent->right = y;
  y->left = x;
  x->parent = y;
}


void Tree::rotateRight(TreeNode* x)
{
  TreeNode* y = x->left;
  x->left = y->right;
  if (y->right != nullptr) y->right->parent = x;
  y->parent = x->parent;

  if (x == header.parent)
    // x was the root
    header.parent = y;
  else if (x == x->parent->right)
    // x was on the right of its parent
    x->parent->right = y;
  else
    // x was on the left of its parent
    x->parent->left = y;
  y->right = x;
  x->parent = y;
}


void Tree::verify() const
{
  // Checks for an empty tree
  if (empty() || begin() == end())
  {
    bool ok = (empty() &&
        begin() == end() &&
        header.left == &header &&
        header.right == &header);
    if (!ok) throw LogicException("Invalid empty tree");
    return;
  }

  unsigned int len = countBlackNodes(header.left);
  size_t counter = 0;
  for (TreeNode* x = begin(); x != end(); x = x->increment())
  {
    TreeNode* L = x->left;
    TreeNode* R = x->right;
    ++counter;

    if (x->color == none)
      // Nodes must have a color
      throw LogicException("Colorless node included in a tree");

    if (x->color == red)
      if ((L && L->color == red) || (R && R->color == red))
        // A red node can have only nullptr and black children
        throw LogicException("Wrong color on node");

    if (L && x->nm<L->nm)
      // Left child isn't smaller
      throw LogicException("Wrong sorting on left node");

    if (R && R->nm<x->nm)
      // Right child isn't bigger
      throw LogicException("Wrong sorting on right node");

    if (!L && !R && countBlackNodes(x) != len)
      // All leaf nodes have the same number of black nodes on their path
      // to the root
      throw LogicException("Unbalanced count of black nodes");
  }

  // Check whether the header has a good pointer to the leftmost element
  if (header.left != minimum(header.parent))
    throw LogicException("Incorrect tree minimum");

  // Check whether the header has a good pointer to the rightmost element
  if (header.right != maximum(header.parent))
    throw LogicException("Incorrect tree maximum");

  // Check whether the measured node count match the expectation?
  if (counter != size())
    throw LogicException("Incorrect tree size");

  // If we reach this point, then this tree is healthy
}

} // end namespace
} // end namespace
