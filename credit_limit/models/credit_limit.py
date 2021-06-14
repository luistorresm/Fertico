from odoo import models, fields, api
import datetime

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_limit = fields.Float(company_dependent=True)
    grace_payment_days =  fields.Integer(string="Dias de gracia", company_dependent=True)
    allowed_sale = fields.Boolean(string="Permitir ventas a credito", company_dependent=True)

    
    def check_grace_days(self):
        
        grace = True
        now = datetime.datetime.now()
        invoices = self.env['account.invoice'].search(['&','&',('date_due','<',now.strftime("%Y-%m-%d")),('state','!=','posted'),('partner_id','=',self._origin.id)])
        
        for invoice in invoices:
            if invoice.payment_term_id.credit:
                difference = now.date() - invoice.date_due
                if difference.days > self.grace_payment_days:
                    grace = False
                    
        self.allowed_sale = grace
        return grace
    
    
    @api.onchange('credit_limit','grace_payment_days','allowed_sale')
    def on_change_limit(self):
        if self.credit_limit > 0 and self.check_grace_days():
            self.allowed_sale = True
        else:
            self.allowed_sale = False
 


class AccountPaymentTerm(models.Model):
    
    _inherit = 'account.payment.term'

    credit = fields.Boolean(string="Crédito")


    '''@api.onchange('line_ids')
    def on_change_lines(self):
        
        days = False
        
        for line in self.line_ids:
            if line.days:
                days = True

        self.credit = days'''

    

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def check_grace_days(self):
        
        grace = True
        now = datetime.datetime.now()
        invoices = self.env['account.invoice'].search(['&','&',('date_due','<',now.strftime("%Y-%m-%d")),('state','!=','posted'),('partner_id','=',self.partner_id.id)])
        
        for invoice in invoices:
            if invoice.payment_term_id.credit:
                difference = now.date() - invoice.date_due
                if difference.days > self.partner_id.grace_payment_days:
                    grace = False

        self.partner_id.allowed_sale = grace
        return grace

    def credit_conditions(self):
        limit = self.partner_id.credit_limit
        total = self.amount_total
        credit = limit - total

        if credit >= 0:
            return True
        else:
            return False


    def action_confirm(self):
        if self.payment_term_id.credit:
            
            if self.partner_id.allowed_sale:
            
                if self.credit_conditions() & self.check_grace_days():
                
                    return super(SaleOrder, self).action_confirm()
                
                else:
                    
                    res = {'warning': {
                        'title': 'Advertencia',
                        'message': 'El cliente tiene deudas'
                    }}
                    return res
            
            else:
                res = {'warning': {
                        'title': 'Advertencia',
                        'message': 'El cliente no tiene permitidas ventas a crédito'
                    }}
                return res

        else:
            return super(SaleOrder, self).action_confirm()


class AccountMove(models.Model):
    _inherit = 'account.invoice'

    def action_post(self):
        
        res = super(AccountMove, self).action_post()
        
        if self.payment_term_id.credit:
            
            credit=self.partner_id.credit_limit-self.amount_total
            self.partner_id.credit_limit=credit

            if self.partner_id.credit_limit <= 0:
                self.partner_id.allowed_sale = False
        
        return res
        

