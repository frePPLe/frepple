
# Defining a function. The function is available during the complete
# lifetime of the interpreter, which is not restricted to a single
# command
def my_function(x):
	return x * x

def read_csv_file():
  # This function reads a CSV-formatted file, creates an XML string and
  # then passes the string to Frepple for processing
  csvin = open('items.csv','r')
  try:
    x = csvin.readlines()
    for l in range(len(x)):
      fields = x[l].strip().split(',')
      x[l] = '<ITEM NAME="%s"><OPERATION NAME="%s"/></ITEM>' % (fields[0],fields[1])
  finally:
    csvin.close()
  x.insert(0,'<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n<ITEMS>')
  x.append('</ITEMS>\n</PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  return

def read_csv_file_direct():
  # This function reads a CSV file and calls a function that accesses the 
  # Frepple C++ API directly, without passing through an XML format
  csvin = open('items.csv','r')
  try:
    for l in csvin.readlines():
      fields = l.strip().split(',')
      frepple.createItem(fields[0],fields[1])
  finally:
    csvin.close()
  return

def create_files(cnt):
  # This function writes out 2 data files: a first one is CSV-formatted, while
  # second one is XML-formatted
  csvout = open('items.csv','w')
  xmlout = open('items.xml','w')
  try:
    xmlout.write('<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n<ITEMS>\n')
    for i in range(cnt):
      csvout.write('item%i,oper%i\n' % (i,i%100))      
      xmlout.write('<ITEM NAME="item%i"><OPERATION NAME="oper%i"/></ITEM>\n' % (i,i%100)) 
    xmlout.write('</ITEMS>\n</PLAN>')
  finally:
    csvout.close()
    xmlout.close()
  return


print '0. In my script file'
