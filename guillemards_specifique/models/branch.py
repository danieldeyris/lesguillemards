# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResBranch(models.Model):
    _inherit = 'res.branch'

    logo = fields.Binary('Website Logo', help="Display this logo on the branch.")
    email = fields.Char('Email')
    website = fields.Char(string="Site WEB", help='eg. http://xyz.com')
    partner_id = fields.Many2one('res.partner', string='Adresse')
    telephone = fields.Char(string='Téléphone')
    street = fields.Char(related="partner_id.street")