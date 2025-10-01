/**
 * Organization Diagram Frontend Logic
 * Extracts JSON payload embedded in #diagram-data and initializes diagram rendering (placeholder logic).
 */
odoo.define('records_management.portal_organization_diagram', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.OrganizationDiagram = publicWidget.Widget.extend({
        selector: '.o_portal_organization_diagram',
        start: function () {
            this._loadData();
            this._bindEvents();
            return this._super.apply(this, arguments);
        },
        _loadData: function () {
            const dataEl = document.getElementById('diagram-data');
            if (!dataEl) {
                return;
            }
            try {
                this.diagramData = JSON.parse(dataEl.textContent.trim());
                // Placeholder: update simple counters
                if (this.diagramData && this.diagramData.stats) {
                    const stats = this.diagramData.stats;
                    this._setText('#companies-count', stats.companies || '-');
                    this._setText('#departments-count', stats.departments || '-');
                    this._setText('#users-count', stats.users || '-');
                    this._setText('#connections-count', stats.connections || '-');
                }
            } catch (e) {
                // eslint-disable-next-line no-console
                console.warn('Failed parsing organization diagram data', e);
            }
        },
        _setText: function (selector, value) {
            const el = document.querySelector(selector);
            if (el) {
                el.textContent = value;
            }
        },
        _bindEvents: function () {
            const refreshBtn = document.getElementById('refresh-diagram');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => this._loadData());
            }
            // Further event hooks (export, search) can be added here
        },
    });

    return publicWidget.registry.OrganizationDiagram;
});
