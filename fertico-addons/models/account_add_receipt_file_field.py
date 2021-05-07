from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    receipt_payment_use_ids = fields.Binary(string='Comprobante de Formas de Pago o Uso', track_visibility='always')
    val_payment_term        = fields.Char(related='payment_term_id.name')
    flag_value_pay_term     = fields.Boolean(compute='_set_flag_value_pay_term')


    @api.one
    @api.depends('val_payment_term')
    def _set_flag_value_pay_term(self):
        if self.val_payment_term == 'AL.(PUE) Contado' :
            self.flag_value_pay_term = True
        elif self.val_payment_term == 'CL.(PUE) Contado':
            self.flag_value_pay_term = True   
        elif self.val_payment_term == 'LC.(PUE) Contado':
            self.flag_value_pay_term = True     
        elif self.val_payment_term == 'PI.(PUE) Contado':
            self.flag_value_pay_term = True
        elif self.val_payment_term == 'PM.(PUE) Contado':
            self.flag_value_pay_term = True