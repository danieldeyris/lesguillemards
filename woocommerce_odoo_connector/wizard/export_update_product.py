# -*- coding: utf-8 -*-
#################################################################################
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
##########H#########Y#########P#########N#########O#########S###################
from urllib import parse as urlparse
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError


class UpdateWoocommerceProducts(models.TransientModel):
    _inherit = ["export.templates"]

    def woocommerce_update_now(self, record, remote_id):
        channel = self._context.get('channel_id')
        woocommerce = self._context.get('woocommerce')
        response = self.woocommerce_update_template(
            woocommerce, channel, record, remote_id)
        return [True, response]

    def woocommerce_update_template(self, woocommerce, channel, template_record, remote_id):
        if len(template_record.product_variant_ids)>1:
            return_list = self.update_woocommerce_variable_product(
                woocommerce, channel, template_record, remote_id)
            data_list = return_list
        else:
            returnid = self.update_woocommerce_simple_product(
                woocommerce, channel, template_record, remote_id)
            data_list = (returnid, [])
        return data_list

    def update_woocommerce_attribute_dict(self, woocommerce, channel, variant):
        attribute_dict = []
        if variant.product_template_attribute_value_ids:
            for attribute_line in variant.product_template_attribute_value_ids:
                attr_name, attr_id = self.update_woocommerce_attribute(
                    woocommerce, channel, attribute_line.attribute_id,attribute_line.product_attribute_value_id)
                value_name = attribute_line.product_attribute_value_id.name
                attribute_dict.append({
                    'id'	: attr_id,
                    'name'	: attr_name,
                    'option': value_name,
                })
        return attribute_dict

    def update_woocommerce_attribute_value(self, attribute_line):
        value_list = []
        if attribute_line:
            for value in attribute_line.value_ids:
                value_list.append(value.name)
        return value_list

    def update_woocommerce_attribute(self, woocommerce, channel, attribute_id,attribute_value_ids):
        if attribute_id:
            vals_list = [attribute_id.name,""]
            updated = self.env['export.woocommerce.attributes'].with_context({
                "channel_id": channel,
                "woocommerce": woocommerce,
            }).export_attribute(attribute_id,attribute_value_ids)
            if updated[0]:
                    vals_list[1] = updated[1]
            return vals_list

    def update_woocommerce_attribute_line(self, woocommerce, channel, template):
        attribute_list = []
        attribute_count = 0
        if template.attribute_line_ids:
            for attribute_line in template.attribute_line_ids:
                attr_name, attr_id = self.update_woocommerce_attribute(
                    woocommerce, channel, attribute_line.attribute_id,attribute_line.value_ids)
                values = self.update_woocommerce_attribute_value(attribute_line)
                attribute_dict = {
                    'name'		: attr_name,
                    'id'		: attr_id,
                    'variation'	: True,
                    'visible'	: True,
                    'position'	: attribute_count,
                    'options'	: values,
                }
                attribute_count += 1
                attribute_list.append(attribute_dict)
        return attribute_list

    def update_woocommerce_variation(self, woocommerce, channel, store_template_id, template):
        count = 0
        variant_list = []
        if store_template_id and template:
            for variant in template.product_variant_ids:
                match_record = self.env['channel.product.mappings'].search([
                    ('product_name', '=', variant.id),
                    ('channel_id', '=', channel.id)])
                if match_record:
                    quantity = channel.get_quantity(variant)
                    variant_data = {
                        'regular_price'	: str(variant.get_regular_price(channel)) or "",
                        'visible'		: True,
                        'sku'			: variant.default_code or "",
                        'stock_quantity': quantity,
                        'description'	: variant.description or "",
                        'price'			: str(variant.get_regular_price(channel)) or "",
                        'sale_price'	: str(variant.get_standard_price(channel)) or "",
                        'manage_stock'	: template.manage_stock,
                        'in_stock'		: True,
                        'attributes'	: self.update_woocommerce_attribute_dict(woocommerce, channel, variant),
                    }
                    if variant.length or variant.width or variant.height:
                        dimensions = {
                            'width': str(variant.width) or "",
                            'length': str(variant.length) or "",
                            'unit': str(variant.dimensions_uom_id.name) or "",
                            'height': str(variant.height) or "",
                        }
                        variant_data['dimensions'] = dimensions
                    if variant.weight:
                        variant_data['weight'] = str(variant.weight) or ""
                    if channel.export_images and variant.web_image_id:
                        variant_data.update({'image': {'id': variant.web_image_id}})
                    return_dict = woocommerce.put("products/"+str(store_template_id)+"/variations/"+str(
                        match_record.store_variant_id), variant_data).json()
                    if "message" in return_dict:
                        _logger.info("Error in updating Variants ===> %r",return_dict["message"])
                        continue
                    count += 1
                    variant_list.append(return_dict['id'])
                else:
                    _logger.info(
                        '<<<<<<<<<<< Product not updated to Woocommerce. >>>>>>>>>>')
            return variant_list
        else:
            raise UserError(
                _('Error in updating Product Variant with template id (%s)' % template.id))

    def update_woocommerce_variable_product(self, woocommerce, channel, template, remote_id):
        if template:
            product_dict = {
                'name'				: template.name,
                'sku' 				: "",
                'type'				: 'variable',
                'categories'		: self.set_woocommerce_product_categories(woocommerce, channel, template),
                'status'			: 'publish',
                'manage_stock'		: template.manage_stock,
                'attributes'		: self.update_woocommerce_attribute_line(woocommerce, channel, template),
                'default_attributes': self.update_woocommerce_attribute_dict(woocommerce, channel, template.product_variant_ids[0]),
            }
            if channel.synchro_text:
                product_dict['short_description'] = template.description_short_web or template.description_sale or ""
                product_dict['description'] = template.description_web or template.description or ""

            if template.length or template.width or template.height:
                dimensions = {
                    u'width': str(template.width) or "",
                    u'length': str(template.length) or "",
                    u'unit': str(template.dimensions_uom_id.name) or "",
                    u'height': str(template.height) or "",
                }
                product_dict['dimensions'] = dimensions
            if template.weight:
                product_dict['weight'] = str(template.weight) or ""
            if woocommerce:
                url = 'products/%s' % remote_id

                if channel.export_images:
                    self.env["export.images"].update_template_images_ids(template, woocommerce)
                    product_dict['images'] = self.env["export.images"].get_woocommerce_template_image(template)

                return_dict = woocommerce.put(url, product_dict).json()

                if 'id' in return_dict:
                    store_template_id = return_dict['id']
                    return_list = self.update_woocommerce_variation(woocommerce, channel, remote_id, template)
                    if len(return_list):
                        return (store_template_id, return_list)
                else:
                    raise UserError(
                        _("Error in Updating Product Template in Woocommerce."))

    def update_woocommerce_simple_product(self, woocommerce, channel, template, remote_id):
        quantity = channel.get_quantity(template)
        product_dict = {
            'name'				: template.name,
            'sku' 				: template.default_code or "",
            'regular_price'		: str(template.get_regular_price(channel)) or "",
            'type'				: 'simple',
            'categories'		: self.set_woocommerce_product_categories(woocommerce, channel, template),
            'status'			: 'publish',
            'attributes'		: self.update_woocommerce_attribute_line(woocommerce, channel, template),
            'price'				: str(template.get_regular_price(channel)) or "",
            'sale_price'		: str(template.get_standard_price(channel)) or "",
            'manage_stock'		: template.manage_stock,
            'stock_quantity'	: quantity,
            'in_stock'			: True,
        }
        if channel.synchro_text:
            product_dict['short_description'] = template.description_short_web or template.description_sale or ""
            product_dict['description'] = template.description_web or template.description or ""

        if channel.export_images:
            self.env["export.images"].update_template_images_ids(template, woocommerce)
            product_dict['images'] = self.env["export.images"].get_woocommerce_template_image(template)

        if template.length or template.width or template.height:
            dimensions = {
                'width': str(template.width) or "",
                'length': str(template.length) or "",
                'unit': str(template.dimensions_uom_id.name) or "",
                'height': str(template.height) or "",
            }
            product_dict['dimensions'] = dimensions
        if template.weight:
            product_dict['weight'] = str(template.weight)
        if woocommerce:
            url = 'products/%s' % remote_id
            return_dict = woocommerce.put(url, product_dict).json()
        if 'id' in return_dict:
            return return_dict['id']
        else:
            raise UserError(_('Simple Product Updation Failed'))

    def set_woocommerce_product_categories(self, woocommerce, channel, template):
        categ_list = []
        if template.categ_id:
            cat_id = self.export_woocommerce_categories_id(
                woocommerce, channel, template.categ_id)
            if cat_id:
                categ_list.append({'id': cat_id})
        if template.channel_category_ids:
            for category_channel in template.channel_category_ids:
                if category_channel.instance_id.id == channel.id:
                    for category_id in category_channel.extra_category_ids:
                        extra_categ_id = self.update_woocommerce_categories_id(
                            woocommerce, channel, category_id)
                        categ_list.append({'id': extra_categ_id})
        return categ_list

    def update_woocommerce_categories_id(self, woocommerce, channel, cat_record):
        store_cat_id = None
        is_cat_mapped = self.env['channel.category.mappings'].search([
            ('channel_id', '=', channel.id),
            ("odoo_category_id", '=', cat_record.id)
        ])
        if not is_cat_mapped:
            remote_object = self.env['export.categories'].create({
                "channel_id": channel.id,
                "operation": 'export',
            }).with_context({
                "channel_id": channel,
                "woocommerce": woocommerce,
                "with_product":True
                }).woocommerce_export_now(cat_record, cat_record.id)
            if remote_object[0]:
                store_cat_id = remote_object[1].id
                _logger.info(
                    "Product Category Exported with ID (%r)", cat_record.id)
        else:
            store_cat_id = is_cat_mapped.store_category_id
        return store_cat_id
