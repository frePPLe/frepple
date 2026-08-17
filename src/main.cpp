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

#include <cxxabi.h>
#include <execinfo.h>
#include <signal.h>

#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <sstream>

#include "freppleinterface.h"
using namespace std;

#ifndef NDEBUG
extern "C" const char* __asan_default_options() {
  return "detect_leaks=0:halt_on_error=1:abort_on_error=1";
}
#endif

void usage() {
  cout
      << "\nfrePPLe v" << FreppleVersion()
      << " command line application\n"
         "\nUsage:\n"
         "  frepple [options] [files | directories]\n"
         "\nThis program reads XML input data, and executes the modeling and\n"
         "planning commands included in them.\n"
         "The XML input can be provided in the following ways:\n"
         "  - Passing one or more XML files and/or directories as arguments.\n"
         "    When a directory is specified, the application will process\n"
         "    all files with the extension '.xml'.\n"
         "  - Passing one or more Python files with the extension '.py'\n"
         "    The Python commands are executed in the embedded interpreter.\n"
         "  - When passing no file or directory arguments, input will be read\n"
         "    from the standard input. XML data can be piped to the "
         "application.\n"
         "\nOptions:\n"
         "  -validate -v  Validate the XML input for correctness.\n"
         "  -check -c     Only validate the input, without executing the "
         "content.\n"
         "  -? -h -help   Show these instructions.\n"
         "\nEnvironment: The variable FREPPLE_HOME optionally points to a\n"
         "     directory where the initialization files init.xml, init.py,\n"
         "     frepple.xsd and module libraries will be searched.\n"
         "\nReturn codes: 0 when successful, non-zero in case of errors\n"
         "\nMore information on this program: http://www.frepple.com\n\n\n";
}

void handler(int sig) {
  ostringstream o;
  o << "Planning engine terminating due to ";
  bool stacktrace = true;
  switch (sig) {
    case SIGHUP:
      o << "hangup signal";
      stacktrace = false;
      break;
    case SIGINT:
      o << "interrupt signal";
      stacktrace = false;
      break;
    case SIGQUIT:
      o << "quit signal";
      break;
    case SIGILL:
      o << "illegal instruction";
      break;
    case SIGABRT:
      o << "abort signal";
      break;
    case SIGBUS:
      o << "bad memory access";
      break;
    case SIGFPE:
      o << "floating-point exception";
      break;
    case SIGKILL:
      o << "kill signal";
      stacktrace = false;
      break;
    case SIGSEGV:
      o << "segmentation violation";
      break;
    case SIGTERM:
      o << "termination signal";
      break;
    case SIGSTKFLT:
      o << "stack fault on coprocressor";
      break;
    case SIGXCPU:
      o << "CPU limit reached";
      stacktrace = false;
      break;
    case SIGXFSZ:
      o << "file size limit reached";
      stacktrace = false;
      break;
    default:
      o << "signal " << sig;
  }
  o << '\n';

  // Capture and log stack trace
  if (stacktrace) {
    const int max_frames = 32;
    void* addrlist[max_frames];
    int addrlen = backtrace(addrlist, max_frames);

    if (addrlen > 0) {
      o << "\nStack trace:\n";
      char** symbollist = backtrace_symbols(addrlist, addrlen);

      for (int i = 0; i < addrlen; ++i) {
        char* begin_name = nullptr;
        char* begin_offset = nullptr;
        char* end_offset = nullptr;

        // Find function name and offset in backtrace symbol string
        for (char* p = symbollist[i]; *p; ++p) {
          if (*p == '(') {
            begin_name = p;
          } else if (*p == '+') {
            begin_offset = p;
          } else if (*p == ')' && begin_offset) {
            end_offset = p;
            break;
          }
        }

        if (begin_name && begin_offset && end_offset &&
            begin_name < begin_offset) {
          *begin_name++ = '\0';
          *begin_offset++ = '\0';
          *end_offset = '\0';

          int status;
          char* demangled =
              abi::__cxa_demangle(begin_name, nullptr, nullptr, &status);

          o << "  [" << i << "] ";
          if (status == 0) {
            o << demangled << " + " << begin_offset << '\n';
            free(demangled);
          } else {
            o << begin_name << " + " << begin_offset << '\n';
          }
        } else {
          o << "  [" << i << "] " << symbollist[i] << '\n';
        }
      }
      free(symbollist);
    }
  }

  FreppleLog(o.str().c_str());
  exit(sig);
}

int main(int argc, char* argv[]) {
  // Install signal handlers.
  // In a debug build we don't do it, to allow debuggers to handle the
  // signal themselves.
#if !defined(DEBUG)
#ifdef SIGHUP
  signal(SIGHUP, handler);
#endif
#ifdef SIGINT
  signal(SIGINT, handler);
#endif
#ifdef SIGQUIT
  signal(SIGQUIT, handler);
#endif
#ifdef SIGILL
  signal(SIGILL, handler);
#endif
#ifdef SIGABRT
  signal(SIGABRT, handler);
#endif
#ifdef SIGBUS
  signal(SIGBUS, handler);
#endif
#ifdef SIGFPE
  signal(SIGFPE, handler);
#endif
#ifdef SIGKILL
  signal(SIGKILL, handler);
#endif
#ifdef SIGSEGV
  signal(SIGSEGV, handler);
#endif
#ifdef SIGTERM
  signal(SIGTERM, handler);
#endif
#ifdef SIGSTKFLT
  signal(SIGSTKFLT, handler);
#endif
#ifdef SIGXCPU
  signal(SIGXCPU, handler);
#endif
#ifdef SIGXFSZ
  signal(SIGXFSZ, handler);
#endif
#endif

  // Storing the chosen options...
  bool validate = false;
  bool validate_only = false;
  bool input = false;

  try {
    // Analyze the command line arguments.
    for (int i = 1; i < argc; ++i) {
      if (argv[i][0] == '-') {
        // An option on the command line
        if (!strcmp(argv[i], "-validate") || !strcmp(argv[i], "-v"))
          validate = true;
        else if (!strcmp(argv[i], "-check") || !strcmp(argv[i], "-c"))
          validate_only = true;
        else {
          if (strcmp(argv[i], "-?") && strcmp(argv[i], "-h") &&
              strcmp(argv[i], "-help"))
            cout << "\nError: Option '" << argv[i] << "' not recognized.\n";
          usage();
          return EXIT_FAILURE;
        }
      } else {
        // A file or directory name on the command line
        if (!input) {
          // Initialize the library if this wasn't done before
          FreppleInitialize();
          input = true;
        }
        filesystem::path p(argv[i]);
        if (p.extension() == ".py")
          FreppleReadPythonFile(argv[i]);
        else if (p.extension() == ".json")
          FreppleReadJSONFile(argv[i]);
        else
          FreppleReadXMLFile(argv[i], validate, validate_only, true);
      }
    }

    // When no filenames are specified, we read the standard input
    if (!input) {
      FreppleInitialize();
      FreppleReadXMLFile(nullptr, validate, validate_only, true);
    }
  } catch (const exception& e) {
    ostringstream ch;
    ch << "Error: " << e.what();
    FreppleLog(ch.str());
    return EXIT_FAILURE;
  } catch (...) {
    FreppleLog("Error: Unknown exception type");
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
