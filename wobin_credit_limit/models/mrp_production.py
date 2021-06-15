from odoo import api, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def write(self, vals):
        self = self.with_context(production_id=self.id)
        return super(MrpProduction, self).write(vals)
