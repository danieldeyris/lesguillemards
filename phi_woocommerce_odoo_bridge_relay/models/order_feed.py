# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2020-Present Phidias (https://www.phidias.fr)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import fields,models


class OrderFeed(models.Model):
	_name        = 'order.feed'
	_inherit     = 'order.feed'

	shipping_code_relaypoint = fields.Char('Shipping Code Relaypoint')
