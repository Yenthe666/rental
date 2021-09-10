odoo.define("website_rentals.DateRangePicker", function (require) {
    const { Component } = owl;
    const { useState } = owl.hooks;
    const { css } = owl.tags;
    const useExternalXml = require("website_rentals.useExternalXml");

    const STYLE = css `
        #timeslots #timeslot_start,
        #timeslots #timeslot_end {
            flex-grow: 1;
            margin-top: 8px;
            min-width: 49%;
        }

        #timeslots {
            margin-top: 30px;
        }

        .card-container {
            width: 100%;
            justify-content: space-between;
            margin: 0;
            padding-right: 36px;
            gap: 3%;
            margin-top: 16px;
        }

        .card {
            width: 30%;
            padding: 14px 0;
            margin-bottom: 8px;
            text-align: center;
            color: #555;
        }

        .card.selected {
            background: #3aadaa;
            color: white;
        }

        .card.disabled {
            background: #eee;
            color: #989898;
            pointer-events: none;
        }

        .card:not(.selected):hover {
            cursor: pointer;
            background: #f7f7f7;
        }

        .card p {
            font-size: 13px;
            margin: 0;
        }

        .card p small {
            font-size: 12px;
        }
    `;

    class DateRangePicker extends Component {
        static template = "website_rentals.DateRangePicker";
        static style = STYLE;

        state = useState({
            timeslotsStart: [],
            timeslotsEnd: [],
            sameDay: false,
            selectedTimeslots: {
                start: undefined,
                end: undefined,
            }
        })

        setup() {
            useExternalXml(["/website_rentals/static/src/components/DateRangePicker.xml"]);
        }

        selectStartTimeslot(timeslot) {
            this.state.selectedTimeslots.start = timeslot.id;
            if(this.props.hasOwnProperty("onSelect")) this.props.onSelect();
        }

        selectEndTimeslot(timeslot) {
            this.state.selectedTimeslots.end = timeslot.id;
            if(this.props.hasOwnProperty("onSelect")) this.props.onSelect();
        }

        reset() {
            this.state.selectedTimeslots.start = undefined;
            this.state.selectedTimeslots.end = undefined;
            if(this.props.hasOwnProperty("onSelect")) this.props.onSelect();
        }

        findSelectedStart() {
            let res = undefined;
            this.filterStartTimeslots(this.state.timeslotsStart).forEach(timeslot => {
                if(!timeslot.disabled && timeslot.id === this.state.selectedTimeslots.start) {
                    res = timeslot;
                }
            });
            return res;
        }

        findSelectedEnd() {
            let res = undefined;
            this.filterEndTimeslots(this.state.timeslotsEnd).forEach(timeslot => {
                if(!timeslot.disabled && timeslot.id === this.state.selectedTimeslots.end) {
                    res = timeslot;
                }
            });
            return res;
        }

        filterStartTimeslots(timeslots) {
            if(!timeslots) {
                return timeslots;
            }

            if(this.state.sameDay) {
                return timeslots.slice(0, timeslots.length - 1);
            }

            return timeslots;
        }

        /**
         * Handles filtering the timeslots that cannot be selected.
         *
         * When a user selects a start time, then they should not be allowed
         * to select an end time that comes before the selected start. This will
         * disable those times.
         */
        filterEndTimeslots(timeslots) {
            const startTimeslot = this.findSelectedStart();

            // Nothing to worry about filtering if the user hasn't selected a start time yet
            if(!startTimeslot) {
                return timeslots;
            }

            // Nothing to worry about filtering if there are no timeslots populated
            if(!timeslots) {
                return timeslots;
            }

            let res = timeslots.map(timeslot => Object.assign({}, timeslot));
            res.forEach(timeslot => {
                if(this.state.sameDay && (timeslot.hour + (timeslot.minutes / 60)) <= (startTimeslot.hour + (startTimeslot.minutes / 60))) {
                    timeslot.disabled = true;
                } else {
                    timeslot.disabled = false;
                }
            });
            return res;
        }
    }

    return DateRangePicker;
});
