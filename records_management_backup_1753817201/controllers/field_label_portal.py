# -*- coding: utf-8 -*-
"""
Field Label Customization Portal Controller
Provides API endpoints for getting custom field labels in portal
"""

import json
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class FieldLabelPortalController(CustomerPortal):
    
    @http.route(['/portal/field-labels/get'], type='json', auth="user", methods=['POST'], website=True)
    def get_field_labels(self, customer_id=None, department_id=None, **kwargs):
        """
        API endpoint to get custom field labels for a customer/department
        Used by portal forms to display custom field names
        """
        if not request.env.user.has_group('base.group_portal'):
            return {'error': 'Access denied'}
        
        # If no customer_id provided, try to get from current user's partner
        if not customer_id and request.env.user.partner_id.is_company:
            customer_id = request.env.user.partner_id.id
        elif not customer_id and request.env.user.partner_id.parent_id:
            customer_id = request.env.user.partner_id.parent_id.id
        
        if not customer_id:
            return {'error': 'No customer context available'}
        
        try:
            labels = request.env['field.label.customization'].sudo().get_labels_for_context(
                customer_id=customer_id,
                department_id=department_id
            )
            
            return {
                'success': True,
                'labels': labels,
                'customer_id': customer_id,
                'department_id': department_id
            }
        except Exception as e:
            return {'error': str(e)}
    
    @http.route(['/portal/field-labels/transitory-config'], type='json', auth="user", methods=['POST'], website=True)
    def get_transitory_field_config(self, customer_id=None, department_id=None, **kwargs):
        """
        Get complete field configuration for transitory items including labels
        """
        if not request.env.user.has_group('base.group_portal'):
            return {'error': 'Access denied'}
        
        # If no customer_id provided, try to get from current user's partner
        if not customer_id and request.env.user.partner_id.is_company:
            customer_id = request.env.user.partner_id.id
        elif not customer_id and request.env.user.partner_id.parent_id:
            customer_id = request.env.user.partner_id.parent_id.id
        
        if not customer_id:
            return {'error': 'No customer context available'}
        
        try:
            customer = request.env['res.partner'].sudo().browse(customer_id)
            config = customer.get_transitory_field_config()
            
            return {
                'success': True,
                'config': config,
                'customer_name': customer.name
            }
        except Exception as e:
            return {'error': str(e)}


class FieldLabelAdminController(http.Controller):
    
    @http.route(['/records/admin/field-labels/preview'], type='json', auth="user", methods=['POST'], website=True)
    def preview_field_labels(self, customer_id=None, department_id=None, **kwargs):
        """
        Preview field labels for admin users
        Shows how labels will appear for customers
        """
        if not request.env.user.has_group('records_management.group_records_manager'):
            return {'error': 'Access denied - Manager access required'}
        
        try:
            labels = request.env['field.label.customization'].get_labels_for_context(
                customer_id=customer_id,
                department_id=department_id
            )
            
            # Get field configuration if available
            config = {}
            if customer_id:
                customer = request.env['res.partner'].browse(customer_id)
                config = customer.get_transitory_field_config()
            
            return {
                'success': True,
                'labels': labels,
                'config': config,
                'preview_context': {
                    'customer_id': customer_id,
                    'department_id': department_id
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    @http.route(['/records/admin/field-labels/apply-preset'], type='json', auth="user", methods=['POST'], website=True)
    def apply_label_preset(self, config_id, preset_name, **kwargs):
        """
        Apply a preset to a field label configuration
        """
        if not request.env.user.has_group('records_management.group_records_manager'):
            return {'error': 'Access denied - Manager access required'}
        
        try:
            config = request.env['field.label.customization'].browse(config_id)
            if not config.exists():
                return {'error': 'Configuration not found'}
            
            preset_methods = {
                'corporate': config.action_apply_corporate_preset,
                'legal': config.action_apply_legal_preset,
                'healthcare': config.action_apply_healthcare_preset,
                'financial': config.action_apply_financial_preset,
            }
            
            if preset_name in preset_methods:
                preset_methods[preset_name]()
                return {
                    'success': True,
                    'message': f'{preset_name.title()} preset applied successfully'
                }
            else:
                return {'error': f'Unknown preset: {preset_name}'}
                
        except Exception as e:
            return {'error': str(e)}
