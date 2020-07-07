# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
  
#modelo para enviar datos hacia el reporte
class ReportContact(models.AbstractModel):
    #el nombre apunta hacia el reporte y ser forma por report.nombre_del_modulo.id_del_template
    _name = 'report.fertico_reports.report_contact'

    #este metodo es obligatorio es el que carga los dato que se envian al reporte
    @api.model
    def get_report_values(self, docids, data=None):
        #docids no devuelve los ids seleccionados del modelo sobre el que vamos a trabajar
        # dentro de este metodo podemos realizar todas las operacines y obtener toda la información que necesitamos 
        partners = self.env['res.partner'].browse(docids)

        docs=[]

        for partner in partners:
            moves=self.env['account.move.line'].search([('partner_id', '=', partner.id)])
            doc={'name':partner.name,
                'moves': moves
            }
            docs.append(doc)
            
        #el return devuelve un objeto con el que obtendremos los datos
        #para acceder a ellos se hace con el nombre que se da en el retur
        
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': docs
        }           