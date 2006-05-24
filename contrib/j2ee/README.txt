
This directory includes a framework to use Frepple in a J2EE environment.
The project is built in the ECLIPSE IDE and uses JBOSS as the application 
server.

It includes functionality to support the following J2EE technologies:

  - JMS, Java Messaging System
    A message-driven bean is defined that receives XML-formatted
    JMS text-messages, and passes them to frepple for processing.
    This example uses JBOSSMQ as the JMS provider, but it shouldn't
    be difficult to adjust to other providers.

  - EJB, Enterprise Java Bean
    This bean acts as a simple wrapper in the form of an enterprise
    java entity bean.
    
  - Webservice
    The EJB mentioned above can easily be deployed as a web service
    in JBOSS.
    
  - Webservice client
    This is a test client that connects to the frepple webservice,
    which can be implemented either as a java or a C++ webservice.
    
 Good Luck! 
