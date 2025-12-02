/** @odoo-module **/
/**
 * Records Management Camera Barcode Scanner
 *
 * OWL component providing mobile camera barcode scanning for Records Management.
 * Uses Scanbot SDK 7.1 WASM-based barcode recognition with RTU UI.
 *
 * Features:
 * - Launches Scanbot RTU scanner overlay from existing wizard
 * - Cross-browser support (Chrome, Firefox, Safari, Edge)
 * - Multiple format support: QR, EAN, Code-128/39, UPC, DataMatrix, PDF417
 * - Single scan mode returns immediately with result
 * - Audio feedback on successful scans
 *
 * @author Records Management System
 * @version 18.0.1.3.0
 * @license LGPL-3
 */

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

// Scanbot SDK License Key (valid for localhost and Odoo.sh domain)
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

// Scanbot SDK 7.1 CDN URLs
const SCANBOT_SDK_URL = "https://cdn.jsdelivr.net/npm/scanbot-web-sdk@7.1.1/bundle/ScanbotSDK.ui2.min.js";
const SCANBOT_ENGINE_PATH = "https://cdn.jsdelivr.net/npm/scanbot-web-sdk@7.1.1/bundle/bin/complete/";

/**
 * Audio feedback generator for barcode scanning events.
 */
class ScannerAudio {
    static audioContext = null;

    static getContext() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        return this.audioContext;
    }

    static playTone(frequency, duration, type = 'sine') {
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
    }

    static playSuccess() {
        this.playTone(880, 0.1);
        setTimeout(() => this.playTone(1100, 0.15), 100);
    }

    static playError() {
        this.playTone(200, 0.3, 'square');
    }
}

/**
 * Scanbot SDK Loader - Dynamically loads the SDK script
 */
class ScanbotLoader {
    static sdkReady = false;
    static loading = false;
    static loadPromise = null;

    static async load() {
        console.log('[Scanbot] Starting SDK load...');
        
        if (this.sdkReady && window.ScanbotSDK) {
            console.log('[Scanbot] SDK already loaded');
            return true;
        }

        if (this.loading && this.loadPromise) {
            console.log('[Scanbot] SDK loading in progress, waiting...');
            return this.loadPromise;
        }

        this.loading = true;
        this.loadPromise = this._loadScript();
        return this.loadPromise;
    }

    static async _loadScript() {
        return new Promise((resolve, reject) => {
            if (window.ScanbotSDK) {
                console.log('[Scanbot] SDK already available on window');
                this.sdkReady = true;
                this.loading = false;
                resolve(true);
                return;
            }

            console.log('[Scanbot] Loading SDK from:', SCANBOT_SDK_URL);
            const script = document.createElement('script');
            script.src = SCANBOT_SDK_URL;
            script.async = true;

            script.onload = () => {
                console.log('[Scanbot] SDK script loaded successfully');
                // Give a brief moment for the SDK to initialize on window
                setTimeout(() => {
                    if (window.ScanbotSDK) {
                        console.log('[Scanbot] ScanbotSDK available on window:', typeof window.ScanbotSDK);
                        this.sdkReady = true;
                    } else {
                        console.warn('[Scanbot] Script loaded but ScanbotSDK not on window');
                    }
                    this.loading = false;
                    resolve(true);
                }, 100);
            };

            script.onerror = (e) => {
                console.error('[Scanbot] Failed to load SDK script:', e);
                this.loading = false;
                reject(new Error('Failed to load Scanbot SDK from CDN'));
            };

            document.head.appendChild(script);
        });
    }
}

/**
 * Launch Scanbot RTU Scanner and return result
 * This is a standalone function that can be called from anywhere
 */
