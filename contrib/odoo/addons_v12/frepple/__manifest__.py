# -*- coding: utf-8 -*-
{
    "name": "frepple",
    "version": "6.1.0",
    "category": "Manufacturing",
    "summary": "Advanced planning and scheduling",
    "author": "frePPLe",
    "website": "https://frepple.com",
    "license": "AGPL-3",
    "description": "Connector to frePPLe - finite capacity planning and scheduling",
    "depends": ["product", "purchase", "sale", "resource", "mrp"],
    "external_dependencies": {"python": ["pyjwt"]},
    "data": [
        "frepple_data.xml",
        "security/frepple_security.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": True,
}
