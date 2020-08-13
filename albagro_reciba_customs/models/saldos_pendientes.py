# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\

# Tickets de PROYECTO DE RECIBA:

# SP_AL.RECIBA_TK-000005 Mensaje de consulta de facturas abiertas de ventas en relacion al productor en orden de compra
# SP_AL.RECIBA_TK-000006 Calculo de saldos entre facturas abiertas de ventas vs Orden de compra del productor
# SP_AL.RECIBA_TK-000007 Historico de confirmación de ordenes de compra a detalle de facturas liquidadas
# SP_AL.RECIBA_TK-000009 Creacion de nueva vista para el seguimiento de liquidación de facturas de reciba y programación de pagos

#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    selected_sl_inv = fields.Boolean(string='Selected Discount', store=True) 

    @api.onchange('selected_sl_inv')
    def _onchange_selected_sl_inv(self):
        self.ensure_one()
        _logger.info('\n\n\n ID FACTURA: %s\n\n\n', self._origin.id)        
                        
        #Update trial 1:
        invoice_recordset = self.env['account.invoice'].browse(self._origin.id)
        invoice_recordset.selected_sl_inv = True
        _logger.info('\n\n\n invoice_recordset.selected_sl_inv: %s\n\n\n', invoice_recordset.selected_sl_inv)
        
        #Update trial 2:
        values = {'selected_sl_inv': True}
        recordset = self.env['account.invoice'].write(values)
        _logger.info('\n\n\n recordset: %s\n\n\n', recordset)   




class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    pending_sales_invoices_ids = fields.One2many('account.invoice', 'partner_id', 
                                                 string='Pending Sales Invoices',
                                                 compute='get_invoices')   
    
    ammount_sl_pending_inv = fields.Float(string='Ammount of Pedinng Sales Invoices', 
                                          digits=dp.get_precision('Product Unit of Measure'),
                                          compute='sum_residual_signed') 

    ammount_select_discounts = fields.Float(string='Ammount of Selected Discounts', 
                                            digits=dp.get_precision('Product Unit of Measure'))     


    def get_invoices(self):       
        '''Fill new One2Many field with debted bills belonging to a client,
           determining its state as open:''' 
        domain=[('state', '=', 'open'), 
                ('partner_id', '=', self.partner_id.id),
                '|', ('type', '=', 'in_invoice'),
                     ('type', '=', 'in_refund')]                                                                     
        self.pending_sales_invoices_ids = self.env['account.invoice'].search(domain)                                            

    @api.multi
    def sum_residual_signed(self):
        '''Sumatory of pending sales invoices'''
        for rec in self:
            rec.ammount_sl_pending_inv = sum(line.residual_signed for line in rec.pending_sales_invoices_ids)                                            
    
    @api.onchange('pending_sales_invoices_ids')
    def determine_discounts(self):
        invoice_id = self._origin.id
        _logger.info('\n\n\n invoice_id : %s\n\n\n', invoice_id)
        #Update trial 3:
        self.ensure_one()
        invoice_recordset = self.env['account.invoice'].browse(invoice_id)
        invoice_recordset.selected_sl_inv = True                       
              
        self.ammount_select_discounts = sum(line.residual_signed for line in self.pending_sales_invoices_ids if line.selected_sl_inv == True)         


    #/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/
    #Inherit native method "button_confirm" in order 
    # to add new validations, data and calculations:
    @api.multi
    def button_confirm(self): 
        #Initialize variables:
        msg = ""; summatory_residual = 0;

        #Retrieve rows from "account.invoice" model where the present provider
        #is revised to detect if has open invoices indicating that must pay its debts:         
        sql_query = """SELECT company_id, SUM(residual_signed) 
                       FROM account_invoice 
                       WHERE (partner_id = %s)
                         AND (state = 'open')
                         AND (type = 'in_invoice' OR type = 'in_refund') 
                       GROUP BY company_id;"""

        self.env.cr.execute(sql_query, (self.partner_id.id,))
        residual_companies = self.env.cr.fetchall()

        

        #Validate if query has results:
        if residual_companies:           
            #Construct the error message, beginning with client with open invoices:
            debtor = self.env['res.partner'].search([('id', '=', self.partner_id.id)]).name
            msg = _('The related contact on the purchase order %s has outstanding balances on sales: \n') % (debtor)
            
            if residual_companies:                
                for val in residual_companies:
                    #Iterate companies with residual (outstanding balance) and concatenate
                    company_name = self.env['res.company'].search([('id', '=', val[0])]).name
                    msg += _('\n[+] %s balance by $%s') % (company_name, val[1])
                    
                    #Sum up residuals in order to indicate how much is debted
                    summatory_residual += val[1] 
             
            
            #Concatenate last part of error message:
            msg += _('\n\nConsider making discounts for settlement.')

            #Error message must be omitted when a given user has permission to invalidate it
            #being this indicated by a checkbox in res.partner:
            uid = self.env.user.id
            name_user = self.env['res.users'].search([('id', '=', uid)]).name        

            #is_valid_user_flag = self.pool.get('res.users').has_group(cr, uid, 'base.group_omit_balances') 
            #user = self.env['res.users'].browse(self._uid)
            #is_valid_user_flag = user.has_group('base.group_omit_balances')            
            is_valid_user_flag = self.env.user.has_group('base.group_omit_balances')         

            _logger.info('\n\n\n uid: %s\n\n\n', uid)            
            _logger.info('\n\n\n is_valid_user_flag: %s\n\n\n', is_valid_user_flag)            
            _logger.info('\n\n\n summatory_residual: %s\n\n\n', summatory_residual)
            _logger.info('\n\n\n ammount_select_discounts: %s\n\n\n', self.ammount_select_discounts)

        
            if is_valid_user_flag == True or not summatory_residual or self.ammount_select_discounts:            
                #Display error message to user like a pop up window:
                raise UserError(msg)
            else:
                #Construction of post's content in Purchase Order Chatter:
                purchase_post =  "<ul style=\"margin:0px 0 9px 0\">"
                purchase_post += "<li><p style='margin:0px; font-size:13px; font-family:\"Lucida Grande\", Helvetica, Verdana, Arial, sans-serif'>Usuario que autorizó la Orden de Compra: " + name_user + "</p></li>"
                purchase_post += "<li><p style='margin:0px; font-size:13px; font-family:\"Lucida Grande\", Helvetica, Verdana, Arial, sans-serif'><strong>Monto de facturas de venta adeudadas:</strong> $" + str(summatory_residual) + "</p></li>"
                purchase_post += "<li><p style='margin:0px; font-size:13px; font-family:\"Lucida Grande\", Helvetica, Verdana, Arial, sans-serif'><strong>Monto de descuentos seleccionados:</strong> $" + str(self.ammount_select_discounts) + "</p></li>"
                purchase_post += "</ul>"

                purchase_order_recorset = self.env['purchase.order'].browse(self.id)
                purchase_order_recorset.message_post(body=purchase_post)
        
        #\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\
        #Continue with the original process of "button_confirm" method:
        return super(PurchaseOrder, self).button_confirm()