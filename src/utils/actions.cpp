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

#define FREPPLE_CORE 
#include "frepple/utils.h"


// These headers are required for the loading of dynamic libraries
#ifdef WIN32
  #include <windows.h>
#else
  #include <dlfcn.h>
#endif


namespace frepple
{


DECLARE_EXPORT bool Command::getVerbose() const
{
  if (verbose==INHERIT)
    // Note: a command gets the level INHERIT by default. In case the command
    // was never added to a commandlist, the owner field will be NULL. In such
    // case the value INHERIT is interpreted as SILENT.
    return owner ? owner->getVerbose() : false;
  else
    return verbose==YES;
}


DECLARE_EXPORT void Command::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_verbose)) setVerbose(pElement.getBool());
}


//
// COMMAND LIST
//


DECLARE_EXPORT bool CommandList::getAbortOnError() const
{
  if (abortOnError==INHERIT)
  {
    // A command list can be nested in another command list. In this case we
    // inherit this field from the owning command list
    CommandList *owning_list = dynamic_cast<CommandList*>(owner);
    return owning_list ? owning_list->getAbortOnError() : true;
  }
  else
    return abortOnError==YES;
}


DECLARE_EXPORT void CommandList::add(Command* c)
{
  // Validity check
  if (!c) throw LogicException("Adding NULL command to a command list");
  if (curCommand) 
    throw RuntimeException("Can't add a command to the list during execution");

  // Set the owner of the command
  c->owner = this;

  // Maintenance of the linked list of child commands
  if (lastCommand)
  {
    // Let the last command in the chain point to this new extra command
    lastCommand->next = c;
    lastCommand = c;
  }
  else
  {
    // This is the first command in this command list
    firstCommand = c;
    lastCommand = c;
  }

  // Update the undoable field
  if(!c->undoable()) can_undo=false;
}


DECLARE_EXPORT void CommandList::undo(Command *c)
{
  // Check validity of argument
  if (c && c->owner != this) 
    throw LogicException("Invalid call to CommandList::undoable(Command*)");

  // Don't even try to undo a list which can't be undone.
  if (!undoable(c))
    throw RuntimeException("Trying to undo a CommandList which " \
      "contains non-undoable actions or is executed in parallel.");

  // Undo all commands and delete them.
  // Note that undoing an operation that hasn't been executed yet or has been
  // undone already is expected to be harmless, so we don't need to worry
  // about that...
  for(Command *i=(c?c->next:firstCommand); i; )
  {
    i->undo();
    Command *t = i;  // Temporarily store the pointer to be deleted
    i = i->next;
    delete t;
  }

  // Maintain the linked list of commands still present
  if (c)
  {
    // Partially undo
    c->next = NULL;
    lastCommand = c;
  }
  else
  {
    // Completely erase the list
    firstCommand = NULL;
    lastCommand = NULL;
  }
}


DECLARE_EXPORT bool CommandList::undoable(const Command *c) const 
{
  // Check validity of argument
  if (c && c->owner!=this) 
    throw LogicException("Invalid call to CommandList::undoable(Command*)");

  // Easy cases
  if (!c || can_undo) return can_undo;

  // Parallel commands can't be undone
  if (maxparallel > 1) return false;

  // Step over the remaining commands and check whether they can be undone
  for (; c; c = c->next) if (!c->undoable()) return false;
  return true;
}


DECLARE_EXPORT Command* CommandList::selectCommand()
{
  ScopeMutexLock l(lock);
  Command *c = curCommand;
  if (curCommand) curCommand = curCommand->next;
  return c;
}


