# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
import logging
import pytz
from datetime import datetime

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    @api.depends('packaging_id')
    def _compute_mandatory_weight(self):
        result = super(StockQuantPackage, self)._compute_mandatory_weight()
        if (self.packaging_id
                and self.packaging_id.package_carrier_type == 'colissimo'):
            result = True
        self.mandatory_weight = result


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    coli_product_code = fields.Char('Product Code', compute='_compute_product_code')

    is_relay_point = fields.Boolean('Point Relais', compute='_compute_is_relay_point')

    coli_cn23_need = fields.Boolean(string="Déclaration douane", compute='_compute_cn23_need')

    def _compute_product_code(self):
        for record in self:
            if record.is_relay_point:
                if record.carrier_id and record.partner_id.code_relaypoint:
                    if not record.partner_id.coli_product_code:
                        point = record.carrier_id.get_relaypoint(record.partner_id.code_relaypoint)
                        record.partner_id.coli_product_code = point.get("typeDePoint")
                    record.coli_product_code = record.partner_id.coli_product_code
                else:
                    record.coli_product_code = False
            else:
                record.coli_product_code = record.carrier_id.get_product_code(self.company_id.country_id, self.partner_id.country_id)

    def _compute_is_relay_point(self):
        for record in self:
            if record.carrier_id and record.carrier_id.coli_service == 'relays_point':
                record.is_relay_point = True
            else:
                record.is_relay_point = False

    def _compute_cn23_need(self):
        for record in self:
            if record.carrier_id:
                record.coli_cn23_need = record.carrier_id.cn23_need(self.partner_id)
            else:
                record.coli_cn23_need = False

    def get_deposit_date_local(self):
        tz_name = self.env.context.get('tz') or self.env.user.tz or 'Europe/Paris'
        user_tz = pytz.timezone(tz_name)

        deposit_date = datetime.now()
        deposit_date = pytz.utc.localize(deposit_date).astimezone(user_tz)
        return deposit_date

    def get_optionInter(self):
        if self.partner_id.country_id.code == 'FR':
            return 0
        else:
            return 1

    def get_delivery_price(self):
        price = sum([l.price_total for l in self.sale_id.order_line if l.is_delivery])
        if not price:
            price = 0
        return price

    def get_ftd(self):
        return self.carrier_id.get_ftd(self.partner_id)

    def get_insurance(self):
        if self.carrier_id.coli_assurance:
            if self.carrier_id.coli_assurance_min_amount and self.sale_id and self.sale_id.amount_total < self.carrier_id.coli_assurance_min_amount :
                return False
            return int(self.carrier_id.coli_assurance) * 100
        else:
            return False

    def get_postal_code(self):
        # if self.partner_id.country_id.code == 'PT':
        #     zip = self.partner_id.zip.split('-')
        #     return zip[0]
        # else:
        #     return self.partner_id.zip
        return self.partner_id.zip.replace('-','')