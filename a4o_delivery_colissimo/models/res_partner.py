# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _description = 'Contact'
    _inherit = 'res.partner'

    @api.depends('name', 'is_company')
    def get_names(self):
        """Get names info for labels."""
        names = {
            'company': '',
            'lastname': self.name,
            'firstname': '.',
            }
        if self.parent_id and self.parent_id.is_company:
            # if link to company get company name.
            names['company'] =self.parent_id.name

        # if self.parent_id and not self.parent_id.is_company:
        #     # if link to company get company name.
        #     names['lastname'] =self.parent_id.name

        return names

    def get_phone(self):
        if self.self.parent_id:
            phone = self.phone or self.self.parent_id.phone
        else:
            phone = self.phone
        if phone:
          phone = phone.replace(' ','')
        return phone

    def get_mobile_phone(self):
        if self.self.parent_id:
            phone = self.mobile or self.self.parent_id.mobile
        else:
            phone = self.mobile
        if phone:
          phone = phone.replace(' ','')
        return phone