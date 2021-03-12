# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    code_relaypoint = fields.Char(index=True)
    coli_product_code = fields.Char('Product Code')

    def get_coli_product_code(self, carrier_id):
        if self.code_relaypoint and not self.coli_product_code:
            self.coli_product_code = carrier_id.get_relaypoint(self.code_relaypoint)
        return self.coli_product_code
