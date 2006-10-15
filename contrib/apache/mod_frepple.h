/***************************************************************************
  file : $URL: file:///C:/develop/SVNrepository/frepple/trunk/contrib/scripting/frepple.i $
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

// Apache include files
// It is important to use "" instead of <>
#include "httpd.h"
#include "http_config.h"
#include "http_core.h"
#include "http_log.h"
#include "http_main.h"
#include "http_protocol.h"
#include "http_request.h"
#include "apr_strings.h"
#include "apr_tables.h"

// Frepple include files
#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;

// Forward declarations of functions
int getInventoryFilter(request_rec *r);
int getInventoryData(request_rec *r);

// Data type for the frepple way-of-working
typedef enum
{
  REPORT = 0,
  COMMAND = 1,
  UPLOAD = 2
} ActionType;

typedef struct {
  ActionType method;
  char *directory;
} dir_config;

// Data structure for configuration data
typedef struct {
  char *home;
} server_config;


// Handler for parsing the report filter
class ReportFilter : public DefaultHandler
{    
  public:
    void startElement (const XMLCh* const, const XMLCh* const,
      const XMLCh* const, const Attributes&);
    ReportFilter(const XMLtag& t, XMLOutput &oo, request_rec *r) 
      : tag(t), req(r), o(oo) {};
  private:
    const XMLtag &tag;
    request_rec *req;
    XMLOutput &o;
};
