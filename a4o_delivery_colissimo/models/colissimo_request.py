# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo.exceptions import UserError
from odoo import fields, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from suds.client import Client, WebFault
from odoo.addons.a4o_delivery_colissimo.data_tools import FromModel
import zeep
import logging
import re
import binascii

_logger = logging.getLogger(__name__)
#logging.getLogger('suds.transport').setLevel(logging.DEBUG)

""""
<MODEL_NAME> = [
    {
        'struct': <name> # Define the name of the object that must be created,
                         # and filled with 'content'
        'type': 'struct'|'direct'|'dict'
                'struct': will use the 'struct' key to build the data.
                'direct': will directly update the returned variable by calling
                          the WSDL method.
                'dict': will return a dictionary containing the data to be
                        transmitted to the WSDL method
                'list': will return a list containing the data to be
                        transmitted to the WSDL method
        'required': <boolean>, used we 'struct' key only, if True this
                    definition is mandatory
        'content': [ # Definition of the content ///
            {
                'src': <string>
                'dst': <string>
                'default': default value if 'src' isn't defined,
                'required': must have a value (different of None)
                'evaluate_default': if True the default value will be evaluate,
                                    else the default value is the value
                'max_size': ...
                },
            { ... },
            ]
        },
    { ... },
"""

LABEL_FORMAT = [
    ('ZPL_10x15_203dpi', 'ZPL 10x15 203dpi'),
    ('ZPL_10x15_300dpi', 'ZPL 10x15 300dpi'),
    ('DPL_10x15_203dpi', 'DPL 10x15 203dpi'),
    ('DPL_10x15_300dpi', 'DPL 10x15 300dpi'),
    ('PDF_10x15_300dpi', 'PDF 10x15 300dpi'),
    ('PDF_A4_300dpi', 'PDF A4 300dpi'),
    ]

WEIGHT_REC20 = {
    't': 'TNE',
    'kg': 'KGM',
    'g': 'GRM',
    }

TYPEPOINT = {
    'A': _('Colissimo Agency'),
    'B': _('Post office'),
    'P': _('Relay point'),
    }

DAYS = [
    'Lundi',
    'Mardi',
    'Mercredi',
    'Jeudi',
    'Vendredi',
    'Samedi',
    'Dimanche',
    ]

BORDEREAUBYPARCELSNUMBERS = [
    {
        'type': 'dict',
        'content': [
            {
                'dst': 'contractNumber',
                'src': "self.credential.get('uid')",
                'max_size': 6,
                'required': True,
                },
            {
                'dst': 'password',
                'src': "self.credential.get('pwd')",
                'required': True,
                },
            {
                'dst': 'generateBordereauParcelNumberList.parcelsNumbers',
                'src': "options['tracking_numbers']",
                'required': True,
                },
            ],
        },
    ]

RECHERCHEPOINT = [
    {
        'type': 'list',
        'content': [
            {
                'dst': 'accountNumber',
                'src': "self.credential.get('uid')",
                'max_size': 6,
                'required': True,
                },
            {
                'dst': 'password',
                'src': "self.credential.get('pwd')",
                'required': True,
                },
            {
                'dst': 'apikey',
                'src': ''
                },
            {
                'dst': 'codTiersPourPartenaire',
                'src': ''
                },
            {
                'dst': 'address',
                'src': 'record.partner_id.street',
                'required': True,
                },
            {
                'dst': 'zipCode',
                'src': 'record.partner_id.zip',
                'max_size': 5,
                'required': True,
                },
            {
                'dst': 'city',
                'src': 'record.partner_id.city',
                'max_size': 35,
                'required': True,
                },
            {
                'dst': 'countryCode',
                'src': ('record.partner_id.country_id '
                        'and record.partner_id.country_id.code '
                        'or "FR"'),
                'default': 'FR',
                'max_size': 2,
                'required': True,
                },
            {
                'dst': 'weight',
                'src': "int((record.shipping_weight or record.weight) * 1000) or None",
                'required': True,
                },
            {
                'dst': 'shippingDate',
                'src': "datetime.now().strftime('%d/%m/%Y')",
                'required': True,
                },
            {
                'dst': 'filterRelay',
                'src': '',
                },
            {
                'dst': 'requestId',
                'src': '',
                },
            {
                'dst': 'lang',
                'src': ('record.partner_id.country_id '
                        'and record.partner_id.country_id.code '
                        'or "FR"'),
                'max_size': 2,
                'default': 'FR',
                },
            {
                'dst': 'optionInter',
                'src': 'record.get_optionInter()',
                },
            ],
        },
    ]


