# -*- coding: utf-8 -*-
{
    'name': "fertico-addons",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'analytic', 'account', 'hr', 'sale'],

    # always loaded
    'data': [
        'security/analytic_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        #'views/account_analytic.xml',
        'views/attendances.xml',
        'views/sales_chanel.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml'
     ]
}