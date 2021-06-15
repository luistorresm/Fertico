# Copyright 2019 Vauxoo
# Licence LGPL-3.0 or later

from odoo import api, models, tools
import psycopg2
import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create_from_ui(self, orders):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        pos_order = self.search(
            [('pos_reference', 'in', submitted_references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = {o['pos_reference'] for o in existing_orders}
        orders_to_save = [
            o for o in orders
            if o['data']['name'] not in existing_references]
        order_ids = []

        for tmp_order in orders_to_save:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            if to_invoice:
                self._match_payment_to_invoice(order)
            pos_order = self._process_order(order)
            order_ids.append(pos_order.id)

            try:
                pos_order.action_pos_order_paid()
            except psycopg2.OperationalError:
                # do not hide transactional errors,
                # the order(s) won't be saved!
                raise
            except BaseException as e:
                _logger.error(
                    'Could not fully process the POS Order: %s',
                    tools.ustr(e))

            if to_invoice:
                pos_order.action_pos_order_invoice()
                pos_order.invoice_id.action_invoice_open()
                pos_order.account_move = pos_order.invoice_id.move_id
        return order_ids
