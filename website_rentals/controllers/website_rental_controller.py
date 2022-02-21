import datetime

from odoo.http import Controller, route, request

class WebsiteRentalController(Controller):
    @route(
        ["/website/rentals/can_rent"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False
    )
    def can_rent(self, product_id, start_date, stop_date, qty=None):
        return request.env["product.product"]\
            .sudo()\
            .browse(product_id)\
            .can_rent(start_date, stop_date, qty=qty)

    @route(
        ["/website/rentals/get_product"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False
    )
    def get_product(self, product_id):
        return request.env["product.product"]\
            .sudo()\
            .search_read(
                [("id", "=", product_id)],
                fields=("id", "name", "display_name", "description_sale", "preparation_time"),
                limit=1,
            )

    @route(
        ["/website/rentals/get_available_rental_qty"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False
    )
    def get_available_rental_qty(self, product_id, start_date, stop_date):
        return request.env["product.product"]\
            .sudo()\
            .browse(product_id)\
            .get_available_rental_qty(start_date, stop_date)

    @route(
        ["/website/rentals/get_rental_hourly_timeslots"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False
    )
    def get_rental_hourly_timeslots(self, product_id, start_date, stop_date, quantity=0, include_start=True, include_stop=True):
        timezone = request.httprequest.cookies.get('tz')
        # Add space between date and time for the start time we get from the js side
        if len(start_date) == 15:
            start_date = start_date[:10] + " " + start_date[10:]
        timeslots = request.env["product.product"]\
            .sudo()\
            .browse(product_id)\
            .get_rental_hourly_timeslots(start_date, stop_date, quantity, include_start, include_stop, timezone)
        return timeslots

    @route(
        ["/website/rentals/get_price"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False
    )
    def get_price(self, product_id, start_date, stop_date, qty):
        currency = request.env.company.currency_id
        wizard = request.env["rental.wizard"]\
            .sudo()\
            .create({
                "product_id": product_id,
                "pickup_date": start_date,
                "return_date": stop_date,
                "quantity": float(qty),
            })

        wizard._compute_unit_price()

        return currency.pretty(wizard.unit_price * float(qty))
