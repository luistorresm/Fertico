from odoo import fields, models, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    #=======================Desactivamos la suma del campo al agrupar las lista============================
    price_unit = fields.Float(group_operator=False)
    