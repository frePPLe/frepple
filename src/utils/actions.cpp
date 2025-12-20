/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
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

#include "frepple/utils.h"

namespace frepple {
namespace utils {

const MetaCategory* CommandManager::metacategory;
const MetaClass* CommandManager::metadata;

//
// COMMAND LIST
//

void CommandList::add(Command* c) {
  // Validity check
  if (!c) throw LogicException("Adding nullptr command to a command list");

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

void CommandList::rollback() {
  // Undo all commands and delete them.
  // Note that undoing an operation that hasn't been executed yet or has been
  // undone already is expected to be harmless, so we don't need to worry
  // about that...
  for (auto i = lastCommand; i;) {
    Command* t = i;  // Temporarily store the pointer to be deleted
    i = i->prev;
    t->next = nullptr;
    delete t;  // The delete is expected to also revert the change!
  }

  // Reset the list
  firstCommand = nullptr;
  lastCommand = nullptr;
}

void CommandList::commit() {
  // Commit the commands
  for (auto i = firstCommand; i;) {
    Command* t = i;  // Temporarily store the pointer to be deleted
    i->commit();
    i = i->next;
    t->prev = nullptr;
    delete t;
  }

  // Reset the list
  firstCommand = nullptr;
  lastCommand = nullptr;
}

CommandList::~CommandList() {
  if (firstCommand) {
    logger << "Warning: Deleting a command list with commands that have"
           << " not been committed or rolled back" << endl;
    rollback();
  }
}

//
// COMMAND MANAGER
//

int CommandManager::initialize() {
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<CommandManager>(
      "commandmanager", "commandmanagers");
  metadata = MetaClass::registerClass<CommandManager>(
      "commandmanager", "commandmanager", Object::create<CommandManager>, true);

  // Initialize the Python class
  auto& x = FreppleCategory<CommandManager>::getPythonType();
  x.setName(metadata->type);
  x.setDoc("frePPLe " + metadata->type);
  metadata->setPythonClass(x);
  return x.typeReady();
}

CommandManager::Bookmark* CommandManager::setBookmark() {
  auto* n = new Bookmark(currentBookmark);
  lastBookmark->nextBookmark = n;
  n->prevBookmark = lastBookmark;
  lastBookmark = n;
  currentBookmark = n;
  return n;
}

void CommandManager::rollback(CommandManager::Bookmark* b) {
  if (!b) throw LogicException("Can't rollback nullptr bookmark");
  if (b == &firstBookmark)
    throw LogicException("Can't rollback default bookmark");

  // Remove all later child bookmarks
  Bookmark* i = lastBookmark;
  while (i && i != b) {
    if (i->isChildOf(b)) {
      // Remove from bookmark list
      if (i->prevBookmark) i->prevBookmark->nextBookmark = i->nextBookmark;
      if (i->nextBookmark)
        i->nextBookmark->prevBookmark = i->prevBookmark;
      else
        lastBookmark = i->prevBookmark;
      i->rollback();
      if (currentBookmark == i) currentBookmark = b;
      Bookmark* tmp = i;
      i = i->prevBookmark;
      delete tmp;
    } else
      // Bookmark has a different parent
      i = i->prevBookmark;
  }
  if (!i) throw LogicException("Can't find bookmark to rollback");
  b->rollback();
}

void CommandManager::commit() {
  if (firstBookmark.active) firstBookmark.commit();
  for (auto i = firstBookmark.nextBookmark; i;) {
    if (i->active) i->commit();
    Bookmark* tmp = i;
    i = i->nextBookmark;
    delete tmp;
  }
  firstBookmark.nextBookmark = nullptr;
  currentBookmark = &firstBookmark;
  lastBookmark = &firstBookmark;
}

void CommandManager::rollback() {
  for (auto i = lastBookmark; i != &firstBookmark;) {
    i->rollback();
    Bookmark* tmp = i;
    i = i->prevBookmark;
    delete tmp;
  }
  firstBookmark.rollback();
  firstBookmark.nextBookmark = nullptr;
  currentBookmark = &firstBookmark;
  lastBookmark = &firstBookmark;
}

bool CommandManager::empty() const {
  if (firstBookmark.active && !firstBookmark.empty()) return false;
  for (auto bkmrk = firstBookmark.nextBookmark; bkmrk;
       bkmrk = bkmrk->nextBookmark) {
    if (!bkmrk->empty()) return false;
  }
  return true;
}

//
// COMMAND SETPROPERTY
//

CommandSetProperty::CommandSetProperty(Object* o, const string& nm,
                                       const DataValue& , short tp)
    : obj(o), name(nm), type(tp) {
  if (!o || nm.empty()) return;

  // Store old value
  old_exists = o->hasProperty(name);
  if (old_exists) {
    switch (type) {
      case 1:  // Boolean
        old_bool = obj->getBoolProperty(name);
        break;
      case 2:  // Date
        old_date = obj->getDateProperty(name);
        break;
      case 3:  // Double
        old_double = obj->getDoubleProperty(name);
        break;
      case 4:  // String
        old_string = obj->getStringProperty(name);
        break;
      default:
        break;
    }
  }
}

void CommandSetProperty::rollback() {
  if (!obj || name.empty()) {
    if (old_exists && obj) {
      switch (type) {
        case 1:  // Boolean
        {
          bool tmp_bool = obj->getBoolProperty(name);
          obj->setBoolProperty(name, old_bool);
          old_bool = tmp_bool;
        } break;
        case 2:  // Date
        {
          Date tmp_date = obj->getDateProperty(name);
          obj->setDateProperty(name, old_date);
          old_date = tmp_date;
        } break;
        case 3:  // Double
        {
          double tmp_double = obj->getDoubleProperty(name);
          obj->setDoubleProperty(name, old_double);
          old_double = tmp_double;
        } break;
        case 4:  // String
        {
          string tmp_string = obj->getStringProperty(name);
          obj->setStringProperty(name, old_string);
          old_string = tmp_string;
        } break;
        default:
          break;
      }
    } else if (obj) {
      switch (type) {
        case 1:  // Boolean
          old_bool = obj->getBoolProperty(name);
          break;
        case 2:  // Date
          old_date = obj->getDateProperty(name);
          break;
        case 3:  // Double
          old_double = obj->getDoubleProperty(name);
          break;
        case 4:  // String
          old_string = obj->getStringProperty(name);
          break;
        default:
          break;
      }
      obj->deleteProperty(name);
    }
  }
  obj = nullptr;
  name = "";
}

//
// THREAD GROUP
//

void ThreadGroup::execute() {
  // Determine the number of threads
  auto numthreads = callables.size();
  if (numthreads > static_cast<size_t>(maxParallel)) numthreads = maxParallel;

  if (numthreads <= 1)
    // Sequential execution
    wrapper(this);
  else {
    // Parallel execution in worker threads
    stack<thread> threads;

    // Launch all threads
    while (numthreads > 0) {
      threads.push(thread(wrapper, this));
      --numthreads;
    }

    // Wait for all threads to finish
    while (!threads.empty()) {
      threads.top().join();
      threads.pop();
    }
  }
}

ThreadGroup::callableWithArgument ThreadGroup::selectNextCallable() {
  lock_guard<mutex> l(lock);
  if (callables.empty())
    // No more functions
    return callableWithArgument(static_cast<callable>(nullptr),
                                static_cast<void*>(nullptr), 0,
                                static_cast<void*>(nullptr));
  callableWithArgument c = callables.top();
  callables.pop();
  return c;
}

void ThreadGroup::wrapper(ThreadGroup* grp) {
  while (true) {
    auto job = grp->selectNextCallable();
    if (!get<0>(job)) return;
    try {
      get<0>(job)(get<1>(job), get<2>(job), get<3>(job));
    } catch (...) {
      // Error message
      logger << "Error: Caught an exception while executing command:" << endl;
      try {
        throw;
      } catch (const exception& e) {
        logger << "  " << e.what() << endl;
      } catch (...) {
        logger << "  Unknown type" << endl;
      }
    }
  };
}

}  // namespace utils
}  // namespace frepple
