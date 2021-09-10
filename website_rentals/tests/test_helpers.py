import datetime
from odoo.tests import TransactionCase
from odoo.addons.website_rentals import helpers


class HelpersTests(TransactionCase):
    def test_parse_date_string(self):
        parsed = helpers.time.parse_datetime("2021-09-10")

        assert type(parsed) == datetime.datetime
        assert parsed.year == 2021
        assert parsed.month == 9
        assert parsed.day == 10
        assert parsed.hour == 0
        assert parsed.minute == 0
        assert parsed.second == 0
        assert parsed.tzinfo == None

    def test_parse_datetime_string(self):
        parsed = helpers.time.parse_datetime("2021-09-10 15:10:05")

        assert type(parsed) == datetime.datetime
        assert parsed.year == 2021
        assert parsed.month == 9
        assert parsed.day == 10
        assert parsed.hour == 15
        assert parsed.minute == 10
        assert parsed.second == 5
        assert parsed.tzinfo == None

    def test_parse_date_object(self):
        today = datetime.date.today()
        parsed = helpers.time.parse_datetime(today)

        assert type(parsed) == datetime.datetime
        assert parsed.year == 2021
        assert parsed.month == 9
        assert parsed.day == 10
        assert parsed.hour == 0
        assert parsed.minute == 0
        assert parsed.second == 0
        assert parsed.tzinfo == None

    def test_parse_datetime_object(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        parsed = helpers.time.parse_datetime(now)

        assert parsed.year == now.year
        assert parsed.month == now.month
        assert parsed.day == now.day
        assert parsed.hour == now.hour
        assert parsed.minute == now.minute
        assert parsed.second == now.second
        assert parsed.tzinfo == None

    def test_nonesense_parameters_should_raise_exception(self):
        with self.assertRaises(Exception):
            helpers.time.parse_datetime(False)

    def test_basic_float_range(self):
        assert helpers.misc.float_range(6.5, 9.51) == [6.5, 7.5, 8.5, 9.5]
        assert helpers.misc.float_range(5.25, 7.10, step=0.25) == [5.25, 5.50, 5.75, 6.0, 6.25, 6.50, 6.75, 7.0]
        assert helpers.misc.float_range(5.6, 6.0, step=0.2) == [5.6, 5.8, 6.0]
