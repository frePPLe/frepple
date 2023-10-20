===================================
How to approve a MO, a PO or a DO ?
===================================

Frepple propagates the sales orders and forecast through the supply path.
The output of the plan is a set of newly proposed manufacturing orders (MO),
purchase orders (PO) and distribution orders (DO).

The material planner will review these proposals. When approved, the proposed
MO, PO and DO need to transfered to the ERP system for execution.

1) | In the PO/MO/DO screen, the planner needs to filter for the records with a proposed status.
2) | Indeed, records with a confirmed or approved status means that this MO/PO/DO is already in the ERP.
3) | The planner needs to sort the records by ordering date (for POs), shipment date (for DOs) or start date (for MOs).
4) | The planner needs to select the records to approve (i.e export to the ERP). Exporting records that don't have
     an execution date pretty close in the future is not a good practice as frePPLe will continue to replan these records.
5) | The planner needs to click on the "Export to ERP" button to create the records in the ERP.
6) | Next time the interface will be run between the ERP and frePPLe, these records will be imported with a
     confirmed status in frePPLe.

.. raw:: html

   <iframe width="1038" height="584" src="https://www.youtube.com/embed/fI_4_PrXWjg" frameborder="0" allowfullscreen></iframe>