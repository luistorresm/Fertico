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
    payment_terms = fields.Integer(string="Plazo de pago")
    interest = fields.Float(string="Interes")
    interest_mo = fields.Float(string="Interes moratorio")
    

class CreditPreApplication(models.Model):
    _name = "credit.preapplication"

    name = fields.Char('Preaplicación')
    crop_type = fields.Many2one('product.product', string="Tipo de cultivo")
    crop_method = fields.Selection([('irrigation', 'Riego'),('rainwater', 'Temporal')], string="Metodo de cultivo")
    hectares = fields.Float(string="Hectareas")
    requested_amount = fields.Float(string="Monto solicitado")
    calculated_amount = fields.Float(string="Monto calculado")
    authorized_amount = fields.Float(string="Monto autorizado")
    credit_type_id = fields.Many2one('credit.types', string="Tipo de crédito")
    payment_terms = fields.Integer(related='credit_type_id.payment_terms', string="Plazo de pago")
    interest = fields.Float(related='credit_type_id.interest', string="Interes")
    interest_mo = fields.Float(related='credit_type_id.interest_mo', string="Interes moratorio")
   