DECLARE_EXPORT void CommandList::execute()
{
  // Execute the actions
  // This field is set asap in this method since it is used a flag to 
  // recognize that execution is in progress.
  curCommand = firstCommand;

  // Message
  if (getVerbose())
    cout << "Start executing command list at " << Date::now() << endl;
  Timer t;

#ifndef MT
  // Compile 1: No multithreading
  if (maxparallel>1) maxparallel = 1;
#else
  if (maxparallel>1)
  {
    // MODE 1: Parallel execution of the commands
    int numthreads = getNumberOfCommands(); 
    // Limit the number of threads to the maximum allowed
    if (numthreads>maxparallel) numthreads = maxparallel; 
    if (numthreads == 1)
      // Only a single command in the list: no need for threads
      wrapper(curCommand);
    else if (numthreads > 1)
    {
#ifdef HAVE_PTHREAD_H
      // Create a thread for every command list. The main thread will then
      // wait for all of them to finish.
      pthread_t threads[numthreads];     // holds thread info
      int errcode;                       // holds pthread error code
      int status;                        // holds return value

      // Create the command threads
      for (int worker=0; worker<numthreads; ++worker)
      {
        if ((errcode=pthread_create(&threads[worker],  // thread struct
                                NULL,                  // default thread attributes
                                wrapper,               // start routine
                                this)))                // arg to routine
        {
          ostringstream ch;
          ch << "Can't create thread " << worker << ", error " << errcode;
          throw RuntimeException(ch.str());  // @todo what if some threads were already created?
        }
      }

      // Wait for the command threads as they exit
      for (int worker=0; worker<numthreads; ++worker)
        // Wait for thread to terminate
        if ((errcode=pthread_join(threads[worker],(void**) &status)))
        {
          ostringstream ch;
          ch << "Can't join with thread " << worker << ", error " << errcode;
          throw RuntimeException(ch.str());
        }
#else
      // Create a thread for every command list. The main thread will then
      // wait for all of them to finish.
      HANDLE* threads = new HANDLE[numthreads];
      unsigned int * m_id = new unsigned int[numthreads];

      // Create the command threads
      for (int worker=0; worker<numthreads; ++worker)
      {
        threads[worker] =  reinterpret_cast<HANDLE>(
          _beginthreadex(0,  // Security atrtributes 
          0,                 // Stack size
          &wrapper,          // Thread function 
          this,              // Argument list
          0,                 // Initial state is 0, "running"
          &m_id[worker]));   // Address to receive the thread identifier
        if (!threads[worker]) 
        {
          ostringstream ch;
          ch << "Can't create thread " << worker << ", error " << errno;
          delete threads;
          delete m_id;
          throw RuntimeException(ch.str());   // @todo what if some threads were already created?
        }
      }

      // Wait for the command threads as they exit
      int res = WaitForMultipleObjects(numthreads, threads, true, INFINITE);
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
        ostringstream ch;
        ch << "Can't join threads: " << error;
        delete threads;
        delete m_id;
        throw RuntimeException(ch.str());
      }
      for (int worker=0; worker<numthreads; ++worker)
        CloseHandle(threads[worker]);
      delete threads;
      delete m_id;
#endif 
    }  // End: else if (numthreads>1)
  } 
  else // Else: sequential
#endif
  if (getAbortOnError())
  {
    // MODE 2: Sequential execution, and a single command failure aborts the
    // whole sequence.
    try
    {
      for(; curCommand; curCommand = curCommand->next) curCommand->execute();
    }
    catch (...)
    {
      cout << "Error: Caught an exception while executing command '"
        << curCommand->getDescription() << "':" <<  endl;
      try { throw; }
      catch (exception& e) {cout << "  " << e.what() << endl;}
      catch (...) {cout << "  Unknown type" << endl;}
      // Undo all commands executed so far
      if (undoable()) undo();
    }
  }
  else
    // MODE 3: Sequential execution, and when a command in the sequence fails
    // the rest continues
    wrapper(this);

  // Clean it up after executing ALL actions.
  for(Command *i=firstCommand; i; )
  {
    Command *t = i;
    i = i->next;
    delete t;
  }
  firstCommand = NULL;
  lastCommand = NULL;

  // Log
  if (getVerbose())
    cout << "Finished executing command list at " << Date::now()
      << " : " << t << endl;
}


#if defined(HAVE_PTHREAD_H) || !defined(MT)
void* CommandList::wrapper(void *arg)
#else
unsigned __stdcall CommandList::wrapper(void *arg)
#endif
{ 
  CommandList *l = static_cast<CommandList*>(arg);
  for(Command *c = l->selectCommand(); c; c = l->selectCommand())
  {
#if defined(HAVE_PTHREAD_H) || !defined(MT)
    // Verfiy whether there has been a cancellation request in the meantime
    pthread_testcancel();
#endif
    try { c->execute(); }
    catch (...)
    {
      // Error message
      cout << "Error: Caught an exception while executing command '" 
        << c->getDescription() << "':" << endl;
      try { throw; }
      catch (exception& e) {cout << "  " << e.what() << endl;}
      catch (...) {cout << "  Unknown type" << endl;}
    }
  }
  return 0;
}


