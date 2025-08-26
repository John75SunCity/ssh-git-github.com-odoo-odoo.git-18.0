# -*- coding: utf-8 -*-
"""
Field Label Customization Portal Controller

Provides API endpoints for getting custom field labels in portal interfaces.
Supports customer-specific field label customization and transitory field
configuration for Records Management portal operations.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

# Standard library imports
import logging

# Odoo core imports
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError

# Odoo addons imports
from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class FieldLabelPortalController(CustomerPortal):
    """
    Portal controller for field label customization

    Provides API endpoints for retrieving custom field labels and configurations
    for portal users, enabling customer-specific field naming conventions.
    """

    @http.route(['/portal/field-labels/get'], type='json', auth="user", methods=['POST'], website=True)
    def get_field_labels(self, customer_id=None, department_id=None):
        """
        API endpoint to get custom field labels for a customer/department

        Args:
            customer_id (int, optional): Customer ID for label context
            department_id (int, optional): Department ID for specific context

        Returns:
            dict: Success status and field labels or error message
        """
        try:
            # Validate portal access
            if not request.env.user.has_group('base.group_portal'):
                return {'error': _('Access denied - Portal access required')}

            # Determine customer context
            resolved_customer_id = self._resolve_customer_id(customer_id)
            if not resolved_customer_id:
                return {'error': _('No customer context available')}

            # Get field labels with proper security context
            labels = request.env['field.label.customization'].sudo().get_labels_for_context(
                customer_id=resolved_customer_id,
                department_id=department_id
            )

            return {
                'success': True,
                'labels': labels,
                'customer_id': resolved_customer_id,
                'department_id': department_id
            }

        except AccessError as e:
            _logger.warning("Access denied in get_field_labels: %s", str(e))
            return {'error': _('Access denied')}
        except Exception as e:
            _logger.error("Error in get_field_labels: %s", str(e))
            return {'error': _('Failed to retrieve field labels: %s') % str(e)}

    @http.route(['/portal/field-labels/transitory-config'], type='json', auth="user", methods=['POST'], website=True)
    def get_transitory_field_config(self, customer_id=None, department_id=None):
        """
        Get complete field configuration for transitory items including labels

        Args:
            customer_id (int, optional): Customer ID for configuration context
            department_id (int, optional): Department ID for specific context

        Returns:
            dict: Complete field configuration with labels and settings
        """
        try:
            # Validate portal access
            if not request.env.user.has_group('base.group_portal'):
                return {'error': _('Access denied - Portal access required')}

            # Determine customer context
            resolved_customer_id = self._resolve_customer_id(customer_id)
            if not resolved_customer_id:
                return {'error': _('No customer context available')}

            # Get customer and configuration
            customer = request.env['res.partner'].sudo().browse(resolved_customer_id)
            if not customer.exists():
                return {'error': _('Customer not found')}

            # Get transitory field configuration
            config = customer.get_transitory_field_config()

            # Apply department-specific overrides if provided
            if department_id:
                config = self._apply_department_overrides(config, department_id, resolved_customer_id)

            return {
                'success': True,
                'config': config,
                'customer_name': customer.name,
                'customer_id': resolved_customer_id,
                'department_id': department_id,
            }

        except AccessError as e:
            _logger.warning("Access denied in get_transitory_field_config: %s", str(e))
            return {'error': _('Access denied')}
        except Exception as e:
            _logger.error("Error in get_transitory_field_config: %s", str(e))
            return {'error': _('Failed to retrieve field configuration: %s') % str(e)}

    @http.route(['/portal/field-labels/validate'], type='json', auth="user", methods=['POST'], website=True)
    def validate_field_values(self, field_values, customer_id=None, department_id=None):
        """
        Validate field values against customer-specific rules

        Args:
            field_values (dict): Field values to validate
            customer_id (int, optional): Customer context
            department_id (int, optional): Department context

        Returns:
            dict: Validation results with errors and warnings
        """
        try:
            if not request.env.user.has_group('base.group_portal'):
                return {'error': _('Access denied - Portal access required')}

            resolved_customer_id = self._resolve_customer_id(customer_id)
            if not resolved_customer_id:
                return {'error': _('No customer context available')}

            # Get field configuration for validation
            customer = request.env['res.partner'].sudo().browse(resolved_customer_id)
            config = customer.get_transitory_field_config()

            # Validate each field
            validation_results = {
                'valid': True,
                'errors': {},
                'warnings': {},
                'processed_fields': len(field_values)
            }

            for field_name, field_value in field_values.items():
                field_config = config.get(field_name, {})

                # Required field validation
                if field_config.get('required', False) and not field_value:
                    validation_results['errors'][field_name] = _('This field is required')
                    validation_results['valid'] = False

                # Custom validation rules
                if field_value and field_config.get('validation_pattern'):
                    if not self._validate_field_pattern(field_value, field_config['validation_pattern']):
                        validation_results['errors'][field_name] = _(
                            'Value does not match required format'
                        )
                        validation_results['valid'] = False

            return {
                'success': True,
                'validation': validation_results
            }

        except Exception as e:
            _logger.error("Error in validate_field_values: %s", str(e))
            return {'error': _('Validation failed: %s') % str(e)}

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _resolve_customer_id(self, provided_customer_id):
        """
        Resolve customer ID from provided value or current user context

        Args:
            provided_customer_id (int, optional): Explicitly provided customer ID

        Returns:
            int: Resolved customer ID or None
        """
        if provided_customer_id:
            return int(provided_customer_id)

        # Try to get from current user's partner context
        user_partner = request.env.user.partner_id

        if user_partner.is_company:
            return user_partner.id
        elif user_partner.parent_id:
            return user_partner.parent_id.id

        return None

    def _apply_department_overrides(self, base_config, department_id, customer_id):
        """
        Apply department-specific configuration overrides

        Args:
            base_config (dict): Base customer configuration
            department_id (int): Department ID for overrides
            customer_id (int): Customer context

        Returns:
            dict: Configuration with department overrides applied
        """
        try:
            # Get department-specific label customizations
            department_labels = request.env['field.label.customization'].sudo().search([
                ('customer_id', '=', customer_id),
                ('department_id', '=', department_id),
                ('active', '=', True)
            ])

            if department_labels:
                # Apply department-specific labels to configuration
                for label_config in department_labels:
                    field_name = label_config.field_name
                    if field_name in base_config:
                        base_config[field_name].update({
                            'label': label_config.custom_label,
                            'help_text': label_config.help_text,
                            'department_override': True
                        })

            return base_config

        except Exception as e:
            _logger.warning("Failed to apply department overrides: %s", str(e))
            return base_config

    def _validate_field_pattern(self, value, pattern):
        """
        Validate field value against pattern

        Args:
            value (str): Field value to validate
            pattern (str): Validation pattern

        Returns:
            bool: True if value matches pattern
        """
        import re
        try:
            return bool(re.match(pattern, str(value)))
        except re.error:
            _logger.warning("Invalid regex pattern: %s", pattern)
            return True  # Allow value if pattern is invalid


class FieldLabelAdminController(http.Controller):
    """
    Administrative controller for field label management

    Provides management interface for Records Management administrators
    to preview and configure field label customizations.
    """

    @http.route(['/records/admin/field-labels/preview'], type='json', auth="user", methods=['POST'], website=True)
    def preview_field_labels(self, customer_id=None, department_id=None):
        """
        Preview field labels for admin users

        Args:
            customer_id (int, optional): Customer ID for preview context
            department_id (int, optional): Department ID for preview context

        Returns:
            dict: Field labels and configuration preview
        """
        try:
            # Validate manager access
            if not request.env.user.has_group('records_management.group_records_manager'):
                return {'error': _('Access denied - Manager access required')}

            # Get field labels for preview
            labels = request.env['field.label.customization'].get_labels_for_context(
                customer_id=customer_id,
                department_id=department_id
            )

            # Get field configuration if customer provided
            config = {}
            customer_name = None
            if customer_id:
                customer = request.env['res.partner'].browse(customer_id)
                if customer.exists():
                    config = customer.get_transitory_field_config()
                    customer_name = customer.name

            return {
                'success': True,
                'labels': labels,
                'config': config,
                'preview_context': {
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'department_id': department_id
                }
            }

        except AccessError as e:
            _logger.warning("Access denied in preview_field_labels: %s", str(e))
            return {'error': _('Access denied')}
        except Exception as e:
            _logger.error("Error in preview_field_labels: %s", str(e))
            return {'error': _('Preview failed: %s') % str(e)}

    @http.route(['/records/admin/field-labels/apply-preset'], type='json', auth="user", methods=['POST'], website=True)
    def apply_label_preset(self, config_id, preset_name):
        """
        Apply a preset to a field label configuration

        Args:
            config_id (int): Field label configuration ID
            preset_name (str): Name of preset to apply

        Returns:
            dict: Success status and message
        """
        try:
            # Validate manager access
            if not request.env.user.has_group('records_management.group_records_manager'):
                return {'error': _('Access denied - Manager access required')}

            # Get and validate configuration
            config = request.env['field.label.customization'].browse(config_id)
            if not config.exists():
                return {'error': _('Configuration not found')}

            # Available presets mapping
            preset_methods = {
                'corporate': config.action_apply_corporate_preset,
                'legal': config.action_apply_legal_preset,
                'healthcare': config.action_apply_healthcare_preset,
                'financial': config.action_apply_financial_preset,
                'manufacturing': config.action_apply_manufacturing_preset,
                'government': config.action_apply_government_preset,
            }

            # Apply selected preset
            if preset_name not in preset_methods:
                return {'error': _('Unknown preset: %s') % preset_name}

            preset_methods[preset_name]()

            # Log the action
            _logger.info("Applied %s preset to configuration %d by user %s",
                        preset_name, config_id, request.env.user.name)

            return {
                'success': True,
                'message': _('%s preset applied successfully') % preset_name.title(),
                'preset_applied': preset_name,
                'config_id': config_id
            }

        except AccessError as e:
            _logger.warning("Access denied in apply_label_preset: %s", str(e))
            return {'error': _('Access denied')}
        except Exception as e:
            _logger.error("Error applying preset %s: %s", preset_name, str(e))
            return {'error': _('Failed to apply preset: %s') % str(e)}

    @http.route(['/records/admin/field-labels/bulk-update'], type='json', auth="user", methods=['POST'], website=True)
    def bulk_update_labels(self, updates):
        """
        Bulk update multiple field label configurations

        Args:
            updates (list): List of update dictionaries with config_id and changes

        Returns:
            dict: Bulk update results
        """
        try:
            if not request.env.user.has_group('records_management.group_records_manager'):
                return {'error': _('Access denied - Manager access required')}

            if not updates or not isinstance(updates, list):
                return {'error': _('Invalid update data provided')}

            results = {
                'success': True,
                'updated': 0,
                'failed': 0,
                'errors': []
            }

            for update_data in updates:
                try:
                    config_id = update_data.get('config_id')
                    changes = update_data.get('changes', {})

                    if not config_id or not changes:
                        results['errors'].append(_('Invalid update data for config ID: %s') % config_id)
                        results['failed'] += 1
                        continue

                    config = request.env['field.label.customization'].browse(config_id)
                    if not config.exists():
                        results['errors'].append(_('Configuration not found: %s') % config_id)
                        results['failed'] += 1
                        continue

                    config.write(changes)
                    results['updated'] += 1

                except Exception as e:
                    results['errors'].append(_('Failed to update config %s: %s') % (
                                           update_data.get('config_id'), str(e)))
                    results['failed'] += 1

            if results['failed'] > 0:
                results['success'] = False

            return results

        except Exception as e:
            _logger.error("Error in bulk_update_labels: %s", str(e))
            return {'error': _('Bulk update failed: %s') % str(e)}

    @http.route(['/records/admin/field-labels/export'], type='http', auth="user", methods=['GET'], website=True)
    def export_label_configuration(self, customer_id=None, format='csv'):
        """
        Export field label configuration

        Args:
            customer_id (int, optional): Customer ID to filter export
            format (str): Export format (csv, xlsx)

        Returns:
            Response: File download response
        """
        try:
            if not request.env.user.has_group('records_management.group_records_manager'):
                return request.redirect('/web/login?redirect=/records/admin/field-labels')

            # Build domain for export
            domain = [('active', '=', True)]
            if customer_id:
                domain.append(('customer_id', '=', int(customer_id)))

            # Get configurations
            configs = request.env['field.label.customization'].search(domain)

            if format == 'xlsx':
                return self._export_xlsx(configs, customer_id)
            else:
                return self._export_csv(configs, customer_id)

        except Exception as e:
            _logger.error("Error exporting label configuration: %s", str(e))
            return request.redirect('/web#view_type=form&model=ir.logging')

    def _export_csv(self, configs, customer_id):
        """Export configurations as CSV"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Customer', 'Department', 'Model', 'Field Name',
            'Original Label', 'Custom Label', 'Help Text', 'Active'
        ])

        # Write data
        for config in configs:
            writer.writerow([
                config.customer_id.name if config.customer_id else '',
                config.department_id.name if config.department_id else '',
                config.model_name,
                config.field_name,
                config.original_label,
                config.custom_label,
                config.help_text or '',
                'Yes' if config.active else 'No'
            ])

        filename = 'field_labels'
        if customer_id:
            customer_name = request.env['res.partner'].browse(customer_id).name
            filename += f'_{customer_name.replace(" ", "_")}'
        filename += '.csv'

        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', f'attachment; filename={filename}')
            ]
        )

    def _export_xlsx(self, configs, customer_id):
        """Export configurations as Excel"""
        try:
            import xlsxwriter
            import io

            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('Field Labels')

            # Headers
            headers = [
                'Customer', 'Department', 'Model', 'Field Name',
                'Original Label', 'Custom Label', 'Help Text', 'Active'
            ]

            # Write headers with formatting
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D7E4BC',
                'border': 1
            })

            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)

            # Write data
            for row, config in enumerate(configs, 1):
                worksheet.write(row, 0, config.customer_id.name if config.customer_id else '')
                worksheet.write(row, 1, config.department_id.name if config.department_id else '')
                worksheet.write(row, 2, config.model_name)
                worksheet.write(row, 3, config.field_name)
                worksheet.write(row, 4, config.original_label)
                worksheet.write(row, 5, config.custom_label)
                worksheet.write(row, 6, config.help_text or '')
                worksheet.write(row, 7, 'Yes' if config.active else 'No')

            workbook.close()
            output.seek(0)

            filename = 'field_labels'
            if customer_id:
                customer_name = request.env['res.partner'].browse(customer_id).name
                filename += f'_{customer_name.replace(" ", "_")}'
            filename += '.xlsx'

            return request.make_response(
                output.getvalue(),
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', f'attachment; filename={filename}')
                ]
            )

        except ImportError:
            # Fallback to CSV if xlsxwriter not available
            return self._export_csv(configs, customer_id)
