from odoo import models, fields, api

class RecibaModality(models.Model):
    _name = 'reciba.modality'
    _description = 'Modality of reciba'

    name = fields.Char(string="Name")