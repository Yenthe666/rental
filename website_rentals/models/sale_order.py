from odoo import _, models, fields
from odoo.exceptions import ValidationError
import pytz


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        scheduling = self.env["website.rentals.scheduling"]
        rental_orders = self.filtered(lambda order: order.is_rental_order)
        rental_order_lines = rental_orders.mapped("order_line").filtered(lambda line: line.product_id.rent_ok)

        for order_line in rental_order_lines:
            quantity_ordered = sum(rental_order_lines.filtered(lambda line: line.product_id == order_line.product_id).mapped("product_uom_qty"))
            if not scheduling.can_rent(
                order_line.product_id,
                order_line.pickup_date,
                order_line.return_date,
                qty=quantity_ordered,
            ):
                raise ValidationError(
                    _(
                        f"{order_line.product_id.display_name} (qty {quantity_ordered}) is not available from {order_line.pickup_date} to {order_line.return_date}."
                    )
                )

        return super().action_confirm()

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        res = super()._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty, **kwargs)

        if not line_id and product_id and self.env["product.product"].browse(product_id).rent_ok:
            if"pickup_date" not in kwargs and "return_date" not in kwargs:
                raise ValidationError(_("Rental products must include a pickup and return date."))

            self.env["sale.order.line"].browse(res["line_id"]).update({
                "is_rental": True,
                "pickup_date": kwargs["pickup_date"],
                "return_date": kwargs["return_date"],
            })

        return res