async function launchScanbotScanner() {
    console.log('[Scanbot] launchScanbotScanner called');
    
    try {
        // Ensure SDK is loaded
        await ScanbotLoader.load();

        if (!window.ScanbotSDK) {
            console.error('[Scanbot] SDK not available after load');
            throw new Error('Scanbot SDK not available - script may have failed to load');
        }

        console.log('[Scanbot] Initializing SDK with license and engine path...');
        console.log('[Scanbot] Engine path:', SCANBOT_ENGINE_PATH);
        
        // Initialize SDK with engine path for CDN usage
        const sdk = await window.ScanbotSDK.initialize({
            licenseKey: SCANBOT_LICENSE_KEY,
            enginePath: SCANBOT_ENGINE_PATH,
        });
        
        console.log('[Scanbot] SDK initialized successfully');

        // Create RTU UI configuration for single barcode scanning
        const config = new window.ScanbotSDK.UI.Config.BarcodeScannerScreenConfiguration();
        
        // Appearance
        config.topBar.title.text = "Records Management Scanner";
        config.topBar.mode = "GRADIENT";
        
        // Single barcode mode - returns after first scan
        config.useCase.singleScanningMode = true;
        
        // AR overlay for visual feedback
        config.useCase.arOverlay.visible = true;
        config.useCase.arOverlay.automaticSelectionEnabled = true;
        
        // Viewfinder styling
        config.viewFinder.visible = true;
        config.viewFinder.style.strokeColor = "#00FF88";
        config.viewFinder.style.strokeWidth = 3;
        
        // Sound feedback
        config.sound.successBeepEnabled = true;
        config.vibration.enabled = true;

        console.log('[Scanbot] Launching scanner UI...');
        
        // Launch scanner and wait for result
        const result = await window.ScanbotSDK.UI.createBarcodeScanner(config);

        console.log('[Scanbot] Scanner result:', result);

        if (result && result.items && result.items.length > 0) {
            const barcode = result.items[0];
            return {
                success: true,
                text: barcode.barcode?.text || barcode.text,
                format: barcode.barcode?.format || barcode.format,
            };
        }

        return { success: false, cancelled: true };
        
    } catch (error) {
        console.error('[Scanbot] Error in launchScanbotScanner:', error);
        throw error;
    }
}

/**
 * Camera Scanner Client Action
 * 
 * This is a lightweight action that launches the Scanbot RTU scanner
 * and processes the result, then navigates back to where the user came from.
 */
export class RMCameraScannerAction extends Component {
    static template = "records_management.CameraScannerAction";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.isDestroyed = false;

        // Extract context params
        const context = this.props.action?.context || {};
        this.operationMode = context.operation_mode || "lookup";
        this.workOrderId = context.work_order_id || null;

        onMounted(() => {
            // Auto-launch scanner after a brief delay
            setTimeout(() => this.launchScanner(), 100);
        });

        onWillUnmount(() => {
            this.isDestroyed = true;
        });
    }

    async launchScanner() {
        try {
            this.notification.add(_t("Starting camera scanner..."), { type: "info", sticky: false });

            const scanResult = await launchScanbotScanner();

            if (this.isDestroyed) return;

            if (scanResult.success && scanResult.text) {
                ScannerAudio.playSuccess();
                
                // Process the barcode
                await this.processBarcode(scanResult.text);
            } else if (scanResult.cancelled) {
                this.notification.add(_t("Scanning cancelled"), { type: "info", sticky: false });
                // Go back
                this.action.doAction({ type: 'ir.actions.act_window_close' });
            }
        } catch (error) {
            console.error("Scanner error:", error);
            ScannerAudio.playError();
            this.notification.add(
                _t("Scanner error: ") + (error.message || "Unknown error"),
                { type: "danger" }
            );
            // Go back on error
            setTimeout(() => {
                if (!this.isDestroyed) {
                    this.action.doAction({ type: 'ir.actions.act_window_close' });
                }
            }, 2000);
        }
    }

    async processBarcode(barcode) {
        if (!barcode || this.isDestroyed) return;

        try {
            // Call the backend - pass work_order_id as part of positional args
            const result = await this.orm.call(
                "barcode.operations.wizard",
                "process_camera_scan",
                [barcode, this.operationMode, this.workOrderId || false]
            );

            if (this.isDestroyed) return;

            if (result.success) {
                this.notification.add(
                    result.message || _t("Container found!"),
                    { type: "success" }
                );

                // Navigate to the container if found
                if (result.container_id) {
                    await this.action.doAction({
                        type: "ir.actions.act_window",
                        res_model: "records.container",
                        res_id: result.container_id,
                        views: [[false, "form"]],
                        target: "current",
                    });
                } else {
                    // Close and go back
                    this.action.doAction({ type: 'ir.actions.act_window_close' });
                }
            } else {
                ScannerAudio.playError();
                this.notification.add(
                    result.error || _t("Barcode not found"),
                    { type: "warning" }
                );
                // Close after showing error
                setTimeout(() => {
                    if (!this.isDestroyed) {
                        this.action.doAction({ type: 'ir.actions.act_window_close' });
                    }
                }, 2000);
            }
        } catch (error) {
            if (this.isDestroyed) return;

            ScannerAudio.playError();
            console.error("Process barcode error:", error);
            
            this.notification.add(
                _t("Error processing barcode: ") + (error.data?.message || error.message),
                { type: "danger" }
            );
        }
    }
}

// Register client action
registry.category("actions").add("rm_camera_scanner", RMCameraScannerAction);

// Export the launcher function for use in other components
export { launchScanbotScanner, ScannerAudio, ScanbotLoader };
