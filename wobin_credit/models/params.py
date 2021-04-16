from odoo import models, fields, api

class CreditParameters(models.Model):
    _name = "credit.parameters"

    name = fields.Char(string="Nombre")
    crop_type = fields.Many2one('product.product', string="Tipo de cultivo")
    crop_method = fields.Selection([('irrigation', 'Riego'),('rainwater', 'Temporal')], string="Metodo de cultivo")
    amount = fields.Float("Monto por hectarea ($)") 

class CreditTypes(models.Model):
    _name = "credit.types"

    name = fields.Char(string="Tipo de crédito")
    payment_terms = fields.Many2one('account.payment.term', string="Plazo de pago")
    interest = fields.Float(string="Interes")
    interest_mo = fields.Float(string="Interes moratorio")