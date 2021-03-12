# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'
    _description = 'Delivery Carrier Selection Wizard'

    @api.onchange('carrier_id')
    def _onchange_carrier_id(self):
        if self.delivery_type == 'colissimo':
            vals = self._get_shipment_rate()
            if vals.get('error_message'):
                return {'error': vals['error_message']}
        else:
            return super(ChooseDeliveryCarrier, self)._onchange_carrier_id()
