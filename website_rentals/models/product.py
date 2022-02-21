import datetime
import dateutil
from odoo import _, models
from odoo.addons.website_rentals.helpers.time import parse_datetime


class Product(models.Model):
    _inherit = "product.product"

    def can_rent(self, start_date, stop_date, qty=None):
        return self.env["website.rentals.scheduling"].can_rent(
            self, start_date, stop_date, qty=qty
        )

    def get_available_rental_qty(self, start_date, stop_date):
        return self.env["website.rentals.scheduling"].get_available_qty(
            self, start_date, stop_date
        )

    def get_rental_hourly_timeslots(self, start_date, stop_date=None, quantity=0, include_start=True, include_stop=True, timezone=None):
        return self.env["website.rentals.scheduling"].get_rental_hourly_timeslots(
            self, start_date, stop_date, quantity, include_start, include_stop, timezone
        )

    def shortest_price_rule(self):
        """
        Returns the shortest duration pricing rule.

        This is used as an interval for generating pricing rules in the
        scheduling helper.
        """
        return self.env["rental.pricing"].search(
            [
                ("id", "in", self.rental_pricing_ids.ids),
                ("unit", "=", "hour")
            ],
            order="duration asc",
            limit=1,
        )
