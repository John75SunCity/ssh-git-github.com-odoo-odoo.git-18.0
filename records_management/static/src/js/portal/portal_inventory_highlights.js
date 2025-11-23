// New file: JS for modern inventory UI - highlights, multi-select actions, clean animations.

odoo.define('records_management.portal_inventory_highlights', ['web.public.widget'], function (require) {
    "use strict";

    // Frontend-compatible implementation - no backend dependencies
    var $ = window.jQuery || window.$;
    var rpc = { query: function(params) {
        return fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        }).then(r => r.json()).then(r => r.result);
    } };

    if (!$) {
        console.warn('[records_management.portal_inventory_highlights] jQuery not found – skipping interactive inventory helpers.');
        return;
    }

    $(document).ready(function () {
        // Scoped table selector for better performance (Grok pattern)
        const $table = $('.multi-select-table');
        if (!$table.length) {
            console.log('[portal_inventory_highlights] No multi-select table found');
            return;
        }
        // Header checkbox - cleaner event binding (Grok pattern)
        $table.find('th input[type="checkbox"]').on('change', function() {
            $table.find('tbody input[type="checkbox"]').prop('checked', this.checked);
            updateBatchButtons();
        });

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

        // Batch action for destruction requests - optimized (Grok pattern)
        window.batchAction = function(action) {
            const selected = $table.find('tbody input:checked').map(function() {
                return parseInt($(this).val());
            }).get();

            if (!selected.length) {
                alert('Please select items first');
                return;
            }

            if (action === 'destruction') {
                // Cleaner confirmation message (Grok pattern)
                if (!confirm(`Request destruction for ${selected.length} item${selected.length > 1 ? 's' : ''}?`)) {
                    return;
                }

                // Simplified POST request (Grok pattern)
                $.post('/my/inventory/request_destruction', { item_ids: selected })
                    .done(function(result) {
                        if (result && result.success) {
                            alert(result.message || 'Destruction request created successfully!');
                            location.reload();
                        } else {
                            alert(result && result.error || 'Failed to create destruction request.');
                        }
                    })
                    .fail(function(error) {
                        console.error('Destruction request error:', error);
                        alert('An error occurred. Please try again.');
                    });
            } else {
                // Generic batch action for other actions
                rpc.query({
                    route: '/my/inventory/batch_action',
                    params: {
                        ids: selected,
                        action: action
                    }
                }).then(function(result) {
                    if (result.success) {
                        alert('Action applied successfully!');
                        location.reload();
                    } else {
                        alert('Action failed. Please try again.');
                    }
                }).catch(function(error) {
                    console.error('Batch action error:', error);
                    alert('An error occurred. Please try again.');
                });
            }
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

            // Add confirmation
            if (!confirm('Add ' + selected.length + ' selected items to pickup request?')) {
                return;
            }

            // Call temp inventory batch to pickup action
            var promises = selected.map(function(itemId) {
                return rpc.query({
                    route: '/my/inventory/add_to_pickup',
                    params: {
                        item_id: itemId
                    }
                });
            });

            Promise.all(promises).then(function(results) {
                var successCount = results.filter(function(r) { return r.success; }).length;
                if (successCount === selected.length) {
                    alert('All ' + successCount + ' items added to pickup request successfully!');
                } else {
                    alert('Added ' + successCount + ' of ' + selected.length + ' items to pickup request.');
                }
                location.reload();
            }).catch(function(error) {
                console.error('Batch pickup error:', error);
                alert('An error occurred while adding items to pickup request.');
            });
        };

        // Row hover highlighting - scoped selector (Grok pattern)
        $table.find('tbody tr').hover(
            function() { $(this).addClass('table-hover-highlight'); },
            function() { $(this).removeClass('table-hover-highlight'); }
        );

        // Row checkbox change handler - optimized (Grok pattern)
        $table.find('tbody input[type="checkbox"]').on('change', function() {
            const total = $table.find('tbody input[type="checkbox"]').length;
            const checked = $table.find('tbody input:checked').length;
            const $headerCheckbox = $table.find('th input[type="checkbox"]')[0];

            if (checked === 0) {
                $headerCheckbox.indeterminate = false;
                $headerCheckbox.checked = false;
            } else if (checked === total) {
                $headerCheckbox.indeterminate = false;
                $headerCheckbox.checked = true;
            } else {
                $headerCheckbox.indeterminate = true;
            }

            updateBatchButtons();
        });

        // Initialize batch button states
        updateBatchButtons();

        // Setup mobile responsive tables (Grok optimization)
        setupMobileView();

        // Initialize Bootstrap tooltips for better UX
        initializeTooltips();

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

        /**
         * Mobile Responsive Tables (from Grok suggestion)
         * Converts tables to card view on mobile devices
         */
        function setupMobileView() {
            const convertTables = function() {
                if (window.innerWidth <= 768) {
                    $('.table').addClass('mobile-card-view');
                } else {
                    $('.table').removeClass('mobile-card-view');
                }
            };

            convertTables();

            // Debounced resize handler (300ms - Grok pattern)
            let resizeTimeout;
            $(window).on('resize', function() {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(convertTables, 300);
            });
        }

        /**
         * Initialize Bootstrap 5 tooltips (from Grok suggestion)
         */
        function initializeTooltips() {
            // Bootstrap 5 tooltip initialization
            const tooltipTriggerList = [].slice.call(
                document.querySelectorAll('[data-bs-toggle="tooltip"]')
            );

            if (window.bootstrap && bootstrap.Tooltip) {
                tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl);
                });
            }
        }

        /**
         * Export functionality (from Grok suggestion)
         * Allows exporting inventory data to Excel/CSV
         */
        window.exportInventory = function(format) {
            format = format || 'xlsx';
            const validFormats = ['xlsx', 'csv', 'pdf'];

            if (!validFormats.includes(format)) {
                alert('Invalid export format. Use: xlsx, csv, or pdf');
                return;
            }

            // Build export URL with current filters
            const searchParam = $('#barcodeSearch').val() || '';
            const typeParam = $('#barcodeTypeFilter').val() || '';
            const statusParam = $('#barcodeStatusFilter').val() || '';

            const params = new URLSearchParams();
            if (searchParam) params.append('search', searchParam);
            if (typeParam) params.append('type', typeParam);
            if (statusParam) params.append('status', statusParam);
            params.append('format', format);

            const exportUrl = window.location.pathname + '/export?' + params.toString();

            // Trigger download
            window.location.href = exportUrl;
        };
    });
});
