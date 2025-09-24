/**
 * Basic navigation tour for Records Management module.
 * Purpose: Validate that the module app icon loads and a core menu opens without JS errors.
 */
odoo.define('records_management.tour.basic', function (require) {
    'use strict';

    const tour = require('web_tour.tour');

    // Root menu XML IDs used:
    // - records_management.menu_records_management_root (app icon / root)
    // - records_management.menu_records_containers (child menu to open)

    tour.register('records_management_basic_tour', {
        test: true,
        url: '/web',
        sequence: 10,
    }, [
        // Wait for the web client home/apps screen
        {
            content: 'Wait for web client to load apps menu',
            trigger: ".o_app[data-menu-xmlid='records_management.menu_records_management_root']",
            run: function () { /* noop */ },
        },
        {
            content: 'Open Records Management root app',
            trigger: ".o_app[data-menu-xmlid='records_management.menu_records_management_root']",
        },
        {
            content: 'Wait for Containers menu to be visible',
            trigger: "a[data-menu-xmlid='records_management.menu_records_containers']",
            run: function () { /* noop */ },
        },
        {
            content: 'Open Containers menu',
            trigger: "a[data-menu-xmlid='records_management.menu_records_containers']",
        },
        {
            content: 'Confirm container list view rendered',
            trigger: '.o_list_view table.o_list_table, .o_kanban_view',
            run: function () { /* end */ },
        },
    ]);
});
