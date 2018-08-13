===============
Remote commands
===============

All operations from the execution screen can also be launched and
monitored remotely through an web service API.

* `Reference`_
* `Authentication`_
* `Example`_


Reference
---------

The API endpoints can be accessed with any modern web tool or programming 
language using the following URLs. The examples are using the excellent
`curl command line tool <https://curl.haxx.se/>`_.

* Run a task on the default database:

  ::
  
   curl -u <user>:<password> http(s)://<server>:<port>/execute/api/<command>/
     --data "<argument1>=<value1>&<argument2>=<value2>"

* Run a task on a scenario database:

  ::
  
   curl -u <user>:<password> http(s)://<server>:<port>/<scenario>/execute/api/<command>/
     --data "<argument1>=<value1>&<argument2>=<value2>"

* Get the status of all running and pending tasks:

  ::
  
   curl -u <user>:<password> http(s)://<server>:<port>/execute/api/status/

* Get the status of a single task:

  ::
  
   curl -u <user>:<password> http(s)://<server>:<port>/execute/api/status/?id=X

The following commands are available.

* :ref:`runplan`
* :ref:`exporttofolder`
* :ref:`importfromfolder`
* :ref:`runwebservice`
* :ref:`scenario_copy`
* :ref:`backup`
* :ref:`empty`
* :ref:`loaddata`
* :ref:`createbuckets`
* :ref:`openbravo_import`
* :ref:`openbravo_export`

All these APIs return a JSON object and they are asynchronous, i.e. they
don't wait for the actual command to finish. In case you need to wait
for a task to finish, you will need to use a loop which periodically
polls the /execute/api/status URL to monitor the status.


Authentication
--------------

FrePPLe supports 2 methods for authentication of your user in this API:

* | **Basic authentication**
  | See https://en.wikipedia.org/wiki/Basic_access_authentication for more 
    details.
  | With curl you use the argument ``-u USER:PASSWORD`` on the command line. 

* | **JSON Web Token**
  | See https://jwt.io/ for more details.
  | With curl you use the argument ``--header 'Authorization: Bearer TOKEN'``
    on the command line.

We strongly recommend the use of a HTTPS configuration of the frePPLe
server when using this API. Without it your data and login credentials
are sent unencrypted over the internet.


Example
-------

To illustrate the above concepts, this section shows a common workflow to upload
new data in the frePPLe database and generate a new plan.

* Delete previous data files.

* Upload data files (in csv or excel format).

* Import the data files into frePPLe.

* Regenerate the plan with the new data.

This example uses linux bash and curl, but it can easily be coded in
any other modern programming language.

  ::

   #!/bin/bash

    server="localhost:8000"

    #declare -a filelist=("buffer.csv" "item.csv")
    id=0
    output=""
    result=""

    #check the status of a task
    function checkstatus () {
      id=$1
      if (($id>0));
      then
        output=$(curl -u admin:admin http://$server/execute/api/status/?id=$id);
      else
        output=$(curl -u admin:admin http://$server/execute/api/status/);
      fi
      if [[ $output =~ .*Failed || $output =~ .*Done ]];
      then
        output="break";
      else
        output="wait";
      fi
      echo $output
    }

    # you may delete all files or just the ones in the arguments
    # you will have to comment the delete all files locationstable
    # and uncomment the lines above
    function deletefiles () {

      #if you want to delete just the files that you will replace
      # for FILE1 in "${filelist[@]}"; do
      #   FILE2=$(basename "$FILE1")
      #   #spaces should be escaped in the URL
      #   FILE2=${FILE2// /\%20}
      #   result=$(curl -X DELETE -u admin:admin http://$server/execute/deletefromfolder/0/"$FILE2"/);
      # done

      #to delete all files in the folder
      result=$(curl -X DELETE -u admin:admin http://$server/execute/deletefromfolder/0/AllFiles/);
    }

    function waitTillComplete () {
      id=$1
      until [[ $WAIT -eq 0 ]]; do
        if [[ "$(checkstatus $id)" =~ "break" ]]; then
          #show the result
          echo $(curl -u admin:admin http://$server/execute/api/status/?id=$id);
          break
        fi

        sleep "$WAIT_TIME"
        ((WAIT--))
      done
    }

    # create the file list
    # if the argument is a directory it will add all the files there
    # If the arguments are files only these will be added
    for FILE0 in "$@"; do
      if [[ -d "${FILE0}" ]]; then
        cd "${FILE0}"
        filelist=(*.csv *.csv.gz *.xlsx)
      else
        filelist=( $filelist "$FILE0" )
      fi
    done

    #delete files before
    echo -e "\n---------------start delete files----------------"
    deletefiles
    echo "---------------end delete files------------------"

    #upload the files in the list
    echo -e "\n---------------start upload files----------------"
    for FILE1 in "${filelist[@]}"; do
      #get filename without path
      FILE2=$(basename "$FILE1")
      if [[ ! "$FILE2" =~ \*.* ]]; then
        curl -X POST -F "$FILE2=@$FILE1" -u admin:admin http://$server/execute/uploadtofolder/0/
      fi
    done
    echo -e "\n---------------end upload files------------------"

    #import the data in the files
    echo -e "\n---------------start import the data----------------"
    WAIT_TIME=10 #seconds
    WAIT=6 #times
    result=$(curl -X POST -u admin:admin http://$server/execute/api/importfromfolder/)
    id=$(echo "${result//[!0-9]/}")
    waitTillComplete $id
    echo "---------------end import the data------------------"

    #run the plan
    echo -e "\n---------------start planning----------------"
    WAIT_TIME=10 #seconds
    WAIT=6 #times
    result=$(curl -u admin:admin --data "constraint=15&plantype=1&env=fcst,invplan,balancing,supply" http://$server/execute/api/runplan/)
    id=$(echo "${result//[!0-9]/}")
    waitTillComplete $id
    echo "---------------end planning------------------"
