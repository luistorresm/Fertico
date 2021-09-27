from odoo import models, fields, api

class PosSession(models.Model):
    _inherit = 'pos.session'

    POS_SESSION_STATE = [
        ('opening_control', 'Opening Control'),  # method action_pos_session_open
        ('opened', 'In Progress'),               # method action_pos_session_closing_control
        ('closing_control', 'Closing Control'),  # method action_pos_session_close
        ('closed', 'Closed & Posted'),           # method action_pos_session_verified
        ('verified', 'Verified'),
    ]

    state = fields.Selection(
        POS_SESSION_STATE)

    pos_verify = fields.Selection([('verified','Verificado'),('unverified','Sin verificar')], string="Verificado", default='unverified')

    def action_pos_session_verified(self):        
        self.pos_verify = 'verified'