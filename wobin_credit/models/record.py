from odoo import models, fields, api

class CreditLands(models.Model):
    _name = "credit.lands"

    image = fields.Binary(string="Foto")
    comments = fields.Char(string="Comentarios")
    record_id = fields.Many2one('credit.record', string="Expediente")

class CreditRecord(models.Model):
    _name = "credit.record"

    name = fields.Char(default="Expediente borrador")
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('credit.preapplication'))
    state = fields.Selection([('draft','Borrador')], default='draft')
    partner_id = fields.Many2one('res.partner', string="Contacto")
    credit_id = fields.Many2one('credit.preapplication', string="Credito en curso")
    credit_initial = fields.Float(string="Crédito inicial")
    credit_consumed = fields.Float(string="Crédito consumido")
    credit_favor = fields.Float(string="Credito a favor")
    ine = fields.Binary(string="INE")
    curp = fields.Binary(string="CURP")
    address = fields.Binary(string="Comprobante de domicilio")
    birth_certificate = fields.Binary(string="Acta de nacimiento")
    marriage_certificate = fields.Binary(string="Acta de matrimonio")
    surface = fields.Binary(string="Comprobante de superficie")
    insurance_policy = fields.Binary(string="Póliza de seguro agrícola")
    lan_images = fields.One2many('credit.lands', 'record_id', string="Fotos del terreno")
    credit_type_id = fields.Many2one('credit.types')
    cycle =  fields.Many2one('credit.cycles', string="Ciclo")

    def create_preapplication(self):
        print("")


    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Expediente-%s' % (self.name)