import os, sys, inspect
from datetime import datetime

from django.db import DEFAULT_DB_ALIAS
from django.conf import settings

# Auxilary functions for debugging
def debugResource(res,mode):
  # if res.name != 'my favorite resource': return 
  print "=> Situation on resource", res.name
  for j in res.loadplans:
    print "=>  ", j.quantity, j.onhand, j.startdate, j.enddate, j.operation.name, j.operationplan.quantity, j.setup
    
def debugDemand(dem,mode):
  if dem.name == 'my favorite demand': 
    print "=> Starting to plan demand ", dem.name
    solver.loglevel = 2
  else:
    solver.loglevel = 0
 
# Send the output to a logfile
try: db = os.environ['FREPPLE_DATABASE'] or DEFAULT_DB_ALIAS
except: db = DEFAULT_DB_ALIAS
if db == DEFAULT_DB_ALIAS:
  frepple.settings.logfile = os.path.join(os.environ['FREPPLE_APP'],'frepple.log')
else:
  frepple.settings.logfile = os.path.join(os.environ['FREPPLE_APP'],'frepple_%s.log' % db)

# use the test database if we are running the test suite
if 'FREPPLE_TEST' in os.environ:
  settings.DATABASES[db]['NAME'] = settings.DATABASES[db]['TEST_NAME']
  if 'TEST_CHARSET' in os.environ:
    settings.DATABASES[db]['CHARSET'] = settings.DATABASES[db]['TEST_CHARSET']
  if 'TEST_COLLATION' in os.environ:
    settings.DATABASES[db]['COLLATION'] = settings.DATABASES[db]['TEST_COLLATION']
  if 'TEST_USER' in os.environ:
    settings.DATABASES[db]['USER'] = settings.DATABASES[db]['TEST_USER']
  
# Create a solver where the plan type are defined by an environment variable
try: plantype = int(os.environ['PLANTYPE'])
except: plantype = 1  # Default is a constrained plan
try: constraint = int(os.environ['CONSTRAINT'])
except: constraint = 15  # Default is with all constraints enabled
solver = frepple.solver_mrp(name="MRP", 
  constraints=constraint, 
  plantype=plantype, 
  #userexit_resource=debugResource,
  #userexit_demand=debugDemand,
  loglevel=0
  )
print "Plan type: ", plantype
print "Constraints: ", constraint

# Welcome message
if settings.DATABASES[db]['ENGINE'] == 'django.db.backends.sqlite3':
  print "frePPLe on %s using sqlite3 database '%s'" % (
    sys.platform, 
    'NAME' in settings.DATABASES[db] and settings.DATABASES[db]['NAME'] or ''
    )
else:
  print "frePPLe on %s using %s database '%s' as '%s' on '%s:%s'" % (
    sys.platform,
    'ENGINE' in settings.DATABASES[db] and settings.DATABASES[db]['ENGINE'] or '', 
    'NAME' in settings.DATABASES[db] and settings.DATABASES[db]['NAME'] or '',
    'USER' in settings.DATABASES[db] and settings.DATABASES[db]['USER'] or '',
    'HOST' in settings.DATABASES[db] and settings.DATABASES[db]['HOST'] or '',
    'PORT' in settings.DATABASES[db] and settings.DATABASES[db]['PORT'] or ''
    )

print "\nStart loading data from the database at", datetime.now().strftime("%H:%M:%S")
frepple.printsize()
from freppledb.execute.load import loadfrepple
loadfrepple()
frepple.printsize()
  
if 'solver_forecast' in [ a for a, b in inspect.getmembers(frepple) ]:
  # The forecast module is available
  print "\nStart forecast netting at", datetime.now().strftime("%H:%M:%S")
  frepple.solver_forecast(name="Netting orders from forecast",loglevel=0).solve()

print "\nStart plan generation at", datetime.now().strftime("%H:%M:%S")
solver.solve()
frepple.printsize()

#print "\nStart exporting static model to the database at", datetime.now().strftime("%H:%M:%S")
#from freppledb.execute.export_database_static import exportfrepple as export_static_to_database
#export_static_to_database()

print "\nStart exporting plan to the database at", datetime.now().strftime("%H:%M:%S")
if settings.DATABASES[db]['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
  from freppledb.execute.export_database_plan_postgresql import exportfrepple as export_plan_to_database
else:
  from freppledb.execute.export_database_plan import exportfrepple as export_plan_to_database
export_plan_to_database()

#print "\nStart saving the plan to flat files at", datetime.now().strftime("%H:%M:%S")
#from freppledb.execute.export_file_plan import exportfrepple as export_plan_to_file
#export_plan_to_file()

#print "\nStart saving the plan to an XML file at", datetime.now().strftime("%H:%M:%S")
#frepple.saveXMLfile("output.1.xml","PLANDETAIL")
#frepple.saveXMLfile("output.2.xml","PLAN")
#frepple.saveXMLfile("output.3.xml","STANDARD")

#print "Start deleting model data at", datetime.now().strftime("%H:%M:%S")
#frepple.erase(True)
#frepple.printsize()

print "\nFinished planning at", datetime.now().strftime("%H:%M:%S")
