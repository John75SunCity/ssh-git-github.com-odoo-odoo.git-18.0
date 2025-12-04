/**
 * Portal Interactive Features - Modernized Vanilla JS (Odoo 18+)
 * Enhanced UI/UX with AJAX, filtering, mobile optimizations, and barcode scanning
 *
 * FEATURES:
 * ✨ AJAX pagination - No page reloads
 * 🔍 Live search with debouncing
 * 📱 Mobile responsive - Auto-converts tables to cards
 * 🧙 Multi-step wizards - Document retrieval with validation
 * 📊 Real-time price calculation
 * 📷 Barcode scanner integration
 * 🔔 Toast notifications
 *
 * MODERNIZED: Converted from jQuery/AMD to vanilla JS IIFE for Odoo 18+ compatibility
 * NO DEPENDENCIES: Pure vanilla JavaScript, Bootstrap 5 optional
 */
(function () {
    'use strict';

    // ============================================================================
    // UTILITY FUNCTIONS
    // ============================================================================

    /**
     * Debounce function for rate-limiting
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Simple HTTP GET request
     */
    function httpGet(url, callback, errorCallback) {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    callback(xhr.responseText);
                } else if (errorCallback) {
                    errorCallback(xhr.status, xhr.statusText);
                }
            }
        };
        xhr.send();
    }

    /**
     * JSON RPC call (for Odoo endpoints)
     */
    function jsonRpc(url, method, params) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', url, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            const csrfToken = document.querySelector('input[name="csrf_token"]');
            if (csrfToken) {
                xhr.setRequestHeader('X-CSRFToken', csrfToken.value);
            }
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            if (response.result) {
                                resolve(response.result);
                            } else if (response.error) {
                                reject(response.error);
                            } else {
                                resolve(response);
                            }
                        } catch (e) {
                            reject(e);
                        }
                    } else {
                        reject(new Error(xhr.statusText));
                    }
                }
            };
            xhr.send(JSON.stringify({
                jsonrpc: '2.0',
                method: method,
                params: params,
                id: Math.floor(Math.random() * 1000000)
            }));
        });
    }

    /**
     * Serialize form data to URL query string
     */
    function serializeForm(form) {
        const formData = new FormData(form);
        const params = new URLSearchParams();
        formData.forEach((value, key) => {
            params.append(key, value);
        });
        return params.toString();
    }

    // ============================================================================
    // PORTAL INVENTORY WIDGET
    // ============================================================================

    const PortalInventory = {
        init: function () {
            const container = document.querySelector('.o_portal_inventory');
            if (!container) return;

            this.container = container;
            this._bindEvents();
            this._setupMobileView();
            this._initializeTooltips();
        },

        _bindEvents: function () {
            // Filter form submission
            const filterForm = this.container.querySelector('.filter-bar form');
            if (filterForm) {
                filterForm.addEventListener('submit', this._onFilterSubmit.bind(this));
            }

            // Pagination clicks
            this.container.addEventListener('click', (ev) => {
                const paginationLink = ev.target.closest('.pagination a');
                if (paginationLink) {
                    this._onPaginationClick(ev, paginationLink);
                }
            });

            // Live search
            const searchInput = this.container.querySelector('.search-input');
            if (searchInput) {
                searchInput.addEventListener('input', debounce(this._onSearchInput.bind(this), 500));
            }

            // Export button
            const exportBtn = this.container.querySelector('.btn-export');
            if (exportBtn) {
                exportBtn.addEventListener('click', this._onExportClick.bind(this));
            }
        },

        _onFilterSubmit: function (ev) {
            ev.preventDefault();
            const form = ev.target;
            const formData = serializeForm(form);

            this._showLoading();

            httpGet(
                window.location.pathname + '?' + formData,
                (data) => {
                    this._updateTableContent(data);
                    this._hideLoading();
                },
                () => {
                    this._hideLoading();
                    this._showError('Failed to load data. Please try again.');
                }
            );
        },

        _onPaginationClick: function (ev, link) {
            ev.preventDefault();
            const url = link.getAttribute('href');

            if (!url || url === '#') return;

            this._showLoading();

            httpGet(url, (data) => {
                this._updateTableContent(data);
                this._hideLoading();
                window.scrollTo(0, 0);
            });
        },

        _onSearchInput: function (ev) {
            const searchTerm = ev.target.value;

            if (searchTerm.length < 3 && searchTerm.length > 0) {
                return; // Wait for at least 3 characters
            }

            this._showLoading();

            httpGet(
                window.location.pathname + '?search=' + encodeURIComponent(searchTerm),
                (data) => {
                    this._updateTableContent(data);
                    this._hideLoading();
                }
            );
        },

        _onExportClick: function (ev) {
            ev.preventDefault();
            const format = ev.target.dataset.format || 'xlsx';

            this._showNotification('Preparing download...', 'info');

            window.location.href = window.location.pathname + '/export?format=' + format;
        },

        _showLoading: function () {
            let overlay = document.getElementById('portal-loading-overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'portal-loading-overlay';
                overlay.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
                overlay.style.cssText = 'background: rgba(0,0,0,0.3); z-index: 9999;';
                overlay.innerHTML = `
                    <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                `;
                document.body.appendChild(overlay);
            } else {
                overlay.classList.remove('d-none');
            }

            const content = document.querySelector('.o_portal_content');
            if (content) content.style.opacity = '0.5';
        },

        _hideLoading: function () {
            const overlay = document.getElementById('portal-loading-overlay');
            if (overlay) overlay.classList.add('d-none');

            const content = document.querySelector('.o_portal_content');
            if (content) content.style.opacity = '1';
        },

        _updateTableContent: function (htmlData) {
            // Parse the HTML response
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlData, 'text/html');

            // Update table content
            const container = document.querySelector('.table-responsive');
            const newContent = doc.querySelector('.table-responsive');
            if (container && newContent) {
                container.innerHTML = newContent.innerHTML;
            }

            // Update pagination
            const pagination = document.querySelector('.pagination');
            const newPagination = doc.querySelector('.pagination');
            if (pagination && newPagination) {
                pagination.innerHTML = newPagination.innerHTML;
            }
        },

        _setupMobileView: function () {
            if (window.innerWidth <= 768) {
                this._convertTableToCards();
            }

            window.addEventListener('resize', debounce(() => {
                if (window.innerWidth <= 768) {
                    this._convertTableToCards();
                } else {
                    this._convertCardsToTable();
                }
            }, 300));
        },

        _convertTableToCards: function () {
            const table = document.querySelector('.table');
            if (table && !table.classList.contains('converted-to-cards')) {
                table.classList.add('converted-to-cards', 'mobile-card-view');
                table.querySelectorAll('tbody tr').forEach(row => {
                    row.classList.add('card', 'mb-2', 'p-2');
                });
            }
        },

        _convertCardsToTable: function () {
            const table = document.querySelector('.table');
            if (table && table.classList.contains('converted-to-cards')) {
                table.classList.remove('converted-to-cards', 'mobile-card-view');
                table.querySelectorAll('tbody tr').forEach(row => {
                    row.classList.remove('card', 'mb-2', 'p-2');
                });
            }
        },

        _initializeTooltips: function () {
            if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
                    new bootstrap.Tooltip(el);
                });
            }
        },

        _showNotification: function (message, type) {
            type = type || 'info';
            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed top-0 end-0 m-3`;
            toast.setAttribute('role', 'alert');
            toast.style.zIndex = '10000';
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;

            document.body.appendChild(toast);

            if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
                new bootstrap.Toast(toast).show();
            } else {
                toast.style.display = 'block';
            }

            setTimeout(() => toast.remove(), 5000);
        },

        _showError: function (message) {
            this._showNotification(message, 'danger');
        }
    };

    // ============================================================================
    // DOCUMENT RETRIEVAL WIZARD
    // ============================================================================

    const PortalDocumentRetrieval = {
        init: function () {
            const wizard = document.querySelector('.document-retrieval-wizard');
            if (!wizard) return;

            this.wizard = wizard;
            this.currentStep = 1;
            this.totalSteps = wizard.querySelectorAll('.wizard-step').length;

            this._bindEvents();
            this._updateStepIndicator();
        },

        _bindEvents: function () {
            // Next step buttons
            this.wizard.querySelectorAll('.btn-next-step').forEach(btn => {
                btn.addEventListener('click', this._onNextStep.bind(this));
            });

            // Previous step buttons
            this.wizard.querySelectorAll('.btn-prev-step').forEach(btn => {
                btn.addEventListener('click', this._onPrevStep.bind(this));
            });

            // Container selection change
            const containerSelect = this.wizard.querySelector('.container-select');
            if (containerSelect) {
                containerSelect.addEventListener('change', this._onContainerChange.bind(this));
            }

            // Form submission
            const form = this.wizard.querySelector('form');
            if (form) {
                form.addEventListener('submit', this._onSubmitForm.bind(this));
            }
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
            this.wizard.querySelectorAll('.wizard-step').forEach(el => {
                el.classList.add('d-none');
            });
            const targetStep = this.wizard.querySelector(`.wizard-step[data-step="${step}"]`);
            if (targetStep) {
                targetStep.classList.remove('d-none');
            }
        },

        _updateStepIndicator: function () {
            const steps = this.wizard.querySelectorAll('.step-indicator .step');
            steps.forEach((el, index) => {
                const stepNum = index + 1;
                if (stepNum < this.currentStep) {
                    el.classList.add('completed');
                    el.classList.remove('active');
                } else if (stepNum === this.currentStep) {
                    el.classList.add('active');
                    el.classList.remove('completed');
                } else {
                    el.classList.remove('active', 'completed');
                }
            });
        },

        _validateCurrentStep: function () {
            const currentStep = this.wizard.querySelector(`.wizard-step[data-step="${this.currentStep}"]`);
            if (!currentStep) return true;

            const requiredInputs = currentStep.querySelectorAll('[required]');
            let isValid = true;

            requiredInputs.forEach(input => {
                if (!input.value) {
                    input.classList.add('is-invalid');
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });

            return isValid;
        },

        _onContainerChange: function (ev) {
            const selectedOptions = Array.from(ev.target.selectedOptions).map(opt => opt.value);
            this._calculatePrice(selectedOptions);
        },

        _calculatePrice: function (containerIds) {
            const priceDisplay = document.querySelector('.price-display');
            if (!priceDisplay) return;

            if (!containerIds || containerIds.length === 0) {
                priceDisplay.textContent = '$0.00';
                return;
            }

            jsonRpc('/my/document-retrieval/calculate-price', 'call', {
                container_ids: containerIds
            }).then(data => {
                priceDisplay.textContent = '$' + data.total_price.toFixed(2);
            }).catch(() => {
                priceDisplay.textContent = '$0.00';
            });
        },

        _onSubmitForm: function (ev) {
            if (!this._validateCurrentStep()) {
                ev.preventDefault();
                return false;
            }
        }
    };

    // ============================================================================
    // BARCODE SCANNER
    // ============================================================================

    const PortalBarcodeScanner = {
        init: function () {
            const scanner = document.querySelector('.barcode-scanner');
            if (!scanner) return;

            this.scanner = scanner;
            this._bindEvents();
        },

        _bindEvents: function () {
            const scanBtn = this.scanner.querySelector('.btn-scan');
            if (scanBtn) {
                scanBtn.addEventListener('click', this._onStartScan.bind(this));
            }

            const barcodeInput = this.scanner.querySelector('.barcode-input');
            if (barcodeInput) {
                barcodeInput.addEventListener('input', debounce(this._onBarcodeInput.bind(this), 500));
            }
        },

        _onStartScan: function (ev) {
            ev.preventDefault();
            PortalInventory._showNotification('Please scan barcode or enter manually...', 'info');

            const input = this.scanner.querySelector('.barcode-input');
            if (input) input.focus();
        },

        _onBarcodeInput: function (ev) {
            const barcode = ev.target.value;

            if (barcode.length >= 8) {
                this._processBarcode(barcode);
            }
        },

        _processBarcode: function (barcode) {
            const scanType = this.scanner.dataset.scanType || 'container';

            jsonRpc('/my/barcode/process/' + scanType, 'call', {
                barcode: barcode
            }).then(data => {
                if (data.success) {
                    this._displayScanResult(data.record);
                } else {
                    PortalInventory._showNotification(data.message || 'Barcode not found', 'danger');
                }
            }).catch(() => {
                PortalInventory._showNotification('Error processing barcode. Please try again.', 'danger');
            });
        },

        _displayScanResult: function (record) {
            const resultContainer = this.scanner.querySelector('.scan-result');
            if (!resultContainer) return;

            resultContainer.innerHTML = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <h5 class="alert-heading">${record.name}</h5>
                    <p class="mb-0">${record.details || 'No additional details'}</p>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;

            // Clear input for next scan
            const input = this.scanner.querySelector('.barcode-input');
            if (input) input.value = '';
        }
    };

    // ============================================================================
    // INITIALIZATION
    // ============================================================================

    function initPortalFeatures() {
        PortalInventory.init();
        PortalDocumentRetrieval.init();
        PortalBarcodeScanner.init();
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPortalFeatures);
    } else {
        initPortalFeatures();
    }

    // Export for global access if needed
    window.PortalInventory = PortalInventory;
    window.PortalDocumentRetrieval = PortalDocumentRetrieval;
    window.PortalBarcodeScanner = PortalBarcodeScanner;

})();
