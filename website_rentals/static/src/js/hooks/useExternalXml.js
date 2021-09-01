odoo.define("website_rentals.useExternalXml", function(require) {
    const { useEnv, onWillStart } = owl.hooks;
    const fetchCache = {};

    /**
     * At this point, there is no support in Odoo for loading Owl XML templates
     * into the Odoo QWeb engine. This mean that Owl will not be able to
     * recongize templates by their t-name.
     *
     * This hook can be used to manually load templates in as a workaround.
     *
     * This was a recommended from the Odoo core team:
     * https://github.com/odoo/odoo/issues/75426#issuecomment-903897145
     *
     * Usage:
     *
     *     const { Component } = owl;
     *     const useExternalXml = require("website_rentals.useExternalXml");
     *
     *     class MyComponent extends Component {
     *         static template = "my_module.MyComponent";
     *
     *         setup() {
     *             useExternalXml(["/my_module/static/src/components/MyComponent.xml"]);
     *         }
     *     }
     */
    return function useExternalXml(urls) {
        const env = useEnv();

        onWillStart(async() => {
            const requests = await Promise.all(urls.map(url => fetchCache[url] || (fetchCache[url] = fetch(url))));
            const unreadRequests = requests.filter(req => !req.bodyUsed);
            const contents = await Promise.all(unreadRequests.map(req => req.text()));

            contents.forEach(xml => env.qweb.addTemplates(xml));
        });
    };
});
