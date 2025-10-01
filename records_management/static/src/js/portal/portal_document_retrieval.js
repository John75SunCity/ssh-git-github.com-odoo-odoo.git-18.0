/**
 * Portal Document Retrieval Logic
 * Extracted from inline script in portal_document_retrieval.xml for compliance with
 * asset pipeline and security guidelines.
 */
odoo.define('records_management.portal_document_retrieval', function(require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    const RetrievalPortal = publicWidget.Widget.extend({
        selector: '.o_portal_document_retrieval',
        events: {
            'change #calc_priority': '_onPricingChanged',
            'change #calc_items': '_onPricingChanged',
            'click [data-action="add-item"]': '_onAddItem',
            'change [data-retrieval-role="type-select"]': '_onTypeChanged',
            'click [data-action="remove-item"]': '_onRemoveItem',
            'change [data-retrieval-role="item-select"], input[data-retrieval-role], textarea[data-retrieval-role]': '_onItemFieldChanged',
            'change #priority': '_onPriorityMirror',
        },

        start() {
            this.itemCounter = 0;
            // Load server-provided options from data attributes if present
            const $options = this.$('#retrieval-form');
            try {
                this.containerOptions = JSON.parse($options.data('container-options') || '[]');
                this.documentOptions = JSON.parse($options.data('document-options') || '[]');
            } catch (e) {
                console.warn('[RetrievalPortal] Failed to parse options JSON', e);
                this.containerOptions = [];
                this.documentOptions = [];
            }
            // Initialize default item and pricing
            this._addRetrievalItem();
            this._updatePricing();
            return this._super.apply(this, arguments);
        },

        // Event Handlers
        _onPricingChanged() {
            this._updatePricing();
        },
        _onAddItem(ev) {
            ev.preventDefault();
            this._addRetrievalItem();
        },
        _onTypeChanged(ev) {
            const $select = $(ev.currentTarget);
            const id = $select.data('item-id');
            this._populateItemOptions(id);
            this._updateItemsData();
        },
        _onRemoveItem(ev) {
            ev.preventDefault();
            const id = $(ev.currentTarget).data('item-id');
            this.$(`#item-${id}`).remove();
            this._updateItemsData();
        },
        _onItemFieldChanged() {
            this._updateItemsData();
        },
        _onPriorityMirror() {
            const val = this.$('#priority').val();
            this.$('#calc_priority').val(val);
            this._updatePricing();
        },

        // Core Logic
        _updatePricing() {
            const priority = this.$('#calc_priority').val();
            const itemCount = parseInt(this.$('#calc_items').val(), 10) || 1;
            fetch('/my/document-retrieval/calculate-price', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { priority: priority, item_count: itemCount }
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.result) {
                    this._renderPricing(data.result);
                }
            })
            .catch(err => console.error('[RetrievalPortal] Pricing fetch failed', err));
        },

        _renderPricing(pricing) {
            const el = this.$('#pricing-breakdown');
            if (!el.length) { return; }
            const html = `
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
                </div>`;
            el.html(html);
        },

        _addRetrievalItem() {
            this.itemCounter += 1;
            const id = this.itemCounter;
            const $container = this.$('#items-container');
            const html = `
                <div class="border p-3 mb-3" id="item-${id}" data-item-id="${id}">
                    <div class="row">
                        <div class="col-md-3">
                            <label>Item Type:</label>
                            <select class="form-control" data-retrieval-role="type-select" data-item-id="${id}" id="type-${id}">
                                <option value="container">Container</option>
                                <option value="document">Document</option>
                                <option value="file">File</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label>Select Item:</label>
                            <select class="form-control" data-retrieval-role="item-select" data-item-id="${id}" id="item-select-${id}">
                                <option value="">Select a container...</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label>Barcode:</label>
                            <input type="text" class="form-control" data-retrieval-role="barcode" id="barcode-${id}" placeholder="Item barcode"/>
                        </div>
                        <div class="col-md-2">
                            <label>&nbsp;</label>
                            <button type="button" class="btn btn-danger btn-sm form-control" data-action="remove-item" data-item-id="${id}">
                                <i class="fa fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-12">
                            <label>Description:</label>
                            <input type="text" class="form-control" data-retrieval-role="description" id="description-${id}" placeholder="Describe the item to retrieve"/>
                        </div>
                    </div>
                </div>`;
            $container.append(html);
            this._populateItemOptions(id);
            this._updateItemsData();
        },

        _populateItemOptions(id) {
            const type = this.$(`#type-${id}`).val();
            const $select = this.$(`#item-select-${id}`);
            $select.prop('disabled', false);
            $select.empty();
            if (type === 'container') {
                $select.append('<option value="">Select a container...</option>');
                this.containerOptions.forEach(opt => {
                    $select.append(`<option value="${opt[0]}">${_.escape(opt[1])}</option>`);
                });
            } else if (type === 'document') {
                $select.append('<option value="">Select a document...</option>');
                this.documentOptions.forEach(opt => {
                    $select.append(`<option value="${opt[0]}">${_.escape(opt[1])}</option>`);
                });
            } else { // file
                $select.append('<option value="">Not applicable</option>');
                $select.prop('disabled', true);
            }
        },

        _updateItemsData() {
            const items = [];
            this.$('#items-container [id^="item-"]').each((idx, el) => {
                const id = $(el).data('item-id');
                const type = this.$(`#type-${id}`).val();
                const itemSelectVal = this.$(`#item-select-${id}`).val();
                const barcode = this.$(`#barcode-${id}`).val();
                const description = this.$(`#description-${id}`).val();
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
            this.$('#items-data').val(JSON.stringify(items));
        },
    });

    publicWidget.registry.RetrievalPortal = RetrievalPortal;
    return RetrievalPortal;
});
