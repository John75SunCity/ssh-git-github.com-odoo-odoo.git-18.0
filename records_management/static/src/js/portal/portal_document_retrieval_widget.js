/**
 * Portal Document Retrieval Widget - Vanilla JavaScript (Odoo 18 Compatible)
 * 
 * PURPOSE: Multi-step wizard for document/container retrieval requests
 * USE CASE: /my/document-retrieval route - retrieval cart functionality
 * 
 * FEATURES:
 * ✓ Dynamic item addition/removal
 * ✓ Real-time pricing calculation
 * ✓ Container/Document type selection
 * ✓ Barcode input support
 * ✓ Form validation
 * 
 * CONVERSION NOTES (Odoo 18):
 * - Removed: odoo.define(), publicWidget dependency
 * - Replaced: jQuery with native DOM APIs
 * - Uses fetch() for AJAX pricing calculations
 */

(function() {
    'use strict';

    class PortalDocumentRetrieval {
        constructor(container) {
            this.container = container;
            this.itemCounter = 0;
            this.containerOptions = [];
            this.documentOptions = [];
            this.init();
        }

        init() {
            this._parseOptions();
            this._setupEventHandlers();
            this._addRetrievalItem(); // Start with one item
            this._updatePricing();
            console.log('[PortalDocumentRetrieval] Initialized');
        }

        _parseOptions() {
            const form = this.container.querySelector('#retrieval-form');
            if (form) {
                try {
                    const containerOpts = form.dataset.containerOptions;
                    const documentOpts = form.dataset.documentOptions;
                    this.containerOptions = containerOpts ? JSON.parse(containerOpts) : [];
                    this.documentOptions = documentOpts ? JSON.parse(documentOpts) : [];
                } catch (e) {
                    console.warn('[PortalDocumentRetrieval] Failed to parse options JSON', e);
                }
            }
        }

        _setupEventHandlers() {
            // Use event delegation for dynamic elements
            this.container.addEventListener('change', (e) => {
                if (e.target.matches('#calc_priority, #calc_items')) {
                    this._updatePricing();
                } else if (e.target.matches('[data-retrieval-role="type-select"]')) {
                    this._onTypeChanged(e);
                } else if (e.target.matches('[data-retrieval-role="item-select"], input[data-retrieval-role], textarea[data-retrieval-role]')) {
                    this._updateItemsData();
                } else if (e.target.matches('#priority')) {
                    this._onPriorityMirror();
                }
            });

            this.container.addEventListener('click', (e) => {
                if (e.target.matches('[data-action="add-item"]') || e.target.closest('[data-action="add-item"]')) {
                    e.preventDefault();
                    this._addRetrievalItem();
                } else if (e.target.matches('[data-action="remove-item"]') || e.target.closest('[data-action="remove-item"]')) {
                    e.preventDefault();
                    const btn = e.target.closest('[data-action="remove-item"]');
                    const id = btn.dataset.itemId;
                    this._removeItem(id);
                }
            });
        }

        _onTypeChanged(e) {
            const id = e.target.dataset.itemId;
            this._populateItemOptions(id);
            this._updateItemsData();
        }

        _onPriorityMirror() {
            const priority = this.container.querySelector('#priority');
            const calcPriority = this.container.querySelector('#calc_priority');
            if (priority && calcPriority) {
                calcPriority.value = priority.value;
                this._updatePricing();
            }
        }

        _removeItem(id) {
            const item = this.container.querySelector(`#item-${id}`);
            if (item) {
                item.remove();
                this._updateItemsData();
                this._updateItemCount();
            }
        }

        _updatePricing() {
            const calcPriority = this.container.querySelector('#calc_priority');
            const calcItems = this.container.querySelector('#calc_items');
            
            const priority = calcPriority ? calcPriority.value : 'standard';
            const itemCount = calcItems ? parseInt(calcItems.value, 10) || 1 : 1;

            fetch('/my/document-retrieval/calculate-price', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { priority: priority, item_count: itemCount },
                    id: Math.floor(Math.random() * 1000000)
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.result) {
                    this._renderPricing(data.result);
                }
            })
            .catch(err => console.error('[PortalDocumentRetrieval] Pricing fetch failed', err));
        }

        _renderPricing(pricing) {
            const el = this.container.querySelector('#pricing-breakdown');
            if (!el) return;

            el.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <strong>Base Retrieval:</strong> $${pricing.base_retrieval_cost.toFixed(2)}<br/>
                        <strong>Priority (Items):</strong> $${pricing.priority_item_cost.toFixed(2)}
                    </div>
                    <div class="col-md-6">
                        <strong>Base Delivery:</strong> $${pricing.base_delivery_cost.toFixed(2)}<br/>
                        <strong>Priority (Order):</strong> $${pricing.priority_order_cost.toFixed(2)}
                    </div>
                </div>
                <hr/>
                <div class="text-center">
                    <h5><strong>Total: $${pricing.total_cost.toFixed(2)}</strong></h5>
                    ${pricing.has_custom_rates ? '<small class="text-success">Custom rates applied</small>' : ''}
                </div>
            `;
        }

        _addRetrievalItem() {
            this.itemCounter++;
            const id = this.itemCounter;
            const container = this.container.querySelector('#items-container');
            if (!container) return;

            const html = `
                <div class="border rounded p-3 mb-3 bg-light" id="item-${id}" data-item-id="${id}">
                    <div class="row">
                        <div class="col-md-3">
                            <label class="form-label">Item Type</label>
                            <select class="form-select" data-retrieval-role="type-select" data-item-id="${id}" id="type-${id}">
                                <option value="container">Container</option>
                                <option value="document">Document</option>
                                <option value="file">File</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Select Item</label>
                            <select class="form-select" data-retrieval-role="item-select" data-item-id="${id}" id="item-select-${id}">
                                <option value="">Select a container...</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Barcode</label>
                            <input type="text" class="form-control" data-retrieval-role="barcode" id="barcode-${id}" placeholder="Scan or enter barcode"/>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">&nbsp;</label>
                            <button type="button" class="btn btn-outline-danger w-100" data-action="remove-item" data-item-id="${id}">
                                <i class="fa fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-12">
                            <label class="form-label">Description</label>
                            <input type="text" class="form-control" data-retrieval-role="description" id="description-${id}" 
                                   placeholder="Describe the item to retrieve (optional)"/>
                        </div>
                    </div>
                </div>
            `;

            container.insertAdjacentHTML('beforeend', html);
            this._populateItemOptions(id);
            this._updateItemsData();
            this._updateItemCount();
        }

        _populateItemOptions(id) {
            const typeSelect = this.container.querySelector(`#type-${id}`);
            const itemSelect = this.container.querySelector(`#item-select-${id}`);
            if (!typeSelect || !itemSelect) return;

            const type = typeSelect.value;
            itemSelect.innerHTML = '';
            itemSelect.disabled = false;

            if (type === 'container') {
                itemSelect.innerHTML = '<option value="">Select a container...</option>';
                this.containerOptions.forEach(opt => {
                    itemSelect.innerHTML += `<option value="${opt[0]}">${this._escapeHtml(opt[1])}</option>`;
                });
            } else if (type === 'document') {
                itemSelect.innerHTML = '<option value="">Select a document...</option>';
                this.documentOptions.forEach(opt => {
                    itemSelect.innerHTML += `<option value="${opt[0]}">${this._escapeHtml(opt[1])}</option>`;
                });
            } else {
                itemSelect.innerHTML = '<option value="">Enter barcode manually</option>';
                itemSelect.disabled = true;
            }
        }

        _updateItemsData() {
            const items = [];
            const itemElements = this.container.querySelectorAll('#items-container [id^="item-"]');

            itemElements.forEach(el => {
                const id = el.dataset.itemId;
                const type = this.container.querySelector(`#type-${id}`)?.value || 'container';
                const itemSelectVal = this.container.querySelector(`#item-select-${id}`)?.value || '';
                const barcode = this.container.querySelector(`#barcode-${id}`)?.value || '';
                const description = this.container.querySelector(`#description-${id}`)?.value || '';

                if (description || barcode || itemSelectVal) {
                    const record = { type, barcode, description };
                    if (type === 'container' && itemSelectVal) {
                        record.container_id = itemSelectVal;
                    } else if (type === 'document' && itemSelectVal) {
                        record.document_id = itemSelectVal;
                    }
                    items.push(record);
                }
            });

            const itemsDataField = this.container.querySelector('#items-data');
            if (itemsDataField) {
                itemsDataField.value = JSON.stringify(items);
            }
        }

        _updateItemCount() {
            const count = this.container.querySelectorAll('#items-container [id^="item-"]').length;
            const calcItems = this.container.querySelector('#calc_items');
            if (calcItems) {
                calcItems.value = count;
                this._updatePricing();
            }
        }

        _escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }

    // ========================================================================
    // Auto-initialization
    // ========================================================================
    function initDocumentRetrieval() {
        const containers = document.querySelectorAll('.o_portal_document_retrieval');
        containers.forEach(container => {
            new PortalDocumentRetrieval(container);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDocumentRetrieval);
    } else {
        initDocumentRetrieval();
    }

    // Export globally
    window.PortalDocumentRetrieval = PortalDocumentRetrieval;

})();
