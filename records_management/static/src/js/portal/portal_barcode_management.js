/**
 * Records Management Portal - Barcode Management Logic
 * Extracted from inline template (portal_barcode_template.xml) to comply with
 * modernization and security guidelines (no inline JS, progressive enhancement).
 */
odoo.define('records_management.portal_barcode_management', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const { qweb } = require('web.core');
    const ajax = require('web.ajax');

    const BarcodePortal = publicWidget.Widget.extend({
        selector: '[data-rm-portal-barcode]',
        events: {
            'click [data-action="generate-barcode"]': '_onGenerateBarcode',
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
            if ($btn.prop('disabled')) {
                return;
            }
            $btn.prop('disabled', true).addClass('disabled');
            $btn.append('<span class="spinner-border spinner-border-sm ms-2" role="status" aria-hidden="true"></span>');
            ajax.jsonRpc('/records_management/portal/generate_barcode', 'call', {
                barcode_type: 'generic',
                barcode_format: 'code128',
            }).then(result => {
                if (!result || !result.success) {
                    console.error('[BarcodePortal] Generation failed', result && result.error);
                    return;
                }
                const tbody = this.$('#barcodeTable tbody');
                if (result.row_html) {
                    // Insert at top
                    tbody.prepend(result.row_html);
                } else if (result.barcode) {
                    // Fallback minimal row
                    const b = result.barcode;
                    const row = `<tr data-barcode-id="${b.id}">
                        <td><code>${_.escape(b.name)}</code><br/><small class="text-muted">Format: ${_.escape(b.barcode_format)}</small></td>
                        <td><span class="badge bg-secondary">${_.escape(b.barcode_type)}</span></td>
                        <td>-</td><td>-</td>
                        <td><span class="badge bg-success">${_.escape(b.state)}</span></td>
                        <td></td><td>-</td>
                        <td><div class="btn-group btn-group-sm" role="group">
                            <button class="btn btn-outline-secondary" data-barcode-action="viewBarcodeDetails" data-barcode-id="${b.id}"><i class="fa fa-eye"/></button>
                        </div></td>
                    </tr>`;
                    tbody.prepend(row);
                }
                this._filterBarcodes();
            }).catch(err => {
                console.error('[BarcodePortal] Generation error', err);
            }).always(() => {
                $btn.find('.spinner-border').remove();
                $btn.prop('disabled', false).removeClass('disabled');
            });
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

        _filterBarcodes() {
            const searchTerm = (this.$('#barcodeSearch').val() || '').toLowerCase();
            const typeFilter = (this.$('#barcodeTypeFilter').val() || '').toLowerCase();
            const statusFilter = (this.$('#barcodeStatusFilter').val() || '').toLowerCase();

            this.$('#barcodeTable tbody tr').each(function () {
                const $row = $(this);
                const barcodeText = $row.find('code').text().toLowerCase();
                const typeText = $row.find('td:nth-child(2)').text().toLowerCase();
                const statusText = $row.find('td:nth-child(5)').text().toLowerCase();

                const matchesSearch = !searchTerm || barcodeText.includes(searchTerm);
                const matchesType = !typeFilter || typeText.includes(typeFilter);
                const matchesStatus = !statusFilter || statusText.includes(statusFilter);

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
                return;
            }
            const w = window.open('', '_blank');
            if (!w) {
                return;
            }
            w.document.write(`<img src="${barcodeImage}" style="max-width:100%;"/>`);
            w.document.close();
            w.print();
        },

        _downloadBarcodeImage() {
            const barcodeImage = this.$('#modalBarcodeImage').attr('src');
            if (!barcodeImage) {
                return;
            }
            const link = document.createElement('a');
            link.href = barcodeImage;
            link.download = 'barcode.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },
    });

    publicWidget.registry.BarcodePortal = BarcodePortal;
    return BarcodePortal;
});
/**
 * Portal Barcode Management (extracted from inline template)
 * Provides UI interactions: generate, print, view details, edit, duplicate, deactivate,
 * filtering, and image print/download for barcodes.
 * Progressive enhancement: attaches only if container with data-module present.
 */
(function () {
  'use strict';

  function q(selector, ctx) { return (ctx || document).querySelector(selector); }
  function qa(selector, ctx) { return Array.from((ctx || document).querySelectorAll(selector)); }

  const root = q('[data-rm-portal-barcode]');
  if (!root) { return; }

  // Public-ish namespace for debugging
  const API = {
    generateNewBarcode,
    printBarcode,
    viewBarcodeDetails,
    editBarcode,
    duplicateBarcode,
    deactivateBarcode,
    filterBarcodes,
    clearFilters,
    printBarcodeImage,
    downloadBarcodeImage,
  };
  root.RMPortalBarcode = API;

  // Event delegation bindings
  function init() {
    const generateBtn = q('[data-action="generate-barcode"]', root);
    if (generateBtn) generateBtn.addEventListener('click', generateNewBarcode);

    const clearBtn = q('[data-action="clear-filters"]', root);
    if (clearBtn) clearBtn.addEventListener('click', clearFilters);

    const searchInput = q('#barcodeSearch', root);
    if (searchInput) searchInput.addEventListener('keyup', filterBarcodes);

    const typeFilter = q('#barcodeTypeFilter', root);
    if (typeFilter) typeFilter.addEventListener('change', filterBarcodes);

    const statusFilter = q('#barcodeStatusFilter', root);
    if (statusFilter) statusFilter.addEventListener('change', filterBarcodes);

    // Button actions in table (use delegation)
    root.addEventListener('click', function (ev) {
      const btn = ev.target.closest('[data-barcode-action]');
      if (!btn) return;
      const id = btn.getAttribute('data-barcode-id');
      const action = btn.getAttribute('data-barcode-action');
      if (action && typeof API[action] === 'function') {
        API[action](id);
      }
    });
  }

  // --- Core Functions (logic unchanged from inline placeholders in portal_barcode_template.xml) ---
  /**
   * Trigger barcode generation via server call (future enhancement).
    // TODO: Implement server call (e.g., via Odoo JSON-RPC to /records_management/portal/generate_barcode) & refresh logic
   * then refresh the barcode table to reflect the new entry.
   */
    function generateNewBarcode(ev) {
        const btn = ev && ev.target ? ev.target.closest('[data-action="generate-barcode"]') : null;
        if (btn && btn.disabled) return;
        if (btn) {
            btn.disabled = true;
            btn.classList.add('disabled');
            btn.insertAdjacentHTML('beforeend', '<span class="spinner-border spinner-border-sm ms-2" role="status" aria-hidden="true"></span>');
        }
        fetch('/records_management/portal/generate_barcode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ barcode_type: 'generic', barcode_format: 'code128' })
        }).then(r => r.json()).then(result => {
            if (!result.success) { console.error('Generation failed', result.error); return; }
            const tbody = q('#barcodeTable tbody', root);
            if (result.row_html) {
                const temp = document.createElement('tbody');
                temp.innerHTML = result.row_html.trim();
                const newRow = temp.firstElementChild;
                if (newRow) tbody.prepend(newRow);
            } else if (result.barcode) {
                const b = result.barcode;
                const row = document.createElement('tr');
                row.setAttribute('data-barcode-id', b.id);
                row.innerHTML = `<td><code>${b.name}</code><br/><small class="text-muted">Format: ${b.barcode_format}</small></td>
                    <td><span class="badge bg-secondary">${b.barcode_type}</span></td><td>-</td><td>-</td>
                    <td><span class="badge bg-success">${b.state}</span></td><td></td><td>-</td>
                    <td><div class="btn-group btn-group-sm" role="group"><button class="btn btn-outline-secondary" data-barcode-action="viewBarcodeDetails" data-barcode-id="${b.id}"><i class="fa fa-eye"></i></button></div></td>`;
                tbody.prepend(row);
            }
            filterBarcodes();
        }).catch(err => console.error('Generation error', err)).finally(() => {
            if (btn) { btn.querySelector('.spinner-border')?.remove(); btn.disabled = false; btn.classList.remove('disabled'); }
        });
    }

  function printBarcode(barcodeId) {
    console.log('Printing barcode:', barcodeId);
  }

  function viewBarcodeDetails(barcodeId) {
    console.log('Viewing barcode details:', barcodeId);
    const modal = q('#barcodeDetailsModal');
    if (modal && window.jQuery) {
      window.jQuery(modal).modal('show');
    }
  }

  function editBarcode(barcodeId) { console.log('Editing barcode:', barcodeId); }
  function duplicateBarcode(barcodeId) { console.log('Duplicating barcode:', barcodeId); }
  function deactivateBarcode(barcodeId) { console.log('Deactivating barcode:', barcodeId); }

  function filterBarcodes() {
    const searchTerm = (q('#barcodeSearch', root)?.value || '').toLowerCase();
    const typeFilter = (q('#barcodeTypeFilter', root)?.value || '').toLowerCase();
    const statusFilter = (q('#barcodeStatusFilter', root)?.value || '').toLowerCase();
    qa('#barcodeTable tbody tr', root).forEach(row => {
      const barcodeText = (row.querySelector('code')?.textContent || '').toLowerCase();
      const typeText = (row.querySelector('td:nth-child(2)')?.textContent || '').toLowerCase();
      const statusText = (row.querySelector('td:nth-child(5)')?.textContent || '').toLowerCase();
      const matchesSearch = !searchTerm || barcodeText.includes(searchTerm);
      const matchesType = !typeFilter || typeText.includes(typeFilter);
      const matchesStatus = !statusFilter || statusText.includes(statusFilter);
      row.style.display = (matchesSearch && matchesType && matchesStatus) ? '' : 'none';
    });
  }

  function clearFilters() {
    const search = q('#barcodeSearch', root); if (search) search.value = '';
    const type = q('#barcodeTypeFilter', root); if (type) type.value = '';
    const status = q('#barcodeStatusFilter', root); if (status) status.value = '';
    filterBarcodes();
  }

  function printBarcodeImage() {
    const barcodeImage = q('#modalBarcodeImage')?.getAttribute('src');
    if (!barcodeImage) return;
    const printWindow = window.open('', '_blank');
    printWindow.document.write('<img src="' + barcodeImage + '" style="max-width:100%;"/>');
    printWindow.document.close();
    printWindow.print();
  }

  function downloadBarcodeImage() {
    const barcodeImage = q('#modalBarcodeImage')?.getAttribute('src');
    if (!barcodeImage) return;
    const link = document.createElement('a');
    link.href = barcodeImage;
    link.download = 'barcode.png';
    link.click();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
