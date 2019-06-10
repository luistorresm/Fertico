# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Fertico Blocking Rules',
    'summary': 'Fertico DO,MO,SO Blocking Rules',
    'sequence': 100,
    'license': 'OEEL-1',
    'website': 'https://www.odoo.com/page/sales',
    'version': '1.0',
    'author': 'Odoo Inc',
    'description': """
Fertico DO,MO,SO Blocking Rules
===============================
* [MO] Manufacturing: Manufacturing/Manufacturing Orders form
* [DO] Inventory Transfers: Inventory/Transfers form
* [SO] Sales: Sales/Sales Orders form
    """,
    'category': 'Custom Development',
    'depends': ['sale_management', 'mrp', 'sale_stock'],
    'data': [
        'views/product_views.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
