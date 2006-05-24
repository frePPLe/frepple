/***************************************************************************
 file : $URL$
 version : $LastChangedRevision$  $LastChangedBy$
 date : $LastChangedDate$
 email : johan_de_taeye@yahoo.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2005 by Johan De Taeye                                    *
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

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.net.URL;
import java.util.Enumeration;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.Source;
import javax.xml.transform.Templates;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;

import org.apache.log4j.Logger;
import org.w3c.dom.Document;

import frepple.backend.ConnectionFactory;
import frepple.backend.api;

/**
 * This servlet is used to update data in the frepple backend.
 */
public class Update extends HttpServlet {

	private static final long serialVersionUID = 1L;
	private api connection = null; // todo the servlet should use the ejb
                                   // instead?

    private int count = 0;

    private static Logger log = Logger.getLogger(Update.class);

    private Templates xslt = null;

    private Document doc = null;

    public final static String FS = System.getProperty("file.separator");

    /*
     * -> Add config file with all XML and XSLT data files -> Incoming request
     * have a relative path /frepple/output/demand/...
     * /frepple/output/buffer/... -> We can derive the required xslt -> The
     * resulting xml then has to be sent to the backend either synchroneously
     * over webservice either asynchroneously over JMS
     * 
     * Should this transforming process be part of a servlet? Or is it part of a
     * more generic "backend preprocessor"? e.g. also webservice data may
     * benefit from such preprocessing... input would in flexible ways, and the
     * resulting xml is sent to the backend and result returned? Java or c++?
     */
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        log.info("Initializing Update servlet");
        String ctx = getServletContext().getRealPath("") + FS;

        // Build a DOM document
        try {
            // Get a Document Builder Factory
            DocumentBuilderFactory factory = DocumentBuilderFactory
                    .newInstance();
            // Turn on validation, and turn off namespaces
            factory.setValidating(true);
            factory.setNamespaceAware(false);
            DocumentBuilder builder = factory.newDocumentBuilder();
            doc = builder.parse(new File(ctx + "WEB-INF" + FS + "xslt" + FS
                    + "test.xml"));
        } catch (Exception e) {
            e.printStackTrace();
        }

        // Create a backend connection
        try {
            connection = ConnectionFactory.create();
        } catch (Exception e) {
            e.printStackTrace();
        }

        // Create XSLT transformers
        try {
            TransformerFactory tFactory = TransformerFactory.newInstance();
            //get the real path for xml and xsl files.
            //String ctx = getServletContext().getRealPath("") + FS;
            // Get the XML input document and the stylesheet.
            Source xslSource = new StreamSource(new URL("file", "", ctx
                    + "WEB-INF" + FS + "xslt" + FS + "test.xslt").openStream());
            // Generate the transformer.
            xslt = tFactory.newTemplates(xslSource);
        } catch (Exception ex) {
            log.error("Failed creating initializing the transformers", ex);
        }

    }

    public String getServletInfo() {
        return "Servlet to update data in the frepple backend";
    }

    protected void doGet(HttpServletRequest req, HttpServletResponse response)
            throws IOException, ServletException {
        doPost(req, response);
    }

    protected void doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {

        // Logging the request
        log.debug("Receiving " + req.getMethod() + " request "
                + req.getRequestURI() + "  " + req.getQueryString());

        // Set the response headers
        resp.setContentType("application/xml;");

        // Output goes in the response stream.
        PrintWriter out = resp.getWriter();

        // Run the transform
        try {
            // Get the XML and XSLT source.
            // The XML source is a DOM document in memory.
            // The XSLT source is a precompiled stylesheet.
            Source xmlSource = new javax.xml.transform.dom.DOMSource(doc);
            Transformer transformer = xslt.newTransformer();

            // Pass the parameters in the http request to the xslt stylesheet
            String param;
            String value;
            for (Enumeration params = req.getParameterNames(); params
                    .hasMoreElements();) {
                param = (String) params.nextElement();
                value = req.getParameter(param);
                if (value != null)
                    transformer.setParameter(param, value);
            }

            // Perform the transformation, sending the output to the response.
            transformer.transform(xmlSource, new StreamResult(out));
        } catch (Exception ex) {
            // Transformation failed
            // Log to error log
            log.error("Transformation error when processing" + req.getMethod()
                    + " request " + req.getRequestURI() + "  "
                    + req.getQueryString() + " from client ip-adress "
                    + req.getRemoteHost(), ex);
            // Log to client
            out.println("<h1>An Error Has Occurred</h1><pre>");
            out.write(ex.getMessage());
            out.println("</pre>");
        }

        // Finalize
        out.close();
    }

}
