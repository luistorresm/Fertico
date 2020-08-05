# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def button_confirm(self):
        #Retrieve rows from "account.invoice" model where the present provider
        #is revised to detect if has open invoices indicating that must pay its debts: 
        sql_query = """SELECT company_id, SUM(residual_signed) FROM account_invoice WHERE type = 'in_invoice' OR type = 'in_refund' GROUP BY company_id;"""
        self.env.cr.execute(sql_query)
        residual_companies = self.env.cr.fetchall()
        _logger.info('\n\n\n residual_companies: %s\n\n\n', residual_companies)
        
        if residual_companies:
            #Construct the error message:
            msg = ""
            msg = _('The related contact on the purchase order has outstanding balances on sales: \n')
            #Iterate companies with residual and concatenate:
            for val in residual_companies:
                msg += _('\n%s balance by $%s') % (val[0], val[1]) 
                #Concatenate last part of error message:
                msg += _('\nconsider making discounts for settlement.')
                _logger.info('\n\n\n %s \n\n\n', msg) 

            #Display error message:
            raise UserError(msg)
        
        #Continue with the original process of "button_confirm" method:
        return super(PurchaseOrder, self).button_confirm()