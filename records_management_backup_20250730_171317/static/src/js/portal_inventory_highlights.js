// New file: JS for modern inventory UI - highlights, multi-select actions, clean animations.

odoo.define('records_management.portal_inventory_highlights', function (require) {
    "use strict";

    var core = require('web.core');
    var rpc = require('web.rpc');

    $(document).ready(function () {
        // Multi-select
        window.selectAll = function() {
            var headerCheckbox = $('th input[type="checkbox"]')[0];
            $('.multi-select-table tbody input[type="checkbox"]').prop('checked', headerCheckbox.checked);
            updateBatchButtons();
        };

        // Update batch button states based on selection
        function updateBatchButtons() {
            var selectedCount = $('.multi-select-table tbody input:checked').length;
            $('.batch-action-btn').prop('disabled', selectedCount === 0);
            if (selectedCount > 0) {
                $('.batch-counter').text(selectedCount + ' items selected');
            } else {
                $('.batch-counter').text('');
            }
        }

        // Batch action example
        window.batchAction = function(action) {
            var selected = $('.multi-select-table tbody input:checked').map(function() { 
                return parseInt($(this).val()); 
            }).get();
            
            if (selected.length === 0) {
                alert('Please select items first');
                return;
            }

            rpc.query({
                route: '/my/inventory/batch_action',
                params: {
                    ids: selected,
                    action: action
                }
            }).then(function(result) {
                if (result.success) {
                    alert('Action applied successfully!');
                    location.reload(); // Refresh the page to show updates
                } else {
                    alert('Action failed. Please try again.');
                }
            }).catch(function(error) {
                console.error('Batch action error:', error);
                alert('An error occurred. Please try again.');
            });
        };

        // Add temp inventory
        window.addTempInventory = function() {
            var type = prompt('Type (box/document/file):');
            if (!type) return;
            
            var desc = prompt('Description:');
            if (!desc) return;

            rpc.query({
                route: '/my/inventory/add_temp',
                params: {
                    type: type,
                    description: desc
                }
            }).then(function(result) {
                if (result.barcode) {
                    alert('Temp barcode created: ' + result.barcode);
                    // Optionally refresh the page or update the table
                    location.reload();
                } else {
                    alert('Failed to create temp inventory');
                }
            }).catch(function(error) {
                console.error('Add temp inventory error:', error);
                alert('An error occurred. Please try again.');
            });
        };

        // Batch to pickup
        window.batchToPickup = function() {
            var selected = $('.multi-select-table tbody input:checked').map(function() { 
                return parseInt($(this).val()); 
            }).get();
            
            if (selected.length === 0) {
                alert('Please select items first');
                return;
            }

            // Call temp inventory batch to pickup action
            selected.forEach(function(itemId) {
                rpc.query({
                    route: '/my/inventory/add_to_pickup',
                    params: {
                        item_id: itemId
                    }
                });
            });

            alert('Selected items added to pickup request');
            location.reload();
        };

        // Row highlighting on hover
        $('.multi-select-table tbody tr').hover(
            function() {
                $(this).addClass('table-hover-highlight');
            },
            function() {
                $(this).removeClass('table-hover-highlight');
            }
        );

        // Checkbox change handler
        $('.multi-select-table tbody input[type="checkbox"]').change(function() {
            updateBatchButtons();
            
            // Update header checkbox state
            var totalCheckboxes = $('.multi-select-table tbody input[type="checkbox"]').length;
            var checkedCheckboxes = $('.multi-select-table tbody input:checked').length;
            var headerCheckbox = $('th input[type="checkbox"]')[0];
            
            if (checkedCheckboxes === 0) {
                headerCheckbox.indeterminate = false;
                headerCheckbox.checked = false;
            } else if (checkedCheckboxes === totalCheckboxes) {
                headerCheckbox.indeterminate = false;
                headerCheckbox.checked = true;
            } else {
                headerCheckbox.indeterminate = true;
            }
        });

        // Initialize batch button states
        updateBatchButtons();

        // Add smooth animations for state changes
        $('.table tr').each(function() {
            var $row = $(this);
            var originalBg = $row.css('background-color');
            
            $row.on('click', 'input[type="checkbox"]', function() {
                if ($(this).is(':checked')) {
                    $row.addClass('selected-row');
                } else {
                    $row.removeClass('selected-row');
                }
            });
        });

        // Status badge styling
        $('.badge').each(function() {
            var status = $(this).text().toLowerCase();
            $(this).removeClass('badge-secondary');
            
            switch(status) {
                case 'active':
                    $(this).addClass('badge-success');
                    break;
                case 'pending':
                    $(this).addClass('badge-warning');
                    break;
                case 'archived':
                    $(this).addClass('badge-secondary');
                    break;
                default:
                    $(this).addClass('badge-info');
            }
        });
    });
});
