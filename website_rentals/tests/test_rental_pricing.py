from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class RentalPricingTests(TransactionCase):
    def test_start_end_time_range_constraint(self):
        rule = self.env.ref("sale_renting.rental_pricing_1")

        rule.end_time = rule.start_time + 2

        with self.assertRaises(ValidationError):
            rule.end_time = rule.start_time - 2
