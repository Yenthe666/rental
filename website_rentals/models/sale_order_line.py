from odoo import models, fields
import datetime


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    pickup_date_no_timezone = fields.Char(
        string="Pickup date without timezone",
        compute='_compute_pickup_date_no_timezone'
    )

    return_date_no_timezone = fields.Char(
        string="Return date without timezone",
        compute='_compute_pickup_date_no_timezone'
    )

    def _compute_pickup_date_no_timezone(self):
        lang = self.env.user.lang
        if not lang:
            lang = self.env.ref('base.user_admin').lang
        lang_id = self.env['res.lang'].search([('code', '=', lang)], limit=1)
        for record in self:
            if record.pickup_date:
                record.pickup_date_no_timezone = record.pickup_date.replace(tzinfo=None).strftime(
                    lang_id.date_format + ' ' + lang_id.time_format
                )
            if record.return_date:
                record.return_date_no_timezone = record.return_date.replace(tzinfo=None).strftime(
                    lang_id.date_format + ' ' + lang_id.time_format
                )
