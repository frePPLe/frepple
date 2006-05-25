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


#include "mod_frepple.h"


char *reportdata =
  "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>"
  "<PLAN>"
  "  <BUFFERS>"
  "    <BUFFER NAME=\"1\">"
  "      <LOCATION NAME=\"Location 1\"/>"
  "      <ITEM NAME=\"item 1\"/>"
  "			<LEVEL>1</LEVEL>"
  "			<CLUSTER>1</CLUSTER>"
  "						<PROFILE>"
  "							<FLOW>"
  "								<DATE>2005-01-31T00:00:00</DATE>"
  "								<QUANTITY>-1</QUANTITY>"
  "								<ONHAND>-1</ONHAND>"
  "								<MINIMUM>0</MINIMUM>"
  "								<ID>55</ID>"
  "							</FLOW>"
  "      </PROFILE>"
  "    </BUFFER>"
  "    <BUFFER NAME=\"2\">"
  "      <LOCATION NAME=\"Location 2\"/>"
  "      <ITEM NAME=\"item 2\"/>"
  "    </BUFFER>"
  "    <BUFFER NAME=\"3\">"
  "      <LOCATION NAME=\"Location 3\"/>"
  "      <ITEM NAME=\"item 1\"/>"
  "    </BUFFER>"
  "  </BUFFERS>"
  "</PLAN>";
  

#define BLOCKSIZE 256


// Forward declaration of the module structure
extern "C" module AP_MODULE_DECLARE_DATA frepple_module;


// Creating configuration structure for the server
static void* create_server_config(apr_pool_t *p, server_rec *s)
{
  server_config *conf = 
    (server_config *) apr_pcalloc(p, sizeof(server_config));
  conf->home = NULL;
  return conf;
}


// Creating configuration structure for a directory
static void *create_directory_config(apr_pool_t *p, char *dummy)
{
  dir_config *conf = 
    (dir_config *) apr_pcalloc(p, sizeof(dir_config));
  conf->method = REPORT;
  conf->directory = NULL;
  return conf;
}


// Called during the parsing of the FreppleHome directive
static const char *setHome(cmd_parms *cmd, void *cfg, const char *value)
{
  server_rec *s = cmd->server;
  server_config *conf =
    (server_config*) ap_get_module_config(s->module_config, &frepple_module);

  // Find home directory as relative to the server root
  const char *cfgFile = ap_server_root_relative(cmd->pool, value);
  if (!cfgFile)
    return apr_pstrcat
      (cmd->pool, "Invalid frepple configuration ", value, NULL);

  conf->home = apr_pstrdup(cmd->pool, cfgFile);  
  return NULL;
}


static const char *add_options
  (cmd_parms *cmd, void *in_dc, const char *arg1, const char *arg2)
{
  dir_config *dc = (dir_config*) in_dc;
  if (!strcasecmp(arg1,"REPORT"))
    dc->method = REPORT;
  else if (!strcasecmp(arg1,"UPLOAD"))
    dc->method = UPLOAD;
  else if (!strcasecmp(arg1,"COMMAND"))
  {
    dc->method = COMMAND;
    if (!arg2)
      return apr_pstrcat(cmd->temp_pool, "Missing second argument for  FreppleMethod COMMAND", NULL);
    dc->directory = apr_pstrdup(cmd->pool, arg2);
  }
  else
    return apr_pstrcat(cmd->temp_pool, "Invalid FreppleMethod ", arg1, NULL);
  return NULL;
}


// Definition of the configuration parameters
typedef const char* (*func)();
static const command_rec info_cmds[] =
{
  AP_INIT_TAKE12("FreppleMethod", (func)add_options, NULL, ACCESS_CONF,
      "Possible ways of working: REPORT, COMMAND <dir>, UPLOAD"),
  AP_INIT_TAKE1("FreppleHome", (func) setHome, NULL, RSRC_CONF,
      "The home directory"),
  {NULL}
};