RECHERCHEPOINTONE = [
    {
        'type': 'list',
        'content': [
            {
                'dst': 'accountNumber',
                'src': "self.credential.get('uid')",
                'max_size': 6,
                'required': True,
                },
            {
                'dst': 'password',
                'src': "self.credential.get('pwd')",
                'required': True,
                },
            {
                'dst': 'apikey',
                'src': ''
                },
            {
                'dst': 'codTiersPourPartenaire',
                'src': ''
            },
            {
                'dst': 'id',
                'src': 'record',
                },
            {
                'dst': 'date',
                'src': "datetime.now().strftime('%d/%m/%Y')",
                'required': True,
                },
            {
                'dst': 'weight',
                'src': '1',
                },
            {
                'dst': 'filterRelay',
                'src': '',
                },
            {
                'dst': 'reseau',
                'src': '',
             },
            {
                'dst': 'lang',
                'src': '',
                'max_size': 2,
                'default': 'FR',
                },
            ],
        },
    ]

GENERATELABEL = [
    {
        'type': 'dict',
        'content': [
            {
                'dst': 'contractNumber',
                'src': "self.credential.get('uid')",
                'max_size': 6,
                'required': True,
                },
            {
                'dst': 'password',
                'src': "self.credential.get('pwd')",
                'required': True,
                },
            {
                'dst': 'outputFormat.outputPrintingType',
                'src': "record.carrier_id.coli_label_format",
                'required': True,
                },
            {
                'dst': 'letter.service.productCode',
                'src': "record.coli_product_code",
                'required': True,
                },
            {
                'dst': 'letter.service.commercialName',
                'src': ('record.company_id.partner_id.name '
                        'if record.is_relay_point '
                        'else ""'),
                },
            {
                'dst': 'letter.service.depositDate',
                'src': "record.get_deposit_date_local().strftime('%Y-%m-%d')",
                'required': True,
                },
            {
                'dst': 'letter.service.transportationAmount',
                'src': "int(record.get_delivery_price() * 100)",
                'required': True,
                },
            {
                'dst': 'letter.parcel.weight',
                'src': "options['package'].shipping_weight or options['package'].weight or 0.05",
                'required': True,
                },
            {
                'dst': 'letter.parcel.pickupLocationId',
                'src': "(record.partner_id.code_relaypoint or '' if record.is_relay_point else '')",
                },
            {
                'dst': 'letter.parcel.ftd',
                'src': "'true' if record.get_ftd() else 'false'",
                'required': True,
                },
            {
                'dst': 'letter.parcel.insuranceValue',
                'src': "record.get_insurance()",
                'required': True,
                },
            {
                'dst': 'letter.sender.address.companyName',
                'src': 'record.company_id.partner_id.name',
                'max_size': 35,
                'required': True,
                },
            {
                'dst': 'letter.sender.address.line2',
                'src': 'record.company_id.partner_id.street',
                'max_size': 35,
                'required': True,
                },
            {
                'dst': 'letter.sender.address.line3',
                'src': 'record.company_id.partner_id.street2',
                'max_size': 35,
                },
            {
                'dst': 'letter.sender.address.countryCode',
                'src': 'record.company_id.partner_id.country_id.code',
                'default': 'FR',
                'max_size': 2,
                'required': True,
                },
            {
                'dst': 'letter.sender.address.city',
                'src': 'record.company_id.partner_id.city',
                'max_size': 35,
                'required': True,
                },
            {
                'dst': 'letter.sender.address.zipCode',
                'src': 'record.company_id.partner_id.zip',
                'max_size': 5,
                'required': True,
                },
            {
                'dst': 'letter.sender.address.email',
                'src': 'record.company_id.partner_id.email',
                },
            {
                'dst': 'letter.sender.address.mobileNumber',
                'src': 'record.company_id.partner_id.mobile',
                },
            {
                'dst': 'letter.addressee.address.companyName',
                'src': ('record.partner_id.parent_id.get_names()'
                        '.get("company") if record.is_relay_point '
                        'else record.partner_id.get_names().get("company")'),
                },
            {
                'dst': 'letter.addressee.address.lastName',
                'src': ('record.partner_id.parent_id.get_names()'
                        '.get("lastname") if record.is_relay_point '
                        'else record.partner_id.get_names().get("lastname")'),
                'max_size': 35,
                'required': True,
                },
            {
                'dst': 'letter.addressee.address.firstName',
                'src': ('record.partner_id.parent_id.get_names()'
                        '.get("firstname") if record.is_relay_point '
                        'else record.partner_id.get_names().get("firstname")'),
                'max_size': 35,
                'required': True,
                },
            {
                'dst': 'letter.addressee.address.line2',
                'src': 'record.partner_id.street',
                'max_size': 35,
                'required': True,
                },
            {
                'dst': 'letter.addressee.address.line3',
                'src': 'record.partner_id.street2',
                'max_size': 35,
                },
            {
                'dst': 'letter.addressee.address.countryCode',
                'src': 'record.partner_id.country_id.code',
                'default': 'FR',
                'max_size': 2,
                'required': True,
                },
            {
                'dst': 'letter.addressee.address.city',
                'src': 'record.partner_id.city',
                'max_size': 35,
                'required': True,
                },
            {
                'dst': 'letter.addressee.address.zipCode',
                'src': 'record.partner_id.zip',
                'max_size': 5,
                'required': True,
                },
            {
                'dst': 'letter.addressee.address.email',
                'src': ('record.partner_id.parent_id.email '
                        'if record.is_relay_point '
                        'else record.partner_id.email'),
                },
            {
                'dst': 'letter.addressee.address.mobileNumber',
                'src': ('record.partner_id.parent_id.get_mobile_phone() '
                        'if record.is_relay_point '
                        'else record.partner_id.get_mobile_phone()'),
                },
            {
                'dst': 'letter.addressee.address.phoneNumber',
                'src': ('record.partner_id.parent_id.get_phone() '
                        'if record.is_relay_point '
                        'else record.partner_id.get_phone()'),
                },
            ],
        },
    ]

