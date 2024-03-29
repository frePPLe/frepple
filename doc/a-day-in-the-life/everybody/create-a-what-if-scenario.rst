=========================
Create a what-if scenario
=========================

A what-if scenario allows you to create a sandbox copy of the data, and simulate any
change to the data. You'll also want to compare the planning results in your what-if
scenario with the original plan.

See :doc:`/user-interface/what-if-scenarios` for a quick introduction.

1) | Navigate to Execute screen in the Admin menu.
   | The screen shows a number of tasks, and you want to open the "scenario management" task.
2) | You see a list scenario slots (7 by default). Each one is seperate database that can
     store a seperate dataset.
   | Search a free scenario in the list, and launch the "copy from X" task to clone source
     scenario slot into the chosen scenario slot.
3) | The database copy usually takes a minute or so, obviously depending on the size of
     your dataset.
4) | Once the copy is finished the newly populated scenario appears in the scenario
     selection dropdown in the upper right corner.
   | Select the new scenario.
5) | Congratualtions! You can now make any data changes, new plans, etc in your new scenario.
   | These changes are isolated & sandboxed to this scenario.
6) | At some point you'll want to compare some planning results between the scenario and the
     original dataset.
   | You do this by exporting any frePPLe report as an excel. The popup dialog for the
     export allows you to select which scenarios you want to export. Once the export has
     finished, you can create a pivot table in the excel spreadsheet to summarize, filter and
     compare the data of the selected scenarios.
7) | Once the evaluation of the what-if scenario is done, you'll want to do destroy the
     what-if scenario and release the scenario slot again to other users.
   | Simply navigate back to the "scenario management" section in the execute screen.
     Search for your scenario in the list and select the "release" action from the dropdown.
   | Once the scenario is released it disappears from the dropdown list in the upper right corner.
