/**
 * Records Management Portal - Camera Barcode Scanner
 *
 * PURPOSE: Customer-facing camera barcode scanning for portal pages
 * USE CASE: Scan containers/files to add to pickup requests, retrievals, etc.
 *
 * FEATURES:
 * ✓ Scanbot SDK integration for reliable barcode scanning
 * ✓ Works on mobile and desktop browsers
 * ✓ Adds scanned items to selection lists
 * ✓ Visual feedback with notifications
 * ✓ Continuous scanning mode
 *
 * DEPENDENCIES: Scanbot Web SDK (loaded dynamically from CDN)
 */
(function () {
    'use strict';

    // Scanbot SDK Configuration
    const SCANBOT_SDK_URL = "https://cdn.jsdelivr.net/npm/scanbot-web-sdk@7.0.0/bundle/ScanbotSDK.ui2.min.js";
    const SCANBOT_ENGINE_PATH = "https://cdn.jsdelivr.net/npm/scanbot-web-sdk@7.0.0/bundle/bin/complete/";
    
    // License key (same as backend scanner)
    const SCANBOT_LICENSE_KEY = 
        "E14q8BxTk+CB7vhOEh57o8N/OsEZlL" +
        "urbsbppjJ5R4AkUbFYKvgj4hNrdf7L" +
        "vpF8tKy/NZoB6wBu1QTRPw4t5Ul4uR" +
        "rkTf8H5vd1DPmItpSNji60EGOmtAz+" +
        "uoCnT2MmM0Q2CoJLi9WEZyoUkPsHmc" +
        "hrHmWvar3K4ym1APhzkKOGLi8MJxBt" +
        "+Po7gibE1R2+682lMPIBuFVsEKPfI0" +
        "zSB0gHt8PlWC5zKZ7RBxsZWjxM9Xs+" +
        "uns1kavXysKYbHl0KcFoZi707+qozZ" +
        "+LLtAWMPIFZQklr2I4J4TXMo/te7pS" +
        "6GF0Oh232Lz9gEN49QPsvKlCC+2uRd" +
        "6L52vTMQ3mgA==\nU2NhbmJvdFNESw" +
        "psb2NhbGhvc3R8am9objc1c3VuY2l0" +
        "eS1zc2gtZ2l0LWdpdGh1Yi1jb20tb2" +
        "Rvby1vZG9vLWdpdC0xOC0wLm9kb28u" +
        "Y29tCjE3NjUzMjQ3OTkKODM4ODYwNw" +
        "o4\n";

    /**
     * SDK Loader - Dynamically imports the Scanbot SDK module
     */
    const ScanbotLoader = {
        sdkReady: false,
        loading: false,
        loadPromise: null,

        async load() {
            console.log('[Portal Scanner] Starting SDK load...');

            if (this.sdkReady && window.ScanbotSDK) {
                console.log('[Portal Scanner] SDK already loaded');
                return true;
            }

            if (this.loading && this.loadPromise) {
                console.log('[Portal Scanner] SDK loading in progress, waiting...');
                return this.loadPromise;
            }

            this.loading = true;
            this.loadPromise = this._loadModule();
            return this.loadPromise;
        },

        async _loadModule() {
            try {
                if (window.ScanbotSDK) {
                    console.log('[Portal Scanner] SDK already available on window');
                    this.sdkReady = true;
                    this.loading = false;
                    return true;
                }

                console.log('[Portal Scanner] Importing SDK module from:', SCANBOT_SDK_URL);
                
                // Use dynamic import for ES module
                await import(SCANBOT_SDK_URL);
                
                console.log('[Portal Scanner] Module imported, checking window.ScanbotSDK...');
                
                // Wait a moment for the module to fully initialize
                await new Promise(resolve => setTimeout(resolve, 200));
                
                if (window.ScanbotSDK) {
                    console.log('[Portal Scanner] ScanbotSDK available on window');
                    this.sdkReady = true;
                    this.loading = false;
                    return true;
                } else {
                    console.error('[Portal Scanner] Module loaded but ScanbotSDK not on window');
                    throw new Error('ScanbotSDK not available after module import');
                }
            } catch (e) {
                console.error('[Portal Scanner] Failed to import SDK module:', e);
                this.loading = false;
                throw new Error('Failed to load Scanbot SDK: ' + e.message);
            }
        }
    };

    /**
     * Audio feedback for scanning events
     */
    const ScannerAudio = {
        audioContext: null,

        getContext() {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            return this.audioContext;
        },

        playTone(frequency, duration, type = 'sine') {
            try {
                const ctx = this.getContext();
                const oscillator = ctx.createOscillator();
                const gainNode = ctx.createGain();

                oscillator.type = type;
                oscillator.frequency.value = frequency;
                oscillator.connect(gainNode);
                gainNode.connect(ctx.destination);

                gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);

                oscillator.start(ctx.currentTime);
                oscillator.stop(ctx.currentTime + duration);
            } catch (e) {
                console.warn('Audio playback not available:', e);
            }
        },

        playSuccess() {
            this.playTone(880, 0.1);
            setTimeout(() => this.playTone(1100, 0.15), 100);
        },

        playError() {
            this.playTone(200, 0.3, 'square');
        }
    };

    /**
     * Main Portal Camera Scanner
     */
    const PortalCameraScanner = {
        targetSelectId: null,
        targetCheckboxName: null,
        scanType: null,
        continuousMode: false,
        scannedBarcodes: [],

        /**
         * Launch the camera scanner
         * @param {Object} options - Scanner options
         * @param {string} options.targetSelectId - ID of the select element to add items to
         * @param {string} options.targetCheckboxName - Name of checkbox inputs to check
         * @param {string} options.scanType - Type of scan: 'container', 'file', 'inventory'
         * @param {boolean} options.continuous - Enable continuous scanning mode
         */
        async launch(options = {}) {
            this.targetSelectId = options.targetSelectId || null;
            this.targetCheckboxName = options.targetCheckboxName || null;
            this.scanType = options.scanType || 'container';
            this.continuousMode = options.continuous || false;
            this.scannedBarcodes = [];

            try {
                this._showNotification('Starting camera scanner...', 'info');
                
                await ScanbotLoader.load();

                if (!window.ScanbotSDK) {
                    throw new Error('Scanbot SDK not available');
                }

                // Initialize SDK
                console.log('[Portal Scanner] Initializing SDK...');
                await window.ScanbotSDK.initialize({
                    licenseKey: SCANBOT_LICENSE_KEY,
                    enginePath: SCANBOT_ENGINE_PATH,
                });

                // Configure scanner
                const config = new window.ScanbotSDK.UI.Config.BarcodeScannerScreenConfiguration();
                
                config.topBar.title.text = "Scan Barcode";
                config.topBar.mode = "GRADIENT";
                
                // Single scan mode for each capture
                config.useCase.singleScanningMode = true;
                
                // AR overlay for visual feedback
                config.useCase.arOverlay.visible = true;
                config.useCase.arOverlay.automaticSelectionEnabled = true;
                
                // Viewfinder styling
                config.viewFinder.visible = true;
                config.viewFinder.style.strokeColor = "#00FF88";
                config.viewFinder.style.strokeWidth = 3;
                
                // Feedback
                config.sound.successBeepEnabled = true;
                config.vibration.enabled = true;

                // Launch scanner
                console.log('[Portal Scanner] Launching scanner UI...');
                const result = await window.ScanbotSDK.UI.createBarcodeScanner(config);

                if (result && result.items && result.items.length > 0) {
                    const barcode = result.items[0];
                    const barcodeText = barcode.barcode?.text || barcode.text;
                    
                    ScannerAudio.playSuccess();
                    await this._processScannedBarcode(barcodeText);
                    
                    // If continuous mode, relaunch
                    if (this.continuousMode) {
                        setTimeout(() => this.launch(options), 500);
                    }
                } else {
                    this._showNotification('Scanning cancelled', 'warning');
                }

            } catch (error) {
                console.error('[Portal Scanner] Error:', error);
                ScannerAudio.playError();
                this._showNotification('Scanner error: ' + error.message, 'danger');
            }
        },

        /**
         * Process a scanned barcode
         */
        async _processScannedBarcode(barcode) {
            console.log('[Portal Scanner] Processing barcode:', barcode);
            
            // Check if already scanned
            if (this.scannedBarcodes.includes(barcode)) {
                this._showNotification('Barcode already scanned: ' + barcode, 'warning');
                return;
            }
            
            this.scannedBarcodes.push(barcode);
            
            // Call backend to validate and get item details
            try {
                const response = await fetch('/my/scan/validate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        barcode: barcode,
                        scan_type: this.scanType,
                        csrf_token: this._getCsrfToken()
                    })
                });
                
                const data = await response.json();
                
                // Handle the result from the JSON-RPC response
                const result = data.result || data;
                
                if (result.success) {
                    ScannerAudio.playSuccess();
                    this._showNotification(result.message || 'Item found: ' + barcode, 'success');
                    
                    // Add to target select if specified
                    if (this.targetSelectId && result.item_id) {
                        this._addToSelect(result.item_id, result.item_name || barcode);
                    }
                    
                    // Check target checkbox if specified
                    if (this.targetCheckboxName && result.item_id) {
                        this._checkCheckbox(result.item_id);
                    }
                    
                    // Update scanned items display
                    this._updateScannedItemsDisplay(result);
                } else {
                    ScannerAudio.playError();
                    
                    // Remove from scanned list since it failed
                    const idx = this.scannedBarcodes.indexOf(barcode);
                    if (idx > -1) this.scannedBarcodes.splice(idx, 1);
                    
                    // Show appropriate error message based on error type
                    if (result.access_denied || result.belongs_to_other) {
                        // Item belongs to another customer - show prominent warning
                        this._showOwnershipError(result.message, barcode);
                    } else {
                        // Item not found or other error
                        this._showNotification(result.message || 'Barcode not found: ' + barcode, 'warning');
                    }
                }
            } catch (error) {
                console.error('[Portal Scanner] API error:', error);
                ScannerAudio.playError();
                this._showNotification('Error validating barcode', 'danger');
            }
        },

        /**
         * Show prominent ownership error when item belongs to another customer
         */
        _showOwnershipError(message, barcode) {
            // Create a modal-like alert for prominent display
            const alertHtml = `
                <div class="alert alert-danger alert-dismissible fade show position-fixed" 
                     style="top: 50%; left: 50%; transform: translate(-50%, -50%); 
                            z-index: 10000; min-width: 300px; max-width: 90%; 
                            box-shadow: 0 4px 20px rgba(0,0,0,0.3);"
                     role="alert" id="ownership-error-alert">
                    <h4 class="alert-heading">
                        <i class="fa fa-exclamation-triangle"></i> Access Denied
                    </h4>
                    <p class="mb-2">${message}</p>
                    <hr>
                    <p class="mb-0 small">
                        <strong>Barcode:</strong> ${barcode}<br>
                        <em>This item cannot be added to your request.</em>
                    </p>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            
            // Remove any existing ownership error alert
            const existing = document.getElementById('ownership-error-alert');
            if (existing) existing.remove();
            
            // Add to body
            document.body.insertAdjacentHTML('beforeend', alertHtml);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                const alert = document.getElementById('ownership-error-alert');
                if (alert) alert.remove();
            }, 5000);
        },

        /**
         * Add an item to a select element
         */
        _addToSelect(itemId, itemName) {
            const select = document.getElementById(this.targetSelectId);
            if (!select) {
                console.warn('[Portal Scanner] Target select not found:', this.targetSelectId);
                return;
            }
            
            // Check if already selected
            const existingOption = select.querySelector(`option[value="${itemId}"]`);
            if (existingOption) {
                existingOption.selected = true;
                return;
            }
            
            // Add new option and select it
            const option = document.createElement('option');
            option.value = itemId;
            option.text = itemName;
            option.selected = true;
            select.add(option);
            
            // Trigger change event for any listeners
            select.dispatchEvent(new Event('change'));
        },

        /**
         * Check a checkbox by item ID
         */
        _checkCheckbox(itemId) {
            // Find checkbox with matching value and name
            const checkbox = document.querySelector(
                `input[type="checkbox"][name="${this.targetCheckboxName}"][value="${itemId}"]`
            );
            
            if (checkbox) {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change'));
                
                // Highlight the row briefly
                const container = checkbox.closest('.custom-control, .form-check, div');
                if (container) {
                    container.style.backgroundColor = '#d4edda';
                    setTimeout(() => {
                        container.style.backgroundColor = '';
                    }, 1000);
                }
                
                // Update scanned count display
                this._updateScannedCount();
            } else {
                console.warn('[Portal Scanner] Checkbox not found for item:', itemId);
            }
        },

        /**
         * Update the scanned items count display
         */
        _updateScannedCount() {
            const countDisplay = document.getElementById('scanned-count');
            const container = document.getElementById('scanned-items-display');
            
            if (countDisplay && container) {
                countDisplay.textContent = this.scannedBarcodes.length;
                container.style.display = 'block';
            }
        },

        /**
         * Update the scanned items display area
         */
        _updateScannedItemsDisplay(data) {
            const display = document.getElementById('scanned-items-display');
            if (!display) return;
            
            const badge = document.createElement('span');
            badge.className = 'badge bg-success me-1 mb-1';
            badge.innerHTML = `
                <i class="fa fa-check-circle"></i> 
                ${this._escapeHtml(data.item_name || data.barcode)}
            `;
            display.appendChild(badge);
        },

        /**
         * Show a Bootstrap notification
         */
        _showNotification(message, type = 'info') {
            // Try to use existing notification system
            const container = document.querySelector('.o_notification_manager') || 
                             document.querySelector('#portal-notifications') ||
                             document.body;
            
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            alertDiv.style.cssText = 'top: 70px; right: 20px; z-index: 10000; max-width: 400px;';
            alertDiv.innerHTML = `
                ${this._escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            container.appendChild(alertDiv);
            
            // Auto dismiss after 4 seconds
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }, 4000);
        },

        /**
         * Get CSRF token from the page
         */
        _getCsrfToken() {
            const input = document.querySelector('input[name="csrf_token"]');
            return input ? input.value : '';
        },

        /**
         * Escape HTML to prevent XSS
         */
        _escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return String(text).replace(/[&<>"']/g, m => map[m]);
        }
    };

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        // Attach click handlers to camera scan buttons
        document.querySelectorAll('[data-action="portal-camera-scan"]').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const targetSelect = this.dataset.targetSelect || null;
                const targetCheckboxes = this.dataset.targetCheckboxes || null;
                const scanType = this.dataset.scanType || 'container';
                const continuous = this.dataset.continuous === 'true';
                
                PortalCameraScanner.launch({
                    targetSelectId: targetSelect,
                    targetCheckboxName: targetCheckboxes,
                    scanType: scanType,
                    continuous: continuous
                });
            });
        });
    });

    // Export for global access
    window.PortalCameraScanner = PortalCameraScanner;

})();
