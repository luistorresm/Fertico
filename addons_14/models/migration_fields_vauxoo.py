import time
import logging
import ssl
import base64

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from pytz import timezone
from odoo import _, api, fields, models, tools


_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
except ImportError:
    _logger.warning('OpenSSL library not found. If you plan to use l10n_mx_edi, please install the library from https://pypi.python.org/pypi/pyOpenSSL')


# * / *  * / *  * / *  * / *  * / *  * / *  * / *  * / *  * / *  * / *  * / * 

# Campos que han sido mapeados de todas las clases de la Localización
# Mexicana de Vauxoo, con el fin de que cuando se cargue el nuevo volcado
# de la Base de datos de Fertico, no se pierda la información empresarial

# * / *  * / *  * / *  * / *  * / *  * / *  * / *  * / *  * / *  * / *  * / * 

class PaymentMethod(models.Model):
    """Payment Method for Mexico from SAT Data.
    Electronic documents need this information from such data.
    Here the `xsd <goo.gl/Vk3IF1>`_
    The payment method is an required attribute, to express the payment method
    of assets or services covered by the voucher.
    It is understood as a payment method legends such as check,
    credit card or debit card, deposit account, etc.
    Note: Odoo have the model payment.method, but this model need fields that
    we not need in this feature as partner_id, acquirer, etc., and they are
    there with other purpose, then a new model is necessary in order to avoid
    lose odoo's features"""

    _name = 'l10n_mx_edi.payment.method'
    _description = "Payment Method for Mexico from SAT Data"

    name = fields.Char(
        required=True,
        help='Payment way, is found in the SAT catalog.')
    code = fields.Char(
        required=True,
        help='Code defined by the SAT by this payment way. This value will '
        'be set in the XML node "metodoDePago".')
    active = fields.Boolean(
        default=True,
        help='If this payment way is not used by the company could be '
        'deactivated.')





class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    l10n_mx_tax_type = fields.Selection(
        selection=[
            ('Tasa', "Tasa"),
            ('Cuota', "Cuota"),
            ('Exento', "Exento"),
        ],
        string="Factor Type",
        default='Tasa',
        help="The CFDI version 3.3 have the attribute 'TipoFactor' in the tax lines. In it is indicated the factor "
             "type that is applied to the base of the tax.")





class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_mx_cfdi_tax_type = fields.Selection(
        selection=[
            ('Tasa', "Tasa"),
            ('Cuota', "Cuota"),
            ('Exento', "Exento"),
        ],
        string="Factor Type",
        default='Tasa',
        help="The CFDI version 3.3 have the attribute 'TipoFactor' in the tax lines. In it is indicated the factor "
             "type that is applied to the base of the tax.")






class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    l10n_mx_edi_code = fields.Char(
        'Code', help='Code defined to this position. If this record will be '
        'used as fiscal regime to CFDI, here must be assigned the code '
        'defined to this fiscal regime in the SAT catalog')






class Bank(models.Model):
    _inherit = "res.bank"

    l10n_mx_edi_code = fields.Char(
        "ABM Code",
        help="Three-digit number assigned by the ABM to identify banking "
        "institutions (ABM is an acronym for Asociación de Bancos de México)")





class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    l10n_mx_edi_clabe = fields.Char(
        "CLABE", help="Standardized banking cipher for Mexico. More info "
        "wikipedia.org/wiki/CLABE")





class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_l10n_mx_edi = fields.Boolean('Mexican Electronic Invoicing')





class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    l10n_mx_edi_force_generate_cfdi = fields.Boolean(string='Generate CFDI')
    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Way',
        help='Indicates the way the payment was/will be received, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc.')   





class AccountBankStatementImportJournalCreation(models.TransientModel):
    _inherit = 'account.bank.statement.import.journal.creation'    


    l10n_mx_address_issued_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('type', '=', 'invoice')]",
        string="Address Issued",
        help="Used in multiple-offices environments to fill, with the given address, the node 'ExpedidoEn' in the XML "
             "for invoices of this journal. If empty, the node won't be added.")
    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Way',
        help='Indicates the way the payment was/will be received, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc.')              




class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_mx_edi_payment_method_id = fields.Many2one(
        comodel_name='l10n_mx_edi.payment.method',
        string="Payment Way",
        help="Indicates the way the payment was/will be received, where the options could be: "
             "Cash, Nominal Check, Credit Card, etc.")





class AccountMove(models.Model):
    _inherit = 'account.move'

    # ==== CFDI flow fields ====
    l10n_mx_edi_cfdi_request = fields.Selection(
        selection=[
            ('on_invoice', "On Invoice"),
            ('on_refund', "On Credit Note"),
            ('on_payment', "On Payment"),
        ],
        string="Request a CFDI", store=True,
        #compute='_compute_l10n_mx_edi_cfdi_request',
        help="Flag indicating a CFDI should be generated for this journal entry.")
    l10n_mx_edi_sat_status = fields.Selection(
        selection=[
            ('none', "State not defined"),
            ('undefined', "Not Synced Yet"),
            ('not_found', "Not Found"),
            ('cancelled', "Cancelled"),
            ('valid', "Valid"),
        ],
        string="SAT status", readonly=True, copy=False, required=True, tracking=True,
        default='undefined',
        help="Refers to the status of the journal entry inside the SAT system.")
    l10n_mx_edi_post_time = fields.Datetime(
        string="Posted Time", readonly=True, copy=False,
        help="Keep empty to use the current México central time")
    l10n_mx_edi_usage = fields.Selection(
        selection=[
            ('G01', 'Acquisition of merchandise'),
            ('G02', 'Returns, discounts or bonuses'),
            ('G03', 'General expenses'),
            ('I01', 'Constructions'),
            ('I02', 'Office furniture and equipment investment'),
            ('I03', 'Transportation equipment'),
            ('I04', 'Computer equipment and accessories'),
            ('I05', 'Dices, dies, molds, matrices and tooling'),
            ('I06', 'Telephone communications'),
            ('I07', 'Satellite communications'),
            ('I08', 'Other machinery and equipment'),
            ('D01', 'Medical, dental and hospital expenses.'),
            ('D02', 'Medical expenses for disability'),
            ('D03', 'Funeral expenses'),
            ('D04', 'Donations'),
            ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
            ('D06', 'Voluntary contributions to SAR'),
            ('D07', 'Medical insurance premiums'),
            ('D08', 'Mandatory School Transportation Expenses'),
            ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
            ('D10', 'Payments for educational services (Colegiatura)'),
            ('P01', 'To define'),
        ],
        string="Usage",
        default='P01',
        help="Used in CFDI 3.3 to express the key to the usage that will gives the receiver to this invoice. This "
             "value is defined by the customer.\nNote: It is not cause for cancellation if the key set is not the usage "
             "that will give the receiver of the document.")
    l10n_mx_edi_origin = fields.Char(
        string='CFDI Origin',
        copy=False,
        help="In some cases like payments, credit notes, debit notes, invoices re-signed or invoices that are redone "
             "due to payment in advance will need this field filled, the format is:\n"
             "Origin Type|UUID1, UUID2, ...., UUIDn.\n"
             "Where the origin type could be:\n"
             "- 01: Nota de crédito\n"
             "- 02: Nota de débito de los documentos relacionados\n"
             "- 03: Devolución de mercancía sobre facturas o traslados previos\n"
             "- 04: Sustitución de los CFDI previos\n"
             "- 05: Traslados de mercancias facturados previamente\n"
             "- 06: Factura generada por los traslados previos\n"
             "- 07: CFDI por aplicación de anticipo")

    # ==== CFDI certificate fields ====
    l10n_mx_edi_certificate_id = fields.Many2one(
        comodel_name='l10n_mx_edi.certificate',
        string="Source Certificate")
    l10n_mx_edi_cer_source = fields.Char(
        string='Certificate Source',
        help="Used in CFDI like attribute derived from the exception of certificates of Origin of the "
             "Free Trade Agreements that Mexico has celebrated with several countries. If it has a value, it will "
             "indicate that it serves as certificate of origin and this value will be set in the CFDI node "
             "'NumCertificadoOrigen'.")

    # ==== CFDI attachment fields ====
    l10n_mx_edi_cfdi_uuid = fields.Char(string='Fiscal Folio', copy=False, readonly=True,
        help='Folio in electronic invoice, is returned by SAT when send to stamp.')
    l10n_mx_edi_cfdi_supplier_rfc = fields.Char(string='Supplier RFC', copy=False, readonly=True,
        help='The supplier tax identification number.')
    l10n_mx_edi_cfdi_customer_rfc = fields.Char(string='Customer RFC', copy=False, readonly=True,
        help='The customer tax identification number.')
    l10n_mx_edi_cfdi_amount = fields.Monetary(string='Total Amount', copy=False, readonly=True,
        help='The total amount reported on the cfdi.')

    # ==== Other fields ====
    l10n_mx_edi_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method',
        string="Payment Way",
        help="Indicates the way the invoice was/will be paid, where the options could be: "
             "Cash, Nominal Check, Credit Card, etc. Leave empty if unkown and the XML will show 'Unidentified'.",
        default=lambda self: self.env.ref('l10n_mx_edi.payment_method_otros', raise_if_not_found=False))
    l10n_mx_edi_payment_policy = fields.Selection(string='Payment Policy',
        selection=[('PPD', 'PPD'), ('PUE', 'PUE')],
        compute='_compute_l10n_mx_edi_payment_policy')

    l10n_mx_edi_external_trade = fields.Boolean(
        string="Need external trade?",
        #readonly=False, store=True,
        #compute='_compute_l10n_mx_edi_external_trade',
        help="If this field is active, the CFDI that generates this invoice will include the complement "
             "'External Trade'.")        
    l10n_mx_closing_move = fields.Boolean(
        string='Closing move',
        help='Journal Entry closing the fiscal year.', readonly=True, default=False)             





class AccountPayment(models.Model):
    _inherit = 'account.payment'

    l10n_mx_edi_force_generate_cfdi = fields.Boolean(string='Generate CFDI')





class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    l10n_mx_edi_payment_method_id = fields.Many2one(
        comodel_name='l10n_mx_edi.payment.method',
        string="Payment Way",
        readonly=False, store=True,
        compute='_compute_l10n_mx_edi_payment_method_id',
        help="Indicates the way the payment was/will be received, where the options could be: "
             "Cash, Nominal Check, Credit Card, etc.")





class IrView(models.Model):
    _inherit = 'ir.ui.view'

    l10n_mx_edi_addenda_flag = fields.Boolean(
        string='Is an addenda?',
        help='If True, the view is an addenda for the Mexican EDI invoicing.',
        default=False)





