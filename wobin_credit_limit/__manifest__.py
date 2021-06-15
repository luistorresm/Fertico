# -*- coding: utf-8 -*-
{
    'name': "Límite de crédito",

    'summary': """
        Modulo para control de límite crédito""",

    'description': """
        Límites de crédito
    """,

    'author': "Wobin",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
    'account',
    'sale',
    'contacts',
    'mail'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/credit_security.xml',

        #'views/views.xml',
        #'views/templates.xml',
        'views/block_credit.xml',
        'views/tracking_limit.xml',
        'views/credit_limit.xml',
        'views/res_partner_view.xml',
        'views/account_invoice_view.xml',
        'views/purchase_order_view.xml',
        'views/sale_order_view.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