DECLARE_EXPORT CommandList::~CommandList()
{
  if (!firstCommand) return;
  cout << "Warning: Deleting an action list with actions that have"
    << " not been committed or undone" << endl;
  for(Command *i = firstCommand; i; )
  {
    Command *t = i;  // Temporary storage for the object to delete
    i = i->next;
    delete t;
  }
}


DECLARE_EXPORT void CommandList::endElement(XMLInput& pIn, XMLElement& pElement)
{
  // Replace environment variables with their value.
  pElement.resolveEnvironment();

  if (pElement.isA(Tags::tag_command) && !pIn.isObjectEnd())  
  {
    // We're unlucky with our tag names here. Subcommands end with
    // </COMMAND>, but the command list itself also ends with that tag.
    // We use the isObjectEnd() method to differentiate between both.
    Command * b = dynamic_cast<Command*>(pIn.getPreviousObject());
    if (b) add(b);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pElement.isA(Tags::tag_abortonerror))
    setAbortOnError(pElement.getBool());
  else if (pElement.isA(Tags::tag_maxparallel))
    setMaxParallel(pElement.getInt());
  else
    Command::endElement(pIn, pElement);
}


DECLARE_EXPORT void CommandList::beginElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_command))
    pIn.readto( MetaCategory::ControllerDefault(Command::metadata,pIn) );
}


//
// SYSTEM COMMAND
//


DECLARE_EXPORT void CommandSystem::execute()
{
  // Log
  if (getVerbose())
    cout << "Start executing system command '" << cmdLine
    << "' at " << Date::now() << endl;
  Timer t;

  // Execute
  if (cmdLine.empty())
    throw DataException("Error: Trying to execute empty system command");
  else if (system(cmdLine.c_str()))  // Execution through system() call
    throw RuntimeException("Error while executing system command: " + cmdLine);

  // Log
  if (getVerbose())
    cout << "Finished executing system command '" << cmdLine
    << "' at " << Date::now() << " : " << t << endl;
}


DECLARE_EXPORT void CommandSystem::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_cmdline))
    // No need to replace environment variables here. It's done at execution 
    // time by the command shell.
    pElement >> cmdLine;
  else
  {
    // Replace environment variables with their value.
    pElement.resolveEnvironment();
    Command::endElement(pIn, pElement);
  }
}


//
// LOADLIBRARY COMMAND
//


DECLARE_EXPORT void CommandLoadLibrary::execute()
{
  // Type definition of the initialization function
  typedef const char* (*func)(const ParameterList&);

  // Log
  if (getVerbose())
    cout << "Start loading library '" << lib << "' at " << Date::now() << endl;
  Timer t;

  // Validate
  if (lib.empty())
    throw DataException("Error: No library name specified for loading");

#ifdef WIN32
  // Load the library - The windows way
  // Change the error mode: we handle errors now, not the operating system
  UINT em = SetErrorMode(SEM_FAILCRITICALERRORS);
  HINSTANCE handle = LoadLibraryEx(lib.c_str(),NULL,LOAD_WITH_ALTERED_SEARCH_PATH);
  if (!handle) handle = LoadLibraryEx(lib.c_str(), NULL, 0);
  if (!handle) 
  {
    // Get the error description
    char error[256];
    FormatMessage(
      FORMAT_MESSAGE_IGNORE_INSERTS | FORMAT_MESSAGE_FROM_SYSTEM,
      NULL, 
      GetLastError(),
      0,
      error, 
      256, 
      NULL );
    throw RuntimeException(error);
  }
  SetErrorMode(em);  // Restore the previous error mode

  // Find the initialization routine
  func inithandle =
    reinterpret_cast<func>(GetProcAddress(HMODULE(handle), "initialize"));
  if (!inithandle) 
  {
    // Get the error description
    char error[256];
    FormatMessage(
      FORMAT_MESSAGE_IGNORE_INSERTS | FORMAT_MESSAGE_FROM_SYSTEM,
      NULL, 
      GetLastError(),
      0,
      error, 
      256, 
      NULL );
    throw RuntimeException(error);
  }

#else
  // Load the library - The unix way
  dlerror(); // Clear the previous error
  void *handle = dlopen(lib.c_str(), RTLD_NOW | RTLD_GLOBAL);
  const char *err = dlerror();  // Pick up the error string
  if (err) throw RuntimeException(err);

  // Find the initialization routine
  func inithandle = (func)(dlsym(handle, "initialize"));
  err = dlerror(); // Pick up the error string
  if (err) throw RuntimeException(err);
#endif

  // Call the initialization routine with the parameter list  //@todo do we need to catch exceptions here???
  string x = (inithandle)(parameters);
  if (x.empty()) throw DataException("Invalid module name returned.");
    
  // Insert the new module in the registry
  registry.insert(x);

  // Log
  if (getVerbose())
    cout << "Finished loading module '" << x << "' from library '" << lib
      << "' at " << Date::now() << " : " << t << endl;
}