class Certificate(models.Model):
    _name = 'l10n_mx_edi.certificate'
    _description = 'SAT Digital Sail'
    _order = "date_start desc, id desc"

    content = fields.Binary(
        string='Certificate',
        help='Certificate in der format',
        required=True,
        attachment=False,)
    key = fields.Binary(
        string='Certificate Key',
        help='Certificate Key in der format',
        required=True,
        attachment=False,)
    password = fields.Char(
        string='Certificate Password',
        help='Password for the Certificate Key',
        required=True,)
    serial_number = fields.Char(
        string='Serial number',
        help='The serial number to add to electronic documents',
        readonly=True,
        index=True)
    date_start = fields.Datetime(
        string='Available date',
        help='The date on which the certificate starts to be valid',
        readonly=True)
    date_end = fields.Datetime(
        string='Expiration date',
        help='The date on which the certificate expires',
        readonly=True)

    def get_valid_certificate(self):
        '''Search for a valid certificate that is available and not expired.
        '''
        mexican_dt = self.get_mx_current_datetime()
        for record in self:
            date_start = str_to_datetime(record.date_start)
            date_end = str_to_datetime(record.date_end)
            if date_start <= mexican_dt <= date_end:
                return record
        return None

    def get_mx_current_datetime(self):
        '''Get the current datetime with the Mexican timezone.
        '''
        return fields.Datetime.context_timestamp(
            self.with_context(tz='America/Mexico_City'), fields.Datetime.now())

    def get_data(self):
        '''Return the content (b64 encoded) and the certificate decrypted
        '''
        self.ensure_one()
        cer_pem = self.get_pem_cer(self.content)
        certificate = crypto.load_certificate(crypto.FILETYPE_PEM, cer_pem)
        for to_del in ['\n', ssl.PEM_HEADER, ssl.PEM_FOOTER]:
            cer_pem = cer_pem.replace(to_del.encode('UTF-8'), b'')
        return cer_pem, certificate

    @tools.ormcache('content')
    def get_pem_cer(self, content):
        '''Get the current content in PEM format
        '''
        self.ensure_one()
        return ssl.DER_cert_to_PEM_cert(base64.decodebytes(content)).encode('UTF-8')

    def get_encrypted_cadena(self, cadena):
        '''Encrypt the cadena using the private key.
        '''
        self.ensure_one()
        key_pem = self.get_pem_key(self.key, self.password)
        private_key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_pem)
        encrypt = 'sha256WithRSAEncryption'
        cadena_crypted = crypto.sign(private_key, cadena, encrypt)
        return base64.b64encode(cadena_crypted)


def str_to_datetime(dt_str, tz=timezone('America/Mexico_City')):
    return tz.localize(fields.Datetime.from_string(dt_str))



class ResBank(models.Model):
    _inherit = "res.bank"

    l10n_mx_edi_vat = fields.Char(
        string="VAT",
        help="Indicate the VAT of this institution, the value could be used in the payment complement in Mexico "
             "documents")





class City(models.Model):
    _inherit = 'res.city'

    l10n_mx_edi_code = fields.Char(
        string="Code MX",
        help="Code to use in the CFDI with external trade complement. It is based on the SAT catalog.")






class ResCompany(models.Model):
    _inherit = 'res.company'

    # == PAC web-services ==
    l10n_mx_edi_pac = fields.Selection(
        selection=[('finkok', 'Quadrum (formerly finkok)'), ('solfact', 'Solucion Factible'),
                   ('sw', 'SW sapien-SmarterWEB')],
        string='PAC',
        help='The PAC that will sign/cancel the invoices',
        default='finkok')
    l10n_mx_edi_pac_test_env = fields.Boolean(
        string='PAC test environment',
        help='Enable the usage of test credentials',
        default=False)
    l10n_mx_edi_pac_username = fields.Char(
        string='PAC username',
        help='The username used to request the seal from the PAC')
    l10n_mx_edi_pac_password = fields.Char(
        string='PAC password',
        help='The password used to request the seal from the PAC')
    l10n_mx_edi_certificate_ids = fields.Many2many('l10n_mx_edi.certificate',
        string='Certificates')

    # == Address ==
    l10n_mx_edi_colony_code = fields.Char(
        string='Colony Code',
        compute='_compute_l10n_mx_edi_colony_code',
        inverse='_inverse_l10n_mx_edi_colony_code',
        help='Colony Code configured for this company. It is used in the '
        'external trade complement to define the colony where the domicile '
        'is located.')
    l10n_mx_edi_colony = fields.Char(
        compute='_compute_l10n_mx_edi_colony',
        inverse='_inverse_l10n_mx_edi_colony')

    # == CFDI EDI ==
    l10n_mx_edi_fiscal_regime = fields.Selection(
        [('601', 'General de Ley Personas Morales'),
         ('603', 'Personas Morales con Fines no Lucrativos'),
         ('605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios'),
         ('606', 'Arrendamiento'),
         ('607', 'Régimen de Enajenación o Adquisición de Bienes'),
         ('608', 'Demás ingresos'),
         ('609', 'Consolidación'),
         ('610', 'Residentes en el Extranjero sin Establecimiento Permanente en México'),
         ('611', 'Ingresos por Dividendos (socios y accionistas)'),
         ('612', 'Personas Físicas con Actividades Empresariales y Profesionales'),
         ('614', 'Ingresos por intereses'),
         ('615', 'Régimen de los ingresos por obtención de premios'),
         ('616', 'Sin obligaciones fiscales'),
         ('620', 'Sociedades Cooperativas de Producción que optan por diferir sus ingresos'),
         ('621', 'Incorporación Fiscal'),
         ('622', 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras'),
         ('623', 'Opcional para Grupos de Sociedades'),
         ('624', 'Coordinados'),
         ('625', 'Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas'),
         ('628', 'Hidrocarburos'),
         ('629', 'De los Regímenes Fiscales Preferentes y de las Empresas Multinacionales'),
         ('630', 'Enajenación de acciones en bolsa de valores')],
        string="Fiscal Regime",
        help="It is used to fill Mexican XML CFDI required field "
        "Comprobante.Emisor.RegimenFiscal.")





class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # == PAC web-services ==
    l10n_mx_edi_pac = fields.Selection(
        related='company_id.l10n_mx_edi_pac', readonly=False,
        string='MX PAC*')
    l10n_mx_edi_pac_test_env = fields.Boolean(
        related='company_id.l10n_mx_edi_pac_test_env', readonly=False,
        string='MX PAC test environment*')
    l10n_mx_edi_pac_username = fields.Char(
        related='company_id.l10n_mx_edi_pac_username', readonly=False,
        string='MX PAC username*')
    l10n_mx_edi_pac_password = fields.Char(
        related='company_id.l10n_mx_edi_pac_password', readonly=False,
        string='MX PAC password*')
    l10n_mx_edi_certificate_ids = fields.Many2many(
        related='company_id.l10n_mx_edi_certificate_ids', readonly=False,
        string='MX Certificates*')

    # == CFDI EDI ==
    l10n_mx_edi_fiscal_regime = fields.Selection(
        related='company_id.l10n_mx_edi_fiscal_regime', readonly=False,
        string="Fiscal Regime",
        help="It is used to fill Mexican XML CFDI required field "
        "Comprobante.Emisor.RegimenFiscal.")





class ResCountry(models.Model):
    _inherit = 'res.country'

    l10n_mx_edi_code = fields.Char(
        'Code MX', help='Country code defined by the SAT in the catalog to '
        'CFDI version 3.3 and new complements. Will be used in the CFDI '
        'to indicate the country reference.')





class ResCurrency(models.Model):
    _inherit = 'res.currency'

    l10n_mx_edi_decimal_places = fields.Integer(
        'Number of decimals', readonly=True,
        help='Number of decimals to be supported for this currency, according '
        'to the SAT. It will be used in the CFDI to format amounts.')





class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_mx_edi_colony = fields.Char(
        string="Colony Name")
    l10n_mx_edi_colony_code = fields.Char(
        string="Colony Code",
        help="Note: Only use this field if this partner is the company address or if it is a branch office.\n"
             "Colony code that will be used in the CFDI with the external trade as Emitter colony. It must be a code "
             "from the SAT catalog.")          

    # == Addenda ==
    l10n_mx_edi_addenda = fields.Many2one(
        comodel_name='ir.ui.view',
        string="Addenda",
        help="A view representing the addenda",
        domain=[('l10n_mx_edi_addenda_flag', '=', True)])
    l10n_mx_edi_addenda_doc = fields.Html(
        string="Addenda Documentation",
        help="How should be done the addenda for this customer (try to put human readable information here to help the "
             "invoice people to fill properly the fields in the invoice)")






class ResUsers(models.Model):
    _inherit = 'res.users'

    l10n_mx_nationality = fields.Char(
        help='Nationality based in the supplier country. Is the '
        'seventh column in DIOT report',
        compute='_compute_nationality', inverse='_inverse_nationality')
    l10n_mx_type_of_third = fields.Char(
        compute='_compute_type_of_third',
        help='Indicate the type of third that is the supplier. Is the first '
        'column in DIOT report.')        
    l10n_mx_type_of_operation = fields.Selection([
        ('03', ' 03 - Provision of Professional Services'),
        ('06', ' 06 - Renting of buildings'),
        ('85', ' 85 - Others')],
        help='Indicate the operations type that makes this supplier. Is the '
        'second column in DIOT report')
    # == Address ==
    l10n_mx_edi_locality = fields.Char(
        string="Locality Name"),
        #store=True, readonly=False,
        #compute='_compute_l10n_mx_edi_locality')
    l10n_mx_edi_addenda_doc = fields.Html(
        string="Addenda Documentation",
        help="How should be done the addenda for this customer (try to put human readable information here to help the "
             "invoice people to fill properly the fields in the invoice)")
    l10n_mx_edi_colony = fields.Char(
        string="Colony Name") 
    # == Addenda ==
    l10n_mx_edi_addenda = fields.Many2one(
        comodel_name='ir.ui.view',
        string="Addenda",
        help="A view representing the addenda",
        domain=[('l10n_mx_edi_addenda_flag', '=', True)]) 
    l10n_mx_edi_usage = fields.Selection(
        selection=[
            ('G01', 'Acquisition of merchandise'),
            ('G02', 'Returns, discounts or bonuses'),
            ('G03', 'General expenses'),
            ('I01', 'Constructions'),
            ('I02', 'Office furniture and equipment investment'),
            ('I03', 'Transportation equipment'),
            ('I04', 'Computer equipment and accessories'),
            ('I05', 'Dices, dies, molds, matrices and tooling'),
            ('I06', 'Telephone communications'),
            ('I07', 'Satellite communications'),
            ('I08', 'Other machinery and equipment'),
            ('D01', 'Medical, dental and hospital expenses.'),
            ('D02', 'Medical expenses for disability'),
            ('D03', 'Funeral expenses'),
            ('D04', 'Donations'),
            ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
            ('D06', 'Voluntary contributions to SAR'),
            ('D07', 'Medical insurance premiums'),
            ('D08', 'Mandatory School Transportation Expenses'),
            ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
            ('D10', 'Payments for educational services (Colegiatura)'),
            ('P01', 'To define'),
        ],
        string="Usage",
        default='P01',
        help="Used in CFDI 3.3 to express the key to the usage that will gives the receiver to this invoice. This "
             "value is defined by the customer.\nNote: It is not cause for cancellation if the key set is not the usage "
             "that will give the receiver of the document.")
    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Method',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Indicates the way the payment was/will be received, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc.')             






class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_mx_address_issued_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('type', '=', 'invoice')]",
        string="Address Issued",
        help="Used in multiple-offices environments to fill, with the given address, the node 'ExpedidoEn' in the XML "
             "for invoices of this journal. If empty, the node won't be added.")






