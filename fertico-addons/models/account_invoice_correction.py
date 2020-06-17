from odoo import fields, models, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    user_id = fields.Many2one(readonly=False, required=True)
    team_id = fields.Many2one(required=True)

    