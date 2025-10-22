/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useRef, onMounted } from "@odoo/owl";

// Google Maps API key - hardcoded for now, can be moved to system parameter if needed
const GOOGLE_MAPS_API_KEY = "AIzaSyD3jkyp3IiN2uxW1wqmxsNbKU1NdQtnq1c";
let googleMapsLoaded = false;
let googleMapsLoading = false;
const loadCallbacks = [];

function loadGoogleMaps() {
    return new Promise((resolve, reject) => {
        if (googleMapsLoaded) {
            resolve();
            return;
        }

        if (googleMapsLoading) {
            loadCallbacks.push(resolve);
            return;
        }

        googleMapsLoading = true;
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places,geometry`;
        script.async = true;
        script.defer = true;
        script.onload = () => {
            googleMapsLoaded = true;
            googleMapsLoading = false;
            resolve();
            loadCallbacks.forEach(cb => cb());
            loadCallbacks.length = 0;
        };
        script.onerror = () => {
            googleMapsLoading = false;
            reject(new Error('Failed to load Google Maps API'));
        };
        document.head.appendChild(script);
    });
}

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

    async renderMap() {
        const latitude = this.props.record.data[this.props.latitudeField];
        const longitude = this.props.record.data[this.props.longitudeField];
        const hasLatitude = !!latitude;
        const hasLongitude = !!longitude;

        if (!hasLatitude || !hasLongitude) {
            this.mapContainer.el.innerHTML = '<span>No location set: latitude or longitude missing.</span>';
            return;
        }

        try {
            await loadGoogleMaps();
            new google.maps.Map(this.mapContainer.el, {
                center: { lat: latitude, lng: longitude },
                zoom: 15,
                mapTypeId: 'roadmap'
            });
            // Add marker
            new google.maps.Marker({
                position: { lat: latitude, lng: longitude },
                map: new google.maps.Map(this.mapContainer.el, {
                    center: { lat: latitude, lng: longitude },
                    zoom: 15
                })
            });
        } catch (error) {
            console.error('Error loading Google Maps:', error);
            this.mapContainer.el.innerHTML = '<span>Failed to load Google Maps. Please check your internet connection.</span>';
        }
    }
}

// Register as a field widget definition (expects an object with a `component` key in Odoo 19)
registry.category("fields").add("map_widget", {
    component: MapWidget,
    displayName: "Map",
    supportedTypes: ["char", "text", "float", "integer"],
});
