# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api,  _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_quotation_send(self):
        self.order_line.check_product_qty_stock()
        self.order_line.validate_prices()
        return super(SaleOrder, self).action_quotation_send()

    def action_confirm(self):
        self.order_line.check_product_qty_stock()
        self.order_line.validate_prices()
        return super(SaleOrder, self).action_confirm()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def validate_prices(self):
        if self.filtered(lambda ol: ol.price_unit < ol.product_id.standard_price):
            p_list = [ol.product_id.name for ol in self.filtered(lambda ol: ol.price_unit < ol.product_id.standard_price)]
            raise ValidationError(_("The Products : {} Has the Unit/Sale Price less than the Cost Price.".format(", ".join(p_list))))

    def check_product_qty_stock(self):
        warning = []
        for line in self:
            res = line._onchange_product_id_check_availability()
            if 'warning' in res:
                warning.append(_("%s : " % line.product_id.name) + res['warning']['message'])
        if warning:
            raise ValidationError("{}".format("\n".join(warning)))
        return True
