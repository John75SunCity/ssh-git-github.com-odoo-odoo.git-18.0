/** @odoo-module **/

import { registry } from "@web/core/registry";
import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Portal Interactive Features
 * Enhanced UI/UX with AJAX, filtering, and mobile optimizations
 * Based on Grok recommendations for Records Management portal
 */

publicWidget.registry.PortalInventory = publicWidget.Widget.extend({
    selector: '.o_portal_inventory',
    events: {
        'submit .filter-bar form': '_onFilterSubmit',
        'click .pagination a': '_onPaginationClick',
        'input .search-input': '_onSearchInput',
        'click .btn-export': '_onExportClick',
    },

    /**
     * Initialize widget
     */
    start: function () {
        this._super.apply(this, arguments);
        this._setupMobileView();
        this._initializeTooltips();
    },

    /**
     * Handle filter form submission with AJAX
     */
    _onFilterSubmit: function (ev) {
        ev.preventDefault();
        const $form = $(ev.currentTarget);
        const formData = $form.serialize();
        
        this._showLoading();
        
        $.ajax({
            url: window.location.pathname,
            type: 'GET',
            data: formData,
            success: (data) => {
                this._updateTableContent(data);
                this._hideLoading();
            },
            error: () => {
                this._hideLoading();
                this._showError('Failed to load data. Please try again.');
            }
        });
    },

    /**
     * Handle pagination clicks with AJAX
     */
    _onPaginationClick: function (ev) {
        ev.preventDefault();
        const $link = $(ev.currentTarget);
        const url = $link.attr('href');
        
        if (!url || url === '#') return;
        
        this._showLoading();
        
        $.get(url, (data) => {
            this._updateTableContent(data);
            this._hideLoading();
            window.scrollTo(0, 0);
        });
    },

    /**
     * Live search with debouncing
     */
    _onSearchInput: _.debounce(function (ev) {
        const searchTerm = $(ev.currentTarget).val();
        
        if (searchTerm.length < 3 && searchTerm.length > 0) {
            return; // Wait for at least 3 characters
        }
        
        this._showLoading();
        
        $.ajax({
            url: window.location.pathname,
            type: 'GET',
            data: { search: searchTerm },
            success: (data) => {
                this._updateTableContent(data);
                this._hideLoading();
            }
        });
    }, 500),

    /**
     * Handle export button click
     */
    _onExportClick: function (ev) {
        ev.preventDefault();
        const format = $(ev.currentTarget).data('format') || 'xlsx';
        
        // Show download notification
        this._showNotification('Preparing download...', 'info');
        
        // Trigger download
        window.location.href = `${window.location.pathname}/export?format=${format}`;
    },

    /**
     * Show loading spinner
     */
    _showLoading: function () {
        $('#loading').removeClass('d-none');
        $('.o_portal_content').css('opacity', '0.5');
    },

    /**
     * Hide loading spinner
     */
    _hideLoading: function () {
        $('#loading').addClass('d-none');
        $('.o_portal_content').css('opacity', '1');
    },

    /**
     * Update table content from AJAX response
     */
    _updateTableContent: function (data) {
        const $container = $('.table-responsive');
        const $newContent = $(data).find('.table-responsive');
        
        if ($newContent.length) {
            $container.html($newContent.html());
        }
        
        // Update pagination
        const $pagination = $('.pagination');
        const $newPagination = $(data).find('.pagination');
        if ($newPagination.length) {
            $pagination.html($newPagination.html());
        }
    },

    /**
     * Setup mobile view detection and adjustments
     */
    _setupMobileView: function () {
        if (window.innerWidth <= 768) {
            this._convertTableToCards();
        }
        
        // Handle window resize
        $(window).on('resize', _.debounce(() => {
            if (window.innerWidth <= 768) {
                this._convertTableToCards();
            } else {
                this._convertCardsToTable();
            }
        }, 300));
    },

    /**
     * Convert table to card view for mobile
     */
    _convertTableToCards: function () {
        const $table = $('.table');
        if ($table.length && !$table.hasClass('converted-to-cards')) {
            $table.addClass('converted-to-cards mobile-card-view');
            // Card conversion logic here
        }
    },

    /**
     * Convert cards back to table for desktop
     */
    _convertCardsToTable: function () {
        const $table = $('.table');
        if ($table.hasClass('converted-to-cards')) {
            $table.removeClass('converted-to-cards mobile-card-view');
        }
    },

    /**
     * Initialize Bootstrap tooltips
     */
    _initializeTooltips: function () {
        $('[data-bs-toggle="tooltip"]').tooltip();
    },

    /**
     * Show notification toast
     */
    _showNotification: function (message, type) {
        type = type || 'info';
        const toast = `
            <div class="toast align-items-center text-white bg-${type} border-0 position-fixed top-0 end-0 m-3" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        $('body').append(toast);
        const $toast = $('.toast').last();
        new bootstrap.Toast($toast[0]).show();
        
        setTimeout(() => $toast.remove(), 5000);
    },

    /**
     * Show error message
     */
    _showError: function (message) {
        this._showNotification(message, 'danger');
    },
});

/**
 * Document Retrieval Wizard
 * Multi-step form with validation
 */
publicWidget.registry.PortalDocumentRetrieval = publicWidget.Widget.extend({
    selector: '.document-retrieval-wizard',
    events: {
        'click .btn-next-step': '_onNextStep',
        'click .btn-prev-step': '_onPrevStep',
        'submit form': '_onSubmitForm',
        'change .container-select': '_onContainerChange',
    },

    start: function () {
        this._super.apply(this, arguments);
        this.currentStep = 1;
        this.totalSteps = $('.wizard-step').length;
        this._updateStepIndicator();
    },

    _onNextStep: function (ev) {
        ev.preventDefault();
        
        if (this._validateCurrentStep()) {
            this.currentStep++;
            this._showStep(this.currentStep);
            this._updateStepIndicator();
        }
    },

    _onPrevStep: function (ev) {
        ev.preventDefault();
        this.currentStep--;
        this._showStep(this.currentStep);
        this._updateStepIndicator();
    },

    _showStep: function (step) {
        $('.wizard-step').addClass('d-none');
        $(`.wizard-step[data-step="${step}"]`).removeClass('d-none');
    },

    _updateStepIndicator: function () {
        $('.step-indicator .step').each((index, el) => {
            const stepNum = index + 1;
            if (stepNum < this.currentStep) {
                $(el).addClass('completed').removeClass('active');
            } else if (stepNum === this.currentStep) {
                $(el).addClass('active').removeClass('completed');
            } else {
                $(el).removeClass('active completed');
            }
        });
    },

    _validateCurrentStep: function () {
        const $currentStep = $(`.wizard-step[data-step="${this.currentStep}"]`);
        const $requiredInputs = $currentStep.find('[required]');
        let isValid = true;
        
        $requiredInputs.each(function () {
            if (!$(this).val()) {
                $(this).addClass('is-invalid');
                isValid = false;
            } else {
                $(this).removeClass('is-invalid');
            }
        });
        
        return isValid;
    },

    _onContainerChange: function (ev) {
        const selectedContainers = $(ev.currentTarget).val();
        this._calculatePrice(selectedContainers);
    },

    _calculatePrice: function (containerIds) {
        if (!containerIds || containerIds.length === 0) {
            $('.price-display').html('$0.00');
            return;
        }
        
        $.ajax({
            url: '/my/document-retrieval/calculate-price',
            type: 'POST',
            data: JSON.stringify({ container_ids: containerIds }),
            contentType: 'application/json',
            success: (data) => {
                $('.price-display').html(`$${data.total_price.toFixed(2)}`);
            }
        });
    },

    _onSubmitForm: function (ev) {
        if (!this._validateCurrentStep()) {
            ev.preventDefault();
            return false;
        }
    },
});

/**
 * Barcode Scanner Integration
 */
publicWidget.registry.PortalBarcodeScanner = publicWidget.Widget.extend({
    selector: '.barcode-scanner',
    events: {
        'click .btn-scan': '_onStartScan',
        'input .barcode-input': '_onBarcodeInput',
    },

    _onStartScan: function (ev) {
        ev.preventDefault();
        // Integration with device camera or barcode scanner
        this._showNotification('Please scan barcode...', 'info');
    },

    _onBarcodeInput: _.debounce(function (ev) {
        const barcode = $(ev.currentTarget).val();
        
        if (barcode.length >= 8) {
            this._processBarcode(barcode);
        }
    }, 500),

    _processBarcode: function (barcode) {
        const scanType = $('.barcode-scanner').data('scan-type') || 'container';
        
        $.ajax({
            url: `/my/barcode/process/${scanType}`,
            type: 'POST',
            data: JSON.stringify({ barcode: barcode }),
            contentType: 'application/json',
            success: (data) => {
                if (data.success) {
                    this._displayScanResult(data.record);
                } else {
                    this._showError(data.message || 'Barcode not found');
                }
            }
        });
    },

    _displayScanResult: function (record) {
        $('.scan-result').html(`
            <div class="alert alert-success">
                <h5>${record.name}</h5>
                <p>${record.details}</p>
            </div>
        `);
    },

    _showNotification: function (message, type) {
        // Reuse notification method from PortalInventory
        publicWidget.registry.PortalInventory.prototype._showNotification.call(this, message, type);
    },

    _showError: function (message) {
        this._showNotification(message, 'danger');
    },
});

export default publicWidget.registry;
