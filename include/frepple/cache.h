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

#pragma once

#include <atomic>

#include "frepple/utils.h"

using namespace std;

namespace frepple {

namespace utils {

class AbstractCacheEntry {
  friend class Cache;

 public:
  void markDirty();

  /* Update the status WITHOUT flushing to the database. */
  virtual void clearDirty() const;

  /* Returns true when the entry needs to be written to the database.
   * The cache needs to be locked when you call this method.
   */
  bool isDirty() const;

 protected:
  shared_ptr<void> val = nullptr;

  /* Promotes this object as most-recently used. */
  void moveToFront() const;

  /* Add a new to the cache. */
  void insertAtFront() const;

  /* Auxilary method to remove an object from the cache. */
  void removeFromCache() const;

  /* Method to remove an object from the cache. */
  virtual void expire() const = 0;

  /* Write an object to the database if it has changed.
   * The object isn't necessarily removed the memory.
   */
  virtual void flush() = 0;

  virtual size_t getSize() const = 0;

  virtual recursive_mutex* getLock() const { return nullptr; }

 private:
  AbstractCacheEntry* prev = nullptr;
  AbstractCacheEntry* next = nullptr;
  AbstractCacheEntry* nextdirty = nullptr;
  AbstractCacheEntry* prevdirty = nullptr;
};

/* A class for an object that is cacheable.
 * The cached object needs to implement 2 methods:
 *  - T(U*):
 *    Called to construct an object in memory given a certain key object.
 *  - unsigned long size() const:
 *    Memory size used by the cached object. An approximate value suffices.
 */
template <class T, class U>
class CacheEntry : public AbstractCacheEntry {
 public:
  ~CacheEntry() {
    removeFromCache();
    // Note: reference count of the shared pointer is reduced as well, resulting
    // in the destruction of its object
  }

  void flush() override;

  void expire() const override {
    const_cast<CacheEntry<T, U>*>(this)->val.reset();
  }

  recursive_mutex* getLock() const override {
    return val ? static_pointer_cast<T>(
                     const_cast<CacheEntry<T, U>*>(this)->val)
                     ->getLock()
               : nullptr;
  }

  void clearDirty() const override {
    AbstractCacheEntry::clearDirty();
    if (!val) return;
    static_pointer_cast<T>(val)->clearDirty();
  }

  size_t getSize() const override {
    return val ? static_pointer_cast<T>(val)->getSize() : 0;
  }

  shared_ptr<T> getValue(const U* key) const;
};

/* Memory cache with a Least Recently Used strategy. */
class Cache : public Object {
  friend class AbstractCacheEntry;
  template <class T, class U>
  friend class CacheEntry;

 public:
  // Constructor
  Cache() {
    initType(metadata);
    for (auto c = threads; c > 0; --c)
      workers.push(
          thread(workerthread, this, static_cast<int>(workers.size())));
  };

  // Destructor
  ~Cache() override { setThreads(0); };

  // Global cache instance
  static Cache* instance;

  static Cache* getInstance() { return instance; }

  void printStatus();

  void setMaximum(unsigned long s) {
    if (s <= 0) {
      logger << "Warning: Cache object limit must be bigger than 0" << endl;
      return;
    }
    max_objects = s;
    if (count > max_objects) {
      work_to_do.notify_all();
      {
        // Wait till the worker threads have reduced the objects in memory
        unique_lock<mutex> l(lock);
        master_waiting.wait(l, [this] { return this->count <= max_objects; });
      }
    }
  }

  unsigned long getMaximum() const { return max_objects; }

  int getThreads() const { return threads; }

  void setThreads(int i);

  static const MetaClass* metadata;
  static const MetaCategory* metacategory;
  static int initialize();
  const MetaClass& getType() const override { return *metadata; }

  static const Keyword tag_write_immediately;
  static const Keyword tag_threads;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addUnsignedLongField<Cls>(Tags::maximum, &Cls::getMaximum,
                                 &Cls::setMaximum);
    m->addIntField<Cls>(tag_threads, &Cls::getThreads, &Cls::setThreads);
    m->addBoolField<Cls>(tag_write_immediately, &Cls::getWriteImmediately,
                         &Cls::setWriteImmediately2);
    m->addShortField<Cls>(Tags::loglevel, &Cls::getLogLevel, &Cls::setLogLevel);
  }

  /* Write changed objects to the database.
   * The cached objects remain in memory.
   */
  void flush();

  /* Mark all dirty entries clean again, WITHOUT flushing to the database. */
  void clearDirty();

  static PyObject* pythonFlush(PyObject* self, PyObject* args);
  static PyObject* pythonClear(PyObject* self, PyObject* args);
  static PyObject* pythonPrintStatus(PyObject* self, PyObject* args);

  /* Write changed objects to the database and remove them from the cache
   * memory. */
  void clear();

  bool getWriteImmediately() const { return writeImmediately; }

  void setWriteImmediately2(bool b) {
    writeImmediately = b;
    if (b) work_to_do.notify_all();
  }

  bool setWriteImmediately(bool b) {
    auto tmp = writeImmediately;
    writeImmediately = b;
    if (b) work_to_do.notify_all();
    return tmp;
  }

  void checkIntegrity() const;

  short getLogLevel() const { return loglevel; }

  virtual void setLogLevel(short v) { loglevel = v; }

  pair<size_t, size_t> getStatus() const;

 private:
  // Worker thread to persist dirty objects
  static void workerthread(Cache*, int);

  stack<thread> workers;

  // Number of worker threads
  int threads = 1;

  // Counts the number of objects in the cache
  atomic<unsigned long> count{0};

  // Aproximate memory size of the cached objects
  atomic<unsigned long> size{0};

  // Write dirty objects immediately, or wait lazily till the cache size limit
  // is reached or flush is called explicitly
  bool writeImmediately = true;

  // Pointer to the most recently used object in the cache
  AbstractCacheEntry* firstEntry = nullptr;

  // Pointer to the least recently used object in the cache
  AbstractCacheEntry* lastEntry = nullptr;

  // Object changed the longest time ago
  AbstractCacheEntry* firstDirty = nullptr;

  // Object changed most recently
  AbstractCacheEntry* lastDirty = nullptr;

  short loglevel = 0;

  mutex lock;

  condition_variable work_to_do;

  condition_variable master_waiting;

  unsigned long max_objects = ULONG_MAX;  // Unlimited

  // Cache statistics
  atomic<unsigned long> stats_reads{0};
  atomic<unsigned long> stats_writes{0};
};

inline bool AbstractCacheEntry::isDirty() const {
  return prevdirty || Cache::instance->firstDirty == this;
}

template <class T, class U>
void CacheEntry<T, U>::flush() {
  if (!val) return;
  auto lock = static_pointer_cast<T>(val)->getLock();
  if (lock) {
    lock_guard exlusive(*lock);
    static_pointer_cast<T>(val)->flush();
  } else
    static_pointer_cast<T>(val)->flush();
  ++Cache::instance->stats_writes;
}

template <class T, class U>
shared_ptr<T> CacheEntry<T, U>::getValue(const U* key) const {
  if (val) {
    auto increase_reference_count = static_pointer_cast<T>(val);
    // Already in memory
    moveToFront();
    return increase_reference_count;
  } else {
    // Not in memory yet
    ++Cache::instance->stats_reads;
    const_cast<CacheEntry<T, U>*>(this)->val = make_shared<T>(key);
    insertAtFront();
    return static_pointer_cast<T>(val);
  }
}

}  // namespace utils
}  // namespace frepple
