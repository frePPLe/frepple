/***************************************************************************
 file : $URL$
 version : $LastChangedRevision$  $LastChangedBy$
 date : $LastChangedDate$
 email : johan_de_taeye@yahoo.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2004 by Johan De Taeye                                    *
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
package frepple.servlet;

import javax.servlet.http.HttpServlet;

import java.io.IOException;
import java.io.PrintWriter;
import java.net.URL;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.xml.transform.Source;
import javax.xml.transform.Templates;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;

import org.apache.log4j.Logger;
import frepple.backend.ConnectionFactory;
import frepple.backend.api;

/** This servlet is used to update data in the frepple backend.
 */
public class Output extends HttpServlet {

	private static final long serialVersionUID = 1L;
	private api connection = null;  
    private int count = 0;
    private Templates stylesheet;
    
    public final static String FS = System.getProperty("file.separator");
    private static Logger log = Logger.getLogger(Output.class);
        
    public void init(ServletConfig config) throws ServletException {
        super.init(config);

        log.info("Initializing Output servlet");

        // Initialize the connection to the backend
        try {
            connection = ConnectionFactory.create();
        } catch (Exception e) {
            e.printStackTrace();
        }  

        // Initialize the XSLT processor
        /*  @todo cleanup
         *  
         * -> Pick up all xslt and their context path from a properties file
         * -> Load all xslt transformers on init
         * -> Incoming request have a relative path 
         * 			/frepple/output/demand/...
         *          /frepple/output/buffer/... 
         * -> We can derive the required xslt 
         * -> how do we get the XML in a consistent and flexible way?
         *
        TransformerFactory transFact = TransformerFactory.newInstance( );
        String curName = null;
        try {
            curName = "/WEB-INF/xslt/test.xslt";
            URL xsltURL = getServletContext( ).getResource(curName);
            String xsltSystemID = xsltURL.toExternalForm( );
            stylesheet = transFact.newTemplates(new StreamSource(xsltSystemID));            
        } catch (TransformerConfigurationException tce) {
            log("Unable to compile stylesheet", tce);
            throw new ServletException("Unable to compile stylesheet");
        } catch (MalformedURLException mue) {
            log("Unable to locate XSLT file: " + curName);
            throw new ServletException(
                    "Unable to locate XSLT file: " + curName);
        }
        
        @todo set proper classpath, and set correct jaxp / xalan properties
        */
    }

    public String getServletInfo() {
        return "Servlet info";
    }

    protected void doGet(HttpServletRequest request,
            HttpServletResponse response) throws IOException,
            ServletException {
        
        log.debug("Receiving request " + request.getLocalName());

        // Set the response headers
        response.setContentType("text/html; charset=UTF-8");
        
        // Output goes in the response stream.
        PrintWriter out = response.getWriter();
        out.println("<html><body>");

        // Run the transform
        try {
            TransformerFactory tFactory = TransformerFactory.newInstance();
            //get the real path for xml and xsl files.
            String ctx = getServletContext().getRealPath("") + FS;
            // Get the XML input document and the stylesheet.
            Source xmlSource = new StreamSource(new URL("file", "", ctx+"WEB-INF"+FS+"xslt"+FS+"test.xml").openStream());
            Source xslSource = new StreamSource(new URL("file", "", ctx+"WEB-INF"+FS+"xslt"+FS+"test.xslt").openStream());
            // Generate the transformer.
            Transformer transformer = tFactory.newTransformer(xslSource);
            // Perform the transformation, sending the output to the response.
            transformer.transform(xmlSource, new StreamResult(out));            
        } catch (Exception ex) {
            out.println("<h1>An Error Has Occurred</h1><pre>");
            out.write(ex.getMessage());
            ex.printStackTrace(out);
            out.println("</pre>");
        }
        
        // Finalize
        out.println("</body></html>");
        out.close();
    }

}
