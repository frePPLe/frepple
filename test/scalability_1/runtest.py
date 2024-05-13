#!/usr/bin/env python3
#
# Copyright (C) 2007 by frePPLe bv
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
import os
import sys
import subprocess

runtimes = {}


def createdata(outfile, duplicates, header, body, footer, subst):
    # Print the header
    outfile.write(header)

    # Iteration
    if subst == 0:
        for cnt in range(duplicates):
            print(body, file=outfile)
    elif subst == 1:
        for cnt in range(duplicates):
            print(body % (cnt), file=outfile)
    elif subst == 2:
        for cnt in range(duplicates):
            print(body % (cnt, cnt), file=outfile)
    elif subst == 3:
        for cnt in range(duplicates):
            print(body % (cnt, cnt, cnt), file=outfile)
    elif subst == 4:
        for cnt in range(duplicates):
            print(body % (cnt, cnt, cnt, cnt), file=outfile)
    elif subst == 5:
        for cnt in range(duplicates):
            print(body % (cnt, cnt, cnt, cnt, cnt), file=outfile)
    elif subst == 6:
        for cnt in range(duplicates):
            print(body % (cnt, cnt, cnt, cnt, cnt, cnt), file=outfile)
    elif subst == 7:
        for cnt in range(duplicates):
            print(body % (cnt, cnt, cnt, cnt, cnt, cnt, cnt), file=outfile)

    # Finalize
    outfile.write(footer)


# Main loop
for counter in [5000, 10000, 15000, 20000, 25000]:
    print("\ncounter", counter)
    outfile = open("input.xml", "wt")

    createdata(
        outfile,
        counter,
        '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
        + "<current>2009-01-01T00:00:00</current>\n"
        + "<items>\n",
        '<item name="ITEMNM_%d" category="cat1" description="DCRP_%d"/>',
        "</items>\n",
        2,
    )
    createdata(
        outfile,
        counter,
        "<operations>\n",
        '<operation name="Make ITEMNM_%d" xsi:type="operation_fixed_time" '
        + 'duration="P1D"><location name="factory"/></operation>',
        "</operations>\n",
        1,
    )
    createdata(
        outfile,
        counter,
        "<resources>\n",
        '<resource name="RESNM_%d"><location name="factory"/><loads>'
        + '<load><operation name="Make ITEMNM_%d"/></load></loads></resource>',
        "</resources>\n",
        2,
    )
    createdata(
        outfile,
        counter,
        "<flows>\n",
        '<flow xsi:type="flow_start"><operation name="Delivery ITEMNM_%d"/>'
        + '<buffer name="BUFNM_%d" onhand="10"/>'
        + "<quantity>-1</quantity></flow>\n"
        + '<flow xsi:type="flow_end"><operation name="Make ITEMNM_%d"/>'
        + '<buffer name="BUFNM_%d"/><quantity>1</quantity></flow>',
        "</flows>\n",
        4,
    )
    createdata(
        outfile,
        counter,
        "<demands>\n",
        '<demand name="DEMANDNM1_%d" quantity="10" due="2009-03-03T00:00:00" '
        + 'priority="1"><location name="factory"/><item name="ITEMNM_%d"/>'
        + '<operation name="Delivery ITEMNM_%d" xsi:type="operation_fixed_time" duration="P0D"/>'
        + "</demand>\n"
        + '<demand name="DEMANDNM2_%d" quantity="10" due="2009-03-03T00:00:00" '
        + 'priority="2"><location name="factory"/><item name="ITEMNM_%d"/></demand>'
        + '<operation name="Delivery ITEMNM_%d" xsi:type="operation_fixed_time" duration="P0D"/>'
        + "</demand>\n"
        + '<demand name="DEMANDNM3_%d" quantity="10" due="2009-03-03T00:00:00" '
        + 'priority="1"><location name="factory"/><item name="ITEMNM_%d"/>'
        + '<operation name="Delivery ITEMNM_%d" xsi:type="operation_fixed_time" duration="P0D"/>'
        + "</demand>\n",
        "</demands></plan>\n",
        9,
    )

    outfile.close()

    # Run the execution
    starttime = os.times()
    with open(os.devnull, "w") as f:
        subprocess.call([os.environ["EXECUTABLE"], "./commands.xml"], stdout=f)

    # Measure the time
    endtime = os.times()
    runtimes[counter] = endtime[4] - starttime[4]
    print("time: %.3f" % (endtime[4] - starttime[4]))

    # Clean up the input and the output
    os.remove("input.xml")
    os.remove("output.xml")
    # if os.path.isfile("input_%d.xml" % counter):
    #  os.remove("input_%d.xml" % counter)
    # os.rename("input.xml", "input_%d.xml" % counter)
    # if os.path.isfile("output_%d.xml" % counter):
    #  os.remove("output_%d.xml" % counter)
    # os.rename("output.xml", "output_%d.xml" % counter)

# Define failure criterium
if runtimes[25000] > runtimes[5000] * 5 * 1.05:
    print("\nTest failed. Run time scales worse than linear with model size.\n")
    sys.exit(1)

print("\nTest passed\n")
