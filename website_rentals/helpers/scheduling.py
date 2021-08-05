import dateutil
from datetime import timedelta
from odoo import fields, models


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

        return self.get_available_qty(product, start_date, stop_date) >= (qty or 0)

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

        res = self.env["sale.order.line"]

        reservations = self.get_reservations(product)
        if not reservations:
            return res

        for reservation in reservations:
            if self.range_overlaps(
                (start_date, stop_date),
                (
                    reservation.pickup_date - timedelta(hours=-reservation.product_id.product_tmpl_id.preparation_time),
                    reservation.return_date
                ),
            ):
                res |= reservation

        return res

    def get_reservations(self, product):
        """
        Check if a given product is already on order/out to another customer.

        Returns a list of order lines where this product is currently reserved.
        """

        return self.env["sale.order.line"].search(
            [
                ("order_id.is_rental_order", "=", True),
                ("order_id.rental_status", "in", ("pickup", "return")),
                ("product_id", "=", product.id),
            ]
        )

    def range_overlaps(self, range_a, range_b):
        """
        Checks if two date ranges overlap.

            range_overlaps((a_start, a_end), (b_start, b_end))
        """

        def str_to_datetime(data):
            if type(data) != str:
                return data.replace(tzinfo=None)
            return dateutil.parser.parse(data).replace(tzinfo=None)

        # ensure that we are working with datetime objects and not strings
        range_a = (str_to_datetime(range_a[0]), str_to_datetime(range_a[1]))
        range_b = (str_to_datetime(range_b[0]), str_to_datetime(range_b[1]))

        return ((range_a[0] <= range_b[1]) and (range_a[1] >= range_b[0]))