# Campos de UoM para que funcionen algunos campos de account.move.lines
"""
class UoMCategory(models.Model):
    _name = 'uom.category'
    _description = 'Product UoM Categories'

    name = fields.Char('Unit of Measure Category', required=True, translate=True)
    measure_type = fields.Selection([
        ('unit', 'Units'),
        ('weight', 'Weight'),
        ('time', 'Time'),
        ('length', 'Length'),
        ('volume', 'Volume'),
    ], string="Type of Measure")


class UoM(models.Model):
    _name = 'uom.uom'
    _description = 'Product Unit of Measure'
    _order = "name"

    name = fields.Char('Unit of Measure', required=True, translate=True)
    category_id = fields.Many2one(
        'uom.category', 'Category', required=True, ondelete='cascade',
        help="Conversion between Units of Measure can only occur if they belong to the same category. The conversion will be made based on the ratios.")
    factor = fields.Float(
        'Ratio', default=1.0, digits=0, required=True,  # force NUMERIC with unlimited precision
        help='How much bigger or smaller this unit is compared to the reference Unit of Measure for this category: 1 * (reference unit) = ratio * (this unit)')
    factor_inv = fields.Float(
        'Bigger Ratio', compute='_compute_factor_inv', digits=0,  # force NUMERIC with unlimited precision
        readonly=True, required=True,
        help='How many times this Unit of Measure is bigger than the reference Unit of Measure in this category: 1 * (this unit) = ratio * (reference unit)')
    rounding = fields.Float(
        'Rounding Precision', default=0.01, digits=0, required=True,
        help="The computed quantity will be a multiple of this value. "
             "Use 1.0 for a Unit of Measure that cannot be further split, such as a piece.")
    active = fields.Boolean('Active', default=True, help="Uncheck the active field to disable a unit of measure without deleting it.")
    uom_type = fields.Selection([
        ('bigger', 'Bigger than the reference Unit of Measure'),
        ('reference', 'Reference Unit of Measure for this category'),
        ('smaller', 'Smaller than the reference Unit of Measure')], 'Type',
        default='reference', required=1)
    measure_type = fields.Selection(string="Type of measurement category", 
                                    related='category_id.measure_type',  #Comentado de related
                                    store=True, readonly=True)

    _sql_constraints = [
        ('factor_gt_zero', 'CHECK (factor!=0)', 'The conversion ratio for a unit of measure cannot be 0!'),
        ('rounding_gt_zero', 'CHECK (rounding>0)', 'The rounding precision must be strictly positive.'),
        ('factor_reference_is_one', "CHECK((uom_type = 'reference' AND factor = 1.0) OR (uom_type != 'reference'))", "The reference unit must have a conversion factor equal to 1.")
    ]
"""    








class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_id = fields.Many2one('product.product', string='Product') #Campo agregado
    l10n_mx_edi_customs_number = fields.Char(
        help='Optional field for entering the customs information in the case '
        'of first-hand sales of imported goods or in the case of foreign trade'
        ' operations with goods or services.\n'
        'The format must be:\n'
        ' - 2 digits of the year of validation followed by two spaces.\n'
        ' - 2 digits of customs clearance followed by two spaces.\n'
        ' - 4 digits of the serial number followed by two spaces.\n'
        ' - 1 digit corresponding to the last digit of the current year, '
        'except in case of a consolidated customs initiated in the previous '
        'year of the original request for a rectification.\n'
        ' - 6 digits of the progressive numbering of the custom.',
        string='Customs number',
        copy=False)
    l10n_mx_edi_umt_aduana_id = fields.Many2one(
        comodel_name='uom.uom',
        string="UMT Aduana",
        readonly=True, store=True, compute_sudo=True,
        #related='product_id.l10n_mx_edi_umt_aduana_id', RELATED COMENTADO
        help="Used in complement 'Comercio Exterior' to indicate in the products the TIGIE Units of Measurement. "
             "It is based in the SAT catalog.")
    l10n_mx_edi_qty_umt = fields.Float(
        string="Qty UMT",
        digits='Product Unit of Measure',
        #readonly=False, store=True,  
        #compute='_compute_l10n_mx_edi_qty_umt',
        help="Quantity expressed in the UMT from product. It is used in the attribute 'CantidadAduana' in the CFDI")
    l10n_mx_edi_price_unit_umt = fields.Float(
        string="Unit Value UMT",
        #readonly=True, store=True,
        #compute='_compute_l10n_mx_edi_price_unit_umt',
        help="Unit value expressed in the UMT from product. It is used in the attribute 'ValorUnitarioAduana' in the "
             "CFDI")





class L10nMxEdiResLocality(models.Model):
    _name = 'l10n_mx_edi.res.locality'
    _description = 'Locality'

    name = fields.Char(required=True, translate=True)
    country_id = fields.Many2one(
        'res.country', string='Country', required=True)
    state_id = fields.Many2one(
        'res.country.state', 'State',
        domain="[('country_id', '=', country_id)]", required=True)
    code = fields.Char()





class L10nMXEdiTariffFraction(models.Model):
    _name = 'l10n_mx_edi.tariff.fraction'
    _description = "Mexican EDI Tariff Fraction"

    code = fields.Char(
        help="Code defined in the SAT to this record.")
    name = fields.Char(
        help="Name defined in the SAT catalog to this record.")
    uom_code = fields.Char(
        help="UoM code related with this tariff fraction. This value is defined in the SAT catalog and will be "
             "assigned in the attribute 'UnidadAduana' in the merchandise.")
    active = fields.Boolean(
        help="If the tariff fraction has expired it could be disabled to do not allow select the record.", default=True)






class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_mx_edi_tariff_fraction_id = fields.Many2one(
        comodel_name='l10n_mx_edi.tariff.fraction',
        string="Tariff Fraction",
        help="It is used to express the key of the tariff fraction corresponding to the description of the product to "
             "export.")
    l10n_mx_edi_umt_aduana_id = fields.Many2one(
        comodel_name='uom.uom',
        string="UMT Aduana",
        help="Used in complement 'Comercio Exterior' to indicate in the products the TIGIE Units of Measurement. "
             "It is based in the SAT catalog.")





class ResCompany(models.Model):
    _inherit = 'res.company'

    # == Address ==
    l10n_mx_edi_locality = fields.Char(
        compute='_compute_l10n_mx_edi_locality',
        inverse='_inverse_l10n_mx_edi_locality')
    l10n_mx_edi_locality_id = fields.Many2one(
        'l10n_mx_edi.res.locality', string='Locality',
        related='partner_id.l10n_mx_edi_locality_id', readonly=False,
        help='Municipality configured for this company')

    # == External Trade ==
    l10n_mx_edi_num_exporter = fields.Char(
        'Number of Reliable Exporter',
        help='Indicates the number of reliable exporter in accordance '
        'with Article 22 of Annex 1 of the Free Trade Agreement with the '
        'European Association and the Decision of the European Community. '
        'Used in External Trade in the attribute "NumeroExportadorConfiable".')





class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # == External Trade==
    l10n_mx_edi_num_exporter = fields.Char(
        related='company_id.l10n_mx_edi_num_exporter', readonly=False,
        string='Number of Reliable Exporter')





class ResPartner(models.Model):
    _inherit = 'res.partner'

    # == Address ==
    l10n_mx_edi_locality = fields.Char(
        string="Locality Name"),
        #store=True, readonly=False,
        #compute='_compute_l10n_mx_edi_locality')
    l10n_mx_edi_locality_id = fields.Many2one(
        comodel_name='l10n_mx_edi.res.locality',
        string="Locality",
        help="Optional attribute used in the XML that serves to define the locality where the domicile is located.")

    # == External Trade ==
    l10n_mx_edi_curp = fields.Char(
        string="CURP", size=18,
        help="In Mexico, the Single Code of Population Registration (CURP) is a unique alphanumeric code of 18 "
             "characters used to officially identify both residents and Mexican citizens throughout the country.")
    l10n_mx_edi_external_trade = fields.Boolean(
        'Need external trade?', help='check this box to add by default '
        'the external trade complement in invoices for this customer.')       





"""
class ProductUoM(models.Model):
    _name = 'uom.uom'

    l10n_mx_edi_code_aduana = fields.Char(
        string="Customs code",
        help="Used in the complement of 'Comercio Exterior' to indicate in the products the UoM. It is based in the "
             "SAT catalog.")





class StockLandedCost(models.Model):
    _name = 'stock.landed.cost'

    l10n_mx_edi_customs_number = fields.Char(
        help='Optional field for entering the customs information in the case '
        'of first-hand sales of imported goods or in the case of foreign trade'
        ' operations with goods or services.\n'
        'The format must be:\n'
        ' - 2 digits of the year of validation followed by two spaces.\n'
        ' - 2 digits of customs clearance followed by two spaces.\n'
        ' - 4 digits of the serial number followed by two spaces.\n'
        ' - 1 digit corresponding to the last digit of the current year, '
        'except in case of a consolidated customs initiated in the previous '
        'year of the original request for a rectification.\n'
        ' - 6 digits of the progressive numbering of the custom.',
        string='Customs number', size=21, copy=False)
"""




class StockMove(models.Model):

    _inherit = 'stock.move'

    move_orig_fifo_ids = fields.Many2many(
        'stock.move', 'stock_move_move_fifo_rel', 'move_dest_id',
        'move_orig_id', 'Original Fifo Move',
        help="Optional: previous stock move when chaining them")        





class Country(models.Model):
    _inherit = 'res.country'

    demonym = fields.Char(translate=True, help="Adjective for relationship"
                          " between a person and a country.")





class ResPartner(models.Model):
    """Inherited to complete the attributes required to DIOT Report

    Added required fields according with the provisions in the next SAT
    document `Document <goo.gl/THPLDk>`_. To allow generate the form A-29
    requested by this SAT.
    """
    _inherit = 'res.partner'

    l10n_mx_type_of_third = fields.Char(
        compute='_compute_type_of_third',
        help='Indicate the type of third that is the supplier. Is the first '
        'column in DIOT report.')
    l10n_mx_type_of_operation = fields.Selection([
        ('03', ' 03 - Provision of Professional Services'),
        ('06', ' 06 - Renting of buildings'),
        ('85', ' 85 - Others')],
        help='Indicate the operations type that makes this supplier. Is the '
        'second column in DIOT report')
    l10n_mx_nationality = fields.Char(
        help='Nationality based in the supplier country. Is the '
        'seventh column in DIOT report',
        compute='_compute_nationality', inverse='_inverse_nationality')








# //////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////

#  INTENTO DE MAPEO DE LOCALIZACION DE ODOO VERSION 11.0 
#  por consultar vistas del sistema

# //////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////

class Partner(models.Model):
    _inherit = "res.partner"

    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string="Payment Method",
        help='This payment method will be used by default in the related '
        'documents (invoices, payments, and bank statements).')#,
        #default=lambda self: self.env.ref('l10n_mx_edi.payment_method_otros',
        #                                  raise_if_not_found=False))
    """
    l10n_mx_edi_donations = fields.Boolean(
        'Need donations?',
        help='Use this field when the invoice require the complement to '
        '"Donations". This value will be used to indicate the use of the '
        'information from the document that authorize to receive '
        'deductible donations, granted by SAT')
    
    l10n_mx_edi_voucher_nss = fields.Char(
        'NSS', help='Optional attribute to express the Employee Social '
        'Security Number'
    )  
    """
    # --> Campo ya conseguido por las definiiciones de arriba <--  
    # 
    #
    #def _get_usage_selection(self):
        #return self.env['account.move'].fields_get().get(
        #   'l10n_mx_edi_usage').get('selection')   #EDITADO DE ACCOUNT.INVOICE   
    #
    #     
    #l10n_mx_edi_usage = fields.Selection(
    #    _get_usage_selection, 'Usage', default='P01',
    #    help='This usage will be used instead of the default one for invoices.'
    #)  
    """
    l10n_mx_edi_property_licence = fields.Char(
        'Licence Number', help='Permission number, licence or authorization '
        'of construction provided by the borrower of the partial construction '
        'services. If this is the address in construction assign here the '
        'licence number.')
    l10n_mx_edi_is_indirect = fields.Boolean(
        'Indirect Supplier',
        help="When marked, the Acknowledgment of receipt and the Purchase "
        "Order fields on the portal are required.",
        oldname='l10n_mx_ed_is_indirect') 
    """               





class ProductSatCode(models.Model):
    #Added to manage the product codes from SAT master data
    #This code must be defined in CFDI 3.3, in each concept, and this is set
    #by each product.
    #Is defined a new catalog to only allow select the codes defined by the SAT
    #that are load by data in the system.
    #This catalog is found `here <https://goo.gl/iAUGEh>`_ in the page
    #c_ClaveProdServ.

    #This model also is used to define the uom code defined by the SAT

    _name = 'l10n_mx_edi.product.sat.code'

    code = fields.Char(
        help='This value is required in CFDI version 3.3 to express the '
        'code of product or service covered by the present concept. Must be '
        'used a key from SAT catalog.', required=True)
    name = fields.Char(
        help='Name defined by SAT catalog to this product',
        required=True)
    applies_to = fields.Selection([
        ('product', 'Product'),
        ('uom', 'UoM'),
    ], required=True,
        help='Indicate if this code could be used in products or in UoM',)
    active = fields.Boolean(
        help='If this record is not active, this cannot be selected.',
        default=True)






