# -*- coding: utf-8 -*-
from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    image = fields.Binary(related="branch_id.logo")


class PosSession(models.Model):
    _inherit = 'pos.session'

    branch_email = fields.Char(related="branch_id.email")
    branch_website = fields.Char(related="branch_id.website")
    branch_telephone = fields.Char(related="branch_id.telephone")