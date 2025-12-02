/** @odoo-module **/
/**
 * Records Management Camera Barcode Scanner
 *
 * OWL component providing mobile camera barcode scanning for Records Management.
 * Uses Scanbot SDK WASM-based barcode recognition engine for cross-browser support.
 *
 * Features:
 * - Live camera preview with embedded barcode detection (not fullscreen)
 * - WASM-based engine works on all modern browsers (Chrome, Firefox, Safari, Edge)
 * - Single scan mode (stops after each scan) or Continuous mode
 * - Multiple format support: QR, EAN, Code-128/39, UPC, DataMatrix, PDF417, Aztec
 * - Audio feedback on successful scans
 * - Manual barcode entry fallback
 * - Duplicate scan prevention (2-second debounce)
 * - Integration with Records Management operations
 *
 * @author Records Management System
 * @version 18.0.1.2.0
 * @license LGPL-3
 */

import { Component, useState, useRef, onWillUnmount, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
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

// Scanbot SDK CDN URLs - Use the base SDK (not RTU UI) for embedded scanning
const SCANBOT_SDK_URL = "https://cdn.jsdelivr.net/npm/scanbot-web-sdk@7.0.0/bundle/ScanbotSDK.min.js";
const SCANBOT_ENGINE_PATH = "https://cdn.jsdelivr.net/npm/scanbot-web-sdk@7.0.0/bundle/bin/barcode-scanner/";

/**
 * Audio feedback generator for barcode scanning events.
 * Uses Web Audio API to generate success/error tones.
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
        // Pleasant ascending tones
        this.playTone(880, 0.1);
        setTimeout(() => this.playTone(1100, 0.15), 100);
    }

    static playError() {
        // Low warning tone
        this.playTone(200, 0.3, 'square');
    }
}

/**
 * Scanbot SDK Loader - Dynamically loads the SDK script
 */
class ScanbotLoader {
    static sdk = null;
    static loading = false;
    static loadPromise = null;

    static async load() {
        // Return cached SDK if already loaded
        if (this.sdk) {
            return this.sdk;
        }

        // Return existing promise if currently loading
        if (this.loading && this.loadPromise) {
            return this.loadPromise;
        }

        this.loading = true;
        this.loadPromise = this._loadScript();
        return this.loadPromise;
    }

    static async _loadScript() {
        return new Promise((resolve, reject) => {
            // Check if already loaded globally
            if (window.ScanbotSDK) {
                this._initializeSDK().then(resolve).catch(reject);
                return;
            }

            // Create script element
            const script = document.createElement('script');
            script.src = SCANBOT_SDK_URL;
            script.async = true;

            script.onload = async () => {
                try {
                    await this._initializeSDK();
                    resolve(this.sdk);
                } catch (error) {
                    reject(error);
                }
            };

            script.onerror = () => {
                this.loading = false;
                reject(new Error('Failed to load Scanbot SDK'));
            };

            document.head.appendChild(script);
        });
    }

    static async _initializeSDK() {
        if (!window.ScanbotSDK) {
            throw new Error('ScanbotSDK not found after script load');
        }

        this.sdk = await window.ScanbotSDK.initialize({
            licenseKey: SCANBOT_LICENSE_KEY,
            enginePath: SCANBOT_ENGINE_PATH,
        });

        console.log('Scanbot SDK initialized successfully');
        this.loading = false;
        return this.sdk;
    }
}

/**
 * Camera Barcode Scanner Dialog Component
 *
 * Provides an embedded camera interface for barcode scanning with:
 * - Scanbot SDK WASM-based barcode recognition (embedded, not fullscreen)
 * - Live video preview inside the dialog
 * - Single scan or continuous scan mode toggle
 * - Operation mode selection (lookup, retrieval, shredding, etc.)
 * - Result display and navigation
 */
export class RMCameraScannerDialog extends Component {
    static template = "records_management.CameraScannerDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        operationMode: { type: String, optional: true },
        workOrderId: { type: Number, optional: true },
        onScanComplete: { type: Function, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");

        // Component lifecycle flag to prevent calls after unmount
        this.isDestroyed = false;

        this.state = useState({
            cameraActive: false,
            scanning: false,
            hasCamera: true,
            permissionDenied: false,
            lastScannedBarcode: null,
            lastScannedResult: null,
            scanCount: 0,
            manualBarcode: "",
            selectedCamera: "environment", // 'environment' (back) or 'user' (front)
            errorMessage: null,
            operationMode: this.props.operationMode || "lookup",
            sdkReady: false,
            sdkLoading: true,
            // Scan mode: 'single' stops after each scan, 'continuous' keeps scanning
            scanMode: "single",
            processing: false, // Flag to show processing state
        });

        this.videoRef = useRef("videoElement");
        this.scannerContainerRef = useRef("scannerContainer");
        this.stream = null;
        this.scanbotSDK = null;
        this.barcodeScanner = null;
        this.lastScanTime = 0;

        // Check for camera support
        this.checkCameraSupport();

        onMounted(() => {
            this.loadScanbotSDK();
        });

        onWillUnmount(() => {
            this.isDestroyed = true;
            this.stopCamera();
            this.cleanupScanbotScanner();
        });
    }

    async loadScanbotSDK() {
        try {
            this.scanbotSDK = await ScanbotLoader.load();
            if (!this.isDestroyed) {
                this.state.sdkReady = true;
                this.state.sdkLoading = false;
                console.log('Scanbot SDK loaded and ready');
            }
        } catch (error) {
            console.error('Failed to load Scanbot SDK:', error);
            if (!this.isDestroyed) {
                this.state.sdkLoading = false;
                this.state.errorMessage = _t("Failed to load barcode scanner engine. Using manual entry.");
            }
        }
    }

    cleanupScanbotScanner() {
        if (this.barcodeScanner) {
            try {
                this.barcodeScanner.dispose();
            } catch (e) {
                console.warn('Error disposing barcode scanner:', e);
            }
            this.barcodeScanner = null;
        }
    }

    async checkCameraSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.state.hasCamera = false;
            this.state.errorMessage = _t("Camera not supported in this browser.");
        }
    }

    get operationModes() {
        return [
            { value: "lookup", label: _t("Container Lookup") },
            { value: "retrieval", label: _t("Retrieval Scan") },
            { value: "shredding", label: _t("Shredding/Destruction") },
            { value: "bin", label: _t("Bin Service") },
            { value: "file", label: _t("File/Document") },
            { value: "location", label: _t("Location Scan") },
        ];
    }

    /**
     * Start camera with Scanbot embedded barcode scanner
     * The scanner renders inside the video element container, not fullscreen
     */
    async startCamera() {
        if (this.isDestroyed) return;
        
        this.state.errorMessage = null;
        this.state.permissionDenied = false;

        // Check if SDK is ready
        if (!this.state.sdkReady || !this.scanbotSDK) {
            this.notification.add(_t("Scanner loading... Please wait."), { type: "info" });
            return;
        }

        try {
            // Create the Scanbot barcode scanner attached to our container
            const containerElement = this.scannerContainerRef.el;
            if (!containerElement) {
                throw new Error("Scanner container not found");
            }

            // Configure the embedded barcode scanner
            const config = {
                containerId: containerElement.id || 'scanbot-scanner-container',
                videoConstraints: {
                    facingMode: this.state.selectedCamera,
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                },
                overlay: {
                    visible: true,
                    textFormat: "TextAndFormat",
                    polygonFillColor: "rgba(0, 255, 136, 0.2)",
                    polygonStrokeColor: "#00FF88",
                    polygonStrokeWidth: 3,
                },
                returnBarcodeImage: false,
                onBarcodesDetected: (result) => this.onBarcodesDetected(result),
                onError: (error) => this.onScanError(error),
            };

            // Create the scanner - it will render inside the container
            this.barcodeScanner = await this.scanbotSDK.createBarcodeScanner(config);
            
            if (!this.isDestroyed) {
                this.state.cameraActive = true;
                this.state.scanning = true;
                this.notification.add(_t("Camera ready - point at barcode"), { type: "info", sticky: false });
            }

        } catch (error) {
            console.error("Camera/Scanner error:", error);

            if (this.isDestroyed) return;

            if (error.name === "NotAllowedError" || error.message?.includes("Permission")) {
                this.state.permissionDenied = true;
                this.state.errorMessage = _t("Camera access denied. Please allow camera access and try again.");
            } else if (error.name === "NotFoundError") {
                this.state.hasCamera = false;
                this.state.errorMessage = _t("No camera found. Please use manual entry.");
            } else {
                this.state.errorMessage = _t("Camera error: ") + (error.message || "Unknown error");
            }

            this.notification.add(this.state.errorMessage, { type: "warning" });
        }
    }

    /**
     * Handle barcodes detected by Scanbot SDK
     */
    onBarcodesDetected(result) {
        if (this.isDestroyed || !result.barcodes || result.barcodes.length === 0) {
            return;
        }

        // Get the first detected barcode
        const barcode = result.barcodes[0];
        const barcodeText = barcode.text;
        const barcodeFormat = barcode.format;

        // Debounce duplicate scans (2 second window)
        const currentTime = Date.now();
        if (barcodeText === this.state.lastScannedBarcode && currentTime - this.lastScanTime < 2000) {
            return;
        }

        console.log("Scanned: " + barcodeText + " (" + barcodeFormat + ")");
        this.lastScanTime = currentTime;
        this.state.lastScannedBarcode = barcodeText;

        // In single scan mode, pause scanning while processing
        if (this.state.scanMode === "single") {
            this.pauseScanning();
        }

        // Play success sound
        ScannerAudio.playSuccess();

        // Process the barcode
        this.processBarcode(barcodeText);
    }

    /**
     * Handle scanner errors
     */
    onScanError(error) {
        console.error("Scanbot scanner error:", error);
        if (!this.isDestroyed) {
            this.notification.add(_t("Scanner error: ") + error.message, { type: "warning" });
        }
    }

    /**
     * Pause scanning (for single scan mode)
     */
    pauseScanning() {
        if (this.barcodeScanner && !this.isDestroyed) {
            this.state.scanning = false;
            // Scanbot SDK pause method
            try {
                this.barcodeScanner.pauseDetection();
            } catch (e) {
                console.warn("Could not pause detection:", e);
            }
        }
    }

    /**
     * Resume scanning
     */
    resumeScanning() {
        if (this.barcodeScanner && this.state.cameraActive && !this.isDestroyed) {
            this.state.scanning = true;
            try {
                this.barcodeScanner.resumeDetection();
            } catch (e) {
                console.warn("Could not resume detection:", e);
            }
        }
    }

    stopCamera() {
        if (this.barcodeScanner) {
            try {
                this.barcodeScanner.dispose();
            } catch (e) {
                console.warn("Error stopping scanner:", e);
            }
            this.barcodeScanner = null;
        }
        
        // Also stop any direct stream if exists
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }
        
        if (!this.isDestroyed) {
            this.state.cameraActive = false;
            this.state.scanning = false;
        }
    }

    toggleCamera() {
        this.state.selectedCamera = this.state.selectedCamera === "environment" ? "user" : "environment";
        if (this.state.cameraActive) {
            this.stopCamera();
            // Small delay to allow cleanup
            setTimeout(() => {
                if (!this.isDestroyed) {
                    this.startCamera();
                }
            }, 300);
        }
    }

    toggleScanMode() {
        this.state.scanMode = this.state.scanMode === "single" ? "continuous" : "single";
        this.notification.add(
            this.state.scanMode === "single" 
                ? _t("Single scan mode: Camera pauses after each scan")
                : _t("Continuous scan mode: Keeps scanning after each scan"),
            { type: "info", sticky: false }
        );
    }

    async processBarcode(barcode) {
        if (!barcode || this.isDestroyed) return;

        this.state.scanCount++;
        this.state.processing = true;

        try {
            // Call the backend to process the barcode
            const result = await this.orm.call(
                "barcode.operations.wizard",
                "process_camera_scan",
                [[], barcode, this.state.operationMode],
                { work_order_id: this.props.workOrderId || false }
            );

            // Check if component is still mounted
            if (this.isDestroyed) return;

            this.state.processing = false;

            if (result.success) {
                this.state.lastScannedResult = result;

                this.notification.add(
                    result.message || _t("Barcode processed: ") + barcode,
                    { type: "success", sticky: false }
                );

                // Callback if provided
                if (this.props.onScanComplete && !this.isDestroyed) {
                    this.props.onScanComplete(result);
                }
            } else {
                ScannerAudio.playError();
                this.state.lastScannedResult = { error: result.error || _t("Unknown error") };

                this.notification.add(
                    result.error || _t("Barcode not found: ") + barcode,
                    { type: "warning", sticky: false }
                );
            }

            // In continuous mode, keep scanning; in single mode, stay paused
            if (this.state.scanMode === "continuous" && !this.isDestroyed) {
                // Small delay before resuming in continuous mode
                setTimeout(() => this.resumeScanning(), 500);
            }

        } catch (error) {
            if (this.isDestroyed) return;

            ScannerAudio.playError();
            console.error("Process barcode error:", error);

            this.state.processing = false;
            this.state.lastScannedResult = { error: error.message };
            
            this.notification.add(
                _t("Error processing barcode: ") + (error.data?.message || error.message),
                { type: "danger", sticky: false }
            );
        }
    }

    async onManualSubmit() {
        const barcode = this.state.manualBarcode.trim();
        if (!barcode) return;

        this.state.manualBarcode = "";
        await this.processBarcode(barcode);
    }

    onManualInput(ev) {
        this.state.manualBarcode = ev.target.value;
    }

    onManualKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.onManualSubmit();
        }
    }

    onModeChange(ev) {
        this.state.operationMode = ev.target.value;
    }

    async viewContainer() {
        if (!this.state.lastScannedResult?.container_id || this.isDestroyed) return;

        const containerId = this.state.lastScannedResult.container_id;
        
        this.stopCamera();
        this.props.close();

        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "records.container",
            res_id: containerId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    close() {
        this.stopCamera();
        this.props.close();
    }
}

/**
 * Client action wrapper for launching the camera scanner
 */
export class RMCameraScannerAction extends Component {
    static template = "records_management.CameraScannerAction";
    static components = { RMCameraScannerDialog };

    setup() {
        this.dialogService = useService("dialog");
        this.action = useService("action");

        // Extract context params
        const context = this.props.action?.context || {};
        this.operationMode = context.operation_mode || "lookup";
        this.workOrderId = context.work_order_id || null;

        // Auto-open dialog
        onMounted(() => {
            this.openScanner();
        });
    }

    openScanner() {
        this.dialogService.add(RMCameraScannerDialog, {
            operationMode: this.operationMode,
            workOrderId: this.workOrderId,
            onScanComplete: (result) => this.onScanComplete(result),
        });
    }

    onScanComplete(result) {
        // Handle scan completion - could navigate if needed
        console.log("Scan complete:", result);
    }
}

// Register client action
registry.category("actions").add("rm_camera_scanner", RMCameraScannerAction);
