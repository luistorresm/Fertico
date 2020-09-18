# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.translate import _
 
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\

# Tickets de PROYECTO DE RECIBA:

# SP_AL.RECIBA_TK-000005 Mensaje de consulta de facturas abiertas de ventas en relacion al productor en orden de compra
# SP_AL.RECIBA_TK-000006 Calculo de saldos entre facturas abiertas de ventas vs Orden de compra del productor
# SP_AL.RECIBA_TK-000007 Historico de confirmación de ordenes de compra a detalle de facturas liquidadas
# SP_AL.RECIBA_TK-000009 Creacion de nueva vista para el seguimiento de liquidación de facturas de reciba y programación de pagos

#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    selected_sl_inv   = fields.Boolean(string='Descuento Seleccionado') 
    #assigned_pur_ord = fields.Integer(string='Orden de Compra Asignada') 
    seed_id           = fields.Char(string='Semilla/Producto', compute='_get_product_id')
    amount_compensate = fields.Float(string='Monto de Compensación', digits=dp.get_precision('Product Unit of Measure'), compute='set_amount_comp')
    amount_transfer   = fields.Float(string='Monto de Transferencia', digits=dp.get_precision('Product Unit of Measure'), compute='set_amount_dif')    
    payment_date_cust = fields.Char(string='Fecha Depósito', compute='_get_payment_date_cust')
    observation       = fields.Char(string='Observaciones')
    bank_cust         = fields.Char(string='Banco', compute='_get_bank')
    clabe_deposit     = fields.Char(string='Clabe/Cta Déposito', compute='_get_clabe_deposit')
    bank_payer        = fields.Char(string='Banco Pagador', compute='_get_bank_payer')
    clabe_payer       = fields.Char(string='Clabe/Cta Pagador', compute='_get_clabe_payer')
    operation         = fields.Char(string='Operación')

    def change_selected_sl_inv(self):           
        '''This method permits to change status of checkbox and assigning a purchase order'''
        if self.selected_sl_inv:
            values = {'selected_sl_inv': False}
            self.write(values)
        else:
            values = {'selected_sl_inv': True}
            self.write(values)

    @api.one
    @api.depends('number')
    def _get_product_id(self):
        '''This method intends to retrieve product_id from lines with header data'''
        self.seed_id = self.env['account.invoice.line'].search([('invoice_id', '=', self.id)], limit=1).name

    
    @api.one
    @api.depends('number')
    def set_amount_comp(self):
        '''This method intends to retrieve from purchase order info about compensantion amount'''
        self.amount_compensate = self.env['purchase.order'].search([('name', '=', self.origin)]).amount_select_discounts


    @api.one
    @api.depends('number')    
    def set_amount_dif(self):
        '''This method intends to retrieve from purchase order info about transfer amount'''
        self.amount_transfer = self.env['purchase.order'].search([('name', '=', self.origin)]).amount_pending_difference
    
    
    @api.one
    @api.depends('number')
    def _get_payment_date_cust(self):
        '''This method intends to retrieve from account payment the date of payment'''         
        if self.number:
            payment_date_lst = []
            
            sql_query = """SELECT payment_date 
                            FROM account_payment 
                            WHERE communication = %s;"""
            self.env.cr.execute(sql_query, (self.number,))
            result = self.env.cr.fetchall()          
            
            for date in result:
                #Obtain first element in tuple:
                date_aux = date[0]
                year  = date_aux[0:4]
                month = date_aux[5:7]
                day   = date_aux[8:10]
                #Split string of date and concatenate it into a new format:            
                formatted_date = day + '/' + month + '/' + year
                #Fill list of dates:
                payment_date_lst.append(formatted_date)    
            
            self.payment_date_cust = ', '.join(payment_date_lst)
        else:
            self.payment_date_cust = ''


    @api.one
    @api.depends('number')
    def _get_bank(self):
        '''This method intends to retrieve from res.partner.bank the bank_name'''
        self.bank_cust = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)], limit=1).bank_name


    @api.one
    @api.depends('number')    
    def _get_clabe_deposit(self):        
        '''This method intends to retrieve from res.partner.bank the acc_'''
        self.clabe_deposit = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)]).acc_number


    @api.one
    @api.depends('number')
    def _get_bank_payer(self):
        """This method intends to retrieve from account journal the bank_id"""        
        if self.number:
            bank_lst = []
            
            #Retrieve journals from multiple payments:
            sql_query = """SELECT journal_id 
                            FROM account_payment 
                            WHERE communication = %s;"""
            self.env.cr.execute(sql_query, (self.number,))
            result = self.env.cr.fetchall()        
            
            for rslt in result:
                #Obtain first element in tuple:
                journal_aux = rslt[0] 
                #Retrieve bank_id & name of bank:
                bank = self.env['account.journal'].search([('id', '=', journal_aux)]).bank_id.id
                bank_name = self.env['res.bank'].search([('id', '=', bank)]).name
                #Fill list with bank names:
                bank_lst.append(bank_name) 
                            
            self.bank_payer = ', '.join(bank_lst) 
        else:
             self.bank_payer = ''

    
    @api.one
    @api.depends('number')
    def _get_clabe_payer(self):
        '''This method intends to retrieve from account journal the bank_account_id'''        
        if self.number:
            bank_account_lst = []
            #Retrieve journals from multiple payments:
            sql_query = """SELECT journal_id 
                            FROM account_payment 
                            WHERE communication = %s;"""
            self.env.cr.execute(sql_query, (self.number,))
            result = self.env.cr.fetchall()        
            
            for rslt in result:
                #Obtain first element in tuple:
                journal_aux = rslt[0]
                #Retrieve bank_id & name of bank:
                bank_account = self.env['account.journal'].search([('id', '=', journal_aux)]).bank_account_id.id
                account_name = self.env['res.partner.bank'].search([('id', '=', bank_account)]).acc_number
                #Fill list with bank accounts:
                bank_account_lst.append(account_name) 
                            
            self.clabe_payer = ', '.join(bank_account_lst)
        else:
            self.clabe_payer = ''



