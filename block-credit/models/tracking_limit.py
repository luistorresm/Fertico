from odoo import models, fields, api

class ResPartner(models.Model):

    _inherit='res.partner'

    credit_limit = fields.Float(track_visibility='onchange')
    allowed_sale = fields.Boolean(track_visibility='onchange')
    grace_payment_days = fields.Float(track_visibility='onchange')