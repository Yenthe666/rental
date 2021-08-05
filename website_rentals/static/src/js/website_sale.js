odoo.define("website_rentals.WebsiteSale", function (require) {

    const { mount } = owl;
    const RentalWizard = require("website_rentals.RentalWizard");
    const WebsiteSale = require("web.public.widget").registry.WebsiteSale;

    return WebsiteSale.include({
        events: _.extend(WebsiteSale.prototype.events, {
            "click #check_availability": "_openCheckAvailability",
        }),

        _openCheckAvailability() {
            mount(
                RentalWizard,
                {
                    target: document.querySelector("#check_availability_wizard"),
                    props: {productId: this._getProductId(this.$el)}
                }
            )
        },
    });
});
