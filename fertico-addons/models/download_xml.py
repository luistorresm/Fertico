from odoo import models, fields, api

class DownloadWizard(models.TransientModel):
    _name = "download.wizard"

    @api.multi
    def download_xml_function(self):
        invoices = self.env['account.invoice'].browse(self._context.get('active_ids'))
        print(invoices)