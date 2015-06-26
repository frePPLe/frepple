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


//
// COMMAND LIST
//


DECLARE_EXPORT void CommandList::add(Command* c)
{
  // Validity check
  if (!c) throw LogicException("Adding NULL command to a command list");

  // Set the owner of the command
  c->owner = this;

  // Maintenance of the linked list of child commands
  c->prev = lastCommand;
  if (lastCommand)
    // Let the last command in the chain point to this new extra command
    lastCommand->next = c;
  else
    // This is the first command in this command list
    firstCommand = c;
  lastCommand = c;
}


DECLARE_EXPORT void CommandList::rollback()
{
  // Undo all commands and delete them.
  // Note that undoing an operation that hasn't been executed yet or has been
  // undone already is expected to be harmless, so we don't need to worry
  // about that...
  for (Command *i = lastCommand; i; )
  {
    Command *t = i;  // Temporarily store the pointer to be deleted
    i = i->prev;
    delete t; // The delete is expected to also revert the change!
  }

  // Reset the list
  firstCommand = NULL;
  lastCommand = NULL;
}


DECLARE_EXPORT void CommandList::undo()
{
  // Undo all commands and delete them.
  // Note that undoing an operation that hasn't been executed yet or has been
  // undone already is expected to be harmless, so we don't need to worry
  // about that...
  for (Command *i = lastCommand; i; i = i->prev)
    i->undo();
}


DECLARE_EXPORT void CommandList::commit()
{
  // Commit the commands
  for (Command *i = firstCommand; i;)
  {
    Command *t = i;  // Temporarily store the pointer to be deleted
    i->commit();
    i = i->next;
    delete t;
  }

  // Reset the list
  firstCommand = NULL;
  lastCommand = NULL;
}


DECLARE_EXPORT void CommandList::redo()
{
  // Redo the commands
  for (Command* c = firstCommand; c; c = c->next)
    c->redo();
}


DECLARE_EXPORT CommandList::~CommandList()
{
  if (firstCommand)
  {
    logger << "Warning: Deleting a command list with commands that have"
        << " not been committed or rolled back" << endl;
    rollback();
  }
}


//
// COMMAND MANAGER
//


DECLARE_EXPORT CommandManager::Bookmark* CommandManager::setBookmark()
{
  Bookmark* n = new Bookmark(currentBookmark);
  lastBookmark->nextBookmark = n;
  n->prevBookmark = lastBookmark;
  lastBookmark = n;
  currentBookmark = n;
  return n;
}


DECLARE_EXPORT void CommandManager::undoBookmark(CommandManager::Bookmark* b)
{
  if (!b) throw LogicException("Can't undo NULL bookmark");

  Bookmark* i = lastBookmark;
  for (; i && i != b; i = i->prevBookmark)
  {
    if (i->isChildOf(b) && i->active)
    {
      i->undo();
      i->active = false;
    }
  }
  if (!i) throw LogicException("Can't find bookmark to undo");
  currentBookmark = b->parent;
}


DECLARE_EXPORT void CommandManager::redoBookmark(CommandManager::Bookmark* b)
{
  if (!b) throw LogicException("Can't redo NULL bookmark");

  for (Bookmark* i = b; i; i = i->nextBookmark)
  {
    if (i->isChildOf(b) && !i->active)
    {
      i->redo();
      i->active = true;
    }
  }
  currentBookmark = b;
}


