import datetime
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


def current_time():
    # push our current time up 60 seconds to prevent any conflicts with the
    # time checking, if a function takes a couple of seconds to run then
    # our current time will fail checks by the security time functions.
    return datetime.datetime.now() + datetime.timedelta(minutes=1)


class SchedulingTests(TransactionCase):
    def setUp(self):
        super().setUp()


        # sample product data
        self.meeting_room = self.env["product.product"].create(
            {
                "name": "New Meeting Room",
                "categ_id": self.env.ref("sale_renting.cat_renting").id,
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "rent_ok": True,
                "preparation_time": 0.0  # hours
            }
        )
        self.oil_change = self.env["product.product"].create(
            {
                "name": "Oil Change",
                "categ_id": self.env.ref("sale_renting.cat_renting").id,
                "type": "service",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "rent_ok": True,
                "preparation_time": 0.0  # hours
            }
        )
        self.bicycle = self.env["product.product"].create(
            {
                "name": "Bicycle",
                "categ_id": self.env.ref("sale_renting.cat_renting").id,
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "rent_ok": True,
                "preparation_time": 48.0,  # hours
            }
        )

        # sample stock data
        self.env["stock.change.product.qty"].create(
            {
                "product_id": self.meeting_room.id,
                "product_tmpl_id": self.meeting_room.product_tmpl_id.id,
                "new_quantity": 1.0,
            }
        ).change_product_qty()
        self.env["stock.change.product.qty"].create(
            {
                "product_id": self.bicycle.id,
                "product_tmpl_id": self.bicycle.product_tmpl_id.id,
                "new_quantity": 10.0,
            }
        ).change_product_qty()

    def test_overlapping_dates(self):
        scheduling = self.env["website.rentals.scheduling"]

        assert scheduling.range_overlaps(
            (
                current_time(),
                current_time() + datetime.timedelta(hours=5),
            ),
            (
                current_time() - datetime.timedelta(hours=5),
                current_time() + datetime.timedelta(hours=1),
            ),
        )

    def test_non_overlapping_dates(self):
        scheduling = self.env["website.rentals.scheduling"]

        assert not scheduling.range_overlaps(
            (
                current_time(),
                current_time() + datetime.timedelta(hours=5),
            ),
            (
                current_time() - datetime.timedelta(hours=5),
                current_time() - datetime.timedelta(hours=1),
            ),
        )

    def test_exact_match_overlapping_dates(self):
        scheduling = self.env["website.rentals.scheduling"]

        assert scheduling.range_overlaps(
            (
                current_time(),
                current_time() + datetime.timedelta(hours=5),
            ),
            (
                current_time(),
                current_time() + datetime.timedelta(hours=5),
            ),
        )

    def test_get_available_qty(self):
        scheduling = self.env["website.rentals.scheduling"]

        assert scheduling.get_available_qty(
            self.meeting_room,
            current_time(),
            current_time()
        ) == 1.0

        assert scheduling.get_available_qty(
            self.oil_change,
            current_time(),
            current_time()
        ) == 0.0

    def test_rental_orer_without_conflicts(self):
        order = self.env.ref("sale_renting.rental_order_1").copy()
        order.update(
            {
                "order_line": [
                    (6, 0, []),
                    (
                        0,
                        0,
                        {
                            "product_id": self.meeting_room.id,
                            "is_rental": True,
                            "product_uom_qty": 1.0,
                            "pickup_date": current_time(),
                            "return_date": current_time(),
                        },
                    ),
                ]
            }
        )
        order.action_confirm()

        assert order.state == "sale"
        assert len(order.order_line.ids) == 1
        assert order.order_line[0].product_id == self.meeting_room

    def test_rental_order_with_over_qty(self):
        order = self.env.ref("sale_renting.rental_order_1").copy()
        order.update(
            {
                "order_line": [
                    (6, 0, []),
                    (
                        0,
                        0,
                        {
                            "product_id": self.meeting_room.id,
                            "is_rental": True,
                            "product_uom_qty": 5.0,
                            "pickup_date": current_time() + datetime.timedelta(days=2),
                            "return_date": current_time() + datetime.timedelta(days=4),
                        },
                    ),
                ]
            }
        )
        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_rental_order_with_conflicts(self):
        # First order, room is reserved for 10-20 days ahead.
        order = self.env.ref("sale_renting.rental_order_1").copy()
        order.update(
            {
                "order_line": [
                    (6, 0, []),
                    (
                        0,
                        0,
                        {
                            "product_id": self.meeting_room.id,
                            "is_rental": True,
                            "product_uom_qty": 1.0,
                            "pickup_date": current_time() + datetime.timedelta(days=10),
                            "return_date": current_time() + datetime.timedelta(days=20),
                        },
                    ),
                ]
            }
        )
        order.action_confirm()

        # Second order should not be allowed, since it has conflicting dates.
        order = self.env.ref("sale_renting.rental_order_1").copy()
        order.update(
            {
                "order_line": [
                    (6, 0, []),
                    (
                        0,
                        0,
                        {
                            "product_id": self.meeting_room.id,
                            "is_rental": True,
                            "pickup_date": current_time() + datetime.timedelta(days=5),
                            "return_date": current_time() + datetime.timedelta(days=15),
                        },
                    ),
                ]
            }
        )
        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_order_cannot_be_entered_during_security_time(self):
        scheduling = self.env["website.rentals.scheduling"]

        # (now, 10 days fromnow), should fail, cannot rent before the bicycle 48 hours security time
        assert scheduling.can_rent(self.bicycle, current_time(), current_time() + datetime.timedelta(days=10), qty=1) == False

        # (47 hours from now, 10 days from now), should fail, cannot rent before the bicycle 48 hours security time
        assert scheduling.can_rent(self.bicycle, current_time() + datetime.timedelta(hours=47), current_time() + datetime.timedelta(days=10), qty=1) == False

        # (5 days from now, 10 days from now), after 48 hours security time so should be fine
        assert scheduling.can_rent(self.bicycle, current_time() + datetime.timedelta(days=5), current_time() + datetime.timedelta(days=10), qty=1) == True
