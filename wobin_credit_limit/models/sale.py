# Copyright 2019 Vauxoo
# Licence LGPL-3.0 or later

from odoo import _, api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        """Inherit method to add the action_validate_pick_out function after
        running. the original method."""
        action = super(SaleOrder, self).action_confirm()
        self.action_validate_pick_out()
        return action

    @api.multi
    def action_validate_pick_out(self):
        """Method allow to automatically validate the picking if all the
        products on a sale order are in stock and send a message that says so,
        otherwise send a message to the chatter that says that the picking
        couldn't be validated due to missing products. And if there are not
        more pickings to validated send a message saying that."""
        for sale in self:
            pickings = sale.picking_ids.filtered(lambda p: p.state not in
                                                 ['done', 'cancel'])
            messages = []
            if not pickings:
                messages.append(_("There is no more pickings to validate."))

            for picking in pickings:
                picking.action_assign()
                if not all([i.product_uom_qty == i.reserved_availability
                            for i in picking.move_lines]):
                    messages.append(
                        _("The picking %s was not validated because right "
                          "now not all the selected products are in stock.") %
                        picking.name)
                    continue

                for move_line in picking.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
                picking.button_validate()
                messages.append(
                    _("The picking %s was validated.") % picking.name)
            message = '\n'.join(messages)
            sale.message_post(
                body=("<p>" + message + "</p>"))
