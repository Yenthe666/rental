from odoo import models
from odoo.tools import float_repr


class Currency(models.Model):
    _inherit = "res.currency"

    def pretty(self, amount):
        """
        Generates a formatted string for a given amount with the symbol.
        """
        pre = post = u''

        if self.position == 'before':
            pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol=self.symbol or '')
        else:
            post = u'\N{NO-BREAK SPACE}{symbol}'.format(symbol=self.symbol or '')

        return u' {pre}{0}{post}'.format(
            float_repr(amount, self.decimal_places),
            pre=pre,
            post=post
        )
