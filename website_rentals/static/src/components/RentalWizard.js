odoo.define("website_rentals.RentalWizard", function (require) {
    const { Component } = owl;
    const { useState, useRef } = owl.hooks;
    const { xml, css } = owl.tags;
    const DateRangePicker = require("website_rentals.DateRangePicker");
    const useCurrentTime = require("website_rentals.hooks.useCurrentTime");
    const wUtils = require("website.utils");

    const TEMPLATE = xml `
        <div id="rental_wizard" class="modal">
            <div class="modal-dialog modal-dialog-scrollable d-flex s_popup_size_full">
                <div class="modal-content oe_structure">
                    <div class="modal-body">
                        <button
                            type="button"
                            class="close"
                            data-dismiss="modal"
                            t-on-click="cancel"
                            style="position:absolute; right:12px; top:10px; z-index:9999;">
                            <span
                                role="img"
                                aria-label="Close">×</span>
                            <span class="sr-only">Close</span>
                        </button>

                        <section class="o_colored_level o_cc o_cc1">
                            <form t-on-submit.prevent="submit" t-if="state.product">
                                <div class="container">
                                    <div class="row">
                                        <h2 t-if="state.product.display_name" t-esc="state.product.display_name" class="w-full" style="display:block; padding:0 0 6px 0; margin:0;"/>
                                        <p t-if="state.product.description_sale" t-esc="state.product.description_sale" class="w-full" style="display:block;"/>
                                    </div>
                                    <div class="row" style="margin-top:12px;">
                                        <p class="w-full"><strong>Dates</strong></p>
                                        <div class="flex" style="align-items:center;">
                                            <input
                                                t-model="state.startDateInput"
                                                t-on-change="onDateChange"
                                                class="form-control"
                                                name="pickup_date"
                                                type="date"
                                                autocomplete="off"
                                                required="1"
                                                t-att-min="time.now.add(state.product.preparation_time || 0, 'hours').format('YYYY-MM-DD')"
                                                t-att-disabled="state.loading"/>
                                            <span style="padding:0 8px;">to</span>
                                            <input
                                                t-model="state.endDateInput"
                                                t-on-change="onDateChange"
                                                class="form-control"
                                                name="return_date"
                                                type="date"
                                                autocomplete="off"
                                                required="1"
                                                t-att-min="state.startDateInput || time.now.format('YYYY-MM-DD')"
                                                t-att-disabled="!state.startDateInput || state.loading"/>
                                        </div>
                                    </div>

                                    <!-- NOTE: Cannot use t-if here because it causes issues when trying to reference
                                        subcomponents defined in this block. -->
                                    <div t-att-class="(state.startDateInput &amp;&amp; state.endDateInput &amp;&amp; !state.loading) ? '' : 'd-none'">
                                        <div t-if="!state.quantityAvailable" class="row">
                                            <p class="text-danger">No quantity available.</p>
                                        </div>
                                        <t t-if="state.quantityAvailable">
                                            <div id="product_qty" class="row flex">
                                                <p class="w-full" style="margin-top:20px;"><strong>Quantity</strong></p>
                                                <input
                                                    t-model="state.quantity"
                                                    t-on-change="onQtyChange"
                                                    type="number"
                                                    class="form-control quantity"
                                                    name="quantity"
                                                    min="1"
                                                    t-att-max="state.quantityAvailable"
                                                    autocomplete="off"
                                                    required="1"/>
                                                <p class="w-full" style="margin-top:20px;">
                                                    (<span t-esc="state.quantityAvailable"/> Units Available)
                                                </p>
                                            </div>
                                            <DateRangePicker t-ref="pickup-return-picker" onSelect="onTimeslotSelect.bind(state.this)">
                                                <t t-set-slot="start-label">
                                                    <h3><strong>Start</strong></h3>
                                                    <p t-esc="startDate().format('DD.MM.YYYY')"/>
                                                </t>
                                                <t t-set-slot="end-label">
                                                    <h3><strong>End</strong></h3>
                                                    <p t-esc="endDate().format('DD.MM.YYYY')"/>
                                                </t>
                                            </DateRangePicker>
                                        </t>
                                    </div>
                                </div>

                                <hr/>

                                <div class="row" t-if="state.price">
                                    <p class="w-full"><strong>Price</strong></p>
                                    <p class="w-full" t-esc="state.price"/>
                                </div>
                                <div class="row">
                                    <p t-if="state.submitError" t-esc="state.submitError" class="text-danger"/>
                                </div>
                                <div class="row">
                                    <button
                                        class="btn btn-primary"
                                        type="submit"
                                        t-att-disabled="state.submitting || !state.quantityAvailable">
                                        Add <i t-att-class="'fa fa-spinner fa-spin ' + (state.submitting ? '' : 'display-none')"/>
                                    </button>
                                    <button
                                        t-on-click="cancel"
                                        class="btn btn-link"
                                        type="button">Cancel</button>
                                </div>
                            </form>
                            <div t-else="">
                                <i class="fa fa-spinner fa-spin" style="font-size: 24px"/>
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        </div>`;

    const STYLE = css `
        #rental_wizard {
            position: absolute;
            display: initial;
        }


        #rental_wizard h2 {
            padding-bottom: 24px;
        }

        #rental_wizard h3 {
            font-size: 16px;
        }

        #rental_wizard .w-full {
            width: 100%;
        }

        #rental_wizard .flex {
            display: flex;
            flex-wrap: wrap;
        }

        #rental_wizard .display-none {
            display: none;
        }

        #rental_wizard .modal-body {
            max-width: 100%;
            overflow-x: hidden;
        }

        #rental_wizard .modal-content {
            padding: 40px;
        }
    `;

    class RentalWizard extends Component {
        static template = TEMPLATE;
        static style = STYLE;
        static components = { DateRangePicker };

        state = useState({
            this: undefined,
            product: undefined,
            quantity: 1,
            quantityAvailable: undefined,
            price: undefined,
            startDateInput: "",
            endDateInput: "",
            submitError: "",
            submitting: false,
            loading: false,  // used to prevent a "flashing" effect while waiting on ajax calls
        });

        refs = {
            pickupReturnPicker: useRef("pickup-return-picker")
        };

        time = useCurrentTime();

        constructor(parent, props) {
            super(parent, props)
            this.state.this = this;
            this.fetchProduct(props.productId);
        }

        /**
         * Attempts to submit the data, adding the item to the cart if possible.
         */
        submit(event) {
            if(!this.state.quantityAvailable) {
                return;
            }

            this.state.submitError = ""
            this.state.submitting = true;

            this.canOrder().then(validator => {
                this.state.submitting = false;

                if (!validator.canOrder) {
                    this.state.submitError = validator.error;
                } else {
                    return wUtils.sendRequest("/shop/cart/update", {
                        product_id: this.state.product.id,
                        set_qty: this.state.quantity,
                        pickup_date: this.startDateFormatted(),
                        return_date: this.endDateFormatted(),
                    });
                }
            });
        }

        /**
         * Cancels the wizard and closes the modal.
         */
        cancel() {
            this.destroy();
        }

        onDateChange() {
            this.state.loading = true;

            if(moment(this.state.endDateInput) < moment(this.state.startDateInput)) {
                this.state.endDateInput = this.state.startDateInput;
            }

            this.fetchQuantityAvailable().then(() => {
                // Even if quantities are available on the given day, gotta
                // check that there are pickup timeslots available. This is
                // passed to fetchTimeslots() as a callback.
                let checkTimeslots = () => {
                    if(!this.refs.pickupReturnPicker.comp || !this.refs.pickupReturnPicker.comp.state.timeslotsStart.length) {
                        this.state.quantityAvailable = 0;
                    }
                    this.state.loading = false;
                };

                // This is a hack because I cannot find a way in OWL to
                // do the equivalant of useEffect in React (wait until
                // the next "cycle" has passed and the view has been
                // updated).
                //
                // This has to be done because we need to wait until the
                // pickupReturnPicker has been rendered before moving on
                // from here.
                if(this.state.quantityAvailable && !this.refs.pickupReturnPicker.comp) {
                    const waiter = setInterval(() => {
                        if(this.refs.pickupReturnPicker.comp) {
                            this.fetchTimeslots().then(checkTimeslots);
                            this.fetchPrice();
                            clearInterval(waiter);
                        }
                    }, 5)
                } else {
                    this.fetchTimeslots().then(checkTimeslots);
                    this.fetchPrice();
                }
            });
        }

        onQtyChange() {
            this.fetchPrice();
        }

        onTimeslotSelect() {
            this.fetchPrice();
        }

        /**
         * Checks if startDate and endDate are the same day.
         */
        onSameDay() {
            if (!this.state.startDateInput || !this.state.endDateInput) {
                return false;
            }

            return this.startDate().format("YYYY-MM-DD") === this.endDate().format("YYYY-MM-DD")
        }

        /**
         * Checks if it's possible to order this product.
         */
        canOrder() {
            return new Promise(resolve => {
                if(!this.refs.pickupReturnPicker.comp.findSelectedStart() || !this.refs.pickupReturnPicker.comp.findSelectedEnd()) {
                    resolve({canOrder: false, error: "Please select a pickup and return time."});
                    return;
                }

                this.env.services.rpc({
                    route: "/website/rentals/can_rent",
                    params: {
                        product_id: this.state.product.id,
                        start_date: this.startDate(),
                        stop_date: this.endDate(),
                    }
                }).then(res => {
                    resolve({
                        canOrder: res,
                        error: res ? "Date range is not available right now. Please try another date.": false
                    });
                });
            });
        }

        fetchProduct(productId) {
            return new Promise(resolve => {
                this.env.services.rpc({
                    route: "/website/rentals/get_product",
                    params: {
                        product_id: productId,
                    }
                }).then(res => {
                    if (res) this.state.product = res[0];
                    resolve();
                });
            });
        }

        fetchPrice() {
            return new Promise(resolve => {
                if(!this.state.product.id || !this.startDate(true).isValid() || !this.endDate(true).isValid() || !this.state.quantity) {
                    this.state.price = undefined;
                    resolve();
                    return;
                }

                this.env.services.rpc({
                    route: "/website/rentals/get_price",
                    params: {
                        product_id: this.state.product.id,
                        start_date: this.startDateFormatted(),
                        stop_date: this.endDateFormatted(),
                        qty: this.state.quantity,
                    }
                }).then(res => {
                    this.state.price = res;
                    resolve();
                });
            });
        }

        fetchQuantityAvailable() {
            return new Promise(resolve => {
                if (!(this.state.startDateInput && this.state.endDateInput)) {
                    this.state.quantityAvailable = undefined;
                    resolve();
                    return;
                }

                this.env.services.rpc({
                    route: "/website/rentals/get_available_rental_qty",
                    params: {
                        product_id: this.state.product.id,
                        start_date: this.startDate(),
                        stop_date: this.endDate(),
                    }
                }).then(res => {
                    this.state.quantityAvailable = res;
                    resolve();
                });
            });
        }

        fetchTimeslots() {
            return new Promise(resolve => {
                // Not possible to set timeslots without an initialized date range picker component
                if(!this.refs.pickupReturnPicker.comp) {
                    resolve();
                    return;
                }

                let pickupReturnPickerState = this.refs.pickupReturnPicker.comp.state;

                // Users need to set start and end dates before timeslots can be set
                if (!(this.state.startDateInput && this.state.endDateInput)) {
                    pickupReturnPickerState.timeslotsStart = [];
                    pickupReturnPickerState.timeslotsEnd = [];
                    resolve();
                    return;
                }

                pickupReturnPickerState.selectedTimeslot = undefined;
                this._fetchStartTimeslots().then(() => {
                    this._fetchEndTimeslots().then(() => {
                        if(this.refs.pickupReturnPicker.comp) {
                            this.refs.pickupReturnPicker.comp.reset();
                        }
                        pickupReturnPickerState.sameDay = this.onSameDay();
                        resolve();
                    });
                });
            });
        }

        _fetchStartTimeslots() {
            return new Promise(resolve => {
                this.env.services.rpc({
                    route: "/website/rentals/get_rental_hourly_timeslots",
                    params: {
                        product_id: this.state.product.id,
                        date: this.state.startDateInput,
                    }
                }).then(res => {
                    if(this.refs.pickupReturnPicker.comp) {
                        this.refs.pickupReturnPicker.comp.state.timeslotsStart = res.map(timeStr => {
                            return {
                                id: `${this.state.startDateInput}${timeStr}`,
                                title: timeStr,
                                hour: Number(timeStr.split(":")[0]),
                                minutes: Number(timeStr.split(":")[1]),
                            };
                         });
                    }
                    resolve();
                });
            });
        }

        _fetchEndTimeslots() {
            return new Promise(resolve => {
                this.env.services.rpc({
                    route: "/website/rentals/get_rental_hourly_timeslots",
                    params: {
                        product_id: this.state.product.id,
                        date: this.state.endDateInput,
                    }
                }).then(res => {
                    if(this.refs.pickupReturnPicker.comp) {
                        this.refs.pickupReturnPicker.comp.state.timeslotsEnd = res.map(timeStr => {
                            return {
                                id: `${this.state.endDateInput}${timeStr}`,
                                title: timeStr,
                                hour: Number(timeStr.split(":")[0]),
                                minutes: Number(timeStr.split(":")[1]),
                            };
                        });
                    }
                    resolve();
                });
            });
        }

        /**
         * Converts the startDateInput which inputs as a string, to a Date object.
         */
        startDate(useTime = false) {
            let timeStr = this.state.startDateInput;
            if(useTime) {
                if(!this.refs.pickupReturnPicker.comp || !this.refs.pickupReturnPicker.comp.findSelectedStart()) {
                    return moment("Invalid date.");
                }
                timeStr += " " + this.refs.pickupReturnPicker.comp.findSelectedStart().title;
            }
            return moment(timeStr);
        }

        startDateFormatted() {
            return this.startDate(true).format("YYYY-MM-DD HH:mm:ss");
        }

        /**
         * Converts the endDateInput which inputs as a string, to a Date object.
         */
        endDate(useTime = false) {
            let timeStr = this.state.endDateInput;
            if(useTime) {
                if(!this.refs.pickupReturnPicker.comp || !this.refs.pickupReturnPicker.comp.findSelectedEnd()) {
                    return moment("Invalid date.");
                }
                timeStr += " " + this.refs.pickupReturnPicker.comp.findSelectedEnd().title;
            }
            return moment(timeStr);
        }

        endDateFormatted() {
            return this.endDate(true).format("YYYY-MM-DD HH:mm:ss");
        }
    }

    return RentalWizard;
});
