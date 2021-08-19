odoo.define("website_rentals.hooks.useCurrentTime", function(require) {
    const { useState, onWillStart, onWillUnmount } = owl.hooks;

    /**
     * Hook which tracks the current time, updating every 1s.
     *
     * Be aware that the date object is stored as a moment() object, not a
     * native Date object.
     *
     * Usage:
     *     class MyComponent extends Component {
     *         static TEMPLATE = xml`
     *             <div>
     *                 Current Time: <span t-esc="time.now"/>
     *             </div>
     *         `;
     *
     *         time = useCurrentTime()
     *     }
     */
    return function useCurrentTime() {
        const state = useState({ now: moment(), timer: undefined });
        const update = () => state.now = moment();

        onWillStart(() => state.timer = setInterval(update, 1000));
        onWillUnmount(() => clearInterval(state.timer));

        return state;
    };
});
