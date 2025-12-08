/** @odoo-module **/
/**
 * Hard Drive Barcode Scanner
 *
 * OWL component for scanning hard drive serial numbers during destruction workflows.
 * Uses the shared ScanbotSDK infrastructure from rm_camera_scanner.js.
 *
 * Features:
 * - Continuous scanning mode for multiple hard drives
 * - Real-time count display
 * - Audio feedback on successful scans
 * - Integration with hard.drive.scan.wizard
 *
 * @author Records Management System
 * @version 18.0.1.0.0
 * @license LGPL-3
 */

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { launchScanbotScanner, ScannerAudio } from "./rm_camera_scanner";

/**
 * Hard Drive Scanner Client Action
 *
 * This client action launches the Scanbot RTU scanner specifically for
 * hard drive barcode scanning. It supports continuous scanning mode and
 * adds each scanned barcode to the wizard's line items.
 */
export class HardDriveScannerAction extends Component {
    static template = "records_management.HardDriveScannerAction";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.isDestroyed = false;

        // Extract context params
        const context = this.props.action?.context || {};
        this.wizardId = context.wizard_id || null;
        this.operationMode = context.operation_mode || "hard_drive_scan";

        this.state = useState({
            scannedCount: 0,
            lastScanned: "",
            scanning: false,
        });

        onMounted(() => {
            // Auto-launch scanner after a brief delay
            setTimeout(() => this.startScanning(), 100);
        });

        onWillUnmount(() => {
            this.isDestroyed = true;
        });
    }

    /**
     * Close the scanner and return to the wizard
     */
    async closeScanner() {
        if (this.isDestroyed) return;

        // Close the client action and let the wizard refresh
        this.action.doAction({
            type: 'ir.actions.act_window_close'
        });
    }

    /**
     * Start the scanning process
     */
    async startScanning() {
        if (this.isDestroyed || this.state.scanning) return;

        this.state.scanning = true;
        await this.launchScanner();
    }

    async launchScanner() {
        if (this.isDestroyed) return;

        try {
            this.notification.add(_t("Starting camera scanner..."), { type: "info", sticky: false });

            const scanResult = await launchScanbotScanner();

            if (this.isDestroyed) return;

            if (scanResult.success && scanResult.text) {
                ScannerAudio.playSuccess();

                // Add the scanned barcode to the wizard
                await this.addBarcodeToWizard(scanResult.text);

                // Continue scanning for more barcodes
                setTimeout(() => {
                    if (!this.isDestroyed) {
                        this.launchScanner();
                    }
                }, 500);
            } else if (scanResult.cancelled) {
                this.notification.add(_t("Scanning finished"), { type: "info", sticky: false });
                this.state.scanning = false;
                // Close and return to wizard
                await this.closeScanner();
            }
        } catch (error) {
            console.error("Scanner error:", error);
            ScannerAudio.playError();
            this.notification.add(
                _t("Scanner error: ") + (error.message || "Unknown error"),
                { type: "danger" }
            );
            this.state.scanning = false;
            // Return to wizard on error
            setTimeout(() => {
                if (!this.isDestroyed) {
                    this.closeScanner();
                }
            }, 2000);
        }
    }

    async addBarcodeToWizard(barcodeValue) {
        if (!barcodeValue || !this.wizardId || this.isDestroyed) return;

        try {
            const result = await this.orm.call(
                "hard.drive.scan.wizard",
                "add_scanned_barcode",
                [this.wizardId, barcodeValue]
            );

            if (this.isDestroyed) return;

            if (result.success) {
                this.state.scannedCount = result.total_count || this.state.scannedCount + 1;
                this.state.lastScanned = result.serial_number || barcodeValue;

                this.notification.add(
                    _t("✅ Added: %s (Total: %s)", barcodeValue, this.state.scannedCount),
                    { type: "success", sticky: false }
                );
            } else {
                ScannerAudio.playError();
                this.notification.add(
                    result.message || _t("Failed to add barcode"),
                    { type: result.warning ? "warning" : "danger" }
                );
            }
        } catch (error) {
            if (this.isDestroyed) return;

            ScannerAudio.playError();
            console.error("Error adding barcode:", error);
            this.notification.add(
                _t("Error: ") + (error.data?.message || error.message),
                { type: "danger" }
            );
        }
    }

    /**
     * Manual stop and finish
     */
    async onFinish() {
        this.state.scanning = false;
        await this.closeScanner();
    }
}

HardDriveScannerAction.template = "records_management.HardDriveScannerAction";

// Register client action
registry.category("actions").add("records_management.hard_drive_scanner", HardDriveScannerAction);
