/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007 by Johan De Taeye, frePPLe bvba                                    *
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
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

/** @file module.h
  * @brief Header file for the module webservice.
  *
  * @namespace module_webservice
  * @brief A SOAP webservice to publish frePPLe data as a service.
  *
  * The gSOAP toolkit is used to create a SOAP service for frePPLe.
  *
  * A new Python extension is added to run a multi-threaded SOAP webservice
  * server.
  */

#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;

#include "soapH.h"


// Settings specific to gsoap
#define BACKLOG (100) // Max. number of backlog requests
#define MAX_QUEUE (1000) // Max. size of request queue


namespace module_webservice
{


/** Initialization routine for the library. */
MODULE_EXPORT const char* initialize(const Environment::ParameterList& z);


/** @brief This command runs a multi-threaded SOAP webservice server.
  *
  */
class CommandWebservice : public Command
{
  private:
    /** Port number for the server. */
    static unsigned int port;

    /** Number of threads to handle requests. */
    static unsigned int threads;

    /** Worker function for the threads. */
    static void *process_queue(void*);

    /** Put a new connection in the queue. */
    int enqueue(SOAP_SOCKET);

    /** Pick a connection from the queue. */
    SOAP_SOCKET dequeue();

    struct thread_data
    {
      public:
        CommandWebservice* master;
        struct soap *soap_thr; // each thread needs a soap runtime environment
        pthread_t tid;
        unsigned int index;
    };


    SOAP_SOCKET queue[MAX_QUEUE]; // The global request queue of sockets
    int head;
    int tail; // Queue head and tail
    pthread_mutex_t queue_cs;
    pthread_cond_t queue_cv;

  public:
    /** Python interface for the webservice server. */
    static PyObject* pythonService(PyObject*, PyObject*);

    /** Runs the webservice server. */
    void commit();

    /** Returns a descriptive string. */
    string getDescription() const {return "frePPLe webservice";}

    /** Default constructor. */
    explicit CommandWebservice() : head(0), tail(0) {}

    /** Destructor. */
    virtual ~CommandWebservice() {}

    /** Returns the port number. */
    static unsigned int getPort() {return port;}

    /** Updates the port number. */
    static void setPort(int i)
    {
      if (i <= 0 || i>65535)
        throw DataException("Invalid port number: valid range is 1 - 65535");
      port = i;
    }

    /** Returns the number of threads for the server. */
    static unsigned int getThreads() {return threads;}

    /** Updates the number of threads for the server. */
    static void setThreads(int i)
    {
      if (i <= 0 || i>100)
        throw DataException("Invalid number of threads: valid range is 1 - 100");
      threads = i;
    }
};


}

