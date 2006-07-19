/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/dllmain.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
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


#define FREPPLE_CORE
#include "frepple/utils.h"

#if defined(MT) && !defined(HAVE_PTHREAD_H)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <process.h>
#endif

namespace frepple
{

LockManager* LockManager::mgr;

void LockManager::obtainReadLock(const Lock& l, priority p) {}
void LockManager::obtainWriteLock(Lock& l, priority p) {}
void LockManager::releaseReadLock(const Lock& l) {}
void LockManager::releaseWriteLock(Lock& l) {}
DECLARE_EXPORT unsigned int ThreadGroup::MaxThreads = 1;

#ifdef MT
Pool<Lock> pool_locks;


void LockManager::obtainReadLock(const Object* l, priority p)
{
  // Check if exclusivewrite is on and I am not the writer
  // if yes wait, then repeat

  //if (!l->lock)
  //  const_cast<Object*>(l)->lock = pool_locks.Alloc();

  //clog << "Read locking " << l << "  " << l->getType().type <<  endl;
  // if writelock > 0 and I am not the writer, wait, then repeat

  // insert in the table
  // increment readers
};


void LockManager::obtainWriteLock(Object* l, priority p)
{
  // Check if exclusiveread is on
  // if yes wait, then repeat

  l->getType().raiseEvent(l, SIG_BEFORE_CHANGE);

  // if readlock > 0, wait, then repeat
  //if (!l->lock)
  //  l->lock = pool_locks.Alloc();

  //clog << "Write locking " << l << "  " << l->getType().type << endl;

  // increment writers
};


void LockManager::releaseReadLock(const Object* l)
{
  //  readers is expected to be >0
  //  writers is expected to be 0
  //  exclusive write is expected to be off

  //if (!l->lock)
  //  throw RuntimeException("Releasing invalid lock");

  //clog << "Read unlocking " << l << "  " << l->getType().type << endl;

  // decrement readers

  // when readers & writers & wait = 0, remove from table
};


void LockManager::releaseWriteLock(Object* l)
{
  //  readers is expected to be = 0
  //  writers is expected to be me

  l->getType().raiseEvent(l, SIG_AFTER_CHANGE);

  //if (!l->lock)
    //throw RuntimeException("Releasing invalid lock");

  //clog << "Write unlocking " << l << "  " << l->getType().type << endl;

  // decrement writers

  // when readers & writers & wait = 0, remove from table
};


bool Thread::operator==(const Thread& other) const
{
#ifdef HAVE_PTHREAD_H
  return pthread_equal(m_thread, other.m_thread) != 0;
#else
  return other.m_id == m_id;
#endif
}


void Thread::join()
{
#ifdef HAVE_PTHREAD_H
  int res = pthread_join(m_thread, 0);
  if (res) throw RuntimeException("Can't join thread, error " + res);
#else
  int res = WaitForSingleObject(reinterpret_cast<HANDLE>(m_thread), INFINITE);
  if (res != WAIT_OBJECT_0)
    throw RuntimeException("Can't join thread, error " + res);
  res = CloseHandle(reinterpret_cast<HANDLE>(m_thread));
  if (res) throw RuntimeException("Can't close thread handle, error " + res);
#endif
}


#ifdef HAVE_PTHREAD_H
void* ThreadGroup::wrapper(void *param)
#else
unsigned __stdcall ThreadGroup::wrapper(void *param)
#endif
{
  try { static_cast<Thread*>(param)->run(); }
  catch (...)
  {
    // Error message
    clog << "Error: Caught an exception while running thread :" << endl;
    try { throw; }
    catch (bad_exception&){clog << "  bad exception" << endl;}
    catch (exception& e) {clog << "  " << e.what() << endl;}
    catch (...) {clog << "  Unknown type" << endl;}
  }
  return 0;
}


void ThreadGroup::joinAll()
{
  ScopeMutexLock l(m_mutex);
  for (threadlist::iterator i = m_threads.begin(); i != m_threads.end(); ++i)
      (*i)->join();
}

ThreadGroup::~ThreadGroup()
{
  ScopeMutexLock l(m_mutex);
  for (threadlist::iterator it=m_threads.begin(); it!=m_threads.end(); ++it)
  {
#ifdef HAVE_PTHREAD_H
    pthread_detach((*it)->m_thread);
#else
    int res = CloseHandle(reinterpret_cast<HANDLE>((*it)->m_thread));
    if (res) throw RuntimeException("Can't close thread handle, error " + res);
#endif
    delete *it;
  }
}


void ThreadGroup::addThread(Thread* thrd)
{
  ScopeMutexLock l(m_mutex);
  threadlist::iterator it = find(m_threads.begin(), m_threads.end(), thrd);
  // Append in the list, if not added yet
  if (it == m_threads.end() && thrd)
  {
    m_threads.push_back(thrd);
#ifdef HAVE_PTHREAD_H
    int res = pthread_create(&(thrd->m_thread), 0, &wrapper, thrd);
    if (res)throw RuntimeException("Can't create a thread, error " + res);
#else
    thrd->m_thread = _beginthreadex(0, 0, &Thread::wrapper, this, 0, thrd->m_id);
    if (!m_thread) throw RuntimeException("Can't create a thread, error " + errno);
#endif
  }
}


void ThreadGroup::removeThread(Thread* thrd)
{
  ScopeMutexLock l(m_mutex);
  threadlist::iterator it = find(m_threads.begin(), m_threads.end(), thrd);
  if (it != m_threads.end()) m_threads.erase(it);
}


#else // Compiling without thread support



void LockManager::obtainReadLock(const Object* l, priority p)
{
  //clog << "Read locking " << l << "  " << l->getType().type <<  endl;
};


void LockManager::obtainWriteLock(Object* l, priority p)
{
  // Lock already exists
  if (l->lock) return;
  l->lock = reinterpret_cast<Lock*>(l);
  l->getType().raiseEvent(l, SIG_BEFORE_CHANGE);
  //clog << "Write locking " << l << "  " << l->getType().type << endl;
};


void LockManager::releaseReadLock(const Object* l)
{
  //clog << "Read unlocking " << l << "  " << l->getType().type << endl;
};


void LockManager::releaseWriteLock(Object* l)
{
  // There was no lock set
  if (!l->lock) return;
  //clog << "Write unlocking " << l << "  " << l->getType().type << endl;
  l->lock = NULL;
  l->getType().raiseEvent(l, SIG_AFTER_CHANGE);
};


ThreadGroup::~ThreadGroup() {}
void ThreadGroup::joinAll() {}


void ThreadGroup::addThread(Thread* thrd)
{
  if (!thrd) return;
  try { thrd->run(); }
  catch (...)
  {
    // Error message
    clog << "Error: Caught an exception while running thread :" << endl;
    try { throw; }
    catch (bad_exception&){clog << "  bad exception" << endl;}
    catch (exception& e) {clog << "  " << e.what() << endl;}
    catch (...) {clog << "  Unknown type" << endl;}
  }
}


#endif  // endif MT

}  // End Namespace
