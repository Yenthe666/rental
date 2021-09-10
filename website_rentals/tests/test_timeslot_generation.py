import datetime
from freezegun import freeze_time
from unittest import mock
from odoo.tests import TransactionCase


class TimeslotGenerationTests(TransactionCase):
    def setUp(self):
        super().setUp()

        self.scheduling = self.env["website.rentals.scheduling"]

        # product sample data
        self.blank_product = self.env["product.product"].create(
            {
                "name": "No Rental Pricing",
                "categ_id": self.env.ref("sale_renting.cat_renting").id,
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "rent_ok": True,
                "preparation_time": 0.0,  # hours
            }
        )
        self.days_only_product = self.env["product.product"].create(
            {
                "name": "Days Only Rental Pricing",
                "categ_id": self.env.ref("sale_renting.cat_renting").id,
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "rent_ok": True,
                "preparation_time": 0.0,  # hours
                "rental_pricing_ids": [
                    (
                        0,
                        0,
                        {
                            "duration": 1,
                            "unit": "day",
                            "price": 20.0,
                            "start_time": 8.0,
                            "end_time": 18.0,
                        },
                    ),
                ],
            }
        )
        self.meeting_room = self.env["product.product"].create(
            {
                "name": "New Meeting Room",
                "categ_id": self.env.ref("sale_renting.cat_renting").id,
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "rent_ok": True,
                "preparation_time": 0.0,  # hours
                "extra_hourly": 15.0,
                "extra_daily": 40.0,
                "rental_pricing_ids": [
                    (
                        0,
                        0,
                        {
                            "duration": 4,
                            "unit": "hour",
                            "price": 20.0,
                            "start_time": 8.0,
                            "end_time": 18.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "duration": 8,
                            "unit": "hour",
                            "price": 40.0,
                            "start_time": 8.0,
                            "end_time": 18.0,
                        },
                    ),
                ],
            }
        )

    def test_no_rental_pricing_should_return_none(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        assert not self.blank_product.get_rental_hourly_timeslots(tomorrow)

    def test_no_hourly_rental_pricing_should_return_none(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        assert not self.days_only_product.get_rental_hourly_timeslots(tomorrow)

    def test_same_day_start_slot_generation(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        timeslots = self.meeting_room.get_rental_hourly_timeslots(tomorrow)

        assert timeslots["start"] == ["08:00", "12:00", "16:00"]

    def test_same_day_stop_slot_generation(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        timeslots = self.meeting_room.get_rental_hourly_timeslots(tomorrow)

        assert timeslots["stop"] == [
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
        ]

    def test_different_day_start_slot_generation(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        day_after_tomorrow = tomorrow + datetime.timedelta(days=1)
        timeslots = self.meeting_room.get_rental_hourly_timeslots(
            tomorrow, day_after_tomorrow
        )

        assert timeslots["start"] == [
            "08:00",
            "09:00",
            "10:00",
            "11:00",
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
        ]

    def test_different_day_stop_slot_generation(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        day_after_tomorrow = tomorrow + datetime.timedelta(days=1)
        timeslots = self.meeting_room.get_rental_hourly_timeslots(
            tomorrow, day_after_tomorrow
        )

        assert timeslots["stop"] == [
            "08:00",
            "09:00",
            "10:00",
            "11:00",
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
        ]

    @freeze_time("2021-09-10 06:30:00")
    def test_same_day_preparation_time_offset(self):
        self.meeting_room.preparation_time = 3
        timeslots = self.meeting_room.get_rental_hourly_timeslots(
            datetime.datetime.now()
        )
        assert timeslots["start"] == ["12:00", "16:00"]
        assert timeslots["stop"] == ["16:00", "17:00", "18:00"]

    @freeze_time("2021-09-10 06:30:00")
    def test_different_day_preparation_time_offset(self):
        self.meeting_room.preparation_time = 3

        today = datetime.datetime.now()
        tomorrow = today + datetime.timedelta(days=1)
        timeslots = self.meeting_room.get_rental_hourly_timeslots(today, tomorrow)

        assert timeslots["start"] == [
            "10:00",
            "11:00",
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
        ]
        assert timeslots["stop"] == [
            "08:00",
            "09:00",
            "10:00",
            "11:00",
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
        ]

        day_after_tomorrow = tomorrow + datetime.timedelta(days=1)
        timeslots = self.meeting_room.get_rental_hourly_timeslots(
            tomorrow, day_after_tomorrow
        )

        assert timeslots["start"] == [
            "08:00",
            "09:00",
            "10:00",
            "11:00",
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
        ]
        assert timeslots["stop"] == [
            "08:00",
            "09:00",
            "10:00",
            "11:00",
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
        ]

    @freeze_time("2021-09-10 11:30:00")
    def test_timeslots_should_only_generate_after_current_time(self):
        timeslots = self.meeting_room.get_rental_hourly_timeslots(
            datetime.datetime.now()
        )
        assert timeslots["start"] == ["12:00", "16:00"]
        assert timeslots["stop"] == ["16:00", "17:00", "18:00"]
