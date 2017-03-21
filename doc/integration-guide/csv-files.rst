==============
CSV text files
==============

FrePPLe can import CSV-formatted files from a configurable data directory.
And frePPLe can export its planning results in a set of CSV-formatted files as well.

The files are all placed in a folder that is configurable with the UPLOADFILEFOLDER
in the djangosettings.py configuration file. The log files importfromfolder.log 
and exporttofolder.log record all data imports and file exports, together with
any data errors identified during their processing.

The data files to be imported must meet the following criteria:

* | The file name must start with the name of the data object they store.
  | The file name must end with the extension .csv or or .csv.gz. Files
    with the extension .csv.gz are expected to compressed in gzip format.
  | Some examples of valid file names are item.csv.gz, item.csv, demand.csv,
    demand.part1.csv
    
* The first line of the file should contain the field names

* The file should be in CSV format. The delimiter depends on the default
  language (configured with LANGUAGE_CODE in djangosettings.py).
  For english-speaking countries it's a comma. For European countries
  it's a semicolon.

* The file should be encoded in UTF-8 (configurable with the CSV_CHARSET
  setting in djangosettings.py)
  
The export can be customized, i.e. export only the relevant data and with the 
a specific format (file names, dates, separators, ...). The customization is 
done by copying the frepple_exporttofolder.py file and updating the SQL 
statements it contains.

The export and import can be run in 2 ways:

* In the user interface a user can interactively launch the task in 
  the :doc:`execution screen </user-guide/user-interface/execute>`.

* You can run the task from the command line using the 
  :doc:`frepplectl utility</integration-guide/batch-commands>`.

  ::
  
     frepplectl frepple_exporttofolder
     
     frepplectl frepple_importfromfolder
