from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def create(self, vals):
        if vals.get('location_dest_id', False) and self._context.get(
                'production_id', False):
            move_id = self.env['stock.move'].search(
                [('production_id', '=', self._context['production_id'])])
            vals['location_dest_id'] = move_id.location_id.id
        return super(StockMove, self).create(vals)


class Location(models.Model):
    _inherit = "stock.location"

    def get_putaway_strategy(self, product):
        putaway_location = super(Location, self).get_putaway_strategy(product)
        if not putaway_location and self._context.get('production_id', False):
            move_id = self.env['stock.move'].search(
                [('production_id', '=', self._context['production_id'])])
            putaway_location = move_id.location_id
        return putaway_location
