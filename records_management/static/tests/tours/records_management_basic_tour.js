/** @odoo-module **/
/**
 * Basic navigation tour for Records Management module.
 * Hardened version:
 *  - Works in pure ESM test bundling (Odoo ≥16/17/18)
 *  - Falls back to legacy `web_tour.tour` if available
 */

import { registry } from '@web/core/registry';

let legacyTour;
try {
    // eslint-disable-next-line no-undef
    if (typeof require === 'function') {
        // eslint-disable-next-line no-undef
        legacyTour = require('web_tour.tour');
    }
} catch (err) {
    console.debug('[records_management_basic_tour] Legacy tour API not available:', err.message);
}

const steps = [
    {
        content: 'Wait for web client to load apps menu',
        trigger: ".o_app[data-menu-xmlid='records_management.menu_records_management_root']",
    },
    {
        content: 'Open Records Management root app',
        trigger: ".o_app[data-menu-xmlid='records_management.menu_records_management_root']",
    },
    {
        content: 'Wait for Containers menu to be visible',
        trigger: "a[data-menu-xmlid='records_management.menu_records_containers']",
    },
    {
        content: 'Open Containers menu',
        trigger: "a[data-menu-xmlid='records_management.menu_records_containers']",
    },
    {
        content: 'Confirm container list view rendered',
        trigger: '.o_list_view table.o_list_table, .o_kanban_view',
    },
];

// Modern registration path (web_tour.tours registry)
try {
    registry.category('web_tour.tours').add('records_management_basic_tour', {
        url: '/web',
        test: true,
        steps: () => steps,
    });
} catch (err) {
    console.error('[records_management_basic_tour] Modern registration failed:', err.message);
}

// Legacy fallback (still used by some harness modes)
if (legacyTour?.register) {
    try {
        legacyTour.register('records_management_basic_tour', {
            test: true,
            url: '/web',
            sequence: 10,
        }, steps);
    } catch (err) {
        console.warn('[records_management_basic_tour] Legacy registration failed:', err.message);
    }
}

export const RecordsManagementBasicTour = true; // marker export
