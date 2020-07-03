from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    user_id = fields.Many2one('res.users', 'Salesperson', default="", domain="[('sale_team_id','!=', None)]")
    team_id = fields.Many2one('crm.team', 'Sales Channel', default="")

    @api.multi
    @api.onchange('user_id')
    def _onchange_user(self):
        """This method is activated when user_id is changed and add a domain to field team_id"""
        if self.user_id.id:
            self.team_id=self.user_id.sale_team_id.id
            return {'domain': {'team_id': [('id', '=', self.user_id.sale_team_id.id)]}}
        else:
            self.team_id=''
            return {'domain': {'team_id': []}}
            

    @api.multi
    @api.onchange('team_id')
    def _onchange_team(self):
        """This method is activated when team_id is changed and add a domain to field user_id"""
        if self.team_id.id:
            sale_team_ids=[]
            for sl in self.team_id.member_ids:
                sale_team_ids.append(sl.id)
            return {'domain': {'user_id': [('id', 'in', sale_team_ids)]}}
        else:
            self.user_id=''
            return {'domain': {'user_id': [('sale_team_id','!=', None)]}}

    @api.multi
    def action_confirm_sent(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True

    authorized_1=fields.Boolean(default=False)
    authorized_2=fields.Boolean(default=False)
    authorized_3=fields.Boolean(default=False)

    def authorize_1(self):
        self.authorized_1=True
    
    def authorize_2(self):
        self.authorized_2=True

    def authorize_3(self):
        self.authorized_3=True

    