from odoo import models, fields, api

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    @api.model_cr
    def disabe_payment_term(self):
        result=self._cr.execute("update account_payment_term set active=false where id="+str(self.id))