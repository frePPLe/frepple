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


#include "mod_frepple.h"


int getInventoryFilter(request_rec *r)
{
  try
  {

    // Set the response headers: xml data that can be cached by your browser
    ap_set_content_type(r, "application/xml");
    //xxxapr_table_setn(r->headers_out, "Cache-Control", "max-age=10800");
    apr_table_setn(r->headers_out, "Cache-Control", "no-cache");
    if (r->header_only) return OK;

    // Generating the list of locations
    ap_rputs(
      "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>"
      "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">"
      "<LOCATIONS>\n", r);
    for (Location::iterator l = Location::begin(); l != Location::end(); ++l)
      if (!l->getHidden())
        ap_rprintf(r, "<LOCATION NAME=\"%s\"/>\n", l->getName().c_str());

    // Generating the list of items
    ap_rputs(
      "</LOCATIONS><ITEMS>\n", r);
    for (Item::iterator i = Item::begin(); i != Item::end(); ++i)
      if (!i->getHidden())
        ap_rprintf(r, "<ITEM NAME=\"%s\"/>\n", i->getName().c_str());

    // Generating the list of buffers
    ap_rputs(
      "  </ITEMS><BUFFERS>\n", r);
    for (Buffer::iterator b = Buffer::begin(); b != Buffer::end(); ++b)
      if (!b->getHidden())
        ap_rprintf(r,
                   "<BUFFER NAME=\"%s\" LOCATION=\"%s\" ITEM=\"%s\"/>\n",
                   b->getName().c_str(),
                   b->getLocation() ? b->getLocation()->getName().c_str() : "",
                   b->getItem() ? b->getItem()->getName().c_str() : "");
    ap_rputs("</BUFFERS></PLAN>\n", r);

    return OK;
  }
catch (...) {return HTTP_NOT_FOUND;}
};


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

  // Set up the read policy from the client.
  int rc = ap_setup_client_block(r, REQUEST_CHUNKED_ERROR);
  if (rc != OK) return rc;

  // Tell the client that we are ready to receive content and check whether
  // client will send content.
  char *buffer = NULL;
  unsigned int bodylen = 0;
  if (ap_should_client_block(r))
  {
    // Control will pass to this block only if the request has body content
    char *bufferoffset;
    int bufferspace = r->remaining + 100;
    long res;

    // Reject too big buffers, for safety...
    if (r->remaining > 65536)
    {
      ap_log_rerror(APLOG_MARK, APLOG_ERR, 0, r,
                    "Too big body in request: %d bytes", r->remaining);
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
    if (res < 0) return HTTP_INTERNAL_SERVER_ERROR;

    // Finish the buffer it with a null character
    *bufferoffset = '\0';
    ap_log_rerror(APLOG_MARK, APLOG_ERR, 0, r, "read %d %s", bodylen, buffer);
  }

  // Send the response
  XMLOutputString o;
  o.setContentType(XMLOutput::PLANDETAIL);
  o.writeHeader(Tags::tag_plan);
  o.BeginObject(Tags::tag_buffers);

  // Create a parser
  if (buffer)
  {
    try
    {
      SAX2XMLReader* parser = XMLReaderFactory::createXMLReader();
      ReportFilter handler(Tags::tag_buffer, o, r);
      parser->setProperty(XMLUni::fgXercesScannerName,
                          const_cast<XMLCh*>(XMLUni::fgWFXMLScanner));
      parser->setFeature(XMLUni::fgSAX2CoreNameSpaces, false);
      parser->setFeature(XMLUni::fgSAX2CoreValidation, false);
      parser->setFeature(XMLUni::fgSAX2CoreNameSpacePrefixes, false);
      parser->setFeature(XMLUni::fgXercesIdentityConstraintChecking, false);
      parser->setFeature(XMLUni::fgXercesDynamic, false);
      parser->setFeature(XMLUni::fgXercesSchema, false);
      parser->setFeature(XMLUni::fgXercesSchemaFullChecking, false);
      parser->setFeature(XMLUni::fgXercesValidationErrorAsFatal,true);
      parser->setFeature(XMLUni::fgXercesIgnoreAnnotations,true);
      parser->setContentHandler(&handler);
      parser->setErrorHandler(&handler);
      MemBufInputSource a(reinterpret_cast<const XMLByte*>(buffer), bodylen, "memory buffer", false);
      parser->parse(a);
    }
    catch (exception e)
    {
      ap_log_rerror(APLOG_MARK, APLOG_ERR, 0, r, "Exception preparing report %s", e.what());
      return HTTP_INTERNAL_SERVER_ERROR;
    }
    catch (...)
    {
      ap_log_rerror(APLOG_MARK, APLOG_ERR, 0, r, "Exception preparing report: unknown error");
      return HTTP_INTERNAL_SERVER_ERROR;
    }
  }
  else
  {
    for (Buffer::iterator b = Buffer::begin(); b != Buffer::end(); ++b)
      if (!b->getHidden()) b->writeElement(&o, Tags::tag_buffer);
  }

  // Closing tags
  o.EndObject(Tags::tag_buffers);
  o.EndObject(Tags::tag_plan);

  // Send the result
  ap_rputs(o.getData().c_str(), r);
  return OK;
};


void ReportFilter::startElement (const XMLCh* const uri, const XMLCh* const localname,
                                 const XMLCh* const qname, const Attributes& attrs)
{
  char* c = XMLString::transcode(localname);
  hashtype x = XMLtag::hash(c);
  if (x == tag.getHash())
  {
    // Starting a BUFFER element. Now Pick up the NAME attribute.
    char* name = XMLString::transcode(
                   attrs.getValue(Tags::tag_name.getXMLCharacters())
                 );
    if (name)
    {
      Buffer *bufptr = Buffer::find(name);
      // If the buffer exists, write it.
      if (bufptr) bufptr->writeElement(&o, Tags::tag_buffer);
    }
    XMLString::release(&name);
  }
  XMLString::release(&c);
}

