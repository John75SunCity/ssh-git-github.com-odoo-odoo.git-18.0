/** @odoo-module **/
/**
 * Records Management Camera Barcode Scanner
 *
 * OWL component providing mobile camera barcode scanning for Records Management.
 * Uses native BarcodeDetector API (Chrome 83+, Edge 83+) with manual fallback.
 *
 * Features:
 * - Live camera preview with automatic barcode detection
 * - Multiple format support: QR, EAN-13/8, Code-128/39, UPC-A/E
 * - Audio feedback on successful scans
 * - Manual barcode entry fallback
 * - Duplicate scan prevention (2-second debounce)
 * - Integration with Records Management operations
 *
 * @author Records Management System
 * @version 18.0.1.0.0
 * @license LGPL-3
 */

import { Component, useState, useRef, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

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
 * Camera Barcode Scanner Dialog Component
 * 
 * Provides a full-screen camera interface for barcode scanning with:
 * - Live video preview
 * - Automatic barcode detection
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
        });

        this.videoRef = useRef("videoElement");
        this.stream = null;
        this.scanInterval = null;
        this.lastScanTime = 0;
        this.barcodeDetector = null;

        // Check for camera support
        this.checkCameraSupport();

        onWillUnmount(() => {
            this.stopCamera();
        });
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

                // Initialize barcode detection
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
