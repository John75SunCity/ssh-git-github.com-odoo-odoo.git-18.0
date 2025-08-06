/* Field Label Customization Widget for Portal
 * Dynamically updates field labels based on customer configuration
 */

odoo.define('records_management.FieldLabelCustomizer', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var ajax = require('web.ajax');

var FieldLabelCustomizer = publicWidget.Widget.extend({
    selector: '.o_portal_field_customizer',
    
    /**
     * @override
     */
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self._loadCustomLabels();
        });
    },
    
    /**
     * Load custom field labels from the server
     * @private
     */
    _loadCustomLabels: function () {
        var self = this;
        var customerId = this.$el.data('customer-id');
        var departmentId = this.$el.data('department-id');
        
        return ajax.jsonRpc('/portal/field-labels/get', 'call', {
            customer_id: customerId,
            department_id: departmentId
        }).then(function (result) {
            if (result.success && result.labels) {
                self._applyCustomLabels(result.labels);
            }
        }).catch(function (error) {
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
        
        // Update field labels based on data attributes
        this.$el.find('[data-field-name]').each(function () {
            var $element = $(this);
            var fieldName = $element.data('field-name');
            
            if (labels[fieldName]) {
                var customLabel = labels[fieldName];
                
                // Update label text
                if ($element.is('label')) {
                    $element.text(customLabel);
                } else {
                    // Update associated label
                    var labelFor = $element.attr('id');
                    if (labelFor) {
                        $('label[for="' + labelFor + '"]').text(customLabel);
                    }
                    
                    // Update placeholder if exists
                    if ($element.attr('placeholder')) {
                        $element.attr('placeholder', customLabel);
                    }
                }
                
                // Update help text if it references the field name
                var $helpText = $element.siblings('.text-muted, .help-block');
                if ($helpText.length) {
                    var helpContent = $helpText.text();
                    // Simple replacement of field name in help text
                    var defaultLabel = self._getDefaultLabel(fieldName);
                    if (defaultLabel && helpContent.includes(defaultLabel)) {
                        $helpText.text(helpContent.replace(defaultLabel, customLabel));
                    }
                }
            }
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
        // Update section headings that might reference field names
        this.$el.find('h1, h2, h3, h4, h5, h6').each(function () {
            var $heading = $(this);
            var headingText = $heading.text();
            
            // Check if heading contains field references
            Object.keys(labels).forEach(function (fieldName) {
                var defaultLabel = this._getDefaultLabel(fieldName);
                if (defaultLabel && headingText.includes(defaultLabel)) {
                    var newText = headingText.replace(defaultLabel, labels[fieldName]);
                    $heading.text(newText);
                }
            }.bind(this));
        }.bind(this));
    },
    
    /**
     * Update table headers
     * @private
     * @param {Object} labels
     */
    _updateTableHeaders: function (labels) {
        this.$el.find('table th[data-field-name]').each(function () {
            var $th = $(this);
            var fieldName = $th.data('field-name');
            
            if (labels[fieldName]) {
                $th.text(labels[fieldName]);
            }
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
        
        return defaultLabels[fieldName] || fieldName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
});

// Also export a utility function for direct use
var loadTransitoryFieldConfig = function (customerId, departmentId) {
    return ajax.jsonRpc('/portal/field-labels/transitory-config', 'call', {
        customer_id: customerId,
        department_id: departmentId
    });
};

// Auto-initialize on portal pages
publicWidget.registry.FieldLabelCustomizer = FieldLabelCustomizer;

return {
    FieldLabelCustomizer: FieldLabelCustomizer,
    loadTransitoryFieldConfig: loadTransitoryFieldConfig
};

});
