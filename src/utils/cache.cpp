/***************************************************************************
 *                                                                         *
 * Copyright (C) 2018 by frePPLe bv                                        *
 *                                                                         *
 * Permission is hereby granted, free of charge, to any person obtaining   *
 * a copy of this software and associated documentation files (the         *
 * "Software"), to deal in the Software without restriction, including     *
 * without limitation the rights to use, copy, modify, merge, publish,     *
 * distribute, sublicense, and/or sell copies of the Software, and to      *
 * permit persons to whom the Software is furnished to do so, subject to   *
 * the following conditions:                                               *
 *                                                                         *
 * The above copyright notice and this permission notice shall be          *
 * included in all copies or substantial portions of the Software.         *
 *                                                                         *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,         *
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF      *
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                   *
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE  *
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION  *
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION   *
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.         *
 *                                                                         *
 ***************************************************************************/

#include "frepple/cache.h"

#include "frepple/utils.h"

// Uncomment the line below to enable detailed integrity checks of the cache
// #define DEBUG_CACHE

namespace frepple::utils {

Cache* Cache::instance = nullptr;
const MetaClass* Cache::metadata;
const MetaCategory* Cache::metacategory;

const Keyword Cache::tag_write_immediately("write_immediately");
const Keyword Cache::tag_threads("threads");

int Cache::initialize() {
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<Cache>("cache", "");
  metadata = MetaClass::registerClass<Cache>("cache", "cache", true);
  registerFields<Cache>(const_cast<MetaCategory*>(metacategory));

  // Initialize the Python type
  auto& x = FreppleCategory<Cache>::getPythonType();
  x.setName("cache");
  x.setDoc("frePPLe object cache");
  x.supportgetattro();
  x.supportsetattro();
  x.addMethod("flush", pythonFlush, METH_NOARGS,
              "write all objects to the database");
  x.addMethod("clear", pythonClear, METH_NOARGS,
              "remove all cached objects from memory");
  x.addMethod("printStatus", pythonPrintStatus, METH_NOARGS,
              "print a message on the cache performance");
  int tmp = x.typeReady();
  metadata->setPythonClass(x);

  // Initialize the global instance
  instance = new Cache();
  PythonInterpreter::registerGlobalObject("cache", instance);

  return tmp;
}

PyObject* Cache::pythonFlush(PyObject* self, PyObject*) {
  auto c = static_cast<Cache*>(self);
  Py_BEGIN_ALLOW_THREADS;
  try {
    c->flush();
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

void Cache::flush() {
  auto prev = setWriteImmediately(true);
  {
    // Wait till the worker threads have written all dirty objects
    unique_lock<mutex> l(lock);
    master_waiting.wait(l, [this] { return this->firstDirty == nullptr; });
  }
  setWriteImmediately(prev);

#ifdef DEBUG_CACHE
  // Validate things are ok
  Cache::instance->checkIntegrity();
#endif
}

PyObject* Cache::pythonClear(PyObject* self, PyObject*) {
  auto c = static_cast<Cache*>(self);
  Py_BEGIN_ALLOW_THREADS;
  try {
    c->clear();
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

void Cache::clear() {
  lock_guard<mutex> l(lock);
  for (auto entry = lastEntry; entry; entry = entry->prev)
    entry->val = nullptr;  // Decreases the reference count
  firstDirty = nullptr;
  lastDirty = nullptr;
  firstEntry = nullptr;
  lastEntry = nullptr;

#ifdef DEBUG_CACHE
  // Validate things are ok
  Cache::instance->checkIntegrity();
#endif
}

void Cache::clearDirty() {
  while (true) {
    // Find a dirty entry
    AbstractCacheEntry* dirtyentry = nullptr;
    {
      lock_guard<mutex> lk(lock);
      dirtyentry = firstDirty;
    }
    if (!dirtyentry) return;

    // Clear the dirty flag
    dirtyentry->clearDirty();
  }
}

void AbstractCacheEntry::moveToFront() const {
  lock_guard<mutex> l(Cache::instance->lock);
  shared_ptr<void> increase_ref_count = val;
#ifdef DEBUG_CACHE
  // Validate things are ok
  Cache::instance->checkIntegrity();
#endif

  if (Cache::instance->firstEntry == this)
    // Special case: we are already at the front, or already exi
    return;

  // Unlink from current position
  if (prev || next || Cache::instance->firstEntry == this) {
    if (prev)
      prev->next = next;
    else
      Cache::instance->firstEntry = next;
    if (next)
      next->prev = prev;
    else
      Cache::instance->lastEntry = prev;
  } else
    // Re-inserting anew!
    ++Cache::instance->count;

  // Link at the front
  const_cast<AbstractCacheEntry*>(this)->next = Cache::instance->firstEntry;
  const_cast<AbstractCacheEntry*>(this)->prev = nullptr;
  if (Cache::instance->firstEntry)
    Cache::instance->firstEntry->prev = const_cast<AbstractCacheEntry*>(this);
  Cache::instance->firstEntry = const_cast<AbstractCacheEntry*>(this);

#ifdef DEBUG_CACHE
  // Validate things are ok
  Cache::instance->checkIntegrity();
#endif
}

void AbstractCacheEntry::insertAtFront() const {
  lock_guard<mutex> l(Cache::instance->lock);
  shared_ptr<void> increase_ref_count = val;
  if (Cache::instance->firstEntry) {
    // Other entries are already in the cache
    Cache::instance->firstEntry->prev = const_cast<AbstractCacheEntry*>(this);
    const_cast<AbstractCacheEntry*>(this)->next = Cache::instance->firstEntry;
  } else
    // I am the first entry in the cache
    Cache::instance->lastEntry = const_cast<AbstractCacheEntry*>(this);
  Cache::instance->firstEntry = const_cast<AbstractCacheEntry*>(this);

  // Increase cache size
  ++Cache::instance->count;

#ifdef DEBUG_CACHE
  // Validate things are ok
  Cache::instance->checkIntegrity();
#endif

  // Remove excess objects
  if (Cache::instance->count > Cache::instance->max_objects)
    Cache::instance->work_to_do.notify_all();
}

void AbstractCacheEntry::removeFromCache() const {
  shared_ptr<void> increase_ref_count = val;
  if (val) {
    // Maintenance of the cache list
    lock_guard<mutex> l(Cache::instance->lock);

    bool is_dirty = false;
    if (next)
      next->prev = prev;
    else
      Cache::instance->lastEntry = prev;
    if (prev)
      prev->next = next;
    else
      Cache::instance->firstEntry = next;
    --Cache::instance->count;
    const_cast<AbstractCacheEntry*>(this)->val = nullptr;
    if (nextdirty) {
      nextdirty->prevdirty = prevdirty;
      is_dirty = true;
    }
    if (prevdirty) {
      prevdirty->nextdirty = nextdirty;
      is_dirty = true;
    }
    if (Cache::instance->firstDirty == this) {
      Cache::instance->firstDirty = nextdirty;
      is_dirty = true;
    }
    if (Cache::instance->lastDirty == this) {
      Cache::instance->lastDirty = prevdirty;
      is_dirty = true;
    }

#ifdef DEBUG_CACHE
    // Validate things are ok
    Cache::instance->checkIntegrity();
#endif

    // Synchronously flush the object if it is dirty
    if (is_dirty) {
      try {
        const_cast<AbstractCacheEntry*>(this)->flush();
      } catch (const exception& e) {
        logger << "Warning : exception flushing cache: " << e.what() << '\n';
      } catch (...) {
        logger << "Warning : exception flushing cache\n";
      }
    }
  }
}

PyObject* Cache::pythonPrintStatus(PyObject* self, PyObject*) {
  auto c = static_cast<Cache*>(self);
  Py_BEGIN_ALLOW_THREADS;
  try {
    c->printStatus();
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

void Cache::setThreads(int i) {
  if (i < 0) {
    logger << "Warning: Cache thread must be bigger than or equal to 0\n";
    return;
  }
  if (i > threads) {
    // Create extra threads
    auto extra = i - threads;
    threads = i;
    while (extra > 0) {
      workers.push(
          thread(workerthread, this, static_cast<int>(workers.size())));
      --extra;
    }
  } else if (i < threads) {
    // Wait for some threads to stop
    auto original = threads;
    threads = i;
    work_to_do.notify_all();
    for (auto c = original - threads; c > 0; --c) {
      auto& thrd = workers.top();
      thrd.join();
      workers.pop();
    }
  }
}

void Cache::printStatus() {
  logger << "Cache status:\n"
         << "   " << count << " objects (max " << max_objects << ")\n"
         << "   " << stats_reads << " reads and " << stats_writes << " writes"
         << '\n';
}

void AbstractCacheEntry::markDirty() {
  shared_ptr<void> increase_ref_count = val;
  lock_guard<mutex> l(Cache::instance->lock);
  if (isDirty()) return;

  // Update the list of dirty objects
  prevdirty = Cache::instance->lastDirty;
  if (Cache::instance->lastDirty)
    Cache::instance->lastDirty->nextdirty = this;
  else
    Cache::instance->firstDirty = this;
  Cache::instance->lastDirty = this;

  // can show a mismatch of 1 when marking dirty in constructor
  // assert(Cache::instance->checkIntegrity());

  // Wake up the writer thread
  if (Cache::instance->writeImmediately)
    Cache::instance->work_to_do.notify_one();
}

void AbstractCacheEntry::clearDirty() const {
  shared_ptr<void> increase_ref_count = val;
  lock_guard<mutex> l(Cache::instance->lock);
  if (prevdirty)
    prevdirty->nextdirty = nextdirty;
  else
    Cache::instance->firstDirty = nextdirty;
  if (nextdirty)
    nextdirty->prevdirty = prevdirty;
  else
    Cache::instance->lastDirty = prevdirty;
  const_cast<AbstractCacheEntry*>(this)->prevdirty = nullptr;
  const_cast<AbstractCacheEntry*>(this)->nextdirty = nullptr;

#ifdef DEBUG_CACHE
  // Validate things are ok
  Cache::instance->checkIntegrity();
#endif
}

void Cache::workerthread(Cache* me, int index) {
  while (index < me->threads) {
    // Wait until are notified about work to do
    {
      unique_lock<mutex> lk(me->lock);
      me->work_to_do.wait(lk, [me, index] {
        return (me->firstDirty && me->writeImmediately) ||
               (me->count > me->max_objects && me->count > 1) ||
               (index >= me->threads);
      });
    }

    // Define lower cache threshold as 80% of the maximum cache size
    auto threshold = static_cast<unsigned long>(me->max_objects * 0.8);

    // Determine whether or not we want to reduce the cache size now
    bool reduce_size = me->count > threshold;

    // Loop over all work to do
    while (index < me->threads) {
      AbstractCacheEntry* entry2delete = nullptr;
      AbstractCacheEntry* entry2flush = nullptr;

      // Find work to do
      {
        lock_guard<mutex> lk(me->lock);

#ifdef DEBUG_CACHE
        // Validate things are ok
        Cache::instance->checkIntegrity();
#endif

        // Expire entries from the upper limit to the lower limit
        while (reduce_size && me->count > threshold) {
          // Find an object that isn't in use
          auto tmp = me->lastEntry;
          while (tmp && tmp->val.use_count() > 1) tmp = tmp->prev;
          if (!tmp)
            // All objects are in use!
            break;

          // Update cache info
          --me->count;
          if (tmp->next)
            tmp->next->prev = tmp->prev;
          else
            me->lastEntry = tmp->prev;
          if (tmp->prev)
            tmp->prev->next = tmp->next;
          else
            me->firstEntry = tmp->next;
          tmp->prev = nullptr;
          tmp->next = nullptr;

          if (tmp->isDirty()) {
            // Dirty object to write
            entry2delete = tmp;
            if (tmp->prevdirty)
              tmp->prevdirty->nextdirty = tmp->nextdirty;
            else
              me->firstDirty = tmp->nextdirty;
            if (tmp->nextdirty)
              tmp->nextdirty->prevdirty = tmp->prevdirty;
            else
              me->lastDirty = tmp->prevdirty;
            tmp->prevdirty = nullptr;
            tmp->nextdirty = nullptr;
            break;
          } else
            // Delete the object right away
            tmp->expire();
        }

        // Write some dirty object right if we haven't found one yet
        if (!entry2delete && me->writeImmediately && me->firstDirty) {
          // Find an object that isn't in use
          entry2flush = me->firstDirty;
          while (entry2flush && entry2flush->val.use_count() > 1)
            entry2flush = entry2flush->nextdirty;
          if (!entry2flush) entry2flush = me->firstDirty;
          if (entry2flush) {
            // Unlink from the cache
            if (entry2flush->prevdirty)
              entry2flush->prevdirty->nextdirty = entry2flush->nextdirty;
            else
              me->firstDirty = entry2flush->nextdirty;
            if (entry2flush->nextdirty)
              entry2flush->nextdirty->prevdirty = entry2flush->prevdirty;
            else
              me->lastDirty = entry2flush->prevdirty;
            entry2flush->nextdirty = nullptr;
            entry2flush->prevdirty = nullptr;
          }
        }

#ifdef DEBUG_CACHE
        // Validate things are ok
        me->checkIntegrity();
#endif
      }

      // Do the work now
      try {
        if (entry2delete) {
          // Flush and delete a cache entry
          entry2delete->flush();
          {
            lock_guard<mutex> lk(me->lock);
            if (!entry2delete->prev && me->firstEntry != entry2delete)
              // During the execution of the flush, the entry could effectively
              // already be inserted again!
              entry2delete->expire();
          }
        } else if (entry2flush) {
          // Flush a cache entry
          entry2flush->flush();
        } else {
          // No more work to do
          lock_guard<mutex> lk(me->lock);
          if (!me->firstDirty) me->master_waiting.notify_one();
          break;
        }
      } catch (const exception& e) {
        logger << "Warning : exception on cache worker thread: " << e.what()
               << '\n';
      } catch (...) {
        logger << "Warning : exception on cache worker thread\n";
      }
    }
  }
}

pair<size_t, size_t> Cache::getStatus() const {
  lock_guard<mutex> l(Cache::instance->lock);
  size_t count = 0;
  size_t size = 0;
  for (auto ptr = firstEntry; ptr; ptr = ptr->next) {
    ++count;
    size += ptr->getSize();
  }
  return make_pair(count, size);
}

void Cache::checkIntegrity() const {
  // IMPORTANT! We assume the lock is already held by the calling routine.

  // Heads and tails
  if (firstEntry && firstEntry->prev)
    throw LogicException("ERROR: invalid cache head");
  if (lastEntry && lastEntry->next)
    throw LogicException("ERROR: invalid cache tail");
  if (firstDirty && firstDirty->prevdirty)
    throw LogicException("ERROR: invalid cache dirty head");
  if (lastDirty && lastDirty->nextdirty)
    throw LogicException("ERROR: invalid cache dirty tail");

  // Count elements in the cache list - walking forward
  unsigned long cnt = 0;
  unsigned long cntdirty1 = 0;
  AbstractCacheEntry* prev = nullptr;
  for (auto ptr = firstEntry; ptr; ptr = ptr->next) {
    ++cnt;
    if (ptr->isDirty()) ++cntdirty1;
    if (ptr->prev != prev)
      throw LogicException("ERROR: corrupted cache list found in forward walk");
    prev = ptr;
  }
  if (cnt != count) throw LogicException("ERROR: mismatch in cache size");

  // Count elements in the cache list - walking forward
  prev = nullptr;
  cnt = 0;
  for (auto ptr = lastEntry; ptr; ptr = ptr->prev) {
    ++cnt;
    if (ptr->next != prev)
      throw LogicException("ERROR: corrupted cache list in backward walk");
    prev = ptr;
  }
  if (cnt != count) throw LogicException("ERROR: mismatch in cache size");

  // Count elements in the dirty list
  unsigned long cntdirty2 = 0;
  prev = nullptr;
  for (auto ptr = firstDirty; ptr; ptr = ptr->nextdirty) {
    ++cntdirty2;
    if (ptr->prevdirty != prev)
      throw LogicException("ERROR: corrupted dirty cache list");
    prev = ptr;
  }

  if (cntdirty1 != cntdirty2)
    throw DataException("ERROR: mismatch in dirty count");
}

}  // namespace frepple::utils
