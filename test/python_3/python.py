
import datetime

print "Updating global plan information"
frepple.plan.name = "demo model"
frepple.plan.description = unicode( "demo description in unicode object")
frepple.plan.current = datetime.datetime(2007,1,1)

print frepple.buffer_default
print "Creating buffers"
x = frepple.buffalo(name="test", description="pol", category="tttt")
print x.name
x.name = "ppppppp"
print x.name
print x
#print "p", x.name
#print "q", x.description
#

print "Plan name:", frepple.plan.name
print "Plan description:", frepple.plan.description
print "Plan current:", frepple.plan.current
frepple.saveXMLfile("puree.txt")