class ProductProduct(models.Model):
    _inherit = 'product.product'

    l10n_mx_edi_code_sat_id = fields.Many2one(
        'l10n_mx_edi.product.sat.code', 'Code SAT',
        help='This value is required in CFDI version 3.3 to express the code '
        'of the product or service covered by the present concept. Must be '
        'used a key from the SAT catalog.',
        domain=[('applies_to', '=', 'product')]) 
    l10n_mx_edi_umt_aduana_id = fields.Many2one(
        comodel_name='uom.uom',
        string="UMT Aduana",
        help="Used in complement 'Comercio Exterior' to indicate in the products the TIGIE Units of Measurement. "
             "It is based in the SAT catalog.")        






class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_mx_edi_airline_type = fields.Selection([
        ('tua', 'TUA'),
        ('extra', 'Extra Charge'),
    ],string='Flight Extra Fee',
      help='Select a product type if the product is and Airport Use Fee or '
           'an IATA extra charge'
    )
    l10n_mx_edi_ct_type = fields.Selection(
        selection=[
            ('purchase', 'Purchase'),
            ('sale', 'Sale'),
        ], string='Exchange operation type',
        help="When this product is intended to be used to trade currencies, "
        "specifies the type of operation, i.e. if it's a purchase or sale.\n"
        "If set, this field will be used to create and fill the complement's "
        "XML node into the CFDI. If this field is not set in any of the "
        "invoice products, the complement will not be used and the XML node "
        "will not be included.") 
    l10n_mx_edi_art_complement = fields.Selection([
        ('eapa', 'Alienation of Works of Plastic Arts and Antiques'),
        ('pee', 'Payment in Kind')
    ], help='Choose the complemento to use', string='Art Complement')
    l10n_mx_edi_good_type = fields.Selection([
        ('01', 'Picture'),
        ('02', 'Engraved'),
        ('03', 'Sculpture'),
        ('04', 'Others')], help='If this is an art, assign which art type is '
        'this good.', string='Good type')
    l10n_mx_edi_other_good_type = fields.Char(
        'Good type',
        help="If the 'Good Type' is '04', assign the type of this art.")
    l10n_mx_edi_acquisition = fields.Selection([
        ('01', 'Purchase'),
        ('02', 'Donation'),
        ('03', 'Heritage'),
        ('04', 'Legacy'),
        ('05', 'Others')], 'Acquisition',
        help='Assign the way like was acquired this good')
    l10n_mx_edi_other_good_type = fields.Char(
        'Other good type', help="If the 'Acquisition' is '05', assign the "
        "acquisition way to this art.")
    l10n_mx_edi_tax_paid = fields.Float(
        'Tax paid', help='Assign the tax amount paid by the acquisition')
    l10n_mx_edi_acquisition_date = fields.Date(
        'Acquisition date', help='Indicate the acquisition date.')
    l10n_mx_edi_characteristic = fields.Selection([
        ('01', 'Signed'),
        ('02', 'Dated'),
        ('03', 'Framed'),
        ('04', 'Armelladas'),
        ('05', 'Wiring'),
        ('06', 'Serial number'),
        ('07', '2 or more characteristics')], 'Characteristic',
        help='Characteristic of the piece according with the SAT catalog.')
    l10n_mx_edi_pik_dimension = fields.Char(
        string='Piece of Art Dimensions',
        help='Dimensions of the piece of art'
    )   
    l10n_mx_edi_fuel_billing = fields.Boolean(
        string="Need fuel billing?",
        help="Add complements for fuel consumption when invoicing this "
        "product")         
    l10n_mx_edi_tpe_track = fields.Selection([
        ('airway', 'Airway'),
        ('seaway', 'Seaway'),
        ('terrestrial', 'Terrestrial'),
    ],
        string='Track',
        help='Attribute required to express if it is via Air, Maritime or '
        'Terrestrial.')     
    l10n_mx_edi_code_sat_id = fields.Many2one(
        'l10n_mx_edi.product.sat.code', 'Code SAT',
        help='This value is required in CFDI version 3.3 to express the code '
        'of the product or service covered by the present concept. Must be '
        'used a key from the SAT catalog.',
        domain=[('applies_to', '=', 'product')])    





class ProductUoM(models.Model):
    _name = 'product.uom'

    l10n_mx_edi_code_sat_id = fields.Many2one(
        'l10n_mx_edi.product.sat.code', 'Code SAT',
        help='This value is required in CFDI version 3.3 to specify '
        'the standardized unit of measure code applicable to the quantity '
        'expressed in the concept. The unit must correspond to the '
        'description in the concept.', domain=[('applies_to', '=', 'uom')])        






class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_mx_addenda = fields.Selection([
        ('chrysler', 'Chrysler'),
        ('ford', 'Ford'),
        ('porcelanite', 'Porcelanite'),
        ('bosh', 'Bosh'),
        ('nissan', 'Nissan'),
        ('femsa', 'Femsa'),
        ('mabe', 'Mabe'),
        ('calsonic_kansei', 'Calsonic Kansei'),
        ('ahmsa', 'AHMSA'),
        ('faurecia', 'Faurecia'),
        ('pepsico', 'PepsiCo'),
        ('aam', 'AAM'),
        ('agnico', 'Agnico'),
        ('edumex', 'Edumex'),
        ('encinas', 'Encinas'),
        ('envases', 'Envases'),
        ('flextronics', 'Flextronics'),
        ('nestle', 'Nestle'),
        ('sanmina', 'Sanmina'),
        ('sidel', 'Sidel'),
        ('vallen', 'Vallen'),
        ('zfmexico', 'ZF Mexico'),
    ], default='')
    """    
    l10n_mx_edi_product_advance_id = fields.Many2one(
        'product.product', 'Advance product', readonly=False,
        related='company_id.l10n_mx_edi_product_advance_id',
        help='This product will be used in the advance invoices that are '
        'created automatically when is registered a payment without documents '
        'related or with a difference in favor of the customer.')

    l10n_mx_edi_journal_advance_id = fields.Many2one(
        'account.journal', 'Advance Journal', readonly=False,
        related='company_id.l10n_mx_edi_journal_advance_id',
        help='This journal will be used in the advance invoices that are '
        'created automatically when is registered a payment without documents '
        'related or with a difference in favor of the customer.')             
    l10n_mx_edi_minimum_wage = fields.Float(
        related='company_id.l10n_mx_edi_minimum_wage',
        string='Mexican minimum salary', readonly=False,
        help='Indicates the current daily amount of the general minimum wage '
        'in Mexico')  
    """               





class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_mx_edi_amount_authorized_diff = fields.Float(
        'Amount Authorized Difference (Invoice)', limit=1,
        help='This field depicts the maximum difference allowed between a '
        'CFDI and an invoice. When validate an invoice will be verified that '
        'the amount total is the same of the total in the invoice, or the '
        'difference is less that this value.')






class L10nMxEdiIneEntity(models.Model):
    _name = 'l10n_mx_edi_ine.entity'
    _description = 'Entity'

    l10n_mx_edi_ine_entity_id = fields.Many2one(
        'res.country.state',
        string='Entity Code',
        help='Attribute required to register the key of the entity '
        'to which the expense applies. Set this when Process Type is Campaign '
        'or Pre-campaign',
        domain=lambda self: [(
            "country_id", "=", self.env.ref('base.mx').id)])
    l10n_mx_edi_ine_scope = fields.Selection(
        selection=[
            ('local', 'Local'),
            ('federal', 'Federal')
        ],
        string='Scope',
        help='Registers the type of scope of a process of type Campaign or '
        'Pre-campaign. Set this when Process Type is Campaign or Pre-campaign')
    l10n_mx_edi_ine_accounting = fields.Char(
        string='Accounting',
        help='Number assigned to your accounting to make the corresponding '
        'revenue or expenditure records in the Comprehensive Inspection '
        'System. Set this when Process Type is Campaign or Pre-campaign, or '
        'when Process Type is Ordinary and Committee Type is State Executive.'
        'Please use a comma to separate the accounting numbers when yo need '
        'to provide several numbers for one Entity'
    )
    invoice_id = fields.Many2one('account.move')   #EDITADO DE ACCOUNT.INVOICE






