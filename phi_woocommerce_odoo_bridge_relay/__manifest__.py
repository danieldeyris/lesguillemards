# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2020-Present Phidias (https://www.phidias.fr)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
{
  "name"                 :  "Phidias Odoo Multichannel Woocomemrce Connector - relay point",
  "summary"              :  """ Adaptations pour module import prestashop avec point relais""",
  "category"             :  "Website",
  "version"              :  "1.6.3",
  "sequence"             :  1,
  "author"               :  "Phidias",
  "website"              :  "https://www.phidias.fr",
  "description"          :  """Adaptations pour module import prestashop avec point relais""",
  "depends"              :  ['woocommerce_odoo_connector', 'a4o_delivery_relaypoint'],
  "data"                 :  [ 'views/order_feed.xml'],
  "application"          :  False,
  "installable"          :  True,
  "auto_install"         :  True,
}