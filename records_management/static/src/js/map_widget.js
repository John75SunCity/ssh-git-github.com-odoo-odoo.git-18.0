odoo.define('records_management.map_widget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var MapWidget = AbstractField.extend({
        className: 'map_widget',
        _render: function () {
            // Clear previous content and add map container
            this.$el.html('<div class="map_container" style="width:100%;height:300px;"></div>');
            var latitude = this.recordData[this.options.latitude_field];
            var longitude = this.recordData[this.options.longitude_field];
            if (latitude && longitude && typeof google !== 'undefined' && google.maps) {
                var map = new google.maps.Map(this.$('.map_container')[0], {
                    center: { lat: latitude, lng: longitude },
                    zoom: 15
                });
                new google.maps.Marker({
                    position: { lat: latitude, lng: longitude },
                    map: map
                });
            } else {
                this.$('.map_container').html('<span>No location set</span>');
            }
            return this._super();
        }
    });

    fieldRegistry.add('map_widget', MapWidget);

    return MapWidget;
});