// The workhorses!!!
int getInventoryData(request_rec *r)
{
  const char* buf ;
  apr_size_t bytes ;
  apr_bucket_brigade* bb ;
  int status = 0 ;
  apr_bucket* b ;
  int end = 0 ;
  
  // Response header: xml data that can't be cached.
  ap_set_content_type(r, "text/xml");
  apr_table_setn(r->headers_out, "Cache-Control", "no-cache"); 

	/* Set up the read policy from the client.*/
	int rc = ap_setup_client_block(r, REQUEST_CHUNKED_ERROR);
  if (rc != OK) return rc;

  // Tell the client that we are ready to receive content and check whether 
  // client will send content.  
  if (ap_should_client_block(r)) 
  {
    //Control will pass to this block only if the request has body content
    char *buffer;
    char *bufferoffset;
    int bufferspace = r->remaining + 100;
    int bodylen = 0;
    long res;
    
    // Reject too big buffers, for safety... 
    if (r->remaining > 65536) 
    {
      ap_log_rerror(APLOG_MARK, APLOG_ERR, 0, r, 
       "Client sends too big body in request: %d bytes", r->remaining);
      return HTTP_REQUEST_ENTITY_TOO_LARGE;
    }

    // Allocate a buffer in memory
    buffer = static_cast<char*>(apr_palloc(r->pool, bufferspace));
    bufferoffset = buffer;

    // Fill the buffer with client data
    while ((!bodylen || bufferspace >= 32) &&
             (res = ap_get_client_block(r, bufferoffset, bufferspace)) > 0)
    {
      bodylen += res;
      bufferspace -= res;
      bufferoffset += res;
    }

    // Finish the buffer it with \0 character
    *bufferoffset = '\0';

    ap_log_rerror(APLOG_MARK, APLOG_ERR, 0, r, "read %d %s", bodylen, buffer);

    if (res < 0) return HTTP_INTERNAL_SERVER_ERROR;
  }

  // Fake up the response
  ap_rputs(reportdata, r);
  return OK;
};


// Main dispatcher routine which will call the correct generator routine.
static int display_info(request_rec *r)
{
  // Another handler's job...
  if (strcmp(r->handler, "frepple")) return DECLINED;

  // Only handle GET requests
  //r->allowed |= (AP_METHOD_BIT << M_GET);
  //if (r->method_number != M_GET) return DECLINED;

  // Determine the frepple action for this directory
  dir_config *cfg =
    (dir_config *) ap_get_module_config(r->per_dir_config, &frepple_module);
  switch (cfg->method)
  {

    // ACTION 1: Retrieving report data
    // The possible reports have pre-defined, hard-coded names.
    case REPORT:
      if (!strcmp(r->path_info,"/inventorydata.xml"))
        return getInventoryData(r);  
      else if (!strcmp(r->path_info,"/inventoryfilter.xml"))
        return getInventoryFilter(r);
      break;

    // ACTION 2: Uploading data from the request into frepple
    case UPLOAD:
      break;

    // ACTION 3: Execute a command file in frepple
    case COMMAND:
      string c = cfg->directory;
      c += r->path_info;
      ap_set_content_type(r, "text/html");
      try
      {
        // Execute the command file
        FreppleReadXMLFile(c.c_str(), true, false);
        ap_rputs("Success", r);
      }
      catch (exception e)
      {
        ap_rprintf(r, "Error: %s", e.what());
      }
      catch (...)
      {
        ap_rputs("Error: no details", r);
      }
      return OK;
  }

  // This code is only executed if the above dispatcher code can't locate
  // a proper function to dispatch the action to.
  ap_log_rerror(APLOG_MARK, APLOG_ERR, 0, r, "URL doesn't exist: %s", r->uri);
  return HTTP_NOT_FOUND;
}


// A message to be displayed at startup
static int welcome 
  (apr_pool_t *p, apr_pool_t *plog, apr_pool_t *ptemp, server_rec *s)
{
  server_config *conf =
    (server_config*) ap_get_module_config(s->module_config, &frepple_module);
  try
  {
    FreppleWrapperInitialize(conf->home);
    ap_log_error(APLOG_MARK, APLOG_INFO, 0, s, "mod_frepple: Initialized");
    return OK;
  } catch (...) {
    ap_log_error(APLOG_MARK, APLOG_ALERT, 0, s, "mod_frepple: Initialization failed");
    return OK;
  } 
}


// Registration of the hooks
static void register_hooks(apr_pool_t *p)
{
  // The content generator
  ap_hook_handler(display_info, NULL, NULL, APR_HOOK_MIDDLE);
  
  // Initialization hook
  ap_hook_open_logs(welcome, NULL, NULL, APR_HOOK_MIDDLE);  
}


// The Apache magic structure...
extern "C" {
  module AP_MODULE_DECLARE_DATA frepple_module =
  {
    STANDARD20_MODULE_STUFF,
    create_directory_config,    /* dir config creater */
    NULL,                       /* dir merger --- default is to override */
    create_server_config,       /* server config */
    NULL,                       /* merge server config */
    info_cmds,                  /* command apr_table_t */
    register_hooks              /* hook registration function */
  };
}
