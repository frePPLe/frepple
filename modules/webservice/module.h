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

/** @file module.h
  * @brief Header file for the module webservice.
  *
  * @namespace module_webservice
  * @brief A SOAP webservice to publish frePPLe data as a service.
  *
  * The gSOAP toolkit is used to create a SOAP service for frePPLe.
  *
  * A new command is registered when the module is loaded. The COMMAND_WEBSERVICE
  * runs a multi-threaded SOAP webservice server.
  *
  * The XML schema extension enabled by this module is (see mod_webservice.xsd):
  * <PRE>
  *   <xsd:complexType name="COMMAND_WEBSERVICE">
  *     <xsd:complexContent>
  *       <xsd:extension base="COMMAND">
  *         <xsd:choice minOccurs="0" maxOccurs="unbounded">
  *           <xsd:element name="VERBOSE" type="xsd:boolean" />
  *         </xsd:choice>
  *       </xsd:extension>
  *     </xsd:complexContent>
  *   </xsd:complexType>
  * </PRE>
  */

#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;

// Include auto-generated header file
#include "module_webserviceH.h"

// Settings specific to gsoap
#define BACKLOG (100) // Max. number of backlog requests
#define MAX_QUEUE (1000) // Max. size of request queue


namespace module_webservice
{


/** Initialization routine for the library. */
MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z);


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
    /** Runs the webservice server. */
    void execute();

    /** Returns a descriptive string. */
    string getDescription() const {return "Webservice";}

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

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(CommandWebservice);}
};


}

