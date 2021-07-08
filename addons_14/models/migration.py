from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_gid = fields.Integer()
    additional_info = fields.Char()

    def autocomplete(self):
        return True

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    datas_fname = fields.Char('File Name')