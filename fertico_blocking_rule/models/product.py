# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_sale_high_cost = fields.Boolean("Validar precio de venta superior al costo")
