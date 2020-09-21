from odoo import models, fields, api

class RecibaDataTd(models.Model):
    _name = 'reciba.datatd'
    _description = 'Data TD'

    @api.one
    @api.depends('percentage', 'discount')
    def _calculate_complement(self):
        self.complement = (self.percentage * self.discount) / 100
    
    @api.one
    @api.depends('product_id', 'percentage', 'condition')
    def _calculate_name(self):
        if self.product_id and self.condition:
            self.name = self.product_id.name + " " + str(self.percentage)+"% " + self.condition

    name = fields.Char(string="Name", compute="_calculate_name")
    description = fields.Char(string="Name", compute="_calculate_name")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    condition = fields.Selection([('humedad', 'Humedad'),
                                ('quebrado', 'Grano quebrado'),
                                ('danado', 'Grano dañado'),
                                ('impureza', 'Grano impureza')], required=True)
    percentage = fields.Float(string="Percentage (%)")
    discount = fields.Float(string="Discount Kg")
    complement =  fields.Float(string="Complement", compute="_calculate_complement")
