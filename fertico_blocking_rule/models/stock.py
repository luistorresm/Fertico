# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_done(self):
        if self._get_overprocessed_stock_moves() or self._check_backorder():
            raise ValidationError(_("You can not deliverer the order because of some products Qty not Reserved"))
        return super(StockPicking, self).action_done()


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def _action_done(self):
        if self.filtered(lambda ml: ml.quantity_done > ml.reserved_availability):
            raise ValidationError(_("You can not deliverer the order because of some products Qty not Reserved"))
        return super(StockMove, self)._action_done()

    # def _action_assign(self):
    #     if self.filtered(lambda ml: ml.product_uom_qty > ml.reserved_availability):
    #         raise ValidationError(_("You can not deliverer the order because of some products Qty not Reserved"))
    #     return super(StockMove, self)._action_assign()
