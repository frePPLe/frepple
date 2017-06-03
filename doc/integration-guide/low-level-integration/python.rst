==========
Python API
==========

FrePPle embeds an interpreter for the `Python`_ programming language. 
The full capabilities of this scripting language and its rich library
are accessible from frePPLe, and Python also has access to the frePPLe
objects in memory.

Python is thus a very powerful way to interact with the planning engine.
For complex data integration tasks and for customization of the algorithms
Python is your big friend.

Here's a simple annotated example of a Python script that is executed
by the planning engine:

  .. code-block:: Python
  
      # Loads the planning engine as a Python module.
      import frepple
      
      # Use the standard Python module to read a CSV-formatted text file
      import csv
      with open('products.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        for row in csvreader:
          # The next line creates an item object in the frePPle core
          # planning engine.
          frepple.item(name=row[0], description=row[1])
      
      # Call the planning engine solver to create a fully constrained plan
      frepple.solver_mrp(plantype=1, constraints=15, loglevel=2).solve()
      
      # Echo the plan resultsto the screen: load of all resources 
      for i in frepple.resources():      
        for j in i.loadplans:
          print(j.operationplan.id, j.resource.name, j.quantity, j.startdate, j.enddate)
      
      # Echo the plan resultsto the screen: inventory profile of all buffers 
      for i in frepple.buffers():      
        for j in i.flowplans:
          print(j.operationplan.id, j.buffer.name, j.quantity, j.date, j.onhand)


You can execute a Python script either from the planning engine's 
executable frepple(.exe), or you can run it from the standard Python 
executable and load the planning engine as an extension module.

There are plenty of sample Python scripts available:

- | A very nice example is the code where the planning engine reads 
    from the PostgreSQL database: https://github.com/frePPLe/frePPLe/blob/master/freppledb/input/commands.py
  | An SQL statement is executed, and in the loop over the resulting records
    we create the objects in the planning engine's memory. 
  
- | Another example is the code to write the plan results from the planning
    engine's memory back to the database: https://github.com/frePPLe/frePPLe/blob/master/freppledb/execute/export_database_plan.py
  | We loop over the relevant objects in memory, and send it to a PostgreSQL
    copy/insert/update command. 
   
.. _`Python`: https://www.python.org/
