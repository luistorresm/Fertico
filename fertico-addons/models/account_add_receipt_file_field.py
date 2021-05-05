from odoo import fields, models, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    receipt_payment_use_ids = fields.Many2many('ir.attachment', relation='receipt_payment_use_att_relation', string='Comprobante de Formas de Pago o Uso', track_visibility='always')
    