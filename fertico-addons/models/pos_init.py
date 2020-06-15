from odoo import models, fields, api

class PosSession(models.Model):
    _inherit = 'pos.session'

    cash_register_balance_start = fields.Monetary(
        related='cash_register_id.balance_start',
        string="Starting Balance",
        help="Total of opening cash control lines.",
        readonly=False)

class PosConfig(models.Model):
    _inherit = 'pos.config'

    def open_session_cb(self):
        """This method init the balance start in 0.00"""

        res = super(PosConfig, self).open_session_cb()
        self.current_session_id.write({
            'cash_register_balance_start': 0.00
        })

        return res

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def write(self, values):
        order = super(PosOrder, self).write(values)
        if self.invoice_id.id:
            channel=self.session_id.crm_team_id
            self.invoice_id.team_id=channel
        return order
