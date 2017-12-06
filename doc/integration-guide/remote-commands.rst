===============
Remote commands
===============

All operations from the execution screen can also be launched and
monitored remotely through an web service API.

* `Reference`_
* `Example`_


Reference
---------

Using curl the API endpoints are accessed using the following patterns:

* Run a task on the default database:

   curl -u <user>:<password> http(s)://<server>:<port>/execute/api/<command>/
     --data "<argument1>=<value1>&<argument2>=<value2>"

* Run a task on a scenario database:

   curl -u <user>:<password> http(s)://<server>:<port>/<scenario>/execute/api/<command>/
     --data "<argument1>=<value1>&<argument2>=<value2>"

The following URLs are available.

* | **GET /execute/api/status/**
  | **GET /execute/api/status/?id=<taskid>**:
  | Returns the list of all running and pending tasks. The second format
    returns the details of a specific task.

  Example usage with curl to retrieve status for active task::

      curl -u admin:admin http://localhost:8000/execute/api/status/

  Example usage with curl to retrieve status of task with id 26::

      curl -u admin:admin http://localhost:8000/execute/api/status/?id=26

* | **POST /execute/api/frepple_run/?constraint=15&plantype=1&env=supply**
  | Generates a plan.

  Example usage with curl::

     curl -u admin:admin --data "constraint=15&plantype=1&env=fcst,invplan,balancing,supply" http://localhost:8000/execute/api/frepple_run/

* | **POST /execute/api/frepple_flush/?models=input.demand,input.operationplan**
  | Emptying database for models given in input.

  Example usage with curl::

     curl -u admin:admin --data "models=input.demand,input.operationplan" http://localhost:8000/execute/api/frepple_flush/

* | **POST /execute/api/frepple_importfromfolder/**
  | Load CSV-formatted data files from a configured data folder into the
    frePPLe database.

  Example usage with curl::

     curl -u admin:admin -X POST http://localhost:8000/execute/api/frepple_importfromfolder/

* | **POST /execute/api/frepple_exporttofolder/**
  | Dump planning results in CSV-formatted data files into a configured
    data folder on the frePPLe server.

  Example usage with curl::

     curl -u admin:admin -X POST http://localhost:8000/execute/api/frepple_exporttofolder/

* | **POST /execute/api/loaddata/?fixture=demo**
  | Loads a predefined dataset.

  Example usage with curl::

      curl -u admin:admin --data "fixture=manufacturing_demo" http://localhost:8000/execute/api/loaddata/

* | **POST /execute/api/frepple_copy/?copy=1&source=db1&destination=db2&force=1**
  | Creates a copy of a database into a scenario.

  Example usage with curl::

      curl -u admin:admin --data "copy=1&source=production&destination=scenario1&force=1" http://localhost:8000/execute/api/frepple_copy/

* | **POST /execute/api/frepple_backup/**
  | Backs up the content of the database to a file (which stays on the
    frePPLe application server).

  Example usage with curl::

      curl -u admin:admin -X POST http://localhost:8000/execute/api/frepple_backup/

* | **POST /execute/api/openbravo_import/?delta=7**
  | Execute the Openbravo import connector, which downloads data from Openbravo.

* | **POST /execute/api/openbravo_export/?filter=1**
  | Execute the Openbravo export connector, which uploads data to Openbravo.

* | **POST /execute/api/odoo_import/**
  | Execute the Odoo import connector, which downloads data from Odoo.

* | **POST /execute/api/frepple_createbuckets/?start=2012-01-01&end=2020-01-01&weekstart=1**
  | Initializes the date bucketization table in the database.

All these APIs return a JSON object and they are synchronous, i.e. they
don't wait for the actual command to finish. In case you need to wait
for a task to finish, you will need to use a loop which periodically
polls the /execute/api/status URL to monitor the status.

For security reasons we strongly recommend the use of a HTTPS
configuration of the frePPLe server when using this API.


Example
-------

To illustrate the above concepts, this section shows a common workflow to upload
new data in the frePPLe database and generate a new plan.

* Delete previous data files.

* | Upload data files with curl.
  | The files can be in csv or excel format.

* Import the data from the files to frePPLe.

* Finally regenerate the plan with the new data.

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
    result=$(curl -X POST -u admin:admin http://$server/execute/api/frepple_importfromfolder/)
    id=$(echo "${result//[!0-9]/}")
    waitTillComplete $id
    echo "---------------end import the data------------------"

    #run the plan
    echo -e "\n---------------start planning----------------"
    WAIT_TIME=10 #seconds
    WAIT=6 #times
    result=$(curl -u admin:admin --data "constraint=15&plantype=1&env=fcst,invplan,balancing,supply" http://$server/execute/api/frepple_run/)
    id=$(echo "${result//[!0-9]/}")
    waitTillComplete $id
    echo "---------------end planning------------------"
