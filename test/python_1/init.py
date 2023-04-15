#
# Copyright (C) 2007-2013 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
import csv


def read_csv_file():
    # This function reads a CSV-formatted file, creates an XML string and
    # then passes the string to Frepple for processing
    x = [
        '<?xml version="1.0" encoding="UTF-8" ?><plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n<items>'
    ]
    for row in csv.reader(open("items.csv", "rt")):
        x.append('<item name="%s" description="%s"/>' % (row[0], row[1]))
    x.append("</items>\n</plan>")
    frepple.readXMLdata("\n".join(x), False, False)
    return


def read_csv_file_direct():
    # This function reads a CSV file and calls a function that accesses the
    # Frepple C++ API directly, without an intermediate XML format.
    for row in csv.reader(open("items.csv", "rt")):
        frepple.item(name=row[0], description=row[1])
    return


def create_files(cnt):
    # This function writes out 2 data files: a first one is CSV-formatted, while
    # second one is XML-formatted
    csvout = open("items.csv", "w")
    xmlout = open("items.xml", "w")
    try:
        xmlout.write(
            '<?xml version="1.0" encoding="UTF-8" ?><plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n<items>\n'
        )
        for i in range(cnt):
            csvout.write("item%i,oper%i\n" % (i, i % 100))
            xmlout.write('<item name="item%i" description="oper%i"/>\n' % (i, i % 100))
        xmlout.write("</items>\n</plan>")
    finally:
        csvout.close()
        xmlout.close()
    return


def my_function(a):
    print("in my function with argument %s" % a, end="")
    return "OK"


print("0. Initialization frePPLe version:", frepple.version)
