package frepple.mail;
import java.io.*;
import java.util.*;
import javax.mail.*;

import org.apache.log4j.Logger;

import frepple.jms.MessageBean;

/** This class uses the JavaMail to read email messages from a POP3 or IMAP
  * mail server, and pass them to on to frepple.
  *  
  * The program is intended as a standalone java application. The application 
  * will poll the mail server with a predefined frequency to read new messages.
  * Messages with MIME types "text/plain" and "application/xml" will be 
  * passed as XML input data to frepple.
  * To garantuee the correct order of the data commands, the messages are 
  * processed in a single thread in the order they are present in the 
  * specified mail folder.
  *  
  * The following configuration parameters are read in from the property 
  * file mail.properties:
  *  - protocol: mail protocol, typically "pop3" or "imap"
  *  - mailhost: host name or ip adress of the mail server
  *  - user: user name to log in at the mail server
  *  - password: password for the above user
  *  - folder: Folder names from which to read messages. 
  *            The normal value is "INBOX".
  *  - polling: Specifies the polling interval (in seconds) of the program.
  *             The default value is 300. 
  */
public class Reader extends TimerTask 
{
  
  static Properties props = new Properties();
  static boolean running = false; 
  private static Logger log = Logger.getLogger(Reader.class);

  /** */
  public static void main(String[] args) {
    
    // Load the properties
    try { props.load(new FileInputStream("mail.properties")); }
    catch (Exception e1)
    {
      log.error("Error reading configuration file 'mail.properties'!", e1);
      System.exit(1);
    }
    
    // Pick up the polling frequency
    int polling = 300;
    try {polling = new Integer(props.getProperty("polling")).intValue();} 
    catch (NumberFormatException e2)
    {log.error("Invalid polling interval.",e2);}
    if (polling <= 0) polling = 300; 
    
    // Report the parameters
    log.info("Starting frepple mail client with paramters:");
    log.info("   Protocol: " + props.getProperty("protocol"));
    log.info("   Hostname: " + props.getProperty("mailhost"));
    log.info("   User: " + props.getProperty("user"));
    log.info("   Folder: "+ props.getProperty("folder"));
    log.info("   Polling: " + polling + " seconds");

    // Polling loop
    Timer t = new Timer();
    t.scheduleAtFixedRate(new Reader(), 0, polling * 1000);
    	
  }

  
  /** This method is the workhorse of this class. It will connect to the mail
    * server and read new incoming messages. 
    */
  public void run()
  {
    // Check if the previous run is still running
    if (running == true) return;
    running = true;
    
    Folder folder = null;
    try 
    {
      // Create a session
      log.debug("Initialize connection to the mail server");
      Session session = Session.getDefaultInstance(System.getProperties(), null);
      Store store = session.getStore(props.getProperty("protocol"));
      store.connect(props.getProperty("mailhost"), 
          props.getProperty("user"),
          props.getProperty("password"));
      
      // Navigate to the proper folder 
      folder = store.getDefaultFolder();
      folder = folder.getFolder(props.getProperty("folder"));
      folder.open(Folder.READ_WRITE);
      log.debug("Connected...");
      log.debug("Retrieving messages...");
      
      // Process the messages
      Message[] msgs = folder.getMessages();
      if (msgs != null)
      {
        for (int i = 0; i < msgs.length; ++i)
        {	
          log.debug("Processing message " + i + ": ");
          if (msgs[i].isMimeType("text/plain") 
              || msgs[i].isMimeType("application/xml"))
            try 
            {
              String data = (String) msgs[i].getContent();
              System.out.println("OK" + data);
              // The message will only be deleted upon successfull processing of the data
              msgs[i].setFlag(Flags.Flag.DELETED, true);
            } catch (Exception e) {
              log.error("Exception thrown processing the message",e);
            }
          else
            log.debug("Skipping, invalid MIME type " 
                  + msgs[i].getContentType());
        }
      }
      log.debug("Closing connection...");
      folder.close(true);
    } catch (MessagingException e) 
    {
      try {folder.close(true);} catch (Exception e1){}
      log.error("Exception thrown accessing the mail server", e);
    }
    
    // Nothing is running any more...
    running = false;
  }
  
}
