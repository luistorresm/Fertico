from odoo import models, fields, api

class ResPartner(models.Model):

    _inherit='res.partner'

    credit_limit = fields.Float(track_visibility='onchange')
    allowed_sale = fields.Boolean(track_visibility='onchange')
    grace_payment_days = fields.Float(track_visibility='onchange')
    website = fields.Char(track_visibility='onchange')

class MailTrackingValue(models.Model):

    _inherit='mail.tracking.value'

    def _user_company(self):
        comp=self.env.user.company_id.name
        return comp

    def _user_name(self):
        user_name=self.env.user.name
        return user_name
    
    author = fields.Char(string='User', default=_user_name)
    contact = fields.Char(string='Contact', related='mail_message_id.record_name', store=True)
    date_change = fields.Datetime(string='Date', related='mail_message_id.date', store=True)
    company_user=fields.Char(string="Company", default=_user_company)

    

    


        
