# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    mandatory_weight = fields.Boolean(string='Mandatory Shipping Weight',
        compute='_compute_mandatory_weight')

    def _compute_mandatory_weight(self):
        self.mandatory_weight = False

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_get_relaypoint(self):
        context = dict(self.env.context or {})
        # Get addresses
        addr = self.partner_id.parent_id or self.partner_id
        address_ids = [addr.id] + [x.id for x in addr.child_ids]
        context.update({
            'picking_id': self.id,
            'address_ids': address_ids,
            'default_address': self.partner_id.id,
            })
        return {
            'name': _('Select the address'),
            #'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery.carrier.relaypoint',
            'view_id': self.env.ref(
                'a4o_delivery_relaypoint.select_relaypoint_view_form').id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
