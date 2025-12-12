/**
 * Portal User Import Widget - Vanilla JavaScript (Odoo 18 Compatible)
 * 
 * PURPOSE: CSV bulk import wizard for contacts/users
 * USE CASE: /my/contacts/import - bulk contact import
 * 
 * FEATURES:
 * ✓ CSV file parsing with preview
 * ✓ Field mapping validation
 * ✓ Batch processing with progress
 * ✓ Error reporting per row
 * ✓ Import summary statistics
 * 
 * CONVERSION NOTES (Odoo 18):
 * - Removed: odoo.define(), publicWidget dependency
 * - Replaced: jQuery with native DOM APIs
 * - Uses native FileReader for CSV parsing
 * - Uses fetch() for batch imports
 */

(function() {
    'use strict';

    class PortalUserImport {
        constructor(container) {
            this.container = container;
            this.csvData = [];
            this.headers = [];
            this.currentStep = 1;
            this.batchSize = 50;
            this.init();
        }

        init() {
            this._setupEventHandlers();
            this._renderStep(1);
            console.log('[PortalUserImport] Initialized');
        }

        _setupEventHandlers() {
            // File input
            this.container.addEventListener('change', (e) => {
                if (e.target.matches('#csv-file-input')) {
                    this._onFileSelected(e.target.files[0]);
                }
            });

            // Button clicks
            this.container.addEventListener('click', (e) => {
                const btn = e.target.closest('[data-action]');
                if (!btn) return;

                const action = btn.dataset.action;
                e.preventDefault();

                switch (action) {
                    case 'next-step':
                        this._nextStep();
                        break;
                    case 'prev-step':
                        this._prevStep();
                        break;
                    case 'start-import':
                        this._startImport();
                        break;
                    case 'download-template':
                        this._downloadTemplate();
                        break;
                    case 'download-errors':
                        this._downloadErrors();
                        break;
                }
            });

            // Drag and drop
            const dropZone = this.container.querySelector('.csv-drop-zone');
            if (dropZone) {
                dropZone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    dropZone.classList.add('drag-over');
                });
                dropZone.addEventListener('dragleave', () => {
                    dropZone.classList.remove('drag-over');
                });
                dropZone.addEventListener('drop', (e) => {
                    e.preventDefault();
                    dropZone.classList.remove('drag-over');
                    const file = e.dataTransfer.files[0];
                    if (file && file.name.endsWith('.csv')) {
                        this._onFileSelected(file);
                    }
                });
            }
        }

        _onFileSelected(file) {
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (e) => {
                const content = e.target.result;
                this._parseCSV(content);
            };
            reader.onerror = () => {
                this._showError('Failed to read file');
            };
            reader.readAsText(file);
        }

        _parseCSV(content) {
            const lines = content.split(/\r?\n/).filter(line => line.trim());
            if (lines.length < 2) {
                this._showError('CSV must have at least a header row and one data row');
                return;
            }

            this.headers = this._parseCSVLine(lines[0]);
            this.csvData = [];

            for (let i = 1; i < lines.length; i++) {
                const values = this._parseCSVLine(lines[i]);
                if (values.length === this.headers.length) {
                    const row = {};
                    this.headers.forEach((header, idx) => {
                        row[header.toLowerCase().trim()] = values[idx];
                    });
                    this.csvData.push(row);
                }
            }

            this._renderPreview();
            this._enableNextStep();
        }

        _parseCSVLine(line) {
            const result = [];
            let current = '';
            let inQuotes = false;

            for (let i = 0; i < line.length; i++) {
                const char = line[i];
                if (char === '"') {
                    inQuotes = !inQuotes;
                } else if (char === ',' && !inQuotes) {
                    result.push(current.trim());
                    current = '';
                } else {
                    current += char;
                }
            }
            result.push(current.trim());
            return result;
        }

        _renderPreview() {
            const previewContainer = this.container.querySelector('#csv-preview');
            if (!previewContainer || this.csvData.length === 0) return;

            const previewRows = this.csvData.slice(0, 5);
            let html = `
                <div class="alert alert-info">
                    <i class="fa fa-info-circle"></i>
                    Found <strong>${this.csvData.length}</strong> records to import
                </div>
                <div class="table-responsive">
                    <table class="table table-sm table-bordered">
                        <thead class="table-light">
                            <tr>
                                ${this.headers.map(h => `<th>${this._escapeHtml(h)}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${previewRows.map(row => `
                                <tr>
                                    ${this.headers.map(h => `<td>${this._escapeHtml(row[h.toLowerCase().trim()] || '')}</td>`).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ${this.csvData.length > 5 ? `<p class="text-muted">Showing first 5 of ${this.csvData.length} records...</p>` : ''}
            `;

            previewContainer.innerHTML = html;
            previewContainer.classList.remove('d-none');
        }

        _validateData() {
            const errors = [];
            const requiredFields = ['name'];
            const emailField = 'email';

            this.csvData.forEach((row, idx) => {
                // Check required fields
                requiredFields.forEach(field => {
                    if (!row[field]) {
                        errors.push({ row: idx + 2, field: field, message: `Missing required field: ${field}` });
                    }
                });

                // Validate email if present
                if (row[emailField] && !this._isValidEmail(row[emailField])) {
                    errors.push({ row: idx + 2, field: emailField, message: 'Invalid email format' });
                }
            });

            return errors;
        }

        _isValidEmail(email) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        }

        async _startImport() {
            const validationErrors = this._validateData();
            if (validationErrors.length > 0) {
                this._showValidationErrors(validationErrors);
                return;
            }

            this._showProgress(0, this.csvData.length);
            this.importErrors = [];
            this.importSuccess = 0;

            const batches = this._createBatches(this.csvData, this.batchSize);
            let processed = 0;

            for (const batch of batches) {
                try {
                    const result = await this._importBatch(batch);
                    this.importSuccess += result.success || 0;
                    if (result.errors) {
                        this.importErrors.push(...result.errors);
                    }
                } catch (err) {
                    batch.forEach((_, idx) => {
                        this.importErrors.push({
                            row: processed + idx + 2,
                            message: err.message || 'Network error'
                        });
                    });
                }

                processed += batch.length;
                this._showProgress(processed, this.csvData.length);
            }

            this._showResults();
        }

        _createBatches(data, size) {
            const batches = [];
            for (let i = 0; i < data.length; i += size) {
                batches.push(data.slice(i, i + size));
            }
            return batches;
        }

        async _importBatch(batch) {
            const response = await fetch('/my/contacts/import/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { records: batch },
                    id: Math.floor(Math.random() * 1000000)
                })
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error.message || 'Import failed');
            }
            return data.result || {};
        }

        _showProgress(current, total) {
            const percent = Math.round((current / total) * 100);
            const progressBar = this.container.querySelector('#import-progress-bar');
            const progressText = this.container.querySelector('#import-progress-text');
            const progressContainer = this.container.querySelector('#import-progress');

            if (progressContainer) {
                progressContainer.classList.remove('d-none');
            }
            if (progressBar) {
                progressBar.style.width = `${percent}%`;
                progressBar.setAttribute('aria-valuenow', percent);
            }
            if (progressText) {
                progressText.textContent = `Processing ${current} of ${total} records...`;
            }
        }

        _showResults() {
            this._renderStep(3);

            const resultsContainer = this.container.querySelector('#import-results');
            if (!resultsContainer) return;

            let html = `
                <div class="alert alert-${this.importErrors.length === 0 ? 'success' : 'warning'}">
                    <h5><i class="fa fa-${this.importErrors.length === 0 ? 'check-circle' : 'exclamation-triangle'}"></i> Import Complete</h5>
                    <p>
                        <strong>${this.importSuccess}</strong> records imported successfully.
                        ${this.importErrors.length > 0 ? `<strong>${this.importErrors.length}</strong> errors.` : ''}
                    </p>
                </div>
            `;

            if (this.importErrors.length > 0) {
                html += `
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <span>Errors</span>
                            <button type="button" class="btn btn-sm btn-outline-secondary" data-action="download-errors">
                                <i class="fa fa-download"></i> Download Errors
                            </button>
                        </div>
                        <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                            <table class="table table-sm">
                                <thead>
                                    <tr><th>Row</th><th>Error</th></tr>
                                </thead>
                                <tbody>
                                    ${this.importErrors.slice(0, 20).map(err => `
                                        <tr>
                                            <td>${err.row}</td>
                                            <td>${this._escapeHtml(err.message)}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                            ${this.importErrors.length > 20 ? `<p class="text-muted">Showing first 20 of ${this.importErrors.length} errors...</p>` : ''}
                        </div>
                    </div>
                `;
            }

            resultsContainer.innerHTML = html;
        }

        _showValidationErrors(errors) {
            const container = this.container.querySelector('#validation-errors');
            if (!container) return;

            container.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="fa fa-exclamation-circle"></i> Validation Errors</h6>
                    <ul class="mb-0">
                        ${errors.slice(0, 10).map(err => `
                            <li>Row ${err.row}: ${this._escapeHtml(err.message)}</li>
                        `).join('')}
                    </ul>
                    ${errors.length > 10 ? `<p class="mb-0 mt-2">...and ${errors.length - 10} more errors</p>` : ''}
                </div>
            `;
            container.classList.remove('d-none');
        }

        _showError(message) {
            const container = this.container.querySelector('#csv-error');
            if (container) {
                container.innerHTML = `<div class="alert alert-danger">${this._escapeHtml(message)}</div>`;
                container.classList.remove('d-none');
            }
        }

        _downloadTemplate() {
            const headers = ['name', 'email', 'phone', 'street', 'city', 'zip', 'country'];
            const example = ['John Doe', 'john@example.com', '555-0100', '123 Main St', 'Anytown', '12345', 'US'];
            const csv = headers.join(',') + '\n' + example.join(',');
            
            this._downloadFile('contact_import_template.csv', csv, 'text/csv');
        }

        _downloadErrors() {
            if (!this.importErrors || this.importErrors.length === 0) return;

            const csv = 'Row,Error\n' + this.importErrors.map(e => `${e.row},"${e.message}"`).join('\n');
            this._downloadFile('import_errors.csv', csv, 'text/csv');
        }

        _downloadFile(filename, content, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        _renderStep(step) {
            this.currentStep = step;
            const steps = this.container.querySelectorAll('[data-step]');
            steps.forEach(s => {
                s.classList.toggle('d-none', parseInt(s.dataset.step, 10) !== step);
            });

            // Update step indicators
            const indicators = this.container.querySelectorAll('.step-indicator');
            indicators.forEach((ind, idx) => {
                ind.classList.toggle('active', idx + 1 === step);
                ind.classList.toggle('completed', idx + 1 < step);
            });
        }

        _nextStep() {
            if (this.currentStep < 3) {
                this._renderStep(this.currentStep + 1);
            }
        }

        _prevStep() {
            if (this.currentStep > 1) {
                this._renderStep(this.currentStep - 1);
            }
        }

        _enableNextStep() {
            const btn = this.container.querySelector('[data-action="next-step"]');
            if (btn) {
                btn.disabled = false;
            }
        }

        _escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }

    // ========================================================================
    // Auto-initialization
    // ========================================================================
    function initUserImport() {
        const containers = document.querySelectorAll('.o_portal_user_import');
        containers.forEach(container => {
            new PortalUserImport(container);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initUserImport);
    } else {
        initUserImport();
    }

    // Export globally
    window.PortalUserImport = PortalUserImport;

})();
