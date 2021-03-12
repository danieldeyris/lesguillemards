# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from .colissimo_request import ColissimoRequest, LABEL_FORMAT
import re
import json
import logging

_logger = logging.getLogger(__name__)


EUROPE = ['FR', 'AD', 'MC', 'AT', 'BE', 'BG', 'CH', 'CY', 'CZ', 'DE', 'DK', 'EE', 'ES', 'GR', 'FI', 'HR', 'HU', 'IE', 'IT', 'IS', 'LT', 'LU', 'LV', 'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'SE', 'SI', 'SK', 'GB']
FRANCE = ['FR', 'AD', 'MC']
DOM_TOM = ['GP', 'MQ', 'GF', 'RE', 'YT', 'PM', 'MF', 'BL','NC', 'PF', 'WF', 'TF']
EUROPE_CN23 = ['CH', 'HR', 'IS', 'NO']


COLISSIMO_SERVICE= [
    ('dom', 'Domicile sans signature'),
    ('dom_sign', 'Domicile avec signature'),
    ('relays_point', 'Point Relais')
]


COLISSIMO_DESTINATION={
    'FRANCE': FRANCE,
    'OM': DOM_TOM,
    'EUROPE': EUROPE,
}

COLISSIMO_ASSURANCE = [
    ('150', '150 EUR'),
    ('300', '300 EUR'),
    ('500', '500 EUR'),
    ('1000', '1000 EUR'),
    ('2000', '2000 EUR'),
    ('5000', '5000 EUR'),
]

COLISSIMO_SERVICE_BY_DESTINATION={
    'dom': {'FRANCE': 'DOM', 'OM' : 'COM', 'EUROPE': 'DOM', 'WORLDWIDE': 'COLI'},
    'dom_sign': { 'FRANCE': 'DOS', 'OM' : 'CDS', 'EUROPE': 'DOS', 'WORLDWIDE': 'COLI'},
    }

CN23_EXCEPTION = ['ES', 'IT', 'DE', 'CH', 'GB', 'GR']


class ProviderColissimo(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('colissimo', "Colissimo")])
    coli_account_number = fields.Char(
        string='Account Number', groups="base.group_system", size=6,
        help="Colissimo contract number (the same is used for the production "
             "and the tests).")
    coli_passwd = fields.Char(
        string='Password', groups="base.group_system",
        help="Password to use for connection")
    coli_label_format = fields.Selection(
        LABEL_FORMAT, string="Label Colissimo Format", required=True,
        default='PDF_10x15_300dpi')
    coli_remove_label = fields.Boolean(
        'Remove the attached colissimo label', default=False,
        help="When canceling a shipment, remove the attached labels.")
    coli_shipping_url = fields.Char(
        string='Shipping URL (colissimo)', groups="base.group_system",
        help="WSDL url for shipping.")
    coli_relaypoint_url = fields.Char(
        string='Relay Point URL', groups="base.group_system",
        help="WSDL url for searching relay point.")
    coli_max_point = fields.Integer(
        string="Relay Points Max", default=5,
        help="Max number of relay points returned by the search request.")
    coli_distance_search = fields.Integer(
        string="Search distance", default=10,
        help="Maximum search distance of relay points in the request.")

    coli_service = fields.Selection(COLISSIMO_SERVICE,
                                     string="Service",
                                     required=True, default='dom')

    coli_assurance_min_amount = fields.Float(string="Montant minimal pour assurance", default=0)

    coli_assurance = fields.Selection(COLISSIMO_ASSURANCE,
                                     string="Assurance")


    def _check_value(self, value, size):
        if re.search("[^0-9]", value):
            raise UserError(_('Only digit chars are authorised in this field!'))
        if len(value) != size:
            raise UserError(_('This field must have to %s characters!') % size)
        return value

    @api.onchange('coli_account_number')
    def onchange_coli_account_number(self):
        if self.coli_account_number:
            self.coli_account_number = self._check_value(
                self.coli_account_number, 6)

    def colissimo_get_delivery_slip(self, pickings):
        _logger.debug("colissimo_get_delivery_slip: begin")
        DeliverySlip = self.env['delivery.slip']
        Attachments = self.env['ir.attachment']

        if not all([x.carrier_tracking_ref for x in pickings]):
            raise UserError(
                _("Some selected pickings are no tracking number!"))

        tracking_numbers = []
        for picking in pickings:
            numbers = picking.carrier_tracking_ref.split(', ')
            for nb in numbers:
                tracking_numbers.append(nb)
        # tracking_numbers = [x.carrier_tracking_ref for x in pickings]
        coli = ColissimoRequest(self.prod_environment, self.log_xml)
        delivery_slips = coli.delivery_slip_request(tracking_numbers, self)
        if not delivery_slips:
            raise UserError(
                _("No delivery slip was returned!"))
        delivery_slip = delivery_slips[0]
        dl = DeliverySlip.create({
            'name': delivery_slip['name'],
            'date': delivery_slip['date'],
            'delivery_type': self.delivery_type,
            'pickings': [(6, 0, [x.id for x in pickings])],
            })
        if dl:
            log_message = (
                _("Delivery slip getting from Colissimo<br/> "
                    "<b>with number:</b> %s") % delivery_slip['name'])
            attachments = [(
                    _('Delivery_Slip_%s.pdf') % delivery_slip['name'],
                    delivery_slip['pdf'])]
            dl.message_post(body=log_message, attachments=attachments)
            form = self.env.ref('a4o_delivery_slip.delivery_slip_view_form')
            return {
                'name': _('Delivery Slip'),
                'type': 'ir.actions.act_window',
                #'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'delivery.slip',
                'views': [(form.id, 'form')],
                'view_id': form.id,
                'target': 'current',
                'res_id': dl.id,
                }

    def colissimo_send_shipping(self, pickings):
        _logger.debug("colissimo_send_shipping: begin")
        res = []
        coli = ColissimoRequest(self.prod_environment, self.log_xml)
        for picking in pickings:
            package_count = len(picking.package_ids) or 1
            _logger.debug(
                "colissimo_send_shipping: Pack. count: %s" % package_count)
            shipping = coli.shipping_request(picking, self)
            carrier_tracking_ref = shipping['tracking_number']

            currency = (
                picking.sale_id.currency_id or picking.company_id.currency_id)
            if currency.name == shipping['currency']:
                carrier_price = float(shipping['price'])
            else:
                quote_currency = self.env['res.currency'].search([
                    ('name', '=', shipping['currency']),
                    ], limit=1)
                carrier_price = quote_currency._convert(
                    float(shipping['price']), currency, picking.company_id,
                    picking.sale_id.date_order or fields.Date.today())

            package_labels = coli.get_response()
            log_message = (
                _("Shipment created into Colissimo<br/> "
                    "<b>Tracking Numbers:</b> %s<br/>"
                    "<b>Packages:</b> %s") % (
                        carrier_tracking_ref,
                        ', '.join([pl[0] for pl in package_labels])))
            if self.coli_label_format.startswith('PDF_'):
                attachments = [(
                        _('Label_Colissimo.pdf'),
                        pdf.merge_pdf([pl[1] for pl in package_labels]))]
            else:
                attachments = [(
                    _('Label_Colissimo-%s.%s') % (
                        pl[0], self.coli_label_format),
                    pl[1]) for pl in package_labels]

            picking.message_post(body=log_message, attachments=attachments)

            try:
                cn23 = [(('cn23.pdf'), pdf.merge_pdf([pl[2] for pl in package_labels]))]
                if cn23:
                    log_message = (_("Shipment CN23 declaration<br/>"))
                    picking.message_post(body=log_message, attachments=cn23)
            except Exception:
                pass

            shipping_data = {
                'exact_price': carrier_price,
                'tracking_number': carrier_tracking_ref,
                }
            res += [shipping_data]
        return res

    def colissimo_cancel_shipment(self, picking):
        picking.message_post(
            body=_("Colissimo does not offer cancellation of requests."
                "Do not put the package %s acts as "
                "cancellation!") % (picking.carrier_tracking_ref))
        picking.write({
            'carrier_tracking_ref': '',
            'carrier_price': 0.0,
            })
        # Remove attachment ...
        if self.coli_remove_label:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', picking._name),
                ('res_id', '=', picking.id),
                ('name', 'like', '_Colissimo'),
                ])
            if attachments:
                attachments.unlink()

    def colissimo_get_tracking_link(self, picking):
        tracking_urls = []
        for nb in picking.carrier_tracking_ref.split(', '):
            tracking_urls.append((
                _("Package_%s") % nb,
                'https://www.laposte.fr/outils/suivre-vos-envois?code=%s' % nb,
                ))
        return (len(tracking_urls) == 1
            and tracking_urls[0][1]
            or json.dumps(tracking_urls))

    def colissimo_rate_shipment(self, order):
        res = {
            'success': False,
            'price': 0.0,
            #'warning_message': _("Don't forget to check the price!"),
            'error_message': None,
            }
        vals = self.base_on_rule_rate_shipment(order)
        if vals.get('success'):
            price = vals['price']
            res.update({
                'success': True,
                'price': price,
                })
        return res

    def colissimo_select_relaypoint(self, pickings):
        _logger.debug('colissimo_select_relaypoint:' % pickings)
        relaypoints = []
        coli = ColissimoRequest(self.prod_environment, self.log_xml)
        for picking in pickings:
            relaypoints += coli.relaypoint_request(picking, self)
        return relaypoints

    def colissimo_get_relaypoint(self, code_relaypoint):
        _logger.debug('colissimo_get_relaypoint: %s' % code_relaypoint)
        coli = ColissimoRequest(self.prod_environment, self.log_xml)
        relaypoint = coli.relaypoint_request_one(code_relaypoint, self)
        return relaypoint

    def get_product_code(self, country_from, country_to):
        # todo : Faire pour expédition hors métropole
        if not country_to:
            raise Exception("Delivery Country cannot be null")

        zone = self.get_country_zone(country_to)
        services = COLISSIMO_SERVICE_BY_DESTINATION.get(self.coli_service)
        if services:
            return services.get(zone)
        return False

    def cn23_need(self, partner_id):
        if partner_id.country_id.code in CN23_EXCEPTION:
            return not self.cn23_exceptions(partner_id)

        if partner_id.country_id.code in EUROPE and partner_id.country_id.code not in EUROPE_CN23:
            return False
        else:
            return True

    @staticmethod
    def get_ftd(partner_id):
        if partner_id.country_id.code in DOM_TOM:
            return True
        else:
            return False

    @staticmethod
    def get_country_zone(country):
        for zone, countries in COLISSIMO_DESTINATION.items():
            if country.code in countries:
                return zone
        return 'WORLDWIDE'

    @staticmethod
    def cn23_exceptions(partner_id):
        if partner_id.country_id.code == 'ES':
            province = partner_id.zip[:2]
            if province in ['35', '38', '51', '52']:
                return True
        elif partner_id.country_id.code == 'IT':
            if partner_id.zip in ['23030', '22060']:
                return True
        elif partner_id.country_id.code == 'DE':
            if partner_id.zip in ['27498', '78266']:
                return True
        elif partner_id.country_id.code == 'CH':
            if partner_id.zip == '8238':
                return True
        elif partner_id.country_id.code == 'GB':
            zone = partner_id.zip[:2]
            if zone in ['JE', 'IM', 'GY']:
                return True
        elif partner_id.country_id.code == 'GR':
            if partner_id.zip in ['63075', '60386', '63086', '63087', '630 75', '603 86', '630 86', '630 87']:
                return True
        return False

