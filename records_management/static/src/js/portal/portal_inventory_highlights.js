/**
 * Records Management Portal - Inventory Highlights & Batch Actions
 * VANILLA JAVASCRIPT VERSION - No external dependencies
 * 
 * FEATURES:
 * ✓ Multi-select table with batch actions
 * ✓ Batch destruction requests
 * ✓ Batch pickup requests
 * ✓ Temporary inventory creation
 * ✓ Export functionality (Excel/CSV/PDF)
 * ✓ Mobile responsive card view
 * ✓ Status badge styling
 * ✓ Row hover highlighting
 * 
 * DEPENDENCIES: NONE (Pure vanilla JavaScript + Bootstrap 5)
 */
(function () {
    'use strict';

    // Debounce utility
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    const PortalInventoryHighlights = {
        table: null,

        init() {
            this.table = document.querySelector('.multi-select-table');
            if (!this.table) {
                console.log('[portal_inventory_highlights] No multi-select table found');
                return;
            }

            this.setupEventHandlers();
            this.setupMobileView();
            this.initializeTooltips();
            this.styleBadges();
            this.updateBatchButtons();
        },

        setupEventHandlers() {
            const self = this;

            // Header checkbox - select/deselect all
            const headerCheckbox = this.table.querySelector('th input[type="checkbox"]');
            if (headerCheckbox) {
                headerCheckbox.addEventListener('change', function() {
                    const checked = this.checked;
                    self.table.querySelectorAll('tbody input[type="checkbox"]').forEach(cb => {
                        cb.checked = checked;
                    });
                    self.updateBatchButtons();
                });
            }

            // Individual row checkboxes
            this.table.querySelectorAll('tbody input[type="checkbox"]').forEach(checkbox => {
                checkbox.addEventListener('change', () => {
                    self.updateHeaderCheckbox();
                    self.updateBatchButtons();
                    
                    // Toggle selected-row class
                    const row = checkbox.closest('tr');
                    if (row) {
                        row.classList.toggle('selected-row', checkbox.checked);
                    }
                });
            });

            // Row hover highlighting
            this.table.querySelectorAll('tbody tr').forEach(row => {
                row.addEventListener('mouseenter', () => row.classList.add('table-hover-highlight'));
                row.addEventListener('mouseleave', () => row.classList.remove('table-hover-highlight'));
            });
        },

        updateHeaderCheckbox() {
            const headerCheckbox = this.table.querySelector('th input[type="checkbox"]');
            if (!headerCheckbox) return;

            const checkboxes = this.table.querySelectorAll('tbody input[type="checkbox"]');
            const checked = this.table.querySelectorAll('tbody input:checked');

            if (checked.length === 0) {
                headerCheckbox.indeterminate = false;
                headerCheckbox.checked = false;
            } else if (checked.length === checkboxes.length) {
                headerCheckbox.indeterminate = false;
                headerCheckbox.checked = true;
            } else {
                headerCheckbox.indeterminate = true;
            }
        },

        updateBatchButtons() {
            const selected = this.table.querySelectorAll('tbody input:checked');
            const count = selected.length;

            document.querySelectorAll('.batch-action-btn').forEach(btn => {
                btn.disabled = count === 0;
            });

            const counter = document.querySelector('.batch-counter');
            if (counter) {
                counter.textContent = count > 0 ? `${count} item${count > 1 ? 's' : ''} selected` : '';
            }
        },

        batchAction(action) {
            const selected = Array.from(this.table.querySelectorAll('tbody input:checked'))
                .map(cb => parseInt(cb.value));

            if (selected.length === 0) {
                alert('Please select items first');
                return;
            }

            if (action === 'destruction') {
                if (!confirm(`Request destruction for ${selected.length} item${selected.length > 1 ? 's' : ''}?`)) {
                    return;
                }

                fetch('/my/inventory/request_destruction', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ item_ids: selected })
                })
                .then(r => r.json())
                .then(result => {
                    if (result && result.success) {
                        alert(result.message || 'Destruction request created successfully!');
                        location.reload();
                    } else {
                        alert(result && result.error || 'Failed to create destruction request.');
                    }
                })
                .catch(error => {
                    console.error('Destruction request error:', error);
                    alert('An error occurred. Please try again.');
                });
            } else {
                // Generic batch action
                fetch('/my/inventory/batch_action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'call',
                        params: { ids: selected, action: action }
                    })
                })
                .then(r => r.json())
                .then(data => {
                    const result = data.result || data;
                    if (result.success) {
                        alert('Action applied successfully!');
                        location.reload();
                    } else {
                        alert('Action failed. Please try again.');
                    }
                })
                .catch(error => {
                    console.error('Batch action error:', error);
                    alert('An error occurred. Please try again.');
                });
            }
        },

        addTempInventory() {
            const type = prompt('Type (box/document/file):');
            if (!type) return;

            const desc = prompt('Description:');
            if (!desc) return;

            fetch('/my/inventory/add_temp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { type: type, description: desc }
                })
            })
            .then(r => r.json())
            .then(data => {
                const result = data.result || data;
                if (result.barcode) {
                    alert('Temp barcode created: ' + result.barcode);
                    location.reload();
                } else {
                    alert('Failed to create temp inventory');
                }
            })
            .catch(error => {
                console.error('Add temp inventory error:', error);
                alert('An error occurred. Please try again.');
            });
        },

        batchToPickup() {
            const selected = Array.from(this.table.querySelectorAll('tbody input:checked'))
                .map(cb => parseInt(cb.value));

            if (selected.length === 0) {
                alert('Please select items first');
                return;
            }

            if (!confirm('Add ' + selected.length + ' selected items to pickup request?')) {
                return;
            }

            const promises = selected.map(itemId => 
                fetch('/my/inventory/add_to_pickup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'call',
                        params: { item_id: itemId }
                    })
                })
                .then(r => r.json())
                .then(data => data.result || data)
            );

            Promise.all(promises)
                .then(results => {
                    const successCount = results.filter(r => r.success).length;
                    if (successCount === selected.length) {
                        alert('All ' + successCount + ' items added to pickup request successfully!');
                    } else {
                        alert('Added ' + successCount + ' of ' + selected.length + ' items to pickup request.');
                    }
                    location.reload();
                })
                .catch(error => {
                    console.error('Batch pickup error:', error);
                    alert('An error occurred while adding items to pickup request.');
                });
        },

        setupMobileView() {
            const convertTables = () => {
                document.querySelectorAll('.table').forEach(table => {
                    if (window.innerWidth <= 768) {
                        table.classList.add('mobile-card-view');
                    } else {
                        table.classList.remove('mobile-card-view');
                    }
                });
            };

            convertTables();

            // Debounced resize handler
            window.addEventListener('resize', debounce(convertTables, 300));
        },

        initializeTooltips() {
            // Bootstrap 5 tooltip initialization
            if (window.bootstrap && bootstrap.Tooltip) {
                document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
                    new bootstrap.Tooltip(el);
                });
            }
        },

        styleBadges() {
            document.querySelectorAll('.badge').forEach(badge => {
                const status = badge.textContent.toLowerCase();
                badge.classList.remove('badge-secondary');

                switch(status) {
                    case 'active':
                        badge.classList.add('badge-success');
                        break;
                    case 'pending':
                        badge.classList.add('badge-warning');
                        break;
                    case 'archived':
                        badge.classList.add('badge-secondary');
                        break;
                    default:
                        badge.classList.add('badge-info');
                }
            });
        },

        exportInventory(format = 'xlsx') {
            const validFormats = ['xlsx', 'csv', 'pdf'];
            if (!validFormats.includes(format)) {
                alert('Invalid export format. Use: xlsx, csv, or pdf');
                return;
            }

            // Build export URL with current filters
            const searchInput = document.querySelector('#barcodeSearch');
            const typeFilter = document.querySelector('#barcodeTypeFilter');
            const statusFilter = document.querySelector('#barcodeStatusFilter');

            const params = new URLSearchParams();
            if (searchInput && searchInput.value) params.append('search', searchInput.value);
            if (typeFilter && typeFilter.value) params.append('type', typeFilter.value);
            if (statusFilter && statusFilter.value) params.append('status', statusFilter.value);
            params.append('format', format);

            const exportUrl = window.location.pathname + '/export?' + params.toString();
            window.location.href = exportUrl;
        }
    };

    // Auto-initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => PortalInventoryHighlights.init());
    } else {
        PortalInventoryHighlights.init();
    }

    // Expose globally for inline onclick handlers
    window.RecordsManagementPortalInventoryHighlights = PortalInventoryHighlights;
    window.batchAction = (action) => PortalInventoryHighlights.batchAction(action);
    window.addTempInventory = () => PortalInventoryHighlights.addTempInventory();
    window.batchToPickup = () => PortalInventoryHighlights.batchToPickup();
    window.exportInventory = (format) => PortalInventoryHighlights.exportInventory(format);
})();
