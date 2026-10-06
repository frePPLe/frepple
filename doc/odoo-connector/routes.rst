====================
Routes in Odoo
====================

Odoo routes are a complex topic. Starting with version 18 of the Frepple
connectors, routes are used to map inter-warehouse replenishment and purchasing
behavior into Frepple. There are more developments to come in future versions of the connectors
to consider the priority of different routes (manufacturing vs purchase vs transport) as well.

**Inter-warehouse routes**


Inter-warehouse routes are mapped to item distributions in Frepple. A route
defined at the warehouse level will create an item distribution for the root item (usually *All items* or *All*).
A route defined on a product category or an individual product creates an item
distribution record for the corresponding category or product.
The distribution lead time is calculated by summing the lead times of the rules in the route.

**Stock pickings**

Inter-warehouse stock pickings in Odoo are imported as confirmed distribution
orders in Frepple. When a proposed distribution order is exported from Frepple
to Odoo, Odoo creates the corresponding stock pickings using the route defined
for the product, its category, or the warehouse. This lets Odoo apply its route
rules to determine how the replenishment is executed.

**Buy rules and supplier locations**

The connector reads Odoo's buy rules to determine which warehouses can receive
each purchased product. It considers buy routes assigned to the product, its
category, and warehouses. A buy route
assigned to a warehouse can make that warehouse a receiving location for all
products. For each buy rule, the connector resolves the receiving warehouse
from the rule's warehouse or destination location.

When a product has supplier information and at least one applicable buy route,
Frepple creates an item supplier record for each supplier and each
warehouse that can receive the product.
The connectors therefore build an item supplier record  for every eligible product-and-warehouse combination.
Supplier lead time, minimum order quantity, cost, priority, and effective dates are mapped from
Odoo's supplier information.
Products without an applicable buy route don't get item supplier records from this mapping.

