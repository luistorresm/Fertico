# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
  

class ReportContact(models.AbstractModel):
    _name = 'report.fertico_reports.report_contact'

    @api.model
    def get_report_values(self, docids, data=None): 
        partners = self.env['res.partner'].browse(docids)

        docs=[]

        for partner in partners:
            moves=self.env['account.move.line'].search([('partner_id', '=', partner.id)])
            doc={'name':partner.name,
                'moves': moves
            }
            docs.append(doc)
            
        
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': docs
        }           