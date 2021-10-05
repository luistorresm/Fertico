from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_init = fields.Float(string="Crédito inicial", company_dependent=True, track_visibility='onchange')
    credit_limit = fields.Float(string="Crédito disponible", company_dependent=True, track_visibility='onchange')
    grace_payment_days =  fields.Integer(string="Dias de crédito", company_dependent=True, track_visibility='onchange')
    allowed_sale = fields.Boolean(string="Permitir ventas a credito", company_dependent=True, track_visibility='onchange')

    
    def check_grace_days(self):
        
        grace = True
        now = datetime.now()
        company=self.env.user.company_id.id
        invoices = self.env['account.move'].search([('partner_id','=',self.id),('company_id','=',company),('invoice_date_due','<',now.strftime("%Y-%m-%d")),('move_type','=','out_invoice'),('state','=','posted'),'|',('payment_state','=','partial'),('payment_state','=','not_paid')])
        
        for invoice in invoices:
            if invoice.invoice_payment_term_id.credit:
                difference = now.date() - datetime.strptime(invoice.date_due, '%Y-%m-%d').date()
                if difference.days > self.grace_payment_days:
                    grace = False
                    
        self.allowed_sale = grace
        return grace

    def update_limit(self):

        total_invoices = 0
        company=self.env.user.company_id.id
        invoices = self.env['account.move'].search([('partner_id','=',self.id),('company_id','=',company),('move_type','=','out_invoice'),('state','=','posted'),'|',('payment_state','=','partial'),('payment_state','=','not_paid')])

        for invoice in invoices:
            if invoice.invoice_payment_term_id.credit:
                total_invoices += invoice.amount_residual
        
        self.credit_limit = self.credit_init - total_invoices

    
    def assign_credit(self):
        return {
                'name': 'Asignar cŕedito',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'credit.limit.assign',
                'view_id': self.env.ref('wobin_credit.res_partner_assign_credit').id,
                'type': 'ir.actions.act_window',
                'res_id': self.env.context.get('cashbox_id'),
                'context': {'default_partner_id':self.id},
                'target': 'new'
            }

    def update_credit(self):
        return {
                'name': 'Actualizar límite cŕedito',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'credit.limit.update',
                'view_id': self.env.ref('wobin_credit.res_partner_update_credit').id,
                'type': 'ir.actions.act_window',
                'res_id': self.env.context.get('cashbox_id'),
                'context': {'default_partner_id':self.id},
                'target': 'new'
            }

    
    
    @api.onchange('credit_limit','grace_payment_days','allowed_sale')
    def on_change_limit(self):
        if self.credit_limit > 0 and self.check_grace_days():
            self.allowed_sale = True
        else:
            self.allowed_sale = False
 

class CreditLimitAssign(models.TransientModel):
    _name='credit.limit.assign'
    
    partner_id = fields.Many2one('res.partner')
    amount = fields.Float(string="Crédito")

    def assign_credit(self):
        self.partner_id.write({'credit_init': self.amount,
                            'credit_limit': self.amount })


class CreditLimitUpdate(models.TransientModel):
    _name='credit.limit.update'
    
    partner_id = fields.Many2one('res.partner')
    amount = fields.Float(string="Crédito")

    def update_credit(self):
        init = self.amount
        credit = self.partner_id.credit_limit
        if init > self.partner_id.credit_init:
            credit += init-self.partner_id.credit_init
        elif init < self.partner_id.credit_init:
            credit -= self.partner_id.credit_init-init
        
        self.partner_id.write({'credit_init': init,
                            'credit_limit': credit })
            


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    credit = fields.Boolean(string="Crédito")
    

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def check_grace_days(self):
        
        grace = True
        now = datetime.now()
        company=self.env.user.company_id.id
        invoices = self.env['account.move'].search([('partner_id','=',self.partner_id.id),('company_id','=',company),('invoice_date_due','<',now.strftime("%Y-%m-%d")),('move_type','=','out_invoice'),('state','=','posted'),'|',('payment_state','=','partial'),('payment_state','=','not_paid')])
        
        for invoice in invoices:
            if invoice.invoice_payment_term_id.credit:
                difference = now.date() - datetime.strptime(invoice.date_due, '%Y-%m-%d').date()
                if difference.days > self.partner_id.grace_payment_days:
                    grace = False
                    self.partner_id.write({'allowed_sale': False})
                    msg = 'La factura ' + invoice.number + ' está vencida'
                    raise UserError(msg)
                    
        if grace:
            return True
        else: 
            return False

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
                    msg = 'El cliente no cuenta con crédito suficiente o tiene facturas vencidas'
                    raise UserError(msg)
            
            else:
                msg = 'El cliente no tiene permitidas ventas a crédito'
                raise UserError(msg)

        else:
            return super(SaleOrder, self).action_confirm()


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        
        res = super(AccountMove, self).action_post()

        if self.move_type == 'out_invoice':

            if self.invoice_payment_term_id.credit:
                
                credit=self.partner_id.credit_limit-self.amount_residual
                self.partner_id.write({'credit_limit': credit})

                if self.partner_id.credit_limit <= 0:
                    self.partner_id.write({'allowed_sale': False})
        
        return res
        

