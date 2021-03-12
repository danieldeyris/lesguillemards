from urllib import parse as urlparse
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError


class WoocommerceImages(models.TransientModel):
    _name = 'export.images'
    _description = 'Export Images'

    def update_woocommerce_image_path_template(self, name, template):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = '/channel/image/product.template/%s/image_1920/492x492.png' % (
            template.id)
        full_image_url = '%s' % urlparse.urljoin(base_url, image_url)
        return full_image_url, name

    def update_woocommerce_image_path(self, name, product):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = '/channel/image/product.product/%s/image_1920/492x492.png' % (
            product.id)
        full_image_url = '%s' % urlparse.urljoin(base_url, image_url)
        return full_image_url, name

    def set_woocommerce_images_path_product(self, name, productImage):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = '/channel/image/product.images/%s/image_1920/492x492.png' % (productImage.id)
        full_image_url = '%s' % urlparse.urljoin(base_url, image_url)
        return full_image_url, name

    def get_woocommerce_template_image(self, template):
        image_list = []
        count = 1
        if template.image_1920:
            template_url, name = self.update_woocommerce_image_path_template(template.name, template)
            values = {
                'src'		: template_url,
                'name'		: name,
                'position'	: 0,
            }
            if template.web_image_id:
                values["id"] = template.web_image_id
            image_list.append(values)

        for image in self.env["product.images"].search([('product_tmpl_id', '=', template.id)], order='sequence, id'):
            template_url, name = self.set_woocommerce_images_path_product(template.name, image)
            values = {
                'src'	: template_url,
                'name'		: name,
                'position'	: count,
            }
            if template.web_image_id:
                values["id"] = image.web_image_id
            image_list.append(values)
            count += 1
        return image_list

    def get_woocommerce_product_image(self, product):
        image_list = []
        if product.image_1920:
            template_url, name = self.update_woocommerce_image_path(product.name, product)
            values = {
                'src'	: template_url,
                'name'		: name,
                'position'	: 0,
            }
            if product.web_image_id:
                values["id"] = product.web_image_id
            image_list.append(values)

        return image_list

    def update_template_images_ids(self, template, woocommerce):
        if template.image_1920 and not template.web_image_id:
            template_url, name = self.update_woocommerce_image_path_template(template.name, template)
            id = self.get_image_web_id(name, template_url, woocommerce)
            if id:
                template.web_image_id = id

        for image in self.env["product.images"].search([('product_tmpl_id', '=', template.id)], order='sequence, id'):
            if not image.web_image_id:
                template_url, name = self.set_woocommerce_images_path_product(template.name, template)
                id = self.get_image_web_id(name, template_url, woocommerce)
                if id:
                    image.web_image_id = id

        if len(template.product_variant_ids) > 1:
            for product in template.product_variant_ids:
                if product.image_1920 and not product.web_image_id:
                    template_url, name = self.update_woocommerce_image_path(product.name, product)
                    id = self.get_image_web_id(name, template_url, woocommerce)
                    if id:
                        product.web_image_id = id

    @staticmethod
    def get_image_web_id(name, template_url, woocommerce):
        temp_product_list = {
            'name'		: "temporaire",
            'type'				: 'simple',
            'status'			: 'private',
            'in_stock'			: False,
        }
        values = {
            'src': template_url,
            'name': name,
            'position': 0,
        }
        image_list = []
        image_list.append(values)
        temp_product_list['images'] = image_list
        return_dict = woocommerce.post('products', temp_product_list).json()
        if 'id' in return_dict:
            return_del = woocommerce.delete('products/' + str(return_dict['id'])).json()
            if 'images' in return_dict:
                images = return_dict['images']
                for image in images:
                    if image["position"] == 0:
                        return image["id"]
        return False