DECLARE_EXPORT void CommandManager::rollback(CommandManager::Bookmark* b)
{
  if (!b)
    throw LogicException("Can't rollback NULL bookmark");
  if (b == &firstBookmark)
    throw LogicException("Can't rollback default bookmark");

  // Remove all later child bookmarks
  Bookmark* i = lastBookmark;
  while (i && i != b)
  {
    if (i->isChildOf(b))
    {
      // Remove from bookmark list
      if (i->prevBookmark)
        i->prevBookmark->nextBookmark = i->nextBookmark;
      if (i->nextBookmark)
        i->nextBookmark->prevBookmark = i->prevBookmark;
      else
        lastBookmark = i->prevBookmark;
      i->rollback();
      if (currentBookmark == i)
        currentBookmark = b;
      Bookmark* tmp = i;
      i = i->prevBookmark;
      delete tmp;
    }
    else
      // Bookmark has a different parent
      i = i->prevBookmark;
  }
  if (!i) throw LogicException("Can't find bookmark to rollback");
  b->rollback();
}


DECLARE_EXPORT void CommandManager::commit()
{
  if (firstBookmark.active) firstBookmark.commit();
  for (Bookmark* i = firstBookmark.nextBookmark; i; )
  {
    if (i->active) i->commit();
    Bookmark *tmp = i;
    i = i->nextBookmark;
    delete tmp;
  }
  firstBookmark.nextBookmark = NULL;
  currentBookmark = &firstBookmark;
  lastBookmark = &firstBookmark;
}


DECLARE_EXPORT void CommandManager::rollback()
{
  for (Bookmark* i = lastBookmark; i != &firstBookmark;)
  {
    i->rollback();
    Bookmark *tmp = i;
    i = i->prevBookmark;
    delete tmp;
  }
  firstBookmark.rollback();
  firstBookmark.nextBookmark = NULL;
  currentBookmark = &firstBookmark;
  lastBookmark = &firstBookmark;
}


//
// THREAD GROUP
//


DECLARE_EXPORT void ThreadGroup::execute()
{
  // CASE 1: No need to create worker threads when either a) only a single
  // worker is allowed or b) only a single function needs to be called.
  if (maxParallel<=1 || countCallables<=1)
  {
    wrapper(this);
    return;
  }

  // CASE 2: Parallel execution in worker threads
  int numthreads = countCallables;
  // Limit the number of threads to the maximum allowed
  if (numthreads > maxParallel) numthreads = maxParallel;
  int worker = 0;
#ifdef HAVE_PTHREAD_H
  // Create a thread for every command list. The main thread will then
  // wait for all of them to finish.
  pthread_t threads[numthreads];     // holds thread info
  int errcode;                       // holds pthread error code

  // Create the threads
  for (; worker<numthreads; ++worker)
  {
    if ((errcode=pthread_create(&threads[worker],  // thread struct
        NULL,                  // default thread attributes
        wrapper,               // start routine
        this)))                // arg to routine
    {
      if (!worker)
      {
        ostringstream ch;
        ch << "Can't create any threads, error " << errcode;
        throw RuntimeException(ch.str());
      }
      // Some threads could be created.
      // Let these threads run and do all the work.
      logger << "Warning: Could create only " << worker
          << " threads, error " << errcode << endl;
    }
  }

  // Wait for the threads as they exit
  for (--worker; worker>=0; --worker)
    // Wait for thread to terminate.
    // The second arg is NULL, since we don't care about the return status
    // of the finished threads.
    if ((errcode=pthread_join(threads[worker],NULL)))
    {
      ostringstream ch;
      ch << "Can't join with thread " << worker << ", error " << errcode;
      throw RuntimeException(ch.str());
    }
#else
  // Create a thread for every command list. The main thread will then
  // wait for all of them to finish.
  HANDLE* threads = new HANDLE[numthreads];
  unsigned int* m_id = new unsigned int[numthreads];

  // Create the threads
  for (; worker<numthreads; ++worker)
  {
    threads[worker] =  reinterpret_cast<HANDLE>(
        _beginthreadex(0,  // Security attributes
            0,                 // Stack size
            &wrapper,          // Thread function
            this,              // Argument list
            0,                 // Initial state is 0, "running"
            &m_id[worker]));   // Address to receive the thread identifier
    if (!threads[worker])
    {
      if (!worker)
      {
        // No threads could be created at all.
        delete[] threads;
        delete[] m_id;
        throw RuntimeException("Can't create any threads, error " + errno);
      }
      // Some threads could be created.
      // Let these threads run and do all the work.
      logger << "Warning: Could create only " << worker
          << " threads, error " << errno << endl;
      break; // Step out of the thread creation loop
    }
  }

  // Wait for the threads as they exit
  int res = WaitForMultipleObjects(worker, threads, true, INFINITE);
  if (res == WAIT_FAILED)
  {
    char error[256];
    FormatMessage(
      FORMAT_MESSAGE_IGNORE_INSERTS | FORMAT_MESSAGE_FROM_SYSTEM,
      NULL,
      GetLastError(),
      0,
      error,
      256,
      NULL );
    delete[] threads;
    delete[] m_id;
    throw RuntimeException(string("Can't join threads: ") + error);
  }

  // Cleanup
  for (--worker; worker>=0; --worker)
    CloseHandle(threads[worker]);
  delete[] threads;
  delete[] m_id;
#endif    // End of #ifdef ifHAVE_PTHREAD_H
}


