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
        sql_query = """SELECT company_id, SUM(residual_signed) FROM account_invoice WHERE (partner_id = %s) AND (state = 'open') AND (type = 'in_invoice' OR type = 'in_refund') GROUP BY company_id;"""
        self.env.cr.execute(sql_query, (self.partner_id.id,))
        residual_companies = self.env.cr.fetchall()
        _logger.info('\n\n\n residual_companies query super complicated with all filters: %s\n\n\n', residual_companies)
        
        sql_query = """SELECT company_id, SUM(residual_signed) FROM account_invoice WHERE (partner_id = %s) AND (type = 'in_invoice' OR type = 'in_refund') GROUP BY company_id;"""
        self.env.cr.execute(sql_query, (self.partner_id.id,))
        residual_companies2 = self.env.cr.fetchall()
        _logger.info('\n\n\n residual_companies query taking away state conditional: %s\n\n\n', residual_companies2)        
        
        sql_query = """SELECT company_id, SUM(residual_signed) FROM account_invoice WHERE (partner_id = %s) AND (state = 'open') GROUP BY company_id;"""
        self.env.cr.execute(sql_query, (self.partner_id.id,))
        residual_companies3 = self.env.cr.fetchall()
        _logger.info('\n\n\n residual_companiees query taking away types and just leaving state open: %s\n\n\n', residual_companies3)        

        msg = ""        
        flag = False
        contacts_obj = self.env['res.partner']
        
        if residual_companies:
            flag = True
        if residual_companies2:
            flag = True                        
        if residual_companies3:  
            flag = True  
            
        if flag == True:            
            #Construct the error message:
            debtor = contacts_obj.search([('id', '=', self.partner_id.id)]).name
            _logger.info('\n\n\n debtor: %s\n\n\n', debtor)
            msg = _('The related contact on the purchase order %s has outstanding balances on sales: \n') % (debtor)
            
            #Iterate companies with residual and concatenate:
            for val in residual_companies:
                company_name = contacts_obj.search([('id', '=', val[0])]).name
                _logger.info('\n\n\n company_name: %s\n\n\n', company_name)
                msg += _('\n[+] %s balance by $%s') % (company_name, val[1]) 

            #Iterate companies with residual and concatenate:
            for vl in residual_companies2:
                company_name = contacts_obj.search([('id', '=', vl[0])]).name
                _logger.info('\n\n\n company_name: %s\n\n\n', company_name)                
                msg += _('\n[+] %s balance by $%s') % (company_name, vl[1]) 

            #Iterate companies with residual and concatenate:
            for v in residual_companies3:
                company_name = contacts_obj.search([('id', '=', v[0])]).name
                _logger.info('\n\n\n company_name: %s\n\n\n', company_name)                
                msg += _('\n[+] %s balance by $%s') % (company_name, v[1]) 
                
            #Concatenate last part of error message:
            msg += _('\n\nConsider making discounts for settlement.')
             
            #Display error message:
            raise UserError(msg)
        
        #Continue with the original process of "button_confirm" method:
        return super(PurchaseOrder, self).button_confirm()
