# -*- coding: utf-8 -*-
{
    'name': "Fertico Addons",
    'summary': """Custom Addons for Enterprise Fertico""",
    'description': """Module which manages the different customizations that the FERTICO Company requires for its Odoo Server Management""",
    'author': "Wobin",
    'website': "https://fertico.odoo.com/web",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '11.0.1.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'analytic', 'account', 'hr', 'hr_attendance', 'sale', 'point_of_sale', 'pos_sale'],

    # always loaded
    'data': [
        # security files
        'security/analytic_security.xml',
        'security/sales_security.xml',
        'security/ir.model.access.csv',

        # views
        'views/views.xml',
        'views/templates.xml',
        'views/account_analytic.xml',
        'views/attendances.xml',
        'views/sales_chanel.xml',
        'views/block_sales_price.xml',
        'views/pos_init.xml',
        'views/block_create_line.xml'


        # reports
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    # addons made to point of sale
    'qweb': [
        'static/src/xml/pos.xml'
     ]
}