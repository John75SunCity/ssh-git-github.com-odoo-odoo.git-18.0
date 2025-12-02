/** @odoo-module **/
/**
 * Records Management Camera Barcode Scanner
 *
 * OWL component providing mobile camera barcode scanning for Records Management.
 * Uses Scanbot SDK WASM-based barcode recognition engine for cross-browser support.
 *
 * Features:
 * - Live camera preview with professional barcode detection
 * - WASM-based engine works on all modern browsers (Chrome, Firefox, Safari, Edge)
 * - Multiple format support: QR, EAN, Code-128/39, UPC, DataMatrix, PDF417, Aztec
 * - Audio feedback on successful scans
 * - Manual barcode entry fallback
 * - Duplicate scan prevention (2-second debounce)
 * - Integration with Records Management operations
 *
 * @author Records Management System
 * @version 18.0.1.1.0
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

// Scanbot SDK CDN URLs
const SCANBOT_SDK_URL = "https://cdn.jsdelivr.net/npm/scanbot-web-sdk@7.0.0/bundle/ScanbotSDK.ui2.min.js";
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
 * Provides a full-screen camera interface for barcode scanning with:
 * - Scanbot SDK WASM-based barcode recognition
 * - Live video preview
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
            useScanbotRTU: true, // Use Scanbot Ready-To-Use UI
        });

        this.videoRef = useRef("videoElement");
        this.stream = null;
        this.scanInterval = null;
        this.lastScanTime = 0;
        this.scanbotSDK = null;
        this.barcodeScanner = null;

        // Check for camera support and load SDK
        this.checkCameraSupport();

        onMounted(() => {
            this.loadScanbotSDK();
        });

        onWillUnmount(() => {
            this.stopCamera();
            this.cleanupScanbotScanner();
        });
    }

    async loadScanbotSDK() {
        try {
            this.scanbotSDK = await ScanbotLoader.load();
            this.state.sdkReady = true;
            this.state.sdkLoading = false;
            console.log('Scanbot SDK loaded and ready');
        } catch (error) {
            console.error('Failed to load Scanbot SDK:', error);
            this.state.sdkLoading = false;
            this.state.errorMessage = _t("Failed to load barcode scanner engine. Using fallback.");
            // SDK failed - will fall back to native BarcodeDetector or manual
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
            this.state.errorMessage = _t("Camera not supported in this browser. Please use Chrome or Edge.");
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

    async startCamera() {
        this.state.errorMessage = null;
        this.state.permissionDenied = false;

        // If Scanbot SDK is ready, use the RTU UI
        if (this.state.sdkReady && this.state.useScanbotRTU) {
            await this.startScanbotScanner();
            return;
        }

        // Fallback to native camera + detection
        try {
            // Request camera access
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: this.state.selectedCamera,
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                },
            });

            // Attach stream to video element
            if (this.videoRef.el) {
                this.videoRef.el.srcObject = this.stream;
                await this.videoRef.el.play();
                this.state.cameraActive = true;
                this.state.scanning = true;

                // Initialize barcode detection (Scanbot Classic UI or native fallback)
                this.startBarcodeDetection();
            }
        } catch (error) {
            console.error("Camera error:", error);

            if (error.name === "NotAllowedError") {
                this.state.permissionDenied = true;
                this.state.errorMessage = _t("Camera access denied. Please allow camera access and try again.");
            } else if (error.name === "NotFoundError") {
                this.state.hasCamera = false;
                this.state.errorMessage = _t("No camera found. Please connect a camera or use manual entry.");
            } else {
                this.state.errorMessage = _t("Camera error: ") + error.message;
            }

            this.notification.add(this.state.errorMessage, { type: "warning" });
        }
    }

    /**
     * Start Scanbot SDK Ready-To-Use UI Scanner
     * This opens a full-screen scanner overlay with professional UI
     */
    async startScanbotScanner() {
        if (!window.ScanbotSDK || !this.state.sdkReady) {
            this.notification.add(_t("Scanner not ready. Please wait..."), { type: "warning" });
            return;
        }

        try {
            // Configure the Scanbot RTU UI scanner
            const config = new window.ScanbotSDK.UI.Config.BarcodeScannerScreenConfiguration();
            
            // Customize appearance
            config.topBar.title.text = _t("Records Management Scanner");
            config.topBar.mode = "GRADIENT";
            
            // Enable AR overlay for visual feedback
            config.useCase.arOverlay.visible = true;
            config.useCase.arOverlay.automaticSelectionEnabled = true;
            
            // Enable viewfinder
            config.viewFinder.visible = true;
            config.viewFinder.style.strokeColor = "#00FF88";
            config.viewFinder.style.strokeWidth = 3;
            
            // Sound and vibration feedback
            config.sound.successBeepEnabled = true;
            config.sound.buttonClickEnabled = true;
            config.vibration.enabled = true;

            // Launch the scanner
            const scanResult = await window.ScanbotSDK.UI.createBarcodeScanner(config);

            if (scanResult?.items?.length > 0) {
                const barcode = scanResult.items[0].barcode;
                const barcodeText = barcode.text;
                const barcodeFormat = barcode.format;

                console.log(`Scanned: ${barcodeText} (${barcodeFormat})`);
                
                // Play success sound
                ScannerAudio.playSuccess();
                
                // Process the barcode
                this.state.lastScannedBarcode = barcodeText;
                await this.processBarcode(barcodeText);
            } else {
                // User cancelled
                this.notification.add(_t("Scanning cancelled"), { type: "info", sticky: false });
            }
        } catch (error) {
            console.error("Scanbot scanner error:", error);
            ScannerAudio.playError();
            this.notification.add(
                _t("Scanner error: ") + error.message,
                { type: "danger", sticky: false }
            );
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }
        if (this.scanInterval) {
            clearInterval(this.scanInterval);
            this.scanInterval = null;
        }
        this.state.cameraActive = false;
        this.state.scanning = false;
    }

    toggleCamera() {
        this.state.selectedCamera = this.state.selectedCamera === "environment" ? "user" : "environment";
        if (this.state.cameraActive) {
            this.stopCamera();
            this.startCamera();
        }
    }

    startBarcodeDetection() {
        // Check for native BarcodeDetector support
        if ("BarcodeDetector" in window) {
            try {
                this.barcodeDetector = new BarcodeDetector({
                    formats: ["qr_code", "ean_13", "ean_8", "code_128", "code_39", "upc_a", "upc_e", "codabar"],
                });

                // Continuous scanning at 4 FPS
                this.scanInterval = setInterval(async () => {
                    if (this.state.scanning && this.videoRef.el && this.videoRef.el.readyState >= 2) {
                        await this.detectBarcode();
                    }
                }, 250);

                this.notification.add(_t("Camera ready - point at barcode"), { type: "info", sticky: false });

            } catch (error) {
                console.error("BarcodeDetector setup error:", error);
                this.showManualFallback();
            }
        } else {
            this.showManualFallback();
        }
    }

    showManualFallback() {
        this.notification.add(
            _t("Automatic barcode detection not available. Please use manual entry."),
            { type: "info" }
        );
    }

    async detectBarcode() {
        if (!this.barcodeDetector || !this.videoRef.el) return;

        try {
            const barcodes = await this.barcodeDetector.detect(this.videoRef.el);

            if (barcodes.length > 0) {
                const barcode = barcodes[0].rawValue;

                // Debounce duplicate scans (2 second window)
                const currentTime = Date.now();
                if (barcode === this.state.lastScannedBarcode && currentTime - this.lastScanTime < 2000) {
                    return;
                }

                // Process this barcode
                this.lastScanTime = currentTime;
                this.state.lastScannedBarcode = barcode;
                this.state.scanning = false; // Pause scanning during processing

                await this.processBarcode(barcode);

                // Resume scanning after delay
                setTimeout(() => {
                    if (this.state.cameraActive) {
                        this.state.scanning = true;
                    }
                }, 1500);
            }
        } catch (error) {
            console.error("Barcode detection error:", error);
        }
    }

    async processBarcode(barcode) {
        if (!barcode) return;

        this.state.scanCount++;

        try {
            // Call the backend to process the barcode
            const result = await this.orm.call(
                "barcode.operations.wizard",
                "process_camera_scan",
                [[], barcode, this.state.operationMode],
                { work_order_id: this.props.workOrderId || false }
            );

            if (result.success) {
                ScannerAudio.playSuccess();
                this.state.lastScannedResult = result;

                this.notification.add(
                    result.message || _t("Barcode processed: ") + barcode,
                    { type: "success", sticky: false }
                );

                // Callback if provided
                if (this.props.onScanComplete) {
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
        } catch (error) {
            ScannerAudio.playError();
            console.error("Process barcode error:", error);

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
        if (!this.state.lastScannedResult?.container_id) return;

        this.stopCamera();
        this.props.close();

        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "records.container",
            res_id: this.state.lastScannedResult.container_id,
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
        this.openScanner();
    }

    openScanner() {
        this.dialogService.add(RMCameraScannerDialog, {
            operationMode: this.operationMode,
            workOrderId: this.workOrderId,
            onScanComplete: (result) => this.onScanComplete(result),
        });
    }

    onScanComplete(result) {
        // Handle scan completion - navigate to record if found
        if (result.container_id) {
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: "records.container",
                res_id: result.container_id,
                views: [[false, "form"]],
                target: "current",
            });
        }
    }
}

// Register client action
registry.category("actions").add("rm_camera_scanner", RMCameraScannerAction);
