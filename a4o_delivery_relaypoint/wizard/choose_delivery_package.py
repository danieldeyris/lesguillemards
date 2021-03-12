# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, fields, models, _


class ChooseDeliveryPackage(models.TransientModel):
    _description = 'Delivery Package Selection Wizard'
    _inherit = 'choose.delivery.package'

    mandatory_weight = fields.Boolean(string='Mandatory Shipping Weight',
        compute='_compute_mandatory_weight')

    def _compute_mandatory_weight(self):
        self.mandatory_weight = False