class AccountMove(models.Model):
    _inherit = 'account.move'  #EDITADO DE ACCOUNT.INVOICE

    l10n_mx_edi_amount_residual_advances = fields.Monetary(
        'Amount residual with advances', compute='_compute_amount_advances',
        help='save the amount that will be applied as advance when validate '
        'the invoice')
    l10n_mx_edi_amount_advances = fields.Monetary(
        'Amount in advances', compute='_compute_amount_advances',
        help='save the amount that will be applied as advance when validate '
        'the invoice')
    l10n_mx_edi_cancellation_date = fields.Date(
        'Cancellation Date', readonly=True, copy=False,
        help='Save the cancellation date of the CFDI in the SAT')
    l10n_mx_edi_cancellation_time = fields.Char(
        'Cancellation Time', readonly=True, copy=False,
        help='Save the cancellation time of the CFDI in the SAT')
    l10n_mx_edi_total_discount = fields.Monetary(
        "Total Discount", monetary=True,
        default=0.0, currency_field='currency_id',
        compute='_compute_discount',
        help="Sum of discounts on the invoice.",
    )                
    l10n_mx_edi_factoring_id = fields.Many2one(
        "res.partner", "Financial Factor", copy=False, readonly=True,
        states={'open': [('readonly', False)]},
        help="This invoice will be paid by this Financial factoring agent.") 
    l10n_mx_edi_legend_ids = fields.Many2many(
        'l10n_mx_edi.fiscal.legend', string='Fiscal Legends',
        help="Legends under tax provisions, other than those contained in the "
        "Mexican CFDI standard.")    
    l10n_mx_edi_emitter_reference = fields.Char(
        string="Electronic Purse Issuer Reference",
        help="This is needed when a service station invoice a fuel "
        "consumption given an electronic purse issuer credit note. "
        "The format should be: 'electronic purse number|"
        "electronic purse identifier owner bank account'."
        "ex.: 1234|0001234")   

    l10n_mx_edi_ine_process_type = fields.Selection(
        selection=[
            ('ordinary', 'Ordinary'),
            ('precampaign', 'Precampaign'),
            ('campaign', 'Campaign')
        ],
        string='Process Type')
    l10n_mx_edi_ine_committee_type = fields.Selection(
        selection=[
            ('national_executive', 'National Executive'),
            ('state_executive', 'State Executive'),
            ('state_manager', 'State Manager')
        ],
        string='Committee Type',
        help="Set this when Process Type is 'Ordinary'")
    l10n_mx_edi_ine_accounting = fields.Char(
        string='Accounting',
        help="This field is optional. You can fill this field when Process "
        "type is 'Ordinary' and the Committee type is 'National Executive'")
    l10n_mx_edi_ine_entity_ids = fields.One2many(
        'l10n_mx_edi_ine.entity',
        'invoice_id',
        string='Entity / Scope / Accounting Id',
        help="Set this when Committee Type is 'State Executive' or 'State '"
        "Manager'. Set 'Accounting' only when Process Type is 'Campaign' or "
        "Pre-campaign, or when Process type 'Ordinary' and Committee Type "
        "'State Executive', please use comma to separate the accounts numbers"
        "when you need to provide several numbers for one Entity.") 

    l10n_mx_edi_np_partner_id = fields.Many2one(
        'res.partner',
        string="Buyer",
        help="Buyer or buyers information"
    )      
    l10n_mx_edi_property = fields.Many2one(
        'res.partner', 'Address Property in Construction',
        help='Use this field when the invoice require the '
        'complement to "Partial construction services". This value will be '
        'used to indicate the information of the property in which are '
        'provided the partial construction services.')    
    l10n_mx_edi_tpe_transit_date = fields.Date(
        string='Transit Date',
        help='Attribute required to express the date of arrival or '
        'departure of the means of transport used. It is expressed in the '
        'form aaaa-mm-dd'
    )
    l10n_mx_edi_tpe_transit_time = fields.Float(
        string='Transit Time',
        help='Attribute required to express the time of arrival or departure '
        'of the means of transport used. It is expressed in the form hh:mm:ss'
    )
    l10n_mx_edi_tpe_transit_type = fields.Selection([
        ('arrival', 'Arrival'),
        ('departure', 'Departure'),
    ],
        string='Transit Type',
        help='Attribute required to incorporate the operation performed'
    )
    l10n_mx_edi_tpe_partner_id = fields.Many2one(
        'res.partner',
        string='Transport Company',
        help='Attribute required to indicate the transport company of entry '
        'into national territory or transfer to the outside'
    )  
    l10n_mx_edi_serie_cd = fields.Selection([
        ('serie_a', 'Serie A'),
        ('serie_b', 'Serie B'),
        ('serie_c', 'Serie C'),
        ('serie_d', 'Serie D'),
        ('serie_e', 'Serie E')], 'Serie',
        help='Assign the serie according the SAT catalog to the vehicle that '
        'was destroyed')
    l10n_mx_edi_folio_cd = fields.Char(
        'Folio', help='Assign the folio provided by the SAT to this '
        'destruction')
    #l10n_mx_edi_vehicle_id = fields.Many2one(
    #    'fleet.vehicle', 'Vehicle',
    #    help='Indicate the vehicle that was destroyed if you are using the '
    #    'Destruction Certificate. Or the transfer vehicle if you are using '
    #    'the Vehicle Renew and Substitution Complement. If it is a sale of a '
    #    'vehicle, or using the PFIC complement, specify the vehicle.')
    #l10n_mx_edi_decree_type = fields.Selection(
    #    string="Decree Type",
    #    selection=[
    #        ('01', 'Renovation of the motor transport vehicle park'),
    #        ('02', 'Replacement of passenger and freight motor vehicles')
    #    ],
    #    help='Decree which is going to be applicated'
    #)
    #l10n_mx_edi_vehicle_ids = fields.Many2many(
    #    'fleet.vehicle',
    #    string='Used Vehicles',
    #    help='Indicate the vehicles that are going to be replaced'
    #)
    #l10n_mx_edi_substitute_id = fields.Many2one(
    #    'fleet.vehicle', 'Substitute Vehicle',
    #    help='Indicate the vehicle that is going to be replaced')
    #l10n_mx_edi_complement_type = fields.Selection(
    #    related='company_id.l10n_mx_edi_complement_type', readonly=True)  

    l10n_mx_edi_pac_status = fields.Selection(
        selection=[
            ('retry', 'Retry'),
            ('to_sign', 'To sign'),
            ('signed', 'Signed'),
            ('to_cancel', 'To cancel'),
            ('cancelled', 'Cancelled')
        ],
        string='PAC status',
        help='Refers to the status of the invoice inside the PAC.',
        readonly=True,
        copy=False)
    """
    l10n_mx_edi_sat_status = fields.Selection(
        selection=[
            ('none', 'State not defined'),
            ('undefined', 'Not Synced Yet'),
            ('not_found', 'Not Found'),
            ('cancelled', 'Cancelled'),
            ('valid', 'Valid'),
        ],
        string='SAT status',
        help='Refers to the status of the invoice inside the SAT system.',
        readonly=True,
        copy=False,
        required=True,
        track_visibility='onchange',
        default='undefined')
    """
    l10n_mx_edi_cfdi_name = fields.Char(string='CFDI name', copy=False, readonly=True,
        help='The attachment name of the CFDI.')
    l10n_mx_edi_partner_bank_id = fields.Many2one('res.partner.bank',
        string='Partner bank',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('partner_id', '=', partner_id)]",
        help='The bank account the client will pay from. Leave empty if '
        'unkown and the XML will show "Unidentified".')
    """
    l10n_mx_edi_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method',
        string='Payment Way',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Indicates the way the invoice was/will be paid, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc. Leave empty '
        'if unkown and the XML will show "Unidentified".',
        default=lambda self: self.env.ref('l10n_mx_edi.payment_method_otros',
                                          raise_if_not_found=False))
    """                                                  
    l10n_mx_edi_uuid = fields.Char('Fiscal Folio', copy=False, readonly=True,
        help='Unused field to remove in master')
    #l10n_mx_edi_cfdi_uuid = fields.Char(string='Fiscal Folio', copy=False, readonly=True,
    #    help='Folio in electronic invoice, is returned by SAT when send to stamp.',
    #    compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi = fields.Binary(string='Cfdi content', copy=False, readonly=True,
        help='The cfdi xml content encoded in base64.')
    """
    l10n_mx_edi_cfdi_supplier_rfc = fields.Char(string='Supplier RFC', copy=False, readonly=True,
        help='The supplier tax identification number.')
    l10n_mx_edi_cfdi_customer_rfc = fields.Char(string='Customer RFC', copy=False, readonly=True,
        help='The customer tax identification number.')
        
    l10n_mx_edi_cfdi_amount = fields.Monetary(string='Total Amount', copy=False, readonly=True,
        help='The total amount reported on the cfdi.')
    """        
    l10n_mx_edi_cfdi_certificate_id = fields.Many2one('l10n_mx_edi.certificate',
        string='Certificate', copy=False, readonly=True,
        help='The certificate used during the generation of the cfdi.')
    l10n_mx_edi_time_invoice = fields.Char(
        string='Time invoice', readonly=True, copy=False,
        states={'draft': [('readonly', False)]},
        help="Keep empty to use the current México central time")
    """
    l10n_mx_edi_usage = fields.Selection([
        ('G01', 'Acquisition of merchandise'),
        ('G02', 'Returns, discounts or bonuses'),
        ('G03', 'General expenses'),
        ('I01', 'Constructions'),
        ('I02', 'Office furniture and equipment investment'),
        ('I03', 'Transportation equipment'),
        ('I04', 'Computer equipment and accessories'),
        ('I05', 'Dices, dies, molds, matrices and tooling'),
        ('I06', 'Telephone communications'),
        ('I07', 'Satellite communications'),
        ('I08', 'Other machinery and equipment'),
        ('D01', 'Medical, dental and hospital expenses.'),
        ('D02', 'Medical expenses for disability'),
        ('D03', 'Funeral expenses'),
        ('D04', 'Donations'),
        ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
        ('D06', 'Voluntary contributions to SAR'),
        ('D07', 'Medical insurance premiums'),
        ('D08', 'Mandatory School Transportation Expenses'),
        ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
        ('D10', 'Payments for educational services (Colegiatura)'),
        ('P01', 'To define'),
    ], 'Usage', default='P01',
        help='Used in CFDI 3.3 to express the key to the usage that will '
        'gives the receiver to this invoice. This value is defined by the '
        'customer. \nNote: It is not cause for cancellation if the key set is '
        'not the usage that will give the receiver of the document.')
            
    l10n_mx_edi_origin = fields.Char(
        string='CFDI Origin', copy=False,
        help='In some cases like payments, credit notes, debit notes, '
        'invoices re-signed or invoices that are redone due to payment in '
        'advance will need this field filled, the format is: \nOrigin Type|'
        'UUID1, UUID2, ...., UUIDn.\nWhere the origin type could be:\n'
        u'- 01: Nota de crédito\n'
        u'- 02: Nota de débito de los documentos relacionados\n'
        u'- 03: Devolución de mercancía sobre facturas o traslados previos\n'
        u'- 04: Sustitución de los CFDI previos\n'
        '- 05: Traslados de mercancias facturados previamente\n'
        '- 06: Factura generada por los traslados previos\n'
        u'- 07: CFDI por aplicación de anticipo')   
    """            

    l10n_mx_edi_incoterm = fields.Selection(
        [('CIP', 'CARRIAGE AND INSURANCE PAID TO'),
         ('CPT', 'CARRIAGE PAID TO'),
         ('CFR', 'COST AND FREIGHT'),
         ('CIF', 'COST, INSURANCE AND FREIGHT'),
         ('DAF', 'DELIVERED AT FRONTIER'),
         ('DAP', 'DELIVERED AT PLACE'),
         ('DAT', 'DELIVERED AT TERMINAL'),
         ('DDP', 'DELIVERED DUTY PAID'),
         ('DDU', 'DELIVERED DUTY UNPAID'),
         ('DEQ', 'DELIVERED EX QUAY'),
         ('DES', 'DELIVERED EX SHIP'),
         ('EXW', 'EX WORKS'),
         ('FAS', 'FREE ALONGSIDE SHIP'),
         ('FCA', 'FREE CARRIER'),
         ('FOB', 'FREE ON BOARD')],
        string='Incoterm', help='Indicates the INCOTERM applicable to the '
        'external trade customer invoice.')
    """
    l10n_mx_edi_cer_source = fields.Char(
        'Certificate Source',
        help='Used in CFDI like attribute derived from the exception of '
        'certificates of Origin of the Free Trade Agreements that Mexico '
        'has celebrated with several countries. If have a value, will to '
        'indicate that funge as certificate of origin and this value will be '
        'set in the CFDI nose "NumCertificadoOrigen".')            
    l10n_mx_edi_external_trade = fields.Boolean(
        'Need external trade?', compute='_compute_need_external_trade',
        inverse='_inverse_need_external_trade', store=True,
        help='If this field is active, the CFDI that generate this invoice '
        'will to include the complement "External Trade".')   
    """  






class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'  #EDITADO DE ACCOUNT.INVOICE.LINE

    l10n_mx_edi_amount_discount = fields.Float(
        "Unit Discount",
        digits=dp.get_precision('Discount'),
        currency_field='currency_id',
        #compute='_compute_l10n_mx_edi_amount_discount',
        #inverse='_inverse_discount',
        #store=True,
        help="Discount to be applied for each product in the invoice lines ",
    )
    l10n_mx_edi_total_discount = fields.Float(
        "Total Discount",
        digits=dp.get_precision('Discount'),
        currency_field='currency_id',
        #compute='_compute_l10n_mx_edi_total_discount',
        #inverse='_inverse_total_discount',
        #store=True,
        help="Total discount per invoice line. The formula is discount * "
             "quantity of products on the invoice.",
    ) 
    l10n_mx_edi_voucher_id = fields.Many2one(
        'res.partner',
        string='Employee',
        help='Employee information, set this if you want to use the Food '
        'Voucher Complement'
    )    
    l10n_mx_edi_fuel_partner_id = fields.Many2one(
        'res.partner',
        string='Service Station',
        help='Service Station information, set this if the company is an '
        'electronic purse issuer and you are issuing an Invoice',
    )    
    l10n_mx_edi_iedu_id = fields.Many2one(
        'res.partner', string='Student', help="Student information for IEDU "
        "complement:\n Make sure that the student have set CURP.")
    l10n_mx_edi_customs_number = fields.Char(
        help='Optional field for entering the customs information in the case '
        'of first-hand sales of imported goods or in the case of foreign trade'
        ' operations with goods or services.\n'
        'The format must be:\n'
        ' - 2 digits of the year of validation followed by two spaces.\n'
        ' - 2 digits of customs clearance followed by two spaces.\n'
        ' - 4 digits of the serial number followed by two spaces.\n'
        ' - 1 digit corresponding to the last digit of the current year, '
        'except in case of a consolidated customs initiated in the previous '
        'year of the original request for a rectification.\n'
        ' - 6 digits of the progressive numbering of the custom.',
        string='Customs number',
        copy=False)  

    """ No los hallé en v11.0
    l10n_mx_edi_tariff_fraction_id = fields.Many2one(
        'l10n_mx_edi.tariff.fraction', 'Tariff Fraction', store=True,
        related='product_id.l10n_mx_edi_tariff_fraction_id', readonly=True,
        compute_sudo=True,
        help='It is used to express the key of the tariff fraction '
        'corresponding to the description of the product to export. Node '
        '"FraccionArancelaria" to the concept.')
    l10n_mx_edi_umt_aduana_id = fields.Many2one(
        'product.uom', 'UMT Aduana', store=True,
        related='product_id.l10n_mx_edi_umt_aduana_id', readonly=True,
        compute_sudo=True,
        help='Used in complement "Comercio Exterior" to indicate in the '
        'products the TIGIE Units of Measurement, this based in the SAT '
        'catalog.')
    l10n_mx_edi_qty_umt = fields.Float(
        'Qty UMT', help='Quantity expressed in the UMT from product. Is '
        'used in the attribute "CantidadAduana" in the CFDI',
        digits=dp.get_precision('Product Unit of Measure'))
    l10n_mx_edi_price_unit_umt = fields.Float(
        'Unit Value UMT', help='Unit value expressed in the UMT from product. '
        'Is used in the attribute "ValorUnitarioAduana" in the CFDI') 
    """  





