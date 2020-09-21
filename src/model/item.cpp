/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
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

namespace frepple {

template <class Item>
Tree utils::HasName<Item>::st;
const MetaCategory* Item::metadata;
const MetaClass *ItemMTO::metadata, *ItemMTS::metadata;

int Item::initialize() {
  metadata =
      MetaCategory::registerCategory<Item>("item", "items", reader, finder);
  registerFields<Item>(const_cast<MetaCategory*>(metadata));
  return FreppleCategory<Item>::initialize();
}

int ItemMTS::initialize() {
  ItemMTS::metadata = MetaClass::registerClass<ItemMTS>(
      "item", "item_mts", Object::create<ItemMTS>, true);
  return FreppleClass<ItemMTS, Item>::initialize();
}

int ItemMTO::initialize() {
  ItemMTO::metadata = MetaClass::registerClass<ItemMTO>(
      "item", "item_mto", Object::create<ItemMTO>);
  return FreppleClass<ItemMTO, Item>::initialize();
}

Item::~Item() {
  // Remove references from the buffers
  // TODO deleting would be better than leaving buffers with a null item
  bufferIterator bufiter(this);
  while (Buffer* buf = bufiter.next()) buf->setItem(nullptr);

  // Remove references from the demands
  // TODO rewrite using item-based demand iterator
  for (auto l = Demand::begin(); l != Demand::end(); ++l)
    if (l->getItem() == this) l->setItem(nullptr);

  // Remove all item operations referencing this item
  while (firstOperation) delete firstOperation;

  // The ItemSupplier objects are automatically deleted by the
  // destructor of the Association list class.
}

void Demand::setItem(Item* i) {
  // No change
  if (it == i) return;

  // Unlink from previous item
  if (it) {
    if (it->firstItemDemand == this)
      it->firstItemDemand = nextItemDemand;
    else {
      Demand* dmd = it->firstItemDemand;
      while (dmd && dmd->nextItemDemand != this) dmd = dmd->nextItemDemand;
      if (!dmd) throw LogicException("corrupted demand list for an item");
      dmd->nextItemDemand = nextItemDemand;
    }
  }

  // Link at new item
  it = i;
  if (it) {
    nextItemDemand = it->firstItemDemand;
    it->firstItemDemand = this;
  }

  // Trigger recreation of the delivery operation
  if (oper && oper->getHidden()) oper = uninitializedDelivery;

  // Trigger level calculation
  HasLevel::triggerLazyRecomputation();

  // Mark as changed
  setChanged();
}

Date Item::findEarliestPurchaseOrder(const PooledString& batch) const {
  Date earliest = Date::infiniteFuture;
  bufferIterator buf_iter(this);
  while (Buffer* buf = buf_iter.next()) {
    if (buf->getBatch() != batch) continue;
    for (auto flpln = buf->getFlowPlans().begin();
         flpln != buf->getFlowPlans().end(); ++flpln) {
      if (flpln->getDate() >= earliest) break;
      auto opplan = flpln->getOperationPlan();
      if (opplan && opplan->getOperation()->hasType<OperationItemSupplier>() &&
          opplan->getProposed()) {
        earliest = flpln->getDate();
        break;
      }
    }
  }
  return earliest;
}

}  // namespace frepple
