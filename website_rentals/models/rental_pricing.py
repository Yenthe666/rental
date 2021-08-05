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
