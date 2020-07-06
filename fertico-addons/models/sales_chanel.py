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


class ReportPartnerLedger(models.AbstractModel):
    _name = 'report.account.report_partnerledger'

    
