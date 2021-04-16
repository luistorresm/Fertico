from odoo import models, fields, api

class CreditPreApplication(models.Model):
    _name = "credit.preapplication"
    _inherit = ['mail.thread']

    @api.depends('crop_type','crop_method','hectares')
    def get_amount(self):
        amount = 0
        
        if self.crop_type and self.crop_method:
            param = self.env['credit.parameters'].search([('crop_type','=',self.crop_type.id),('crop_method','=',self.crop_method)])
            if param:
                amount = param.amount*self.hectares

        self.calculated_amount = amount

    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('credit.preapplication'))
    name = fields.Char('Preaplicación', default='PRE-00')
    partner_id = fields.Many2one('res.partner', string="Cliente")
    cycle =  fields.Char(string="Ciclo")
    crop_type = fields.Many2one('product.product', string="Tipo de cultivo")
    crop_method = fields.Selection([('irrigation', 'Riego'),('rainwater', 'Temporal')], string="Metodo de cultivo")
    hectares = fields.Float(string="Hectareas")
    calculated_amount = fields.Float(string="Monto permitido", compute="get_amount", store=True)
    requested_amount = fields.Float(string="Monto solicitado")
    authorized_amount = fields.Float(string="Monto autorizado")
    credit_type_id = fields.Many2one('credit.types', string="Tipo de crédito")
    payment_terms = fields.Many2one(related='credit_type_id.payment_terms', string="Plazo de pago", readonly='True')
    date_limit_flag = fields.Boolean(default="False")
    date_limit = fields.Date(string="Fecha límite")
    interest = fields.Float(related='credit_type_id.interest', string="Interes", readonly='True')
    interest_mo = fields.Float(related='credit_type_id.interest_mo', string="Interes moratorio", readonly='True')

    @api.onchange('payment_terms')
    def get_payment_term(self):

        if self.payment_terms and len(self.payment_terms.line_ids) > 1:
            
            if self.payment_terms.line_ids[1].days == 180:
                self.date_limit_flag = True
            else:
                self.date_limit_flag = False
                self.date_limit = ''
        else:
            self.date_limit_flag = False
            self.date_limit = ''


    