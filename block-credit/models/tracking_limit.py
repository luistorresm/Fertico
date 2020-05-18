from odoo import models, fields, api

class ResPartner(models.Model):

    _inherit='res.partner'

    credit_limit = fields.Float(track_visibility='onchange')
    allowed_sale = fields.Boolean(track_visibility='onchange')
    grace_payment_days = fields.Float(track_visibility='onchange')
    website = fields.Char(track_visibility='onchange')

class MailTrackingValue(models.Model):

    _inherit='mail.tracking.value'
    
    author = fields.Char(string='User', related='mail_message_id.author_id.name')
    contact = fields.Char(string='Contact', related='mail_message_id.record_name')
    date_change = fields.Datetime(string='Date', related='mail_message_id.date')