class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    pending_sales_invoices_ids = fields.One2many('account.invoice', 'partner_id', string='Facturas de Venta Pendientes', compute='get_invoices')   
    amount_sl_pending_inv      = fields.Float(string='Monto Facturas de Venta Pendientes', digits=dp.get_precision('Product Unit of Measure'), compute='sum_residual_signed') 
    amount_select_discounts    = fields.Float(string='Monto de Compensación', digits=dp.get_precision('Product Unit of Measure'), compute='sum_select_discounts')
    amount_pending_difference  = fields.Float(string='Monto de Transferencia', digits=dp.get_precision('Product Unit of Measure'), compute='set_amount_pending_difference')

    def get_invoices(self):       
        '''Fill new One2Many field with debted bills belonging to a client, determining its state as open:''' 
        domain =[('state', '=', 'open'), 
                 ('partner_id', '=', self.partner_id.id),
                  '|', ('type', '=', 'out_invoice'),
                       ('type', '=', 'out_refund')]                                                                     
        self.pending_sales_invoices_ids = self.env['account.invoice'].search(domain)                                            

    @api.multi
    def sum_residual_signed(self):
        '''Sumatory for amount of pending sales invoices'''
        for rec in self:
            rec.amount_sl_pending_inv = sum(line.residual_signed for line in rec.pending_sales_invoices_ids)

    @api.multi
    def sum_select_discounts(self):
        '''Determine the amount of selected sales invoices to charge by operator'''
        for rec in self:
            rec.amount_select_discounts = sum(line.residual_signed for line in rec.pending_sales_invoices_ids if line.selected_sl_inv == True)

    def set_amount_pending_difference(self):
        '''Determine the amount of selected sales invoices to charge by operator'''
        self.amount_pending_difference = self.amount_total - self.amount_select_discounts

    #/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/
    #Inherit native method "button_confirm" in order 
    # to add new validations, data and calculations:
    @api.multi
    def button_confirm(self): 
        #Initialize variables:
        msg = ""; summatory_residual = 0

        #Retrieve rows from "account.invoice" model where the present provider
        #is revised to detect if has open invoices indicating that must pay its debts:         
        sql_query = """SELECT company_id, SUM(residual_signed) 
                         FROM account_invoice 
                        WHERE (partner_id = %s)
                          AND (state = 'open')
                          AND (type = 'out_invoice' OR type = 'out_refund') 
                        GROUP BY company_id;"""
                        
        self.env.cr.execute(sql_query, (self.partner_id.id,))
        residual_companies = self.env.cr.fetchall()        

        #Validate if query has results:
        if residual_companies:           
            #Construct the error message, beginning with client with open sales invoices:
            debtor = self.env['res.partner'].search([('id', '=', self.partner_id.id)]).name
            msg = _('El contacto relacionado en la Orden de Compra %s tiene saldos pendientes en Ventas: \n') % (debtor)
                          
            for val in residual_companies:
                #Iterate companies with residual (outstanding balance) and concatenate
                company_name = self.env['res.company'].search([('id', '=', val[0])]).name
                msg += _('\n[+] %s, saldo por $%s') % (company_name, val[1])                    
                #Sum up residuals in order to indicate how much is debted
                summatory_residual += val[1] 
                         
            #Concatenate last part of error message:
            msg += _('\n\nConsidere hacer descuentos para su liquidacion.')

            #Error message must be omitted when a given user has permission to invalidate it
            #being this indicated by a checkbox in "res.users" or when a simple user has indicated
            #all pending sales invoices were paid otherwise this error message must be displayed:
            uid = self.env.user.id
            name_user = self.env['res.users'].search([('id', '=', uid)]).name                   
            is_valid_user_flag = self.env.user.has_group('albagro_reciba_customs.group_omit_validation_pending_invoices')         
        
            if is_valid_user_flag == False and (summatory_residual != self.amount_select_discounts):            
                #Display error message to user like a pop up alert:
                raise UserError(msg)
            else:
                #Construction of post's content in Purchase Order Chatter:
                purchase_post =  "<ul style=\"margin:0px 0 9px 0\">"
                purchase_post += "<li><p style='margin:0px; font-size:13px; font-family:\"Lucida Grande\", Helvetica, Verdana, Arial, sans-serif'>Usuario que autorizó la Orden de Compra: <strong>" + name_user + "</strong></p></li>"
                purchase_post += "<li><p style='margin:0px; font-size:13px; font-family:\"Lucida Grande\", Helvetica, Verdana, Arial, sans-serif'><strong>Monto de facturas de venta adeudadas:</strong> $" + str(summatory_residual) + "</p></li>"
                purchase_post += "<li><p style='margin:0px; font-size:13px; font-family:\"Lucida Grande\", Helvetica, Verdana, Arial, sans-serif'><strong>Monto de descuentos seleccionados:</strong> $" + str(self.amount_select_discounts) + "</p></li>"
                purchase_post += "</ul>"

                purchase_order_recorset = self.env['purchase.order'].browse(self.id)
                purchase_order_recorset.message_post(body=purchase_post)
        
        #\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\*-\
        #Continue with the original process of "button_confirm" method:
        return super(PurchaseOrder, self).button_confirm()