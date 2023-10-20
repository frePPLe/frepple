==============================
How can I forecast a new item?
==============================

New items don't have any sales history yet (or only a very limited one).
FrePPLe's statistical forecast can not generate a reliable forecast yet for them.

A demand planner will need to manually adjust the forecast value.

1) Navigate to Parameters in the Admin menu and change the value of parameter forecast.populateForecastTable from true to false.
2) Navigate to Forecast in the Sales menu and click on the + icon in the upper right corner to add a new forecast record.
3) Navigate to Execute in the Admin menu and click on Launch plan.
4) Navigate to Forecast Report in the Sales menu and filter for your new item.
5) Adjust the forecast by setting customed values in the Forecast Override row.
6) Navigate to Parameters in the Admin menu and revert the value of parameter forecast.populateForecastTable from false to true.
7) Navigate to Execute in the Admin menu and click on Launch plan.

.. raw:: html

   <iframe width="1038" height="584" src="https://www.youtube.com/embed/o7lcwK0nYW0" frameborder="0" allowfullscreen></iframe>