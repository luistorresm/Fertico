# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    @api.multi
    def open_produce_product(self):
        self.ensure_one()
        if self.move_raw_ids.filtered(lambda ml: ml.product_uom_qty > ml.reserved_availability):
            raise ValidationError(_("You can not Produce the Production because of some products Qty not Reserved"))
        return super(MrpProduction, self).open_produce_product()

    @api.multi
    def button_plan(self):
        for production in self:
            if production.move_raw_ids.filtered(lambda ml: ml.product_uom_qty > ml.reserved_availability):
                raise ValidationError(_("You can not Plan the Production because of some products Qty not Reserved"))
        return super(MrpProduction, self).button_plan()
