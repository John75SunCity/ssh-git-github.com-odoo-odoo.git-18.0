/** @odoo-module **/
/**
 * Barcode Command Handler - Portal Barcode Scanner
 *
 * Handles barcode scanning with:
 * - Auto-submit after scan delay
 * - Standard Odoo command processing (O-CMD.*, O-BTN.*)
 * - Multi-scan queuing for batch operations
 * - Real-time feedback and notifications
 *
 * @author Records Management Module
 * @version 18.0.1.0.4
 */

import { jsonrpc } from "@web/core/network/rpc_service";

// Configuration
const BARCODE_SCAN_DELAY = 300; // ms delay after last keypress to auto-submit
const STANDARD_COMMANDS = [
    'O-CMD.MAIN-MENU',
    'O-BTN.validate',
    'O-BTN.discard',
    'O-BTN.cancel',
    'O-CMD.PRINT',
    'O-CMD.PACKING',
    'O-BTN.scrap',
    'O-CMD.RETURN',
];

class BarcodeScannerHandler {
    constructor() {
        this.scanTimeout = null;
        this.scannedItems = [];
        this.init();
    }

    /**
     * Initialize event handlers
     */
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventHandlers());
        } else {
            this.setupEventHandlers();
        }
    }

    /**
     * Setup all event handlers
     */
    setupEventHandlers() {
        const form = document.getElementById('barcode_scan_form');
        const input = document.getElementById('barcode_input');
        const clearBtn = document.getElementById('clear_scanned_items');
        const submitBtn = document.getElementById('submit_scanned_items');

        if (!form || !input) {
            return; // Not on barcode scanner page
        }

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.processBarcode();
        });

        // Auto-submit after scan delay
        input.addEventListener('keyup', (e) => {
            clearTimeout(this.scanTimeout);

            // Ignore if Enter key (form will submit)
            if (e.key === 'Enter') {
                return;
            }

            // Auto-submit after delay (simulates barcode scanner behavior)
            this.scanTimeout = setTimeout(() => {
                if (input.value.trim()) {
                    this.processBarcode();
                }
            }, BARCODE_SCAN_DELAY);
        });

        // Clear scanned items
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearScannedItems());
        }

        // Submit batch request
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitBatchRequest());
        }

        // Keep focus on input
        input.focus();
        document.addEventListener('click', () => {
            if (document.activeElement !== input) {
                input.focus();
            }
        });
    }

    /**
     * Process scanned barcode
     */
    async processBarcode() {
        const input = document.getElementById('barcode_input');
        const operation = document.querySelector('input[name="operation"]').value;
        const endpoint = document.querySelector('input[name="endpoint"]').value;
        const barcode = input.value.trim();

        if (!barcode) {
            return;
        }

        // Hide previous messages
        this.hideMessages();

        // Handle standard Odoo commands
        if (this.isStandardCommand(barcode)) {
            await this.handleStandardCommand(barcode);
            input.value = '';
            input.focus();
            return;
        }

        // Process container barcode via JSON-RPC
        try {
            const result = await jsonrpc(endpoint.replace('/process/', '/my/barcode/process/'), {
                operation: operation,
                barcode: barcode,
            });

            if (result.error) {
                this.showError(result.error);
            } else if (result.redirect) {
                window.location.href = result.redirect;
                return;
            } else if (result.success) {
                this.handleSuccess(result, operation);
            } else if (result.info) {
                this.showInfo(result.info);
            }

            input.value = '';
            input.focus();

        } catch (error) {
            console.error('Barcode processing error:', error);
            this.showError('Error processing barcode. Please try again.');
            input.value = '';
            input.focus();
        }
    }

    /**
     * Check if barcode is a standard Odoo command
     */
    isStandardCommand(barcode) {
        return STANDARD_COMMANDS.includes(barcode);
    }

    /**
     * Handle standard Odoo command
     */
    async handleStandardCommand(command) {
        switch (command) {
            case 'O-CMD.MAIN-MENU':
                window.location.href = '/my/barcode/main';
                break;

            case 'O-BTN.validate':
                if (this.scannedItems.length === 0) {
                    this.showError('No items to validate. Please scan containers first.');
                } else {
                    // Trigger batch submission for current operation
                    await this.submitBatchRequest();
                }
                break;

            case 'O-BTN.discard':
            case 'O-BTN.cancel':
                if (confirm('Are you sure you want to discard the current operation?')) {
                    this.clearScannedItems();
                    this.showInfo('Operation cancelled.');
                }
                break;

            case 'O-CMD.PRINT':
                this.showInfo('PRINT command recognized. Please scan a container to print its movement slip.');
                break;

            case 'O-CMD.PACKING':
                this.showInfo('PACKING command recognized. Please scan a container to print delivery slip.');
                break;

            case 'O-BTN.scrap':
                this.showInfo('SCRAP command recognized. Please scan a container to queue for shredding.');
                break;

            case 'O-CMD.RETURN':
                this.showInfo('RETURN command recognized. Please scan a container to request retrieval.');
                break;

            default:
                this.showInfo(`Command ${command} recognized but not yet implemented.`);
        }
    }

    /**
     * Handle successful scan
     */
    handleSuccess(result, operation) {
        if (operation === 'container') {
            // Direct container view - redirect handled by JSON response
            return;
        }

        // For batch operations (pickup, retrieval), add to queue
        if (['pickup', 'retrieval'].includes(operation) && result.container) {
            this.addToScannedItems(result.container);
            this.showInfo(result.message || `Container ${result.container.name} added successfully`);
        }
    }

    /**
     * Add container to scanned items queue
     */
    addToScannedItems(container) {
        // Check if already scanned
        if (this.scannedItems.find(item => item.id === container.id)) {
            this.showInfo(`Container ${container.name} already scanned`);
            return;
        }

        this.scannedItems.push(container);
        this.updateScannedItemsDisplay();
    }

    /**
     * Update scanned items display
     */
    updateScannedItemsDisplay() {
        const listElement = document.getElementById('scanned_items_list');
        const countElement = document.getElementById('scanned_count');
        const actionsElement = document.getElementById('scanned_actions');

        if (!listElement) return;

        countElement.textContent = this.scannedItems.length;

        if (this.scannedItems.length === 0) {
            listElement.innerHTML = `
                <div class="text-muted text-center py-4">
                    <i class="fa fa-qrcode fa-3x mb-3 opacity-25"></i>
                    <p>No items scanned yet. Start scanning containers...</p>
                </div>
            `;
            actionsElement.style.display = 'none';
        } else {
            listElement.innerHTML = this.scannedItems.map((item, index) => `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${item.name}</strong>
                        <small class="text-muted d-block">${item.barcode || 'No barcode'}</small>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="barcodeScannerHandler.removeScannedItem(${index})">
                        <i class="fa fa-times"></i>
                    </button>
                </div>
            `).join('');
            actionsElement.style.display = 'block';
        }
    }

    /**
     * Remove item from scanned queue
     */
    removeScannedItem(index) {
        this.scannedItems.splice(index, 1);
        this.updateScannedItemsDisplay();
    }

    /**
     * Clear all scanned items
     */
    clearScannedItems() {
        this.scannedItems = [];
        this.updateScannedItemsDisplay();
    }

    /**
     * Submit batch request with scanned items
     */
    async submitBatchRequest() {
        if (this.scannedItems.length === 0) {
            this.showError('No items scanned. Please scan containers first.');
            return;
        }

        const operation = document.querySelector('input[name="operation"]').value;
        const containerIds = this.scannedItems.map(item => item.id);

        this.showInfo(`Processing ${this.scannedItems.length} containers...`);

        try {
            // Submit batch request via JSON-RPC
            const result = await jsonrpc('/my/barcode/batch_request', {
                operation: operation,
                container_ids: containerIds,
            });

            if (result.error) {
                this.showError(result.error);
            } else if (result.success) {
                // Show success message
                this.showInfo(result.message || `Successfully created ${operation} request for ${containerIds.length} containers`);
                
                // Clear scanned items
                this.clearScannedItems();
                
                // Redirect to request details if provided
                if (result.redirect) {
                    setTimeout(() => {
                        window.location.href = result.redirect;
                    }, 1500);
                } else if (result.request_id) {
                    // Default redirect to request view
                    setTimeout(() => {
                        window.location.href = `/my/requests/${result.request_id}`;
                    }, 1500);
                }
            } else {
                this.showError('Unexpected response from server. Please try again.');
            }
        } catch (error) {
            console.error('Batch submission error:', error);
            this.showError('Error creating request. Please try again or contact support.');
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const errorDiv = document.getElementById('scan_error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('d-none');
            setTimeout(() => errorDiv.classList.add('d-none'), 5000);
        }
    }

    /**
     * Show info message
     */
    showInfo(message) {
        const infoDiv = document.getElementById('scan_info');
        if (infoDiv) {
            infoDiv.textContent = message;
            infoDiv.classList.remove('d-none');
            setTimeout(() => infoDiv.classList.add('d-none'), 3000);
        }
    }

    /**
     * Hide all messages
     */
    hideMessages() {
        document.getElementById('scan_error')?.classList.add('d-none');
        document.getElementById('scan_info')?.classList.add('d-none');
        document.getElementById('scan_results')?.classList.add('d-none');
    }
}

// Initialize on page load
const barcodeScannerHandler = new BarcodeScannerHandler();

// Export for global access (needed for onclick handlers)
window.barcodeScannerHandler = barcodeScannerHandler;

export default BarcodeScannerHandler;
