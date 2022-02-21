from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    rental_check_availability_on_all_products = fields.Boolean(
        string='Check availability on all products'
    )
