/**
 * Records Management Portal - Barcode Management Logic
 * Integrated with container/file/temp barcode models and ir.sequence
 */
odoo.define('records_management.portal_barcode_management', function (require) {
    'use strict';

    // Frontend-compatible implementation
    const publicWidget = { Widget: { extend: function(obj) { return obj; } } };
    const qweb = { render: function() { return ''; } };
    const _t = function(str) { return str; };
    const ajax = { 
        jsonRpc: function(url, method, params) { 
            return fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ jsonrpc: '2.0', method: method, params: params })
            }).then(r => r.json()).then(r => r.result);
        }
    };

    const BarcodePortal = publicWidget.Widget.extend({
        selector: '[data-rm-portal-barcode]',
        events: {
            'click [data-action="generate-barcode"]': '_onGenerateBarcode',
            'click [data-action="generate-container-barcode"]': '_onGenerateContainerBarcode',
            'click [data-action="generate-file-barcode"]': '_onGenerateFileBarcode',
            'click [data-action="generate-temp-barcode"]': '_onGenerateTempBarcode',
            'click [data-action="clear-filters"]': '_onClearFilters',
            'keyup #barcodeSearch': '_onFilterChanged',
            'change #barcodeTypeFilter': '_onFilterChanged',
            'change #barcodeStatusFilter': '_onFilterChanged',
            'click [data-barcode-action]': '_onBarcodeRowAction',
            'click [data-action="print-barcode-image"]': '_onPrintBarcodeImage',
            'click [data-action="download-barcode-image"]': '_onDownloadBarcodeImage',
        },

        start() {
            // Initial filter application (noop if empty)
            this._filterBarcodes();
            return this._super.apply(this, arguments);
        },

        /**
         * Handlers
         */
        _onGenerateBarcode(ev) {
            ev.preventDefault();
            const $btn = $(ev.currentTarget);
            const barcodeType = $btn.data('barcode-type') || 'container'; // default to container

            if ($btn.prop('disabled')) {
                return;
            }
            $btn.prop('disabled', true).addClass('disabled');
            const $spinner = $('<span class="spinner-border spinner-border-sm ms-2" role="status" aria-hidden="true"></span>');
            $btn.append($spinner);

            // Route to type-specific generation
            const typeRoutes = {
                'container': '/records_management/portal/generate_container_barcode',
                'file': '/records_management/portal/generate_file_barcode',
                'temp': '/records_management/portal/generate_temp_barcode',
            };

            const route = typeRoutes[barcodeType] || typeRoutes['container'];

            ajax.jsonRpc(route, 'call', {
                barcode_format: 'code128', // respects nomenclature rules
            }).then(result => {
                if (!result || !result.success) {
                    this._showNotification(_t('Barcode generation failed: %s', result && result.error || 'Unknown error'), 'danger');
                    console.error('[BarcodePortal] Generation failed', result && result.error);
                    return;
                }
                this._insertBarcodeRow(result.barcode, result.row_html);
                this._filterBarcodes();
                this._showNotification(_t('Barcode %s generated successfully', result.barcode.name), 'success');
            }).catch(err => {
                console.error('[BarcodePortal] Generation error', err);
                this._showNotification(_t('An error occurred while generating the barcode'), 'danger');
            }).always(() => {
                $spinner.remove();
                $btn.prop('disabled', false).removeClass('disabled');
            });
        },

        /**
         * Type-specific barcode generators (use sequences from models)
         */
        _onGenerateContainerBarcode(ev) {
            ev.preventDefault();
            $(ev.currentTarget).data('barcode-type', 'container');
            this._onGenerateBarcode(ev);
        },

        _onGenerateFileBarcode(ev) {
            ev.preventDefault();
            $(ev.currentTarget).data('barcode-type', 'file');
            this._onGenerateBarcode(ev);
        },

        _onGenerateTempBarcode(ev) {
            ev.preventDefault();
            $(ev.currentTarget).data('barcode-type', 'temp');
            this._onGenerateBarcode(ev);
        },

        _onClearFilters(ev) {
            ev.preventDefault();
            this.$('#barcodeSearch').val('');
            this.$('#barcodeTypeFilter').val('');
            this.$('#barcodeStatusFilter').val('');
            this._filterBarcodes();
        },

        _onFilterChanged() {
            this._filterBarcodes();
        },

        _onBarcodeRowAction(ev) {
            ev.preventDefault();
            const $target = $(ev.currentTarget);
            const action = $target.data('barcode-action');
            const barcodeId = $target.data('barcode-id');
            if (!action) {
                return;
            }
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
         * Core logic methods (mirroring removed inline functions)
         */
        _printBarcode(barcodeId) {
            console.log('[BarcodePortal] Printing barcode', barcodeId);
            // Future: open a print-friendly route or generate PDF
            this._showNotification(_t('Print functionality coming soon'), 'info');
        },

        _viewBarcodeDetails(barcodeId) {
            console.log('[BarcodePortal] Viewing details for', barcodeId);
            // Show modal (Bootstrap 5 assumed)
            const $modal = this.$('#barcodeDetailsModal');
            if ($modal.length) {
                $modal.modal('show');
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

        /**
         * Insert barcode row with type-specific rendering
         */
        _insertBarcodeRow(barcode, rowHtml) {
            const tbody = this.$('#barcodeTable tbody');
            if (rowHtml) {
                tbody.prepend(rowHtml);
            } else if (barcode) {
                // Fallback: render based on barcode model type
                const typeIcons = {
                    'container': 'fa-box',
                    'file': 'fa-file-alt',
                    'temp': 'fa-clock',
                };
                const icon = typeIcons[barcode.barcode_type] || 'fa-barcode';

                const row = $('<tr>').attr('data-barcode-id', barcode.id).html(`
                    <td>
                        <i class="fa ${icon} me-2"></i>
                        <code>${_.escape(barcode.name)}</code>
                        <br/><small class="text-muted">Format: ${_.escape(barcode.barcode_format)}</small>
                        ${barcode.sequence_code ? '<br/><small class="text-muted">Sequence: ' + _.escape(barcode.sequence_code) + '</small>' : ''}
                    </td>
                    <td><span class="badge bg-secondary">${_.escape(barcode.barcode_type)}</span></td>
                    <td>${barcode.linked_record ? _.escape(barcode.linked_record) : '-'}</td>
                    <td>${barcode.created_date ? _.escape(barcode.created_date) : '-'}</td>
                    <td><span class="badge bg-success">${_.escape(barcode.state)}</span></td>
                    <td>${barcode.barcode_image ? '<img src="data:image/png;base64,' + barcode.barcode_image + '" style="height:30px;"/>' : ''}</td>
                    <td>${barcode.last_scanned ? _.escape(barcode.last_scanned) : '-'}</td>
                    <td>
                        <div class="btn-group btn-group-sm" role="group">
                            <button class="btn btn-outline-primary" data-barcode-action="printBarcode" data-barcode-id="${barcode.id}">
                                <i class="fa fa-print"/>
                            </button>
                            <button class="btn btn-outline-secondary" data-barcode-action="viewBarcodeDetails" data-barcode-id="${barcode.id}">
                                <i class="fa fa-eye"/>
                            </button>
                        </div>
                    </td>
                `);
                tbody.prepend(row);
            }
        },

        _filterBarcodes() {
            const searchTerm = (this.$('#barcodeSearch').val() || '').toLowerCase();
            const typeFilter = (this.$('#barcodeTypeFilter').val() || '').toLowerCase();
            const statusFilter = (this.$('#barcodeStatusFilter').val() || '').toLowerCase();

            this.$('#barcodeTable tbody tr').each(function () {
                const $row = $(this);
                const barcodeText = $row.find('code').text().toLowerCase();
                const typeText = $row.find('td:nth-child(2) .badge').text().toLowerCase(); // Updated selector
                const statusText = $row.find('td:nth-child(5) .badge').text().toLowerCase(); // Updated selector

                const matchesSearch = !searchTerm || barcodeText.includes(searchTerm);
                const matchesType = !typeFilter || typeText === typeFilter;
                const matchesStatus = !statusFilter || statusText === statusFilter;

                if (matchesSearch && matchesType && matchesStatus) {
                    $row.show();
                } else {
                    $row.hide();
                }
            });
        },

        _printBarcodeImage() {
            const barcodeImage = this.$('#modalBarcodeImage').attr('src');
            if (!barcodeImage) {
                this._showNotification(_t('No barcode image available'), 'warning');
                return;
            }
            const w = window.open('', '_blank');
            if (!w) {
                this._showNotification(_t('Please allow pop-ups for this site'), 'warning');
                return;
            }
            w.document.write(`<img src="${_.escape(barcodeImage)}" style="max-width:100%;"/>`);
            w.document.close();
            w.print();
        },

        _downloadBarcodeImage() {
            const barcodeImage = this.$('#modalBarcodeImage').attr('src');
            if (!barcodeImage) {
                this._showNotification(_t('No barcode image available'), 'warning');
                return;
            }
            const link = document.createElement('a');
            link.href = barcodeImage;
            link.download = 'barcode.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        /**
         * Helper to show Bootstrap toast/alert notifications
         */
        _showNotification(message, type) {
            type = type || 'info';
            const $alert = $(`
                <div class="alert alert-${type} alert-dismissible fade show position-fixed" 
                     role="alert" style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
                    ${_.escape(message)}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `);
            $('body').append($alert);
            setTimeout(() => $alert.alert('close'), 5000);
        },
    });

    publicWidget.registry.BarcodePortal = BarcodePortal;
    return BarcodePortal;
});
