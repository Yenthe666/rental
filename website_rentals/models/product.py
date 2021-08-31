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

    def get_rental_hourly_timeslots(self, date=None):
        """
        Generates a set of timeslots for a certain time period based on this
        products rental pricing rules.

        The smallest interval, hourly pricing rule is used. For example, if a
        product has three rules for 1 hour, 2 hour, and 3 hours, then this is
        going to generate hourly time slots.
        """

        now = datetime.datetime.now()
        date = parse_datetime(date)

        if not self.rental_pricing_ids:
            return

        if "hour" not in self.mapped("rental_pricing_ids.unit"):
            return

        # Find the lowest duration "hour" pricing rule
        price_rule = self.env["rental.pricing"].search(
            [
                ("id", "in", self.rental_pricing_ids.ids),
                ("unit", "=", "hour")
            ],
            order="duration asc",
            limit=1,
        )

        # Break up the day into segements of `interval size`. If the smallest
        # pricing rule is 2 hours, then this will divy up the day into the slots
        # 2:00, 4:00, 6:00.

        timeslots = []
        current_timeslot = datetime.datetime(
            year=date.year,
            month=date.month,
            day=date.day,
            hour=0,
            minute=0,
            second=0
        )

        if price_rule.start_time:
            current_timeslot = current_timeslot.replace(
                hour=price_rule.start_time_hour,
                minute=price_rule.start_time_minutes,
            )

        if price_rule.end_time:
            date = date.replace(
                hour=price_rule.end_time_hour,
                minute=price_rule.end_time_minutes
            )

        # Account for security time padding.
        if self.preparation_time:
            current_timeslot += datetime.timedelta(hours=self.preparation_time)

        while True:
            if current_timeslot > date:
                break
            if current_timeslot > now:
                timeslots.append(current_timeslot.strftime("%H:%M"))
            current_timeslot += datetime.timedelta(hours=price_rule.duration)

        return timeslots
