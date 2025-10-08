/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useRef, onMounted } from "@odoo/owl";

export class MapWidget extends Component {
    static template = "records_management.MapWidget";
    static props = {
        ...standardFieldProps,
        latitudeField: { type: String, optional: true },
        longitudeField: { type: String, optional: true },
    };

    setup() {
        this.mapContainer = useRef("mapContainer");
        onMounted(() => this.renderMap());
    }

    renderMap() {
        const latitude = this.props.record.data[this.props.latitudeField];
        const longitude = this.props.record.data[this.props.longitudeField];
        const hasLatitude = !!latitude;
        const hasLongitude = !!longitude;
        const hasGoogle = typeof google !== 'undefined';
        const hasGoogleMaps = hasGoogle && google.maps;

        if (hasLatitude && hasLongitude && hasGoogleMaps) {
            new google.maps.Map(this.mapContainer.el, {
                center: { lat: latitude, lng: longitude },
                zoom: 15
            });
        } else if (!hasLatitude || !hasLongitude) {
            this.mapContainer.el.innerHTML = '<span>No location set: latitude or longitude missing.</span>';
        } else if (!hasGoogleMaps) {
            this.mapContainer.el.innerHTML = '<span>Google Maps API not loaded.</span>';
        }
    }
}

// Register as a field widget definition (expects an object with a `component` key in Odoo 19)
registry.category("fields").add("map_widget", {
    component: MapWidget,
    displayName: "Map",
    supportedTypes: ["char", "text", "float", "integer"],
});
