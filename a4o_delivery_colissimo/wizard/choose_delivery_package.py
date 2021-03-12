# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, fields, models, _


class ChooseDeliveryPackage(models.TransientModel):
    _description = 'Delivery Package Selection Wizard'
    _inherit = 'choose.delivery.package'

    @api.depends('delivery_packaging_id')
    def _compute_mandatory_weight(self):
        result = super(ChooseDeliveryPackage, self)._compute_mandatory_weight()
        if (self.delivery_packaging_id
                and self.delivery_packaging_id \
                    .package_carrier_type == 'colissimo'):
            result = True
        self.mandatory_weight = result