class AccountPayment(models.Model):
    _inherit = 'account.payment'

    l10n_mx_edi_pac_status = fields.Selection(
        selection=[
            ('none', 'CFDI not necessary'),
            ('retry', 'Retry'),
            ('to_sign', 'To sign'),
            ('signed', 'Signed'),
            ('to_cancel', 'To cancel'),
            ('cancelled', 'Cancelled')
        ],
        string='PAC status', default='none',
        help='Refers to the status of the CFDI inside the PAC.',
        readonly=True, copy=False)
    l10n_mx_edi_sat_status = fields.Selection(
        selection=[
            ('none', 'State not defined'),
            ('undefined', 'Not Synced Yet'),
            ('not_found', 'Not Found'),
            ('cancelled', 'Cancelled'),
            ('valid', 'Valid'),
        ],
        string='SAT status',
        help='Refers to the status of the CFDI inside the SAT system.',
        readonly=True, copy=False, required=True,
        track_visibility='onchange', default='undefined')
    l10n_mx_edi_cfdi_name = fields.Char(string='CFDI name', copy=False, readonly=True,
        help='The attachment name of the CFDI.')
    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Way',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Indicates the way the payment was/will be received, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc.')
    l10n_mx_edi_cfdi = fields.Binary(
        string='Cfdi content', copy=False, readonly=True,
        help='The cfdi xml content encoded in base64.')
    l10n_mx_edi_cfdi_uuid = fields.Char(string='Fiscal Folio', copy=False, readonly=True,
        help='Folio in electronic invoice, is returned by SAT when send to stamp.')
    l10n_mx_edi_cfdi_certificate_id = fields.Many2one('l10n_mx_edi.certificate',
        string='Certificate', copy=False, readonly=True,
        help='The certificate used during the generation of the cfdi.')
    l10n_mx_edi_cfdi_supplier_rfc = fields.Char('Supplier RFC', copy=False, readonly=True,
        help='The supplier tax identification number.')
    l10n_mx_edi_cfdi_customer_rfc = fields.Char('Customer RFC', copy=False, readonly=True,
        help='The customer tax identification number.')
    l10n_mx_edi_origin = fields.Char(
        string='CFDI Origin', copy=False,
        help='In some cases the payment must be regenerated to fix data in it. '
        'In that cases is necessary this field filled, the format is: '
        '\n04|UUID1, UUID2, ...., UUIDn.\n'
        'Example:\n"04|89966ACC-0F5C-447D-AEF3-3EED22E711EE,89966ACC-0F5C-447D-AEF3-3EED22E711EE"')
    l10n_mx_edi_expedition_date = fields.Date(
        string='Expedition Date', copy=False,
        help='Save the expedition date of the CFDI that according to the SAT '
        'documentation must be the date when the CFDI is issued.')
    l10n_mx_edi_time_payment = fields.Char(
        string='Time payment', readonly=True, copy=False,
        states={'draft': [('readonly', False)]},
        help="Keep empty to use the current Mexico central time")        


    l10n_mx_edi_cancellation_date = fields.Date(
        'Cancellation Date', readonly=True, copy=False,
        help='Save the cancellation date of the CFDI in the SAT')
    l10n_mx_edi_cancellation_time = fields.Char(
        'Cancellation Time', readonly=True, copy=False,
        help='Save the cancellation time of the CFDI in the SAT')        
    l10n_mx_edi_factoring_id = fields.Many2one(
        "res.partner", "Financial Factor", copy=False,
        help="This payment was received from this factoring.")  
    l10n_mx_edi_rfc = fields.Text("Emitter")
    l10n_mx_edi_received_rfc = fields.Text("Received By")
    l10n_mx_edi_uuid = fields.Text(
        "UUID", track_visibility='onchange',
        help="UUID of the xml's attached comma separated if more than one.")
    #total_amount = fields.Monetary(inverse='_inverse_amount')

    l10n_mx_edi_date = fields.Date("Date (att)", track_visibility='onchange',
                                   help="Date on the CFDI attached [If 1 if "
                                        "several we will need to split them]")
    l10n_mx_edi_analysis = fields.Text(
        "Analysis", copy=False, track_visibility='onchange',
        help="See in json (and future with a fancy widget) the summary of the"
             " test run and their result [Per fiscal test]")
    l10n_mx_edi_functionally_approved = fields.Boolean(
        "Functionally Approved", copy=False,
        help="Comply with the functional checks?", track_visibility='onchange',
        default=False, readonly=1, force_save=1
    )
    l10n_mx_edi_fiscally_approved = fields.Boolean(
        "Fiscally Approved", copy=False,
        help="Comply with the fiscal checks?", track_visibility='onchange',
        default=False, readonly=1, force_save=1
    )
    l10n_mx_edi_functional_details = fields.Text(
        'Functional Details', copy=False, track_visibility="onchange",
        help="See in json (and future with a fancy widget) the summary of the"
             " test run and their result [Per functional test]")
    l10n_mx_edi_functional = fields.Selection(
        selection=[
            ('undefined', 'Not checked yet'),
            ('fail', 'Something failed, please check the message log'),
            ('ok', 'All the functional checks Ok!'),
            ('error', 'Trying to check occurred an error, check the log'),
        ],
        string='Functional status',
        help="Inform the functional status regarding other data in the system",
        readonly=True,
        copy=False,
        required=True,
        track_visibility='onchange',
        default='undefined'
    )
    l10n_mx_edi_functional_details_html = fields.Html(
        "Functional", compute="_compute_functional_details_html")
    l10n_mx_edi_partner_bank_id = fields.Many2one(
        'res.partner.bank', 'Partner Bank', help='If the payment was made '
        'with a financial institution define the bank account used in this '
        'payment.')      






class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.payment.register" #Cambido desde "account.register.payments"

    l10n_mx_edi_factoring_id = fields.Many2one(
        "res.partner", "Financial Factor", copy=False,
        help="This payment was received from this factoring.")
    l10n_mx_edi_partner_bank_id = fields.Many2one(
        'res.partner.bank', 'Partner Bank', help='If the payment was made '
        'with a financial institution define the bank account used in this '
        'payment.')        




# //////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////

#  INTENTO DE MAPEO DE LOCALIZACION DE ODOO VERSION 11.0

