odoo.define('records_management.scanbot_scanner', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    var ScanbotScanner = AbstractAction.extend({
        template: 'scanbot_scanner_template',  // Assume a template with <div id="scanner"/>

        start: function () {
            this._super.apply(this, arguments);
            this.initializeScanbot();
        },

        initializeScanbot: function () {
            // Scanbot SDK initialization with license key
            var config = {
                containerId: 'scanner',
                licenseKey: odoo.session.scanbot_license_key,  // From module config or attachment
                onBarcodesDetected: this.onBarcodesDetected.bind(this),
                // Add resizable viewfinder
                viewFinder: {
                    enabled: true,
                    style: {  // Initial slim rectangle
                        width: '100%',
                        height: '20%',  // Slim height for label scanning
                        backgroundColor: 'rgba(0,255,0,0.3)',
                    },
                    resizable: true,  // Enable pinch/mouse resize
                }
            };
            ScanbotSDK.initialize(config).then(function () {
                // Start camera
                ScanbotSDK.startBarcodeScanner();
            });
        },

        onBarcodesDetected: function (result) {
            // Handle scanned barcodes, send to server
            this.do_action({
                type: 'ir.actions.act_window_close',
                infos: { barcodes: result.barcodes }
            });
        },
    });

    core.action_registry.add('scanbot_scanner', ScanbotScanner);

    return ScanbotScanner;
});
