from odoo import models, fields, api
from datetime import datetime, timedelta

class StockProductLot(models.Model):

    _inherit = "stock.production.lot"

    notified = fields.Boolean(default=False)

    @api.model
    def mailmessage(self):
        '''This method send an email in the alert day of lots and serial numbers'''

        #search the email template
        template = self.env['mail.template'].search([('name','=',"caducidad")])
        for temp in template:
            template_id = temp.id
        if template_id:
            #search the lots while the alert day is now
            now = datetime.now()
            lots=self.env['stock.production.lot'].search(['&',('alert_date','<',str(now)),('notified','=',False)])
            for lot in lots:
                #send the emails and change the notified to True
                template.send_mail(lot.id, True)
                lot.write({
                    'notified': True
                })
            return True
        else:
            return False