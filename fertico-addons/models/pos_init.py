from odoo import models, fields, api

class PosSession(models.Model):
    _inherit = 'pos.session'

    cash_register_balance_start = fields.Monetary(
        related='cash_register_id.balance_start',
        string="Starting Balance",
        help="Total of opening cash control lines.",
        readonly=False)

    POS_SESSION_STATE = [
        ('opening_control', 'Opening Control'),  # method action_pos_session_open
        ('opened', 'In Progress'),               # method action_pos_session_closing_control
        ('closing_control', 'Closing Control'),  # method action_pos_session_close
        ('closed', 'Closed & Posted'),           # method action_pos_session_verified
        ('verified', 'Verified'),
    ]

    state = fields.Selection(
        POS_SESSION_STATE)

    @api.multi
    def action_pos_session_verified(self):        
        self.write({'state': 'verified'})


    @api.constrains('user_id', 'state')
    def _check_unicity(self):
        # open if there is no session in 'opening_control', 'opened', 'closing_control' for one user
        if self.search_count([
                ('state', 'not in', ('closed', 'closing_control','verified')),
                ('user_id', '=', self.user_id.id),
                ('rescue', '=', False)
            ]) > 1:
            raise ValidationError(_("You cannot create two active sessions with the same responsible!"))

    @api.constrains('config_id')
    def _check_pos_config(self):
        if self.search_count([
                ('state', '!=', 'closed'),
                ('state', '!=', 'verified'),
                ('config_id', '=', self.config_id.id),
                ('rescue', '=', False)
            ]) > 1:
            raise ValidationError(_("Another session is already opened for this point of sale."))
    

class PosConfig(models.Model):
    _inherit = 'pos.config'

    def open_session_cb(self):
        """This method init the balance start in 0.00"""

        res = super(PosConfig, self).open_session_cb()
        self.current_session_id.write({
            'cash_register_balance_start': 0.00
        })

        return res

    @api.multi
    def open_session_verify(self):
        """ new session button

        create one if none exist
        access cash control interface if enabled or start a session
        """
        self.current_session_id = self.env['pos.session'].create({
            'user_id': self.env.uid,
            'config_id': self.id
        })
        if self.current_session_id.state == 'opened':
            return self.open_ui()


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def write(self, values):
        order = super(PosOrder, self).write(values)
        if self.invoice_id.id:
            channel=self.session_id.crm_team_id
            self.invoice_id.team_id=channel
        return order
