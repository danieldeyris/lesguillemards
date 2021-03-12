# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    branch_id = fields.Many2one('res.branch', required=True)