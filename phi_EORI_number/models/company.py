# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class company(models.Model):
    _inherit = 'res.company'

    phi_eori_number = fields.Char("EORI number")
