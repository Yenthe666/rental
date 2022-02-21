odoo.define("website_rentals.RentalWizard", function (require) {
    const { Component } = owl;
    const { useState, useRef } = owl.hooks;
    const { css } = owl.tags;
    const DateRangePicker = require("website_rentals.DateRangePicker");
    const useCurrentTime = require("website_rentals.hooks.useCurrentTime");
    const useExternalXml = require("website_rentals.useExternalXml");
    const wUtils = require("website.utils");

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
        static template = "website_rentals.RentalWizard";
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

        setup() {
            useExternalXml(["/website_rentals/static/src/components/RentalWizard.xml"]);
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
            this.fetchTimeslotsEnd();
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
                        error: !res ? "Date range is not available right now. Please try another date." : false
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
                const pickupReturnPicker = this.refs.pickupReturnPicker.comp;
                if(!pickupReturnPicker) {
                    resolve();
                    return;
                }

                // Users need to set start and end dates before timeslots can be set
                if (!(this.state.startDateInput && this.state.endDateInput)) {
                    pickupReturnPicker.state.timeslotsStart = [];
                    pickupReturnPicker.state.timeslotsEnd = [];
                    resolve();
                    return;
                }

                pickupReturnPicker.state.selectedTimeslot = undefined;

                this.env.services.rpc({
                    route: "/website/rentals/get_rental_hourly_timeslots",
                    params: {
                        product_id: this.state.product.id,
                        start_date: this.state.startDateInput,
                        stop_date: this.state.endDateInput,
                        quantity: this.state.quantity,
                    }
                }).then(res => {
                    if(!res) {
                        resolve();
                        return;
                    }

                    pickupReturnPicker.state.timeslotsStart = res.start.map(timeStr => {
                        return {
                            id: `${this.state.startDateInput}${timeStr}`,
                            title: timeStr,
                            hour: Number(timeStr.split(":")[0]),
                            minutes: Number(timeStr.split(":")[1]),
                        };
                    });

                    pickupReturnPicker.state.timeslotsEnd = res.stop.map(timeStr => {
                        return {
                            id: `${this.state.endDateInput}${timeStr}`,
                            title: timeStr,
                            hour: Number(timeStr.split(":")[0]),
                            minutes: Number(timeStr.split(":")[1]),
                        };
                    });

                    pickupReturnPicker.reset();
                    pickupReturnPicker.state.sameDay = this.onSameDay();

                    resolve();
                });
            });
        }

        fetchTimeslotsEnd() {
            return new Promise(resolve => {
                // Not possible to set timeslots without an initialized date range picker component
                const pickupReturnPicker = this.refs.pickupReturnPicker.comp;
                if(!pickupReturnPicker) {
                    resolve();
                    return;
                }

                if (pickupReturnPicker.state.selectedTimeslots.start) {
                    this.env.services.rpc({
                        route: "/website/rentals/get_rental_hourly_timeslots",
                        params: {
                            product_id: this.state.product.id,
                            start_date: pickupReturnPicker.state.selectedTimeslots.start,
                            stop_date: this.state.endDateInput,
                            quantity: this.state.quantity,
                            include_start: false,
                            include_stop: true,
                        }
                    }).then(res => {
                        if(!res) {
                            resolve();
                            return;
                        }

                        pickupReturnPicker.state.timeslotsEnd = res.stop.map(timeStr => {
                            return {
                                id: `${this.state.endDateInput}${timeStr}`,
                                title: timeStr,
                                hour: Number(timeStr.split(":")[0]),
                                minutes: Number(timeStr.split(":")[1]),
                            };
                        });

    //                    pickupReturnPicker.reset();
                        pickupReturnPicker.state.sameDay = this.onSameDay();

                        resolve();
                    });
                }
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
