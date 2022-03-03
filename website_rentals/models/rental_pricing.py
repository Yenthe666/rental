from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RentalPricing(models.Model):
    _inherit = "rental.pricing"

    start_time = fields.Float(
        string="Start Time"
    )

    end_time = fields.Float(
        string="End Time"
    )

    @api.constrains("start_time", "end_time")
    def check_time_range(self):
        for rule in self:
            if rule.end_time < rule.start_time:
                raise ValidationError(_("A pricing rule start time cannot be greater than its end time."))

    def _compute_price(self, duration, unit):
        """
        Take the price for extra hours or extra days into account
        """
        price = super(RentalPricing, self)._compute_price(duration, unit)
        if unit == self.unit and 0 < self.duration < duration:
            if self.product_template_id.extra_hourly and self.unit == 'hour':
                duration_rest = duration - self.duration
                price = self.price + self.product_template_id.extra_hourly * duration_rest
            elif self.product_template_id.extra_daily and self.unit == 'day':
                duration_rest = duration - self.duration
                price = self.price + self.product_template_id.extra_daily * duration_rest
        return price

    @property
    def start_time_hour(self):
        self.ensure_one()
        return int(self.start_time)

    @property
    def start_time_minutes(self):
        self.ensure_one()
        return int(60 * (self.start_time - self.start_time_hour))

    @property
    def end_time_hour(self):
        self.ensure_one()
        return int(self.end_time)

    @property
    def end_time_minutes(self):
        self.ensure_one()
        return int(60 * (self.end_time - self.end_time_hour))