# //////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////
"""
class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_product_advance_id = fields.Many2one(
        'product.product', 'Advance product', help='This product will be used '
        'in the advance invoices that are created automatically when is '
        'registered a payment without documents related or with a difference '
        'in favor of the customer.')
    l10n_mx_edi_journal_advance_id = fields.Many2one(
        'account.journal', 'Advance Journal',
        help='This journal will be used in the advance invoices that are '
        'created automatically when is registered a payment without documents '
        'related or with a difference in favor of the customer.')       

    l10n_mx_edi_donat_auth = fields.Char(
        'Authorization Number', help='Number of document on which is '
        'informed the civil organization or escrow, the procedence of the '
        'authorization to receive deductible donations, or its corresponding '
        'renovation granted by SAT')
    l10n_mx_edi_donat_date = fields.Date(
        'Authorization Date', help='Date of document on which is '
        'informed the civil organization or escrow, the procedence of the '
        'authorization to receive deductible donations, or its corresponding '
        'renovation granted by SAT')
    l10n_mx_edi_donat_note = fields.Text(
        'Note', help='Field to prove the voucher issued is derived '
        'from a donation')

    l10n_mx_edi_isepi = fields.Boolean(
        string='Is an Electronic purse issuer?',
        help='This add the electronic purse emission complement for fuel '
        'consumption')

    l10n_mx_edi_minimum_wage = fields.Float(
        'Mexican minimum Wage',
        help='Indicates the current daily amount of the general minimum wage '
        'in Mexico')





class FiscalLegend(models.Model):
    _name = 'l10n_mx_edi.fiscal.legend'
    _description = 'Fiscal Legend'

    name = fields.Char(
        string='Legend Text', required=True,
        help="Text to specify the fiscal legend.")
    tax_provision = fields.Char(
        help="Specifies the Law, Resolution or Tax Disposition that regulates "
        "this legend. It must be expressed in capital letters without "
        "punctuation (e.g. ISR).")
    rule = fields.Char(
        help="Specifies the Article number or rule that regulates the "
        "obligation of this legend.")





class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    def _get_options_payment_mode(self):
        return self.env['hr.expense'].fields_get().get(
            'payment_mode').get('selection')    


    journal_id = fields.Many2one(
        'account.journal', 'Journal',
        domain=[('type', 'in', ['cash', 'bank'])],
        company_dependent=True,
        help='Specifies the journal that will be used to make the '
             'reimbursements to employees, for expenses with type '
             '"to reimburse"')
    expenses_count = fields.Integer(
        compute='_compute_expenses', type='integer')
    sheets_count = fields.Integer(
        compute='_compute_expenses', type='integer')
    l10n_mx_edi_accountant = fields.Many2one(
        "res.users", string="Accountant",
        help="This user will be the responsible to review the expenses report "
             "after the manager actually approve it.")
    l10n_mx_edi_debit_account_id = fields.Many2one(
        'account.account', 'Debtor Number',
        #related='journal_id.default_debit_account_id', comentado
        domain=[('deprecated', '=', False)],
        help="Account defined in the journal to use when the employee receive "
        "money for expenses.")
    l10n_mx_edi_credit_account_id = fields.Many2one(
        'account.account', 'Creditor Number',
        #related='journal_id.default_credit_account_id', comentado
        domain=[('deprecated', '=', False)],
        help="Account defined in the journal to use when the employee paid "
        "an invoice from an expense.")
    l10n_mx_edi_payment_mode = fields.Selection(
        _get_options_payment_mode, 'Payment Mode',
        help='Value used by default in the expenses for this employee.')





class HrExpenseSheet(models.Model):
    _name = "hr.expense.sheet"

    l10n_mx_edi_accountant = fields.Many2one(
        "res.users", string="Accountant",
        related="employee_id.l10n_mx_edi_accountant",
        store=True, inverse="_inverse_accountant",
        help="This user will be the responsible to review the expenses report "
             "after the manager actually approve it.")
    l10n_mx_edi_expenses_count = fields.Integer(
        'Number of Expenses', compute='_compute_expenses_count')
    l10n_mx_edi_open_expenses_count = fields.Integer(
        'Number of Open Expenses', compute='_compute_expenses_count')
    l10n_mx_edi_paid_expenses_count = fields.Integer(
        'Number of Paid Expenses', compute='_compute_expenses_count')
    l10n_mx_edi_paid_invoices_count = fields.Integer(
        'Number of Paid Invoices', compute='_compute_invoices_count')
    l10n_mx_edi_invoices_count = fields.Integer(
        'Number of Open Invoices', compute='_compute_invoices_count')

    #Hybrid definition    
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company"),
        ('petty_account', 'Petty Cash (Debit from the custody of the employee)'),
        ('company_account', 'Company (Generate a payable for the supplier).'),    
    ], default='company_account', tracking=True, states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]}, string="Paid By")        

    
    #payment_mode = fields.Selection(
    #    selection_add=[('petty_account',
    #                    'Petty Cash (Debit from the custody of the employee)'),
    #                   ('company_account',
    #                    'Company (Generate a payable for the supplier).')],
    #    default='company_account',
    #    track_visibility='onchange')






class HrExpense(models.Model):
    _name = 'hr.expense'

    active = fields.Boolean(
        help="In the line this will be necessary to split the expenses once"
             " they are received.", track_visibility='onchange',
        default=True
    )

    l10n_mx_edi_functionally_approved = fields.Boolean(
        "Functionally Approved", copy=False,
        help="Comply with the functional checks?", track_visibility='onchange',
        default=False, readonly=1, force_save=1
    )

    l10n_mx_edi_fiscally_approved = fields.Boolean(
        "Fiscally Approved", copy=False,
        help="Comply with the fiscal checks?", track_visibility='onchange',
        default=False, readonly=1, force_save=1
    )

    l10n_mx_edi_forced_approved = fields.Boolean(
        "Forced Approved", copy=False,
        help="This is a paid not deductible", track_visibility='onchange',
        default=False, readonly=1, force_save=1
    )

    name = fields.Char(states={'downloaded': [('readonly', False)],
                               'draft': [('readonly', False)],
                               'reported': [('readonly', False)],
                               'refused': [('readonly', False)]})
    product_id = fields.Many2one(states={'downloaded': [('readonly', False)],
                                         'draft': [('readonly', False)],
                                         'reported': [('readonly', False)],
                                         'refused': [('readonly', False)]},
                                 track_visibility='onchange')
    quantity = fields.Float(states={'downloaded': [('readonly', False)],
                                    'draft': [('readonly', False)],
                                    'reported': [('readonly', False)],
                                    'refused': [('readonly', False)]})
    unit_amount = fields.Float(states={'downloaded': [('readonly', False)],
                                       'draft': [('readonly', False)],
                                       'reported': [('readonly', False)],
                                       'refused': [('readonly', False)]},
                               default=0.00)
    date = fields.Date(states={'downloaded': [('readonly', False)],
                               'draft': [('readonly', False)],
                               'reported': [('readonly', False)],
                               'refused': [('readonly', False)]},
                       track_visibility='onchange',
                       help="Date the payment was created in the system")
    l10n_mx_edi_uuid = fields.Text(
        "UUID", track_visibility='onchange',
        help="UUID of the xml's attached comma separated if more than one.")
    total_amount = fields.Monetary(inverse='_inverse_amount')

    l10n_mx_edi_date = fields.Date("Date (att)", track_visibility='onchange',
                                   help="Date on the CFDI attached [If 1 if "
                                        "several we will need to split them]")
    l10n_mx_edi_subtotal = fields.Float("Amount Subtotal")
    l10n_mx_edi_tax = fields.Float(
        "Tax", track_visibility='onchange')
    l10n_mx_edi_discount = fields.Float(
        "Discount", track_visibility='onchange')
    l10n_mx_edi_withhold = fields.Float(
        "Withhold", track_visibility='onchange')
    l10n_mx_edi_analysis = fields.Text(
        "Analysis", copy=False, track_visibility='onchange',
        help="See in json (and future with a fancy widget) the summary of the"
             " test run and their result [Per fiscal test]")
    l10n_mx_edi_analysis_html = fields.Html(
        "Analysis HTML", compute="_compute_analysis_html",
        track_visibility='onchange')
    l10n_mx_edi_functional_details = fields.Text(
        'Functional Details', copy=False, track_visibility="onchange",
        help="See in json (and future with a fancy widget) the summary of the"
             " test run and their result [Per functional test]")
    l10n_mx_edi_functional_details_html = fields.Html(
        "Functional", compute="_compute_functional_details_html")
    l10n_mx_edi_accountant = fields.Many2one(
        "res.users", string="Accountant",
        related="sheet_id.l10n_mx_edi_accountant",
        store=True, inverse="_inverse_accountant",
        help="This user will be the responsible to review the expenses report "
             "after the manager actually approve it.")
    l10n_mx_edi_move_id = fields.Many2one(
        'account.move', 'Journal Entry', readonly=True, force_save=1,
    )
    l10n_mx_edi_move_line_id = fields.Many2one(
        'account.move.line', 'Journal Item', readonly=True, force_save=1,
    )
    account_id = fields.Many2one(track_visibility='onchange')
    tax_ids = fields.Many2many(states={'downloaded': [('readonly', False)],
                                       'draft': [('readonly', False)],
                                       'reported': [('readonly', False)],
                                       'refused': [('readonly', False)]},
                               readonly=True)

    l10n_mx_edi_rfc = fields.Text("Emitter")
    l10n_mx_edi_received_rfc = fields.Text("Received By")
    #Hybrid definition
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Paid'),
        ('refused', 'Refused'),
        ('downloaded', 'Just Downloaded'),
    ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True, default='draft', help="Status of the expense.")    
    
    # Campos con definicion original
    #state = fields.Selection(
    #    selection_add=[
    #        ('downloaded', 'Just Downloaded')
    #    ],
    #    default="downloaded",
    #    readonly=False,
    #    inverse='_inverse_state',
    #    track_visibility='onchange',
    #)

    #payment_mode = fields.Selection(
    #    selection_add=[('petty_account',
    #                    'Petty Cash (Debit from the custody of the employee)'),
    #                   ('company_account',
    #                    'Company (Generate a payable for the supplier).')],
    #    default='company_account',
    #    track_visibility='onchange',
    #)


    l10n_mx_edi_sat_status = fields.Selection(
        selection=[
            ('none', 'State not defined'
                     '(answer on sat not possible to manage)'),
            ('undefined', 'Not synced yet with SAT'),
            ('not_found', 'We could not find it in the SAT'),
            ('cancelled', 'Cancelled on SAT'),
            ('valid', 'Perfectly valid on SAT'),
            ('more_than_one', 'Please split in several lines there is more '
                              'than one invoice to check with SAT'),
        ],
        string='SAT status',
        help='Refers to the status of the invoice(s) inside the SAT system.',
        readonly=True,
        copy=False,
        required=True,
        track_visibility='onchange',
        default='undefined'
    )
    l10n_mx_edi_functional = fields.Selection(
        selection=[
            ('undefined', 'Not checked yet'),
            ('fail', 'Something failed, please check the message log'),
            ('ok', 'All the functional checks Ok!'),
            ('error', 'Trying to check occurred an error, check the log'),
        ],
        string='Functional status',
        help="Inform the functional status regarding other data in the system",
        readonly=True,
        copy=False,
        required=True,
        track_visibility='onchange',
        default='undefined'
    )
    email_from = fields.Char(
        track_visibility='onchange',)
    partner_id = fields.Many2one(
        "res.partner", "Supplier",
        track_visibility='onchange',
        help="Partner that generated this invoices",
        ondelete='restrict',
        compute="_compute_partner_id", store=True, inverse='_inverse_partner')
    l10n_mx_count_cfdi = fields.Integer(
        "Count CFDI's", track_visibility='onchange')
    l10n_mx_edi_invoice_id = fields.Many2one(
        'account.move', 'Invoice', help='Invoice created with this expense',
        readonly=True)  #EDITADO DE ACCOUNT.INVOICE
                                         





class HrContractType(models.Model):
    _name = "hr.contract.type"

    l10n_mx_edi_code = fields.Char(
        'Code', help='Code defined by SAT to this contract type.')





class HrPayslipOvertime(models.Model):
    _name = 'hr.payslip.overtime'
    _description = 'Pay Slip overtime'

    name = fields.Char('Description', required=True)
    payslip_id = fields.Many2one(
        'hr.payslip', required=True, ondelete='cascade',
        help='Payslip related.')
    days = fields.Integer(
        help="Number of days in which the employee performed overtime in the "
        "period", required=True)
    hours = fields.Integer(
        help="Number of overtime hours worked in the period", required=True)
    overtime_type = fields.Selection([
        ('01', 'Double'),
        ('02', 'Triples'),
        ('03', 'Simples')], 'Type', required=True, default='01',
        help='Used to express the type of payment of the hours extra.')
    amount = fields.Float(
        help="Amount paid for overtime", required=True, default=0.0)


class HrPayslipActionTitles(models.Model):
    _name = 'hr.payslip.action.titles'
    _description = 'Pay Slip action titles'

    payslip_id = fields.Many2one(
        'hr.payslip', required=True, ondelete='cascade',
        help='Payslip related.')
    category_id = fields.Many2one(
        'hr.salary.rule.category', 'Category', required=True,
        help='Indicate to which perception will be added this attributes in '
        'node XML')
    market_value = fields.Float(
        help='When perception type is 045 this value must be assigned in the '
        'line. Will be used in node "AccionesOTitulos" to the attribute '
        '"ValorMercado"', required=True)
    price_granted = fields.Float(
        help='When perception type is 045 this value must be assigned in the '
        'line. Will be used in node "AccionesOTitulos" to the attribute '
        '"PrecioAlOtorgarse"', required=True)


class HrPayslipExtraPerception(models.Model):
    _name = 'hr.payslip.extra.perception'
    _description = 'Pay Slip extra perception'

    payslip_id = fields.Many2one(
        'hr.payslip', required=True, ondelete='cascade',
        help='Payslip related.')
    node = fields.Selection(
        [('retirement', 'JubilacionPensionRetiro'),
         ('separation', 'SeparacionIndemnizacion')], help='Indicate what is '
        'the record purpose, if will be used to add in node '
        '"JubilacionPensionRetiro" or in "SeparacionIndemnizacion"')
    amount_total = fields.Float(
        help='If will be used in the node "JubilacionPensionRetiro" and '
        'will be used to one perception with code "039", will be used to '
        'the attribute "TotalUnaExhibicion", if will be used to one '
        'perception with code "044", will be used to the attribute '
        '"TotalParcialidad". If will be used in the node '
        '"SeparacionIndemnizacion" will be used in attribute "TotalPagado"')
    amount_daily = fields.Float(
        help='Used when will be added in node "JubilacionPensionRetiro", to '
        'be used in attribute "MontoDiario"')
    accumulable_income = fields.Float(
        help='Used to both nodes, each record must be have the valor to each '
        'one.')
    non_accumulable_income = fields.Float(
        help='Used to both nodes, each record must be have the valor to each '
        'one.')
    service_years = fields.Integer(
        help='Used when will be added in node "SeparacionIndemnizacion", to '
        'be used in attribute "NumAñosServicio"')
    last_salary = fields.Float(
        help='Used when will be added in node "SeparacionIndemnizacion", to '
        'be used in attribute "UltimoSueldoMensOrd"')





class HrPayslipInability(models.Model):
    _name = 'hr.payslip.inability'
    _description = 'Pay Slip inability'

    payslip_id = fields.Many2one(
        'hr.payslip', required=True, ondelete='cascade',
        help='Payslip related with this inability')
    sequence = fields.Integer(required=True, default=10)
    days = fields.Integer(
        help='Number of days in which the employee performed inability in '
        'the payslip period', required=True)
    inability_type = fields.Selection(
        [('01', 'Risk of work'),
         ('02', 'Disease in general'),
         ('03', 'Maternity')], 'Type', required=True, default='01',
        help='Reason for inability: Catalog published in the SAT portal')
    amount = fields.Float(help='Amount for the inability', required=True)





class HrPayslip(models.Model):
    _name = 'hr.payslip'

    l10n_mx_edi_payment_date = fields.Date(
        'Payment Date', required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        default=time.strftime('%Y-%m-01'), help='Save the payment date that '
        'will be added on CFDI.')
    l10n_mx_edi_cfdi_name = fields.Char(
        string='CFDI name', copy=False, readonly=True,
        help='The attachment name of the CFDI.')
    l10n_mx_edi_cfdi = fields.Binary(
        'CFDI content', copy=False, readonly=True,
        help='The cfdi xml content encoded in base64.')
    l10n_mx_edi_inability_line_ids = fields.One2many(
        'hr.payslip.inability', 'payslip_id', 'Inabilities',
        readonly=True, states={'draft': [('readonly', False)]},
        help='Used in XML like optional node to express disabilities '
        'applicable by employee.', copy=True)
    l10n_mx_edi_overtime_line_ids = fields.One2many(
        'hr.payslip.overtime', 'payslip_id', 'Extra hours',
        readonly=True, states={'draft': [('readonly', False)]},
        help='Used in XML like optional node to express the extra hours '
        'applicable by employee.', copy=True)
    l10n_mx_edi_pac_status = fields.Selection(
        [('retry', 'Retry'),
         ('to_sign', 'To sign'),
         ('signed', 'Signed'),
         ('to_cancel', 'To cancel'),
         ('cancelled', 'Cancelled')], 'PAC status',
        help='Refers to the status of the payslip inside the PAC.',
        readonly=True, copy=False)
    l10n_mx_edi_sat_status = fields.Selection(
        [('none', 'State not defined'),
         ('undefined', 'Not Synced Yet'),
         ('not_found', 'Not Found'),
         ('cancelled', 'Cancelled'),
         ('valid', 'Valid')], 'SAT status',
        help='Refers to the status of the payslip inside the SAT system.',
        readonly=True, copy=False, required=True, track_visibility='onchange',
        default='undefined')
    l10n_mx_edi_cfdi_uuid = fields.Char(
        'Fiscal Folio', copy=False, readonly=True,
        help='Folio in electronic payroll, is returned by SAT when send to '
        'stamp.', compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_supplier_rfc = fields.Char(
        'Supplier RFC', copy=False, readonly=True,
        help='The supplier tax identification number.')
    l10n_mx_edi_cfdi_customer_rfc = fields.Char(
        'Customer RFC', copy=False, readonly=True,
        help='The customer tax identification number.')
    l10n_mx_edi_cfdi_amount = fields.Float(
        'Total Amount', copy=False, readonly=True,
        help='The total amount reported on the cfdi.')
    l10n_mx_edi_action_title_ids = fields.One2many(
        'hr.payslip.action.titles', 'payslip_id', string='Action or Titles',
        help='If the payslip have perceptions with code 045, assign here the '
        'values to the attribute in XML, use the perception type to indicate '
        'if apply to exempt or taxed.')
    l10n_mx_edi_extra_node_ids = fields.One2many(
        'hr.payslip.extra.perception', 'payslip_id',
        string='Extra data to perceptions',
        help='If the payslip have perceptions with code in 022, 023 or 025,'
        'must be created a record with data that will be assigned in the '
        'node "SeparacionIndemnizacion", or if the payslip have perceptions '
        'with code in 039 or 044 must be created a record with data that will '
        'be assigned in the node "JubilacionPensionRetiro". Only must be '
        'created a record by node.')
    l10n_mx_edi_balance_favor = fields.Float(
        'Balance in Favor', help='If the payslip include other payments, and '
        'one of this records have the code 004 is need add the balance in '
        'favor to assign in node "CompensacionSaldosAFavor".')
    l10n_mx_edi_comp_year = fields.Integer(
        'Year', help='If the payslip include other payments, and '
        'one of this records have the code 004 is need add the year to assign '
        'in node "CompensacionSaldosAFavor".')
    l10n_mx_edi_remaining = fields.Float(
        'Remaining', help='If the payslip include other payments, and '
        'one of this records have the code 004 is need add the remaining to '
        'assign in node "CompensacionSaldosAFavor".')
    l10n_mx_edi_source_resource = fields.Selection([
        ('IP', 'Own income'),
        ('IF', 'Federal income'),
        ('IM', 'Mixed income')], 'Source Resource',
        help='Used in XML to identify the source of the resource used '
        'for the payment of payroll of the personnel that provides or '
        'performs a subordinate or assimilated personal service to salaries '
        'in the dependencies. This value will be set in the XML attribute '
        '"OrigenRecurso" to node "EntidadSNCF".')
    l10n_mx_edi_amount_sncf = fields.Float(
        'Own resource', help='When the attribute in "Source Resource" is "IM" '
        'this attribute must be added to set in the XML attribute '
        '"MontoRecursoPropio" in node "EntidadSNCF", and must be less that '
        '"TotalPercepciones" + "TotalOtrosPagos"')
    l10n_mx_edi_cfdi_string = fields.Char(
        'CFDI Original String', help='Attribute "cfdi_cadena_original" '
        'returned by PAC request when is stamped the CFDI, this attribute is '
        'used on report.')
    l10n_mx_edi_cfdi_certificate_id = fields.Many2one(
        'l10n_mx_edi.certificate', string='Certificate', copy=False,
        readonly=True, help='The certificate used during the generation of '
        'the cfdi.', compute='_compute_cfdi_values')
    l10n_mx_edi_origin = fields.Char(
        string='CFDI Origin', copy=False,
        help='In some cases the payroll must be regenerated to fix data in it.'
        ' In that cases is necessary this field filled, the format is: '
        '\n04|UUID1, UUID2, ...., UUIDn.\n'
        'Example:\n"04|89966ACC-0F5C-447D-AEF3-3EED22E711EE,'
        '89966ACC-0F5C-447D-AEF3-3EED22E711EE"')
    l10n_mx_edi_expedition_date = fields.Date(
        string='Payslip date', readonly=True, copy=False, index=True,
        states={'draft': [('readonly', False)]},
        help="Keep empty to use the current date")
    l10n_mx_edi_time_payslip = fields.Char(
        string='Time payslip', readonly=True, copy=False,
        states={'draft': [('readonly', False)]},
        help="Keep empty to use the current México central time")
    # Add parameter copy=True
    input_line_ids = fields.One2many(copy=True)





class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_mx_edi_syndicated = fields.Boolean(
        'Syndicated', help='Used in the XML to indicate if the worker is '
        'associated with a union. If it is omitted, it is assumed that it is '
        'not associated with any union.')
    l10n_mx_edi_risk_rank = fields.Selection([
        ('1', 'Class I'),
        ('2', 'Class II'),
        ('3', 'Class III'),
        ('4', 'Class IV'),
        ('5', 'Class V')], 'Risk Rank',
        help='Used in the XML to express the key according to the Class in '
        'which the employers must register, according to the activities '
        'carried out by their workers, as provided in article 196 of the '
        'Regulation on Affiliation Classification of Companies, Collection '
        'and Inspection, or in accordance with the regulations Of the Social '
        'Security Institute of the worker.')






class HrContract(models.Model):
    _inherit = "hr.contract"

    l10n_mx_edi_integrated_salary = fields.Float(
        'Integrated Salary', compute='_compute_integrated_salary',
        help='Used in the CFDI to express the salary '
        'that is integrated with the payments made in cash by daily quota, '
        'gratuities, perceptions, room, premiums, commissions, benefits in '
        'kind and any other quantity or benefit that is delivered to the '
        'worker by his work, Pursuant to Article 84 of the Federal Labor '
        'Law. (Used to calculate compensation).')
    # Overwrite options & default
    schedule_pay = fields.Selection([
        ('01', 'Daily'),
        ('02', 'Weekly'),
        ('03', 'Biweekly'),
        ('04', 'Fortnightly'),
        ('05', 'Monthly'),
        ('06', 'Bimonthly'),
        ('07', 'Unit work'),
        ('08', 'Commission'),
        ('09', 'Raised price'),
        ('10', 'Decennial'),
        ('99', 'Other')], default='02')

    l10n_mx_edi_infonavit_type = fields.Selection(
        [('percentage', _('Percentage')),
         ('vsm', _('Number of minimum wages')),
         ('fixed_amount', _('Fixed amount')), ],
        string='INFONAVIT discount', help="INFONAVIT discount type that "
        "is calculated in the employee's payslip")
    l10n_mx_edi_infonavit_rate = fields.Float(
        string='Infonavit rate', help="Value to be deducted in the employee's"
        " payment for the INFONAVIT concept.This depends on the INFONAVIT "
        "discount type as follows: \n- If the type is percentage, then the "
        "value of this field can be 1 - 100 \n- If the type is number of "
        "minimum wages, the value of this field may be 1 - 25, since it is "
        "\n- If the type is a fixed story, the value of this field must be "
        "greater than zero. In addition, the amount of this deduction must "
        "correspond to the payment period.")






class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'

    l10n_mx_edi_payment_date = fields.Date(
        'Payment Date', required=True,
        default=time.strftime('%Y-%m-01'), help='Save the payment date that '
        'will be added on all payslip created with this batch.')





class HrSalaryRule(models.Model):
    _name = 'hr.salary.rule'

    l10n_mx_edi_code = fields.Char(
        'Our Code', help='Code defined by the company to this record, could '
        'not be related with the SAT catalog. Must be used to indicate the '
        'attribute "Clave" in the payslip lines, if this is empty will be '
        'used the value in the field "Code".')






class PosSession(models.Model):
    _name = 'pos.session'

    l10n_mx_edi_pac_status = fields.Selection(
        selection=[
            ('retry', 'Retry'),
            ('signed', 'Signed'),
            ('to_cancel', 'To cancel'),
            ('cancelled', 'Cancelled')
        ],
        string='PAC status',
        help='Refers to the status of the invoice inside the PAC.',
        readonly=True,
        copy=False)





class PosOrder(models.Model):
    _inherit = 'pos.order'

    xml_generated = fields.Boolean(
        'XML Generated', copy=False,
        help='Indicate if this order was consider in the session XML')
    l10n_mx_edi_uuid = fields.Char(
        'Fiscal Folio', copy=False, index=True,
        help='Folio in electronic document, returned by SAT.',)





class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'

    l10n_mx_edi_niv = fields.Char(
        'NIV', help='Indicate the Vehicle identification number')
    l10n_mx_edi_motor = fields.Char(
        'No. Motor', help='Indicate the motor number if is found')
    l10n_mx_edi_circulation_no = fields.Char(
        'Folio circulation card', help='Indicate the folio number of the '
        'circulation card')
    l10n_mx_edi_landing = fields.Char(
        'Landing', help='If the vehicle destroyed was imported, indicate the '
        'number of landing document that protect the importation.')
    l10n_mx_edi_landing_date = fields.Date(
        'Landing date', help='If the vehicle destroyed was imported, indicate '
        'the date of landing document that protect the importation')
    l10n_mx_edi_aduana = fields.Char(
        'Aduana', help='If the vehicle destroyed was imported, indicate the '
        'aduana that was regularized the legal status in the country of the '
        'product destroyed')
    l10n_mx_edi_fiscal_folio = fields.Char(
        string='Fiscal Folio',
        help='CFDI number issued by the Authorized Destruction Center'
    )
    l10n_mx_edi_int_advice = fields.Char(
        string='Intention Advise Number',
        help='Folio number of the acknowledgment of receipt of the notice of '
        'intention to access the destruction program.'
    )





class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_complement_type = fields.Selection(
        selection=[
            ('destruction', 'Destruction Certificate'),
            ('renew', 'Vehicle Renew and Substitution'),
            ('sale', 'Sale of vehicles'),
            ('pfic', 'Natural person member of the coordinated')
        ],
        string='Vehicle Complement',
        help='Select one of those complements if you want it to be available '
        'for invoice')







class PosOrder(models.Model):
    _inherit = 'pos.order'

    cogs_move_id = fields.Many2one('account.move', 'COGS Journal Entry',
                                   help='Journal entry generated to '
                                   'registered the COGS generated by '
                                   'the order', copy=False)
"""