DECLARE_EXPORT void CommandLoadLibrary::printModules()
{
  cout << "Loaded modules:" << endl;
  for (set<string>::const_iterator i=registry.begin(); i!=registry.end(); ++i)
    cout << "   " << *i << endl;
  cout << endl;
}


DECLARE_EXPORT void CommandLoadLibrary::endElement(XMLInput& pIn, XMLElement& pElement)
{
  // Replace environment variables with their value.
  pElement.resolveEnvironment();

  if (pElement.isA(Tags::tag_filename))
    pElement >> lib;
  else if (pElement.isA(Tags::tag_name))
    pElement >> tempName;
  else if (pElement.isA(Tags::tag_value))
    pElement >> tempValue;
  else if (pElement.isA(Tags::tag_parameter))
  {
    if (!tempValue.empty() && !tempName.empty())
    {
      // New parameter name+value pair ready
      parameters[tempName] = tempValue;
      tempValue.clear();
      tempName.clear();
    }
    else 
      // Incomplete data
      throw DataException("Invalid parameter specification");
  }
  else if (pIn.isObjectEnd())
  {
    tempValue.clear();
    tempName.clear();
  }
  else
    Command::endElement(pIn, pElement);
}


//
// IF COMMAND
//


DECLARE_EXPORT void CommandIf::execute()
{
  // Message
  if (getVerbose())
    cout << "Start executing if-command with condition '" 
      << condition << "' at " << Date::now() << endl;
  Timer t;

  // Check validity
  if(condition.empty())
    throw DataException("Missing condition in If-Command");

  // Evaluate the expression
  int eval = system(condition.c_str());
  
  // Conditional execution
  if (!eval)
  {
    // Exit code was zero
    delete elseCommand;  // To avoid that undo() ever undoes the elseCommand
    elseCommand = NULL;
    if (thenCommand) thenCommand->execute();
  }
  else
  {
    // Exit code was non-zero
    delete thenCommand;  // To avoid that undo() ever undoes the thenCommand
    thenCommand = NULL;
    if (elseCommand) elseCommand->execute();
  }

  // Log
  if (getVerbose())
    cout << "Finished executing if-command at " << Date::now()
      << " : " << t << endl;
}


DECLARE_EXPORT void CommandIf::undo()
{
  if (thenCommand && elseCommand)
  {
    // This condition is only possible if the condition hasn't been evaluated.
    // I.e. when undo() is called before execute().
    int eval = system(condition.c_str());
    if (eval) delete thenCommand;
    else delete elseCommand;
  }

  // Undo then-command
  if (thenCommand && thenCommand->undoable()) thenCommand->undo();

  // Undo else-command
  if (elseCommand && elseCommand->undoable()) elseCommand->undo();
}


DECLARE_EXPORT void CommandIf::beginElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_then) || pElement.isA (Tags::tag_else))
    pIn.readto( MetaCategory::ControllerDefault(Command::metadata,pIn) );
}


DECLARE_EXPORT void CommandIf::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_condition))
    pElement >> condition;
  else if (pElement.isA(Tags::tag_then))
  {
    Command * b = dynamic_cast<Command*>(pIn.getPreviousObject());
    if (!b) throw LogicException("Incorrect object type during read operation");
    thenCommand = b;
    thenCommand->owner = this;
  }
  else if (pElement.isA(Tags::tag_else))
  {
    Command * b = dynamic_cast<Command*>(pIn.getPreviousObject());
    if (!b) throw LogicException("Incorrect object type during read operation");
    elseCommand = b;
    elseCommand->owner = this;
  }
  else
    Command::endElement(pIn, pElement);
}


}
