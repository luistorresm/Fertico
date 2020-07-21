from odoo import models, fields, api

class AccountPartialReconcile(models.Model):
    _inherit='account.partial.reconcile'

    
    @api.multi
    @api.depends('amount')
    def get_paid(self):
        for partial in self:
            data = self.env['account.partial.reconcile'].search(['&',('invoice', '=', partial.invoice.id),('id', '<', partial.id)])
            paid_total=0
            for d in data:
                paid_total+=d.amount
            partial.incial=partial.total-paid_total
            partial.final=partial.total-(paid_total+partial.amount)

    
    total = fields.Monetary(related='debit_move_id.invoice_id.amount_total')
    incial = fields.Float(string="Saldo inicial", compute='get_paid')
    final = fields.Float(string="Saldo final", compute='get_paid')
    invoice = fields.Many2one(related='debit_move_id.invoice_id', store=True)
    customer = fields.Many2one(string="Customer", related='debit_move_id.invoice_id.partner_id', store=True)
    account = fields.Many2one(string="Account", related='debit_move_id.invoice_id.account_id')
    account_type = fields.Selection(related='debit_move_id.invoice_id.account_id.user_type_id.type')
    
