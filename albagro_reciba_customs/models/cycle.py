from odoo import models, fields, api

class RecibaCycle(models.Model):
    _name = 'reciba.cycle'
    _description = 'Cycle of reciba'

    name = fields.Char(string="Name")