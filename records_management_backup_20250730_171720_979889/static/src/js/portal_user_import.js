odoo.define('records_management.portal_user_import', function (require) {
    "use strict";

    var core = require('web.core');
    var ajax = require('web.ajax');
    var Dialog = require('web.Dialog');
    var _t = core._t;

    var PortalUserImport = {
        init: function() {
            this.csvData = [];
            this.validationErrors = [];
            this.importProgress = 0;
            this.totalRows = 0;
            this.setupEventHandlers();
        },

        setupEventHandlers: function() {
            var self = this;

            // File input change handler
            $(document).on('change', '#csv_file_input', function(e) {
                self.handleFileSelect(e);
            });

            // Import button handler
            $(document).on('click', '#start_import_btn', function(e) {
                e.preventDefault();
                self.startImport();
            });

            // Download template button
            $(document).on('click', '#download_template_btn', function(e) {
                e.preventDefault();
                self.downloadTemplate();
            });

            // Cancel import handler
            $(document).on('click', '#cancel_import_btn', function(e) {
                e.preventDefault();
                self.cancelImport();
            });

            // Drag and drop handlers
            $(document).on('dragover', '#csv_drop_zone', function(e) {
                e.preventDefault();
                $(this).addClass('drag-over');
            });

            $(document).on('dragleave', '#csv_drop_zone', function(e) {
                e.preventDefault();
                $(this).removeClass('drag-over');
            });

            $(document).on('drop', '#csv_drop_zone', function(e) {
                e.preventDefault();
                $(this).removeClass('drag-over');
                var files = e.originalEvent.dataTransfer.files;
                if (files.length > 0) {
                    self.processFile(files[0]);
                }
            });
        },

        handleFileSelect: function(event) {
            var file = event.target.files[0];
            if (file) {
                this.processFile(file);
            }
        },

        processFile: function(file) {
            var self = this;

            // Validate file type
            if (!file.name.toLowerCase().endsWith('.csv')) {
                self.showError(_t('Please select a CSV file.'));
                return;
            }

            // Validate file size (5MB limit)
            if (file.size > 5 * 1024 * 1024) {
                self.showError(_t('File size must be less than 5MB.'));
                return;
            }

            // Show loading state
            self.showLoadingState();

            var reader = new FileReader();
            reader.onload = function(e) {
                try {
                    self.parseCSV(e.target.result);
                } catch (error) {
                    self.showError(_t('Error reading file: ') + error.message);
                    self.hideLoadingState();
                }
            };

            reader.onerror = function() {
                self.showError(_t('Error reading file.'));
                self.hideLoadingState();
            };

            reader.readAsText(file);
        },

        parseCSV: function(csvText) {
            var self = this;
            
            try {
                // Parse CSV with proper handling of quotes and commas
                var lines = csvText.split('\n');
                var headers = this.parseCSVLine(lines[0]);
                var data = [];

                // Validate headers
                var requiredHeaders = ['name', 'email', 'phone'];
                var missingHeaders = requiredHeaders.filter(h => !headers.includes(h));
                
                if (missingHeaders.length > 0) {
                    self.showError(_t('Missing required columns: ') + missingHeaders.join(', '));
                    self.hideLoadingState();
                    return;
                }

                // Parse data rows
                for (var i = 1; i < lines.length; i++) {
                    if (lines[i].trim()) {
                        var rowData = this.parseCSVLine(lines[i]);
                        if (rowData.length === headers.length) {
                            var rowObject = {};
                            headers.forEach(function(header, index) {
                                rowObject[header] = rowData[index];
                            });
                            data.push(rowObject);
                        }
                    }
                }

                self.csvData = data;
                self.totalRows = data.length;
                
                // Validate data
                self.validateData();
                
                // Show preview
                self.showPreview(headers, data);
                self.hideLoadingState();

            } catch (error) {
                self.showError(_t('Error parsing CSV: ') + error.message);
                self.hideLoadingState();
            }
        },

        parseCSVLine: function(line) {
            var result = [];
            var current = '';
            var inQuotes = false;
            
            for (var i = 0; i < line.length; i++) {
                var char = line[i];
                
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
        },

        validateData: function() {
            var self = this;
            self.validationErrors = [];

            self.csvData.forEach(function(row, index) {
                var rowErrors = [];

                // Validate required fields
                if (!row.name || row.name.trim() === '') {
                    rowErrors.push('Name is required');
                }

                if (!row.email || row.email.trim() === '') {
                    rowErrors.push('Email is required');
                } else if (!self.isValidEmail(row.email)) {
                    rowErrors.push('Invalid email format');
                }

                if (!row.phone || row.phone.trim() === '') {
                    rowErrors.push('Phone is required');
                } else if (!self.isValidPhone(row.phone)) {
                    rowErrors.push('Invalid phone format');
                }

                if (rowErrors.length > 0) {
                    self.validationErrors.push({
                        row: index + 2, // +2 because of header and 0-based index
                        errors: rowErrors,
                        data: row
                    });
                }
            });
        },

        isValidEmail: function(email) {
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },

        isValidPhone: function(phone) {
            var phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
            return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
        },

        showPreview: function(headers, data) {
            var self = this;
            var previewContainer = $('#csv_preview_container');
            
            var html = `
                <div class="card mt-4">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0">
                            <i class="fa fa-eye"></i> CSV Preview
                            <span class="badge badge-light ml-2">${data.length} rows</span>
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive" style="max-height: 400px;">
                            <table class="table table-striped table-hover">
                                <thead class="thead-dark sticky-top">
                                    <tr>
                                        <th>#</th>
                                        ${headers.map(h => `<th>${h}</th>`).join('')}
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;

            data.slice(0, 50).forEach(function(row, index) {
                var hasError = self.validationErrors.some(e => e.row === index + 2);
                var rowClass = hasError ? 'table-danger' : 'table-success';
                
                html += `<tr class="${rowClass}">`;
                html += `<td>${index + 1}</td>`;
                
                headers.forEach(function(header) {
                    html += `<td>${self.escapeHtml(row[header] || '')}</td>`;
                });
                
                if (hasError) {
                    var errors = self.validationErrors.find(e => e.row === index + 2).errors;
                    html += `<td><span class="badge badge-danger" title="${errors.join(', ')}">Error</span></td>`;
                } else {
                    html += `<td><span class="badge badge-success">Valid</span></td>`;
                }
                
                html += '</tr>';
            });

            if (data.length > 50) {
                html += `
                    <tr>
                        <td colspan="${headers.length + 2}" class="text-center text-muted">
                            <i class="fa fa-info-circle"></i> Showing first 50 rows of ${data.length} total rows
                        </td>
                    </tr>
                `;
            }

            html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;

            // Show validation summary
            if (self.validationErrors.length > 0) {
                html += `
                    <div class="alert alert-warning mt-3">
                        <h6><i class="fa fa-exclamation-triangle"></i> Validation Issues Found</h6>
                        <p>${self.validationErrors.length} rows have validation errors. Please fix these issues before importing:</p>
                        <ul class="mb-0">
                `;
                
                self.validationErrors.slice(0, 10).forEach(function(error) {
                    html += `<li>Row ${error.row}: ${error.errors.join(', ')}</li>`;
                });
                
                if (self.validationErrors.length > 10) {
                    html += `<li>... and ${self.validationErrors.length - 10} more errors</li>`;
                }
                
                html += `
                        </ul>
                    </div>
                `;
            } else {
                html += `
                    <div class="alert alert-success mt-3">
                        <i class="fa fa-check-circle"></i> All rows validated successfully! Ready to import.
                        <button id="start_import_btn" class="btn btn-success btn-sm ml-2">
                            <i class="fa fa-upload"></i> Start Import
                        </button>
                    </div>
                `;
            }

            previewContainer.html(html);
            previewContainer.show();
        },

        startImport: function() {
            var self = this;

            if (self.validationErrors.length > 0) {
                self.showError(_t('Please fix validation errors before importing.'));
                return;
            }

            if (self.csvData.length === 0) {
                self.showError(_t('No data to import.'));
                return;
            }

            // Show progress modal
            self.showProgressModal();

            // Start import process
            self.importProgress = 0;
            self.processImportBatch(0);
        },

        processImportBatch: function(startIndex) {
            var self = this;
            var batchSize = 10; // Process 10 rows at a time
            var endIndex = Math.min(startIndex + batchSize, self.csvData.length);
            var batch = self.csvData.slice(startIndex, endIndex);

            ajax.jsonRpc('/my/users/import_batch', 'call', {
                'users_data': batch,
                'batch_index': Math.floor(startIndex / batchSize)
            }).then(function(result) {
                if (result.success) {
                    self.importProgress = endIndex;
                    self.updateProgress();

                    if (endIndex < self.csvData.length) {
                        // Continue with next batch
                        setTimeout(function() {
                            self.processImportBatch(endIndex);
                        }, 100);
                    } else {
                        // Import complete
                        self.importComplete(result);
                    }
                } else {
                    self.importError(result.error || 'Unknown error occurred');
                }
            }).catch(function(error) {
                self.importError(error.message || 'Network error occurred');
            });
        },

        updateProgress: function() {
            var percentage = Math.round((this.importProgress / this.totalRows) * 100);
            $('#import_progress_bar').css('width', percentage + '%').text(percentage + '%');
            $('#import_status_text').text(`Importing... ${this.importProgress} of ${this.totalRows} users processed`);
        },

        importComplete: function(result) {
            var self = this;
            
            $('#import_progress_modal .modal-body').html(`
                <div class="text-center">
                    <i class="fa fa-check-circle text-success" style="font-size: 3rem;"></i>
                    <h4 class="mt-3">Import Completed Successfully!</h4>
                    <p class="text-muted">
                        ${result.imported_count || self.totalRows} users have been imported successfully.
                    </p>
                    ${result.skipped_count ? `<p class="text-warning">
                        <i class="fa fa-exclamation-triangle"></i> 
                        ${result.skipped_count} users were skipped (already exist).
                    </p>` : ''}
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fa fa-refresh"></i> Refresh Page
                    </button>
                </div>
            `);

            setTimeout(function() {
                $('#import_progress_modal').modal('hide');
                location.reload();
            }, 3000);
        },

        importError: function(errorMessage) {
            $('#import_progress_modal .modal-body').html(`
                <div class="text-center">
                    <i class="fa fa-times-circle text-danger" style="font-size: 3rem;"></i>
                    <h4 class="mt-3">Import Failed</h4>
                    <p class="text-danger">${errorMessage}</p>
                    <button class="btn btn-secondary" data-dismiss="modal">
                        <i class="fa fa-times"></i> Close
                    </button>
                </div>
            `);
        },

        showProgressModal: function() {
            var modalHtml = `
                <div class="modal fade" id="import_progress_modal" tabindex="-1" role="dialog">
                    <div class="modal-dialog modal-dialog-centered" role="document">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="fa fa-upload"></i> Importing Users
                                </h5>
                            </div>
                            <div class="modal-body">
                                <div class="text-center mb-3">
                                    <i class="fa fa-users fa-2x text-primary"></i>
                                </div>
                                <div class="progress mb-3">
                                    <div id="import_progress_bar" class="progress-bar progress-bar-striped progress-bar-animated" 
                                         role="progressbar" style="width: 0%">0%</div>
                                </div>
                                <p id="import_status_text" class="text-center text-muted">
                                    Preparing import...
                                </p>
                                <div class="text-center">
                                    <button id="cancel_import_btn" class="btn btn-outline-danger btn-sm">
                                        <i class="fa fa-times"></i> Cancel Import
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            $('body').append(modalHtml);
            $('#import_progress_modal').modal({
                backdrop: 'static',
                keyboard: false
            });
        },

        cancelImport: function() {
            if (confirm(_t('Are you sure you want to cancel the import?'))) {
                location.reload();
            }
        },

        downloadTemplate: function() {
            var csvContent = 'name,email,phone,department,position,notes\n';
            csvContent += 'John Doe,john@example.com,+1-555-0123,IT,Manager,Sample user\n';
            csvContent += 'Jane Smith,jane@example.com,+1-555-0124,HR,Coordinator,Another sample';

            var blob = new Blob([csvContent], { type: 'text/csv' });
            var url = window.URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'user_import_template.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        },

        showLoadingState: function() {
            $('#csv_file_input').prop('disabled', true);
            $('#csv_drop_zone').addClass('loading');
            
            if ($('#loading_spinner').length === 0) {
                $('#csv_drop_zone').append(`
                    <div id="loading_spinner" class="text-center mt-3">
                        <i class="fa fa-spinner fa-spin fa-2x"></i>
                        <p class="mt-2">Processing file...</p>
                    </div>
                `);
            }
        },

        hideLoadingState: function() {
            $('#csv_file_input').prop('disabled', false);
            $('#csv_drop_zone').removeClass('loading');
            $('#loading_spinner').remove();
        },

        showError: function(message) {
            var alertHtml = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="fa fa-exclamation-circle"></i> ${message}
                    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
            `;
            
            $('#error_container').html(alertHtml);
        },

        escapeHtml: function(text) {
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };

    // Initialize when document is ready
    $(document).ready(function() {
        PortalUserImport.init();
    });

    return PortalUserImport;
});

/* CSS for enhanced styling - should be included in portal templates */
/*
.csv-drop-zone {
    border: 2px dashed #007cba;
    border-radius: 10px;
    padding: 40px;
    text-align: center;
    background: #f8f9fa;
    transition: all 0.3s ease;
    cursor: pointer;
}

.csv-drop-zone:hover, .csv-drop-zone.drag-over {
    border-color: #0056b3;
    background: #e3f2fd;
    transform: scale(1.02);
}

.csv-drop-zone.loading {
    background: #fff3cd;
    border-color: #ffc107;
}

.import-progress {
    position: relative;
    overflow: hidden;
}

.import-progress .progress-bar {
    transition: width 0.3s ease;
}

.validation-error {
    background-color: #f8d7da !important;
}

.validation-success {
    background-color: #d4edda !important;
}

.sticky-top {
    position: sticky;
    top: 0;
    z-index: 10;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

.loading .fa-spinner {
    animation: pulse 1.5s infinite;
}
*/
