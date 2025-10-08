/** @odoo-module **/
/**
 * Basic navigation tour for Records Management module.
 * Simplified version for Odoo 19 compatibility
 */

import { registry } from '@web/core/registry';

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

// Register tour using Odoo 19 standard pattern
try {
    registry.category('web_tour.tours').add('records_management_basic_tour', {
        url: '/web',
        test: true,
        steps: () => steps,
    });
    console.log('[records_management_basic_tour] Tour registered successfully');
} catch (err) {
    console.error('[records_management_basic_tour] Tour registration failed:', err.message);
}