DECLARE_EXPORT ThreadGroup::callableWithArgument ThreadGroup::selectNextCallable()
{
  ScopeMutexLock l(lock);
  if (callables.empty())
  {
    // No more functions
    assert( countCallables == 0 );
    return callableWithArgument(static_cast<callable>(NULL),static_cast<void*>(NULL));
  }
  callableWithArgument c = callables.top();
  callables.pop();
  --countCallables;
  return c;
}


#if defined(HAVE_PTHREAD_H)
void* ThreadGroup::wrapper(void *arg)
#else
unsigned __stdcall ThreadGroup::wrapper(void *arg)
#endif
{
  // Each OS-level thread needs to initialize a Python thread state.
  ThreadGroup *l = static_cast<ThreadGroup*>(arg);
  bool threaded = l->maxParallel > 1 && l->countCallables > 1;
  if (threaded) PythonInterpreter::addThread();

  for (callableWithArgument nextfunc = l->selectNextCallable();
      nextfunc.first;
      nextfunc = l->selectNextCallable())
  {
#if defined(HAVE_PTHREAD_H)
    // Verify whether there has been a cancellation request in the meantime
    if (threaded) pthread_testcancel();
#endif
    try {nextfunc.first(nextfunc.second);}
    catch (...)
    {
      // Error message
      logger << "Error: Caught an exception while executing command:" << endl;
      try {throw;}
      catch (const exception& e) {logger << "  " << e.what() << endl;}
      catch (...) {logger << "  Unknown type" << endl;}
    }
  };

  // Finalize the Python thread state
  if (threaded) PythonInterpreter::deleteThread();
  return 0;
}


//
// LOADMODULE FUNCTION
//


DECLARE_EXPORT PyObject* loadModule
(PyObject* self, PyObject* args, PyObject* kwds)
{

  // Create the command
  char *data = NULL;
  int ok = PyArg_ParseTuple(args, "s:loadmodule", &data);
  if (!ok) return NULL;

  // Load parameters for the module
  Environment::ParameterList params;
  if (kwds)
  {
    PyObject *key, *value;
    Py_ssize_t pos = 0;
    while (PyDict_Next(kwds, &pos, &key, &value))
      params[PythonData(key).getString()] = PythonData(value).getString();
  }

  // Free Python interpreter for other threads.
  // This is important since the module may also need access to Python
  // during its initialization...
  Py_BEGIN_ALLOW_THREADS
  try
  {
    // Load the library
    Environment::loadModule(data, params);
  }
  catch(...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


DECLARE_EXPORT void Environment::printModules()
{
  logger << "Loaded modules:" << endl;
  for (set<string>::const_iterator i=moduleRegistry.begin(); i!=moduleRegistry.end(); ++i)
    logger << "   " << *i << endl;
  logger << endl;
}




} // end namespace
} // end namespace
