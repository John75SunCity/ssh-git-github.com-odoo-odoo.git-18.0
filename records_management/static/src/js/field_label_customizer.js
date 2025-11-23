/* Field Label Customization Widget for Portal
 * Dynamically updates field labels based on customer configuration
 * Odoo 18 Compatible - Pure JavaScript implementation
 */

(function () {
'use strict';

/**
 * Field Label Customizer - Vanilla JS implementation for portal
 */
var FieldLabelCustomizer = {
    selector: '.o_portal_field_customizer',
    
    /**
     * Initialize the customizer
     */
    init: function () {
        var self = this;
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                self._loadCustomLabels();
            });
        } else {
            self._loadCustomLabels();
        }
    },
    
    /**
     * Load custom field labels from the server
     * @private
     */
    _loadCustomLabels: function () {
        var self = this;
        var elements = document.querySelectorAll(this.selector);
        
        if (elements.length === 0) {
            return;
        }
        
        var element = elements[0];
        var customerId = element.dataset.customerId;
        var departmentId = element.dataset.departmentId;
        
        fetch('/portal/field-labels/get', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ 
                jsonrpc: '2.0', 
                method: 'call', 
                params: {
                    customer_id: customerId,
                    department_id: departmentId
                }
            })
        })
        .then(function(response) { return response.json(); })
        .then(function(result) {
            if (result.result && result.result.success && result.result.labels) {
                self._applyCustomLabels(result.result.labels);
            }
        })
        .catch(function (error) {
            console.warn('Failed to load custom field labels:', error);
        });
    },
    
    /**
     * Apply custom labels to form fields
     * @private
     * @param {Object} labels - Dictionary of field names to custom labels
     */
    _applyCustomLabels: function (labels) {
        var self = this;
        var containers = document.querySelectorAll(this.selector);
        
        containers.forEach(function(container) {
            // Update field labels based on data attributes
            container.querySelectorAll('[data-field-name]').forEach(function (element) {
                var fieldName = element.dataset.fieldName;
                
                if (labels[fieldName]) {
                    var customLabel = labels[fieldName];
                    
                    // Update label text
                    if (element.tagName.toLowerCase() === 'label') {
                        element.textContent = customLabel;
                    } else {
                        // Update associated label
                        var labelFor = element.getAttribute('id');
                        if (labelFor) {
                            var label = document.querySelector('label[for="' + labelFor + '"]');
                            if (label) {
                                label.textContent = customLabel;
                            }
                        }
                        
                        // Update placeholder if exists
                        if (element.hasAttribute('placeholder')) {
                            element.setAttribute('placeholder', customLabel);
                        }
                    }
                    
                    // Update help text if it references the field name
                    var helpText = element.nextElementSibling;
                    if (helpText && (helpText.classList.contains('text-muted') || helpText.classList.contains('help-block'))) {
                        var helpContent = helpText.textContent;
                        var defaultLabel = self._getDefaultLabel(fieldName);
                        if (defaultLabel && helpContent.includes(defaultLabel)) {
                            helpText.textContent = helpContent.replace(defaultLabel, customLabel);
                        }
                    }
                }
            });
        });
        
        // Update form headings and section titles
        this._updateFormHeadings(labels);
        
        // Update table headers if any
        this._updateTableHeaders(labels);
    },
    
    /**
     * Update form section headings
     * @private
     * @param {Object} labels
     */
    _updateFormHeadings: function (labels) {
        var self = this;
        var containers = document.querySelectorAll(this.selector);
        
        containers.forEach(function(container) {
            // Update section headings that might reference field names
            container.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(function (heading) {
                var headingText = heading.textContent;
                
                // Check if heading contains field references
                Object.keys(labels).forEach(function (fieldName) {
                    var defaultLabel = self._getDefaultLabel(fieldName);
                    if (defaultLabel && headingText.includes(defaultLabel)) {
                        var newText = headingText.replace(defaultLabel, labels[fieldName]);
                        heading.textContent = newText;
                    }
                });
            });
        });
    },
    
    /**
     * Update table headers
     * @private
     * @param {Object} labels
     */
    _updateTableHeaders: function (labels) {
        var containers = document.querySelectorAll(this.selector);
        
        containers.forEach(function(container) {
            container.querySelectorAll('table th[data-field-name]').forEach(function (th) {
                var fieldName = th.dataset.fieldName;
                
                if (labels[fieldName]) {
                    th.textContent = labels[fieldName];
                }
            });
        });
    },
    
    /**
     * Get default label for a field name
     * @private
     * @param {string} fieldName
     * @returns {string}
     */
    _getDefaultLabel: function (fieldName) {
        var defaultLabels = {
            'container_number': 'Container Number',
            'item_description': 'Item Description',
            'content_description': 'Content Description',
            'date_from': 'Date From',
            'date_to': 'Date To',
            'sequence_from': 'Sequence From',
            'sequence_to': 'Sequence To',
            'destruction_date': 'Destruction Date',
            'record_type': 'Record Type',
            'confidentiality': 'Confidentiality Level',
            'project_code': 'Project Code',
            'client_reference': 'Client Reference',
            'file_count': 'Number of Files',
            'filing_system': 'Filing System',
            'created_by_dept': 'Created By Department',
            'authorized_by': 'Authorized By',
            'special_handling': 'Special Handling Instructions',
            'compliance_notes': 'Compliance Notes',
            'weight_estimate': 'Estimated Weight',
            'size_estimate': 'Estimated Size',
            'parent_container': 'Parent Container',
            'folder_type': 'Item Type',
            'hierarchy_display': 'Location Path'
        };
        
        return defaultLabels[fieldName] || fieldName.replace('_', ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); });
    }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        FieldLabelCustomizer.init();
    });
} else {
    FieldLabelCustomizer.init();
}

// Make available globally for manual initialization if needed
if (typeof window !== 'undefined') {
    window.RecordsManagementFieldLabelCustomizer = FieldLabelCustomizer;
}

})();
