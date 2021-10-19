from odoo import _, api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"


    supplier_number = fields.Char(
        string='Numero de Proveedor',
    )
