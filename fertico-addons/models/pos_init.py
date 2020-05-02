from odoo import models, fields, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    def open_existing_session_cb(self):
        
        res= super(PosConfig, self).open_existing_session_cb()

        print("===================",self.current_session_id.cash_register_balance_start)

        #record = self.env['pos.session'].search([('id', '=', self.current_session_id.id)])
        #print(record.cash_register_balance_start)
        algo=self.current_session_id.write({
            'cash_register_balance_start': False
        })
        print(algo)
        print("===================",self.current_session_id.cash_register_balance_start)
        return res
    
    '''def open_session_cb(self):
        
        res= super(PosConfig, self).open_session_cb()
        self.current_session_id.cash_register_balance_start=0
        print("===================",self.open_session_cb.id)

        return res'''