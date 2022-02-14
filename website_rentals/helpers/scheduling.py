from datetime import datetime, timedelta
from odoo import fields, models
from odoo.addons.website_rentals.helpers.misc import float_range
from odoo.addons.website_rentals.helpers.time import parse_datetime, float_to_time


def _filter_preparation_time(date, cutoff):
    """Creates a filter function for dates that don't meet a cutoff time."""

    def _filter(time):
        return date.replace(hour=float_to_time(time)["hours"], minute=float_to_time(time)["minutes"]) >= cutoff

    return _filter


def _filter_after_now(date):
    """Creates a filter function for timeslot days that are before the current time."""
    return _filter_preparation_time(date, datetime.now())


def _format_timeslot_time(time):
    """
    Formats a floating point time as a string for display.

        self._format_timeslot_time(6.5)   => 06:30
        self._format_timeslot_time(7.75)  => 07:45
    """
    time = float_to_time(time)

    return f"{time['hours']:02}:{time['minutes']:02}"


class SchedulingHelper(models.AbstractModel):
    """Utilities for handling rental scheduling."""

    _name = "website.rentals.scheduling"
    _description = "Scheduling Utilities"

    def can_rent(self, product, start_date, stop_date, qty=None):
        """
        Checks if a given product can be ordered based on it's rental and stock availability.
        Determining if a product can be rented is based on the number of bookings
        in a given time period. For example, if a customer wants to book from
        July 1 to July 4 then this function looks at reservations within that
        time range and compares against the available stock. If there is 4
        available products and only 3 are scheduled to be picked up or already
        are picked up then the product can be rented.
        Non stockable type products have no capacity by default and can always
        be booked.
        """

        if product.type != "product":
            return True

        if not product.rent_ok:
            return False

        return (
            self.get_available_qty(product, start_date, stop_date) >= (qty or 0)
            and parse_datetime(start_date) >= datetime.now() + timedelta(hours=product.preparation_time or 0)
        )

    def get_available_qty(self, product, start_date, stop_date):
        """
        Get the available quantity of a product for a time period.
        This function is finding the total availability for a product based on
        what's currently "out on rent" + "on hand" quantity. This is not a
        perfect solution because if a customer is renting something 6 months
        from now we cannot predict what the on hand quantity is going to be, so
        making an assumption based on what product is currently in the system.
        """

        overlapping_reservations = self.get_overlapping_reservations(product, start_date, stop_date)
        total_units = product.qty_in_rent + product.qty_available

        return max(0, total_units - sum(overlapping_reservations.mapped("product_uom_qty")))

    def get_overlapping_reservations(self, product, start_date, stop_date):
        """Returns order lines that are confirmed for a given product and time period."""

        res = self.env["sale.rental.schedule"]

        reservations = self.env["sale.order.line"]

        if product.product_tmpl_id.rental_check_availability_on_all_products:
            for prod in product.product_tmpl_id.product_variant_ids:
                reservations += self.get_reservations(prod)
        else:
            reservations = self.get_reservations(product)

        if not reservations:
            return res

        rental_schedules = self.env['sale.rental.schedule'].search([('order_line_id', 'in', reservations.ids)])

        for reservation in rental_schedules:
            if self.range_overlaps(
                (start_date, stop_date),
                (
                    reservation.pickup_date,
                    reservation.return_date
                ),
            ):
                res |= reservation

        return res.order_line_id

    def get_reservations(self, product):
        """
        Check if a given product is already on order/out to another customer.
        Returns a list of order lines where this product is currently reserved.
        """

        return self.env["sale.order.line"].search(
            [
                ("order_id.is_rental_order", "=", True),
                ("product_id", "=", product.id),
                '|',
                ("order_id.rental_status", "in", ("pickup", "return")),
                ("order_id.state", "=", "sale")
            ]
        )

    def range_overlaps(self, range_a, range_b):
        """
        Checks if two date ranges overlap.
            range_overlaps((a_start, a_end), (b_start, b_end))
        """
        # ensure that we are working with datetime objects and not strings
        range_a = (parse_datetime(range_a[0]), parse_datetime(range_a[1]))
        range_b = (parse_datetime(range_b[0]), parse_datetime(range_b[1]))

        return ((range_a[0] <= range_b[1]) and (range_a[1] >= range_b[0]))

    def get_rental_hourly_timeslots(self, product, start_date, stop_date=None):
        """
        Generates a set of timeslots for a certain time period based on this
        products rental pricing rules.

        The smallest interval, hourly pricing rule is used. For example, if a
        product has three rules for 1 hour, 2 hour, and 3 hours, then this is
        going to generate hourly time slots for the start slots.
        """
        start_date = parse_datetime(start_date)
        stop_date = parse_datetime(stop_date or start_date)
        is_same_day = start_date.date() == stop_date.date()

        if not product.rental_pricing_ids:
            return

        if "hour" not in product.mapped("rental_pricing_ids.unit"):
            return

        start_times = self._start_timeslots(product, start_date, same_day=is_same_day)
        if not start_times:
            return

        stop_times = self._stop_timeslots(product, stop_date, same_day=is_same_day, offset=start_times[0])
        if not stop_times:
            return

        return {
            "start": list(map(_format_timeslot_time, start_times)),
            "stop": list(map(_format_timeslot_time, stop_times)),
        }

    def _start_timeslots(self, product, date, same_day=False):
        """Rentable start timeslots for a product."""
        price_rule = product.shortest_price_rule()
        step = 1.0 if not same_day else price_rule.duration
        times = float_range(price_rule.start_time, price_rule.end_time, step)

        if product.preparation_time:
            times = filter(
                _filter_preparation_time(
                    date,
                    cutoff=datetime.now() + timedelta(hours=product.preparation_time),
                ),
                times,
            )

        times = filter(_filter_after_now(date), times)

        return list(times)

    def _stop_timeslots(self, product, date, same_day=False, offset=None):
        """Rentalable end timeslots for a product."""
        price_rule = product.shortest_price_rule()
        step = 1.0

        times = float_range(
            offset + price_rule.duration if same_day else price_rule.start_time,
            price_rule.end_time,
            step,
        )

        times = filter(_filter_after_now(date), times)

        return list(times)
