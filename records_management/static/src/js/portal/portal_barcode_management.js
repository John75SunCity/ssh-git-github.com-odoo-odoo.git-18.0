/**
 * Records Management Portal - Barcode Management Logic
 *
 * PURPOSE: Customer-facing barcode generation and management widget
 * USE CASE: /my/barcodes route - portal users generate/view barcodes
 *
 * FEATURES:
 * ✓ Multi-type barcode generation (container/file/temp)
 * ✓ Real-time filtering with debounced search (300ms)
 * ✓ Print/download barcode images
 * ✓ Bootstrap 5 notifications with auto-dismiss
 * ✓ Integration with ir.sequence for proper barcode format
 *
 * PERFORMANCE OPTIMIZATIONS:
 * - Debounced filter updates (300ms) prevents excessive DOM queries
 * - Full row text search (faster than multiple selectors)
 * - Vanilla JavaScript for better performance
 * - Batch DOM operations where possible
 *
 * BARCODE MODELS:
 * - portal.barcode.container (sequence: records.barcode.container)
 * - portal.barcode.file (sequence: records.barcode.file)
 * - portal.barcode.temp (sequence: records.barcode.temp)
 *
 * DEPENDENCIES: NONE (Pure vanilla JavaScript)
 */
(function () {
    'use strict';

    const _t = function(str) { return str; };
    
    // Debounce utility (replaces _.debounce)
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
    
    // HTML escape utility (replaces _.escape)
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    const BarcodePortal = {
        selector: '[data-rm-portal-barcode]',
        containers: null,

        init() {
            this.containers = document.querySelectorAll(this.selector);
            if (this.containers.length === 0) return;

            this._attachEventListeners();
            this._filterBarcodes();
        },

        _attachEventListeners() {
            this.containers.forEach(container => {
                // Generate barcode buttons
                container.querySelectorAll('[data-action="generate-barcode"]').forEach(btn => {
                    btn.addEventListener('click', (e) => this._onGenerateBarcode(e));
                });
                container.querySelectorAll('[data-action="generate-container-barcode"]').forEach(btn => {
                    btn.addEventListener('click', (e) => this._onGenerateContainerBarcode(e));
                });
                container.querySelectorAll('[data-action="generate-file-barcode"]').forEach(btn => {
                    btn.addEventListener('click', (e) => this._onGenerateFileBarcode(e));
                });
                container.querySelectorAll('[data-action="generate-temp-barcode"]').forEach(btn => {
                    btn.addEventListener('click', (e) => this._onGenerateTempBarcode(e));
                });

                // Filter controls
                container.querySelectorAll('[data-action="clear-filters"]').forEach(btn => {
                    btn.addEventListener('click', (e) => this._onClearFilters(e));
                });
                
                const searchInput = container.querySelector('#barcodeSearch');
                if (searchInput) {
                    searchInput.addEventListener('keyup', debounce(() => this._filterBarcodes(), 300));
                }
                
                const typeFilter = container.querySelector('#barcodeTypeFilter');
                if (typeFilter) {
                    typeFilter.addEventListener('change', debounce(() => this._filterBarcodes(), 300));
                }
                
                const statusFilter = container.querySelector('#barcodeStatusFilter');
                if (statusFilter) {
                    statusFilter.addEventListener('change', debounce(() => this._filterBarcodes(), 300));
                }

                // Barcode row actions
                container.querySelectorAll('[data-barcode-action]').forEach(btn => {
                    btn.addEventListener('click', (e) => this._onBarcodeRowAction(e));
                });

                // Print/download actions
                container.querySelectorAll('[data-action="print-barcode-image"]').forEach(btn => {
                    btn.addEventListener('click', (e) => this._onPrintBarcodeImage(e));
                });
                container.querySelectorAll('[data-action="download-barcode-image"]').forEach(btn => {
                    btn.addEventListener('click', (e) => this._onDownloadBarcodeImage(e));
                });
            });
        },


        /**
         * Event Handlers
         */
        _onGenerateBarcode(ev) {
            ev.preventDefault();
            const btn = ev.currentTarget;
            const barcodeType = btn.dataset.barcodeType || 'container';

            if (btn.disabled) return;
            
            btn.disabled = true;
            btn.classList.add('disabled');
            const spinner = document.createElement('span');
            spinner.className = 'spinner-border spinner-border-sm ms-2';
            spinner.setAttribute('role', 'status');
            spinner.setAttribute('aria-hidden', 'true');
            btn.appendChild(spinner);

            const typeRoutes = {
                'container': '/records_management/portal/generate_container_barcode',
                'file': '/records_management/portal/generate_file_barcode',
                'temp': '/records_management/portal/generate_temp_barcode',
            };

            const route = typeRoutes[barcodeType] || typeRoutes['container'];

            fetch(route, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        barcode_format: 'code128'
                    }
                })
            })
            .then(response => response.json())
            .then(data => {
                const result = data.result || data;
                if (!result || !result.success) {
                    throw new Error((result && result.error) || 'Unknown error');
                }
                this._insertBarcodeRow(result.barcode, result.row_html);
                this._filterBarcodes();
                this._notify(`Barcode ${result.barcode.name} created`, 'success');
            })
            .catch(error => {
                console.error('[BarcodePortal] Generation error:', error);
                this._notify(error.message || 'Error generating barcode', 'danger');
            })
            .finally(() => {
                spinner.remove();
                btn.disabled = false;
                btn.classList.remove('disabled');
            });
        },

        _onGenerateContainerBarcode(ev) {
            ev.preventDefault();
            ev.currentTarget.dataset.barcodeType = 'container';
            this._onGenerateBarcode(ev);
        },

        _onGenerateFileBarcode(ev) {
            ev.preventDefault();
            ev.currentTarget.dataset.barcodeType = 'file';
            this._onGenerateBarcode(ev);
        },

        _onGenerateTempBarcode(ev) {
            ev.preventDefault();
            ev.currentTarget.dataset.barcodeType = 'temp';
            this._onGenerateBarcode(ev);
        },

        _onClearFilters(ev) {
            ev.preventDefault();
            const container = ev.currentTarget.closest(this.selector);
            const searchInput = container.querySelector('#barcodeSearch');
            const typeFilter = container.querySelector('#barcodeTypeFilter');
            const statusFilter = container.querySelector('#barcodeStatusFilter');
            
            if (searchInput) searchInput.value = '';
            if (typeFilter) typeFilter.value = '';
            if (statusFilter) statusFilter.value = '';
            
            this._filterBarcodes();
        },

        _onBarcodeRowAction(ev) {
            ev.preventDefault();
            const target = ev.currentTarget;
            const action = target.dataset.barcodeAction;
            const barcodeId = target.dataset.barcodeId;
            
            if (!action) return;
            
            const dispatch = {
                printBarcode: this._printBarcode.bind(this),
                viewBarcodeDetails: this._viewBarcodeDetails.bind(this),
                editBarcode: this._editBarcode.bind(this),
                duplicateBarcode: this._duplicateBarcode.bind(this),
                deactivateBarcode: this._deactivateBarcode.bind(this),
            };
            
            if (dispatch[action]) {
                dispatch[action](barcodeId);
            } else {
                console.warn('[BarcodePortal] Unknown action:', action);
            }
        },

        _onPrintBarcodeImage(ev) {
            ev.preventDefault();
            this._printBarcodeImage();
        },

        _onDownloadBarcodeImage(ev) {
            ev.preventDefault();
            this._downloadBarcodeImage();
        },


        /**
         * Core logic methods
         */
        _printBarcode(barcodeId) {
            console.log('[BarcodePortal] Printing barcode', barcodeId);
            this._notify('Print functionality coming soon', 'info');
        },

        _viewBarcodeDetails(barcodeId) {
            console.log('[BarcodePortal] Viewing details for', barcodeId);
            const modal = document.querySelector('#barcodeDetailsModal');
            if (modal && window.bootstrap) {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        },

        _editBarcode(barcodeId) {
            console.log('[BarcodePortal] Editing barcode', barcodeId);
        },

        _duplicateBarcode(barcodeId) {
            console.log('[BarcodePortal] Duplicating barcode', barcodeId);
        },

        _deactivateBarcode(barcodeId) {
            console.log('[BarcodePortal] Deactivating barcode', barcodeId);
        },

        _insertBarcodeRow(barcode, rowHtml) {
            const tbody = document.querySelector('#barcodeTable tbody');
            if (!tbody) return;

            if (rowHtml) {
                tbody.insertAdjacentHTML('afterbegin', rowHtml);
            } else if (barcode) {
                const typeIcons = {
                    'container': 'fa-box',
                    'file': 'fa-file-alt',
                    'temp': 'fa-clock',
                };
                const icon = typeIcons[barcode.barcode_type] || 'fa-barcode';

                const row = document.createElement('tr');
                row.dataset.barcodeId = barcode.id;
                row.innerHTML = `
                    <td>
                        <i class="fa ${icon} me-2"></i>
                        <code>${escapeHtml(barcode.name)}</code>
                        <br/><small class="text-muted">Format: ${escapeHtml(barcode.barcode_format)}</small>
                        ${barcode.sequence_code ? '<br/><small class="text-muted">Sequence: ' + escapeHtml(barcode.sequence_code) + '</small>' : ''}
                    </td>
                    <td><span class="badge bg-secondary">${escapeHtml(barcode.barcode_type)}</span></td>
                    <td>${barcode.linked_record ? escapeHtml(barcode.linked_record) : '-'}</td>
                    <td>${barcode.created_date ? escapeHtml(barcode.created_date) : '-'}</td>
                    <td><span class="badge bg-success">${escapeHtml(barcode.state)}</span></td>
                    <td>${barcode.barcode_image ? '<img src="data:image/png;base64,' + barcode.barcode_image + '" style="height:30px;"/>' : ''}</td>
                    <td>${barcode.last_scanned ? escapeHtml(barcode.last_scanned) : '-'}</td>
                    <td>
                        <div class="btn-group btn-group-sm" role="group">
                            <button class="btn btn-outline-primary" data-barcode-action="printBarcode" data-barcode-id="${barcode.id}">
                                <i class="fa fa-print"></i>
                            </button>
                            <button class="btn btn-outline-secondary" data-barcode-action="viewBarcodeDetails" data-barcode-id="${barcode.id}">
                                <i class="fa fa-eye"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.insertBefore(row, tbody.firstChild);
            }
        },

        _filterBarcodes() {
            this.containers.forEach(container => {
                const searchInput = container.querySelector('#barcodeSearch');
                const typeFilter = container.querySelector('#barcodeTypeFilter');
                const statusFilter = container.querySelector('#barcodeStatusFilter');

                const s = (searchInput ? searchInput.value : '').trim().toLowerCase();
                const t = (typeFilter ? typeFilter.value : '').toLowerCase();
                const st = (statusFilter ? statusFilter.value : '').toLowerCase();

                const table = container.querySelector('#barcodeTable');
                if (!table) return;

                table.querySelectorAll('tbody tr').forEach(row => {
                    const text = row.textContent.toLowerCase();
                    const typeBadge = row.querySelector('td:nth-child(2) .badge');
                    const statusBadge = row.querySelector('td:nth-child(5) .badge');
                    
                    const typeText = typeBadge ? typeBadge.textContent.toLowerCase() : '';
                    const statusText = statusBadge ? statusBadge.textContent.toLowerCase() : '';

                    const matchesSearch = !s || text.includes(s);
                    const matchesType = !t || typeText === t;
                    const matchesStatus = !st || statusText === st;

                    row.style.display = (matchesSearch && matchesType && matchesStatus) ? '' : 'none';
                });
            });
        },

        _printBarcodeImage() {
            const modalImage = document.querySelector('#modalBarcodeImage');
            if (!modalImage || !modalImage.src) {
                this._notify('No barcode image available', 'warning');
                return;
            }
            
            const w = window.open('', '_blank');
            if (!w) {
                this._notify('Please allow pop-ups for this site', 'warning');
                return;
            }
            
            w.document.write(`<img src="${escapeHtml(modalImage.src)}" style="max-width:100%;"/>`);
            w.document.close();
            w.print();
        },

        _downloadBarcodeImage() {
            const modalImage = document.querySelector('#modalBarcodeImage');
            if (!modalImage || !modalImage.src) {
                this._notify('No barcode image available', 'warning');
                return;
            }
            
            const link = document.createElement('a');
            link.href = modalImage.src;
            link.download = 'barcode.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        _notify(msg, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible position-fixed fade show`;
            notification.style.cssText = 'top:20px;right:20px;z-index:9999;min-width:300px;';
            notification.innerHTML = `
                ${escapeHtml(msg)}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                if (notification.parentNode) {
                    if (window.bootstrap && window.bootstrap.Alert) {
                        const bsAlert = bootstrap.Alert.getInstance(notification) || new bootstrap.Alert(notification);
                        bsAlert.close();
                    } else {
                        notification.remove();
                    }
                }
            }, 5000);
        },
        
        _showNotification(message, type) {
            return this._notify(message, type);
        },
    };

    // Auto-initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => BarcodePortal.init());
    } else {
        BarcodePortal.init();
    }

    // Expose globally
    window.RecordsManagementBarcodePortal = BarcodePortal;
})();