# [TODO] : Finish the management of all possibility to building data.


class ColissimoRequest():
    """ """
    def __init__(self, prod_environment, debug_logger):
        self.debug_logger = debug_logger
        self.client = None
        self.prod_environment = prod_environment
        self.response = []

    def delivery_slip_request(self, tracking_numbers, carrier):
        ''' Send request to get delivery slip from tracking_numbers'''
        self.client = zeep.Client(wsdl=carrier.coli_shipping_url)
        model = BORDEREAUBYPARCELSNUMBERS
        DM = FromModel(carrier.coli_account_number, carrier.coli_passwd)
        options = {'tracking_numbers': tracking_numbers}
        values = DM.build_values(model, None, options=options)[0]
        try:
            r = self.client.service.generateBordereauByParcelsNumbers(**values)
        except zeep.exceptions.Fault as e:
            _logger.error('Fault from Colissimo API: %s' % e)
            raise UserError(_('Fault from Colissimo API: %s') % (e))
        except zeep.exceptions.Error as e:
            _logger.error('Error from Colissimo API: %s' % e)
            raise UserError(_('Error from Colissimo API: %s') % (e))
        else:
            for msg in r.messages:
                if msg['type'] == 'ERROR':
                    raise UserError(
                        _("Error when retrieve label(s): %s (%s)") % (
                            msg['messageContent'], msg['id']))
            self.response.append({
                    'pdf': r['bordereau']['bordereauDataHandler'],
                    'date': r['bordereau']['bordereauHeader']['publishingDate'],
                    'name': r['bordereau']['bordereauHeader']['bordereauNumber'],
                    'details': r['bordereau']['bordereauHeader'],
                    })
            return self.response

    def shipping_request(self, record, carrier):
        """ Removal request to the carrier.
        """
        packages = record.move_line_ids.mapped('result_package_id')
        if not packages:
            raise UserError(_("Some products have not been put in packages!"))

        result = {
            'price': 0.0,
            'currency': record.company_id.currency_id.name,
            }

        self.client = zeep.Client(wsdl=carrier.coli_shipping_url)
        model = GENERATELABEL
        DM = FromModel(carrier.coli_account_number, carrier.coli_passwd)

        # we need to loop on the number of packages because we have to make
        # a label per package.
        for package in packages:
            options = {'package': package}
            values = DM.build_values(model, record, options=options)[0]
            #values = self._build_values(model, record, options=options)
            if record.coli_cn23_need:
                 values = self.get_cn23(record, values, package)
            _logger.debug("shipping_request: %s" % values)
            try:
                r = self.client.service.generateLabel(values)
            except zeep.exceptions.Fault as e:
                _logger.error('Fault from Colissimo API: %s' % e)
                raise UserError(_('Fault from Colissimo API: %s') % (e))
            except zeep.exceptions.Error as e:
                _logger.error('Error from Colissimo API: %s' % e)
                raise UserError(_('Error from Colissimo API: %s') % (e))
            else:
                for msg in r.messages:
                    if msg['type'] == 'ERROR':
                        raise UserError(
                            _("Error when retrieve label(s): %s (%s)") % (
                                msg['messageContent'], msg['id']))
                lbl = r.labelResponse

                self.response.append((
                    lbl['parcelNumber'],
                    lbl['label'],
                    lbl['cn23'],
                ))

                tracking = ', '.join(list(filter(None, [
                            result.setdefault('tracking_number', ''),
                            lbl['parcelNumber'],
                            ])))
                result.update({'tracking_number': tracking})
        return result

    def get_response(self):
        return self.response

    def cancel_request(self, record, carrier):
        raise UserError(
            _("Colissimo does not offer cancellation of requests. "
              "Do not put the package acts as cancellation."))

    def relaypoint_request(self, record, carrier):
        result = []
        self.client = zeep.Client(carrier.coli_relaypoint_url)

        model = RECHERCHEPOINT
        DM = FromModel(carrier.coli_account_number, carrier.coli_passwd)
        data = DM.build_values(model, record)[0]

        _logger.debug("relaypoint_request: %s" % data)
        try:
            r = self.client.service.findRDVPointRetraitAcheminement(*data)
        except WebFault as e:
            _logger.error('Fault from Colissimo API: %s' % e)
            raise UserError(_('Fault from Colissimo API: %s') % (e))
        except Exception as e:
            _logger.error('Error from Colissimo API: %s' % e)
            raise UserError(_('Error from Colissimo API: %s') % (e))
        else:
            if r.errorCode != 0:
                raise UserError(
                    _('Error when retrieve relay points: %s (%s)') % (
                    r.errorMessage, r.errorCode))
            for point in r.listePointRetraitAcheminement:
                address = {
                    'name': str(point.nom),
                    'street': point.adresse1,
                    'street2': ', '.join(
                        filter(None, [point.adresse2, point.adresse3])),
                    'zip': point.codePostal,
                    'city': point.localite,
                    'country_id': record.env['res.country'].search([
                            ('code', '=', point.codePays),
                            ]).id,
                    'code_relaypoint': point.identifiant,
                    'coli_product_code': point.typeDePoint,
                    }
                hours = [
                    (d, getattr(point, 'horairesOuverture%s' % (_(d),)))
                    for d in DAYS
                    ]
                result.append({
                    'address': address,
                    'hours': hours
                    })
            return result

    def relaypoint_request_one(self, id, carrier):
        result = []
        self.client = zeep.Client(carrier.coli_relaypoint_url)

        model = RECHERCHEPOINTONE
        DM = FromModel(carrier.coli_account_number, carrier.coli_passwd)
        data = DM.build_values(model, id)[0]

        _logger.debug("relaypoint_request one: %s" % data)
        try:
            r = self.client.service.findPointRetraitAcheminementByID(*data)
        except WebFault as e:
            _logger.error('Fault from Colissimo API: %s' % e)
            raise UserError(_('Fault from Colissimo API: %s') % (e))
        except Exception as e:
            _logger.error('Error from Colissimo API: %s' % e)
            raise UserError(_('Error from Colissimo API: %s') % (e))
        else:
            if r.errorCode != 0:
                raise UserError(
                    _('Error when retrieve relay point: %s (%s)') % (
                    r.errorMessage, r.errorCode))
            point = r.pointRetraitAcheminement
            address = {
                'name': str(point.nom),
                'street': point.adresse1,
                'street2': ', '.join(
                    filter(None, [point.adresse2, point.adresse3])),
                'zip': point.codePostal,
                'city': point.localite,
                'country_id': carrier.env['res.country'].search([
                        ('code', '=', point.codePays),
                        ]).id,
                'code_relaypoint': point.identifiant,
                'typeDePoint': point.typeDePoint,
                }
            return address

    def get_cn23(self, record, values, package):
        article = []
        for line in package.quant_ids:
            price = 1
            if record.sale_id:
                price = record.env["sale.order.line"].search([('order_id', '=', record.sale_id.id), ('product_id', '=', line.product_id.id) ], limit=1).price_unit
            product = {
                "description": line.product_id.name,
                "quantity": int(line.quantity),
                "weight": line.product_id.weight,
                "value": price,
                "hsCode": line.product_id.hs_code,
                # todo : gestion des pays origine
                "originCountry": 'FR',
            }
            article.append(product)
        cn23 = {
            "includeCustomsDeclarations": 1,
            "contents": {
                "article": article,
                "category": {
                    "value": 3
                }
            },

        }
        values["letter"]["customsDeclarations"] = cn23

        # set delivery price if not set
        if record.sale_id:
            delivery_price = record.get_delivery_price()
            values["letter"]["service"]["totalAmount"] = int(delivery_price * 100)

        values["letter"]["service"]["returnTypeChoice"] = 3

        field = {
            'key': 'EORI',
            'value': record.env.company.phi_eori_number,
        }
        custom_fields = []
        fields = []
        custom_fields.append(field)
        fields.append(field)
        fields = {
            "customField": custom_fields,
            "field": custom_fields,
        }
        values["fields"] = fields
        return values

