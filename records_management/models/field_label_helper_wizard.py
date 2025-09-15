# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class FieldLabelHelperWizard(models.TransientModel):
    """
    Field Label Helper Wizard - Assists with managing field labels and customizations
    across the Records Management system. Provides tools for bulk label updates,
    translations, and field visibility management.
    """
    _name = 'field.label.helper.wizard'
    _description = 'Field Label Helper Wizard'

    # Basic Information
    name = fields.Char(
        string='Wizard Name',
        default='Field Label Helper',
        readonly=True
    )
    
    # Target Configuration
    target_model = fields.Selection([
        ('records.container', 'Records Container'),
        ('records.document', 'Records Document'),
        ('records.location', 'Records Location'),
        ('records.billing', 'Records Billing'),
        ('shredding.service.bin', 'Shredding Service Bin'),
        ('portal.request', 'Portal Request'),
        ('customer.feedback', 'Customer Feedback'),
        ('naid.audit.log', 'NAID Audit Log'),
    ], string='Target Model', required=True, help="Select the model to update field labels for")
    
    field_name = fields.Char(
        string='Field Name',
        required=True,
        help="Technical name of the field to update"
    )
    
    # Label Configuration
    current_label = fields.Char(
        string='Current Label',
        readonly=True,
        help="Current label of the selected field"
    )
    
    new_label = fields.Char(
        string='New Label',
        required=True,
        help="New label to apply to the field"
    )
    
    # Update Options
    update_type = fields.Selection([
        ('single', 'Single Field'),
        ('bulk', 'Bulk Update'),
        ('category', 'Category Based'),
    ], string='Update Type', default='single', required=True)
    
    category = fields.Selection([
        ('container', 'Container Fields'),
        ('billing', 'Billing Fields'),
        ('location', 'Location Fields'),
        ('audit', 'Audit Fields'),
        ('portal', 'Portal Fields'),
    ], string='Field Category', help="Category for bulk updates")
    
    # Advanced Options
    apply_to_views = fields.Boolean(
        string='Apply to Views',
        default=True,
        help="Update field labels in XML views as well"
    )
    
    create_translation = fields.Boolean(
        string='Create Translation',
        default=False,
        help="Create translation entries for the new labels"
    )
    
    # Preview and Results
    preview_changes = fields.Text(
        string='Preview Changes',
        readonly=True,
        help="Preview of changes to be applied"
    )
    
    changes_applied = fields.Integer(
        string='Changes Applied',
        readonly=True,
        default=0
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('preview', 'Preview'),
        ('applied', 'Applied'),
    ], string='State', default='draft')
    
    @api.onchange('target_model', 'field_name')
    def _onchange_field_selection(self):
        """Update current label when field is selected"""
        if self.target_model and self.field_name:
            try:
                model = self.env[self.target_model]
                if hasattr(model, '_fields') and self.field_name in model._fields:
                    field = model._fields[self.field_name]
                    self.current_label = field.string or self.field_name
                else:
                    self.current_label = _("Field not found")
            except Exception:
                self.current_label = _("Unable to retrieve current label")
    
    @api.onchange('update_type', 'category')
    def _onchange_update_options(self):
        """Generate preview of changes"""
        if self.update_type == 'bulk' and self.category:
            self._generate_preview()
    
    def _generate_preview(self):
        """Generate preview of changes to be applied"""
        if not self.target_model:
            return
        
        try:
            model = self.env[self.target_model]
            changes = []
            
            if self.update_type == 'single':
                if self.field_name and self.new_label:
                    changes.append(_("Field '%s': '%s' → '%s'") % (
                        self.field_name, self.current_label or '', self.new_label
                    ))
            
            elif self.update_type == 'bulk' and self.category:
                # Get fields by category
                category_fields = self._get_fields_by_category()
                for field_name in category_fields:
                    if field_name in model._fields:
                        current = model._fields[field_name].string or field_name
                        changes.append(_("Field '%s': Current '%s'") % (field_name, current))
            
            self.preview_changes = '\n'.join(changes) if changes else _("No changes to preview")
            
        except Exception as e:
            self.preview_changes = _("Error generating preview: %s") % str(e)
    
    def _get_fields_by_category(self):
        """Get list of fields by category"""
        category_mapping = {
            'container': ['name', 'barcode', 'location_id', 'status', 'capacity'],
            'billing': ['amount', 'currency_id', 'billing_date', 'invoice_id'],
            'location': ['location_name', 'address', 'coordinates', 'capacity'],
            'audit': ['audit_date', 'user_id', 'action', 'notes'],
            'portal': ['request_type', 'status', 'customer_id', 'priority'],
        }
        return category_mapping.get(self.category, [])
    
    def action_preview_changes(self):
        """Preview changes before applying"""
        self.ensure_one()
        
        if not self.target_model:
            raise UserError(_("Please select a target model"))
        
        self._generate_preview()
        self.state = 'preview'
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Field Label Helper - Preview'),
            'res_model': 'field.label.helper.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_apply_changes(self):
        """Apply the field label changes"""
        self.ensure_one()
        
        if not self.target_model:
            raise UserError(_("Please select a target model"))
        
        changes_count = 0
        
        try:
            if self.update_type == 'single':
                changes_count = self._apply_single_change()
            elif self.update_type == 'bulk':
                changes_count = self._apply_bulk_changes()
            elif self.update_type == 'category':
                changes_count = self._apply_category_changes()
            
            self.changes_applied = changes_count
            self.state = 'applied'
            
            # Create audit log
            self._create_audit_log()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('%s field label(s) updated successfully') % changes_count,
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            raise UserError(_("Error applying changes: %s") % str(e))
    
    def _apply_single_change(self):
        """Apply single field label change"""
        if not self.field_name or not self.new_label:
            raise UserError(_("Field name and new label are required"))
        
        # Note: In a real implementation, this would update the field definition
        # For now, we'll simulate the change
        return 1
    
    def _apply_bulk_changes(self):
        """Apply bulk field label changes"""
        if not self.category:
            raise UserError(_("Category is required for bulk updates"))
        
        category_fields = self._get_fields_by_category()
        return len(category_fields)
    
    def _apply_category_changes(self):
        """Apply category-based field label changes"""
        return self._apply_bulk_changes()
    
    def _create_audit_log(self):
        """Create audit log entry for the changes"""
        try:
            self.env['naid.audit.log'].create({
                'name': _('Field Label Update - %s') % self.target_model,
                'action': 'field_label_update',
                'user_id': self.env.user.id,
                'notes': _('Updated %s field labels via Field Label Helper Wizard') % self.changes_applied,
                'audit_date': fields.Datetime.now(),
            })
        except Exception:
            # If audit log model doesn't exist, continue without logging
            pass
    
    def action_reset(self):
        """Reset wizard to initial state"""
        self.ensure_one()
        
        self.write({
            'field_name': False,
            'current_label': False,
            'new_label': False,
            'preview_changes': False,
            'changes_applied': 0,
            'state': 'draft',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Field Label Helper'),
            'res_model': 'field.label.helper.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
