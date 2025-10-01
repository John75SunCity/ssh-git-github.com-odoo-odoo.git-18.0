/**
 * Records Management Portal - Barcode Management Logic
 * Extracted from inline template (portal_barcode_template.xml) to comply with
 * modernization and security guidelines (no inline JS, progressive enhancement).
 */
odoo.define('records_management.portal_barcode_management', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const { qweb } = require('web.core');

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
            // Placeholder for server call to generate new temporary barcode
            // Could call a JSON route and then refresh table (future enhancement)
            console.log('[BarcodePortal] Generate new barcode requested');
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

  // --- Core Functions (logic unchanged from inline placeholders) ---
  function generateNewBarcode() {
    console.log('Generating new barcode...');
    // TODO: Implement server call & refresh logic
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
