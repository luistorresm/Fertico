from odoo import models, fields, api
from datetime import datetime, timedelta

class StockProductLot(models.Model):

    _inherit = "stock.production.lot"

    notified = fields.Boolean(default=False)

    @api.model
    def mailmessage(self):
        vals = {}
        domain=[('name','=','caducidad')]
        tplate = self.env['mail.template'].search([('name','=',"caducidad")])
        for temp in tplate:
            print('Template', temp.name)
            template = temp.id
        if template:
            now = datetime.now()
            lots=self.env['stock.production.lot'].search(['&',('alert_date','<',str(now)),('notified','=',False)])
            for lot in lots:
                tplate.send_mail(lot.id, True)
                lot.write({
                    'notified': True
                })
            return True
        else:
            return False