# -*- coding: utf-8 -*-
"""
Work Order Creation Wizard

PURPOSE: Provide a guided interface for creating work orders that uses
EXISTING work order models (work.order.shredding, work.order.retrieval, etc.)
rather than creating parallel structures.

INTEGRATION PATTERN:
- Creates EXISTING work order model records (work.order.shredding, etc.)
- Optionally creates/links a sale.order for native Odoo invoicing
- Portal controllers continue to use existing models unchanged
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class WorkOrderWizard(models.TransientModel):
    """
    Wizard for creating Records Management work orders.
    
    This wizard guides users through creating the appropriate type of work order
    using the EXISTING work order models, not new parallel structures.
    """
    _name = 'rm.work.order.wizard'
    _description = 'Create Work Order Wizard'

    # ============================================================================
    # WIZARD STATE
    # ============================================================================
    state = fields.Selection([
        ('type', 'Select Type'),
        ('customer', 'Select Customer'),
        ('items', 'Select Items'),
        ('details', 'Service Details'),
        ('review', 'Review & Create'),
    ], string="Step", default='type')

    # ============================================================================
    # STEP 1: WORK ORDER TYPE
    # ============================================================================
    work_order_type = fields.Selection([
        ('shredding', 'Shredding Service'),
        ('retrieval', 'Container Retrieval'),
        ('destruction', 'Destruction Service'),
        ('access', 'On-Site File Access'),
    ], string="Work Order Type", required=True,
       help="Select the type of work order to create. Each type uses its own specialized model.")
    
    # ============================================================================
    # STEP 2: CUSTOMER & LOCATION
    # ============================================================================
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        domain="[('is_company', '=', True)]"
    )
    
    service_address_id = fields.Many2one(
        comodel_name='res.partner',
        string="Service Address",
        domain="['|', ('id', '=', partner_id), ('parent_id', '=', partner_id)]"
    )
    
    department_id = fields.Many2one(
        comodel_name='records.department',
        string="Department",
        domain="[('partner_id', '=', partner_id)]"
    )
    
    contact_name = fields.Char(string="On-Site Contact")
    contact_phone = fields.Char(string="Contact Phone")

    # ============================================================================
    # STEP 3: ITEM SELECTION
    # ============================================================================
    # Container selection (for retrieval, destruction)
    container_ids = fields.Many2many(
        comodel_name='records.container',
        relation='work_order_wizard_container_rel',
        column1='wizard_id',
        column2='container_id',
        string="Containers"
    )
    
    # Shredding bin selection
    shredding_bin_ids = fields.Many2many(
        comodel_name='shredding.service.bin',
        relation='work_order_wizard_bin_rel',
        column1='wizard_id',
        column2='bin_id',
        string="Shredding Bins"
    )
    
    # File selection (for access)
    file_ids = fields.Many2many(
        comodel_name='records.file',
        relation='work_order_wizard_file_rel',
        column1='wizard_id',
        column2='file_id',
        string="Files"
    )

    # ============================================================================
    # STEP 4: SERVICE DETAILS
    # ============================================================================
    scheduled_date = fields.Datetime(
        string="Scheduled Date/Time",
        default=lambda self: fields.Datetime.now() + timedelta(days=1)
    )
    
    priority = fields.Selection([
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string="Priority", default='normal')
    
    # Shredding specific
    service_type = fields.Selection([
        ('regular', 'Regular Scheduled Service'),
        ('extra', 'Extra/On-Demand Pickup'),
        ('purge', 'One-Time Purge'),
    ], string="Shredding Service Type", default='regular')
    
    # Destruction specific
    witness_required = fields.Boolean(string="Customer Will Witness")
    
    # Retrieval specific
    urgency_level = fields.Selection([
        ('standard', 'Standard (2-3 business days)'),
        ('rush', 'Rush (same day)'),
        ('emergency', 'Emergency (within 2 hours)'),
    ], string="Urgency", default='standard')
    
    # Notes
    notes = fields.Text(string="Notes / Special Instructions")
    
    # Invoice option
    create_invoice = fields.Boolean(
        string="Create Sale Order for Invoicing",
        default=False,
        help="If checked, a linked sale.order will be created for native Odoo invoicing"
    )

    # ============================================================================
    # STEP 5: REVIEW - Computed Preview Fields
    # ============================================================================
    preview_summary = fields.Html(
        string="Work Order Summary",
        compute='_compute_preview_summary'
    )

    # ============================================================================
    # PREVIEW COMPUTATION
    # ============================================================================
    @api.depends('work_order_type', 'partner_id', 'container_ids', 
                 'shredding_bin_ids', 'scheduled_date')
    def _compute_preview_summary(self):
        for wizard in self:
            type_labels = dict(wizard._fields['work_order_type'].selection or [])
            
            lines = [
                f"<h4>{type_labels.get(wizard.work_order_type, 'Work Order')}</h4>",
                "<table class='table table-sm'>",
            ]
            
            if wizard.partner_id:
                lines.append(f"<tr><td><strong>Customer:</strong></td><td>{wizard.partner_id.name}</td></tr>")
            
            if wizard.scheduled_date:
                lines.append(f"<tr><td><strong>Scheduled:</strong></td><td>{wizard.scheduled_date.strftime('%Y-%m-%d %H:%M')}</td></tr>")
            
            if wizard.container_ids:
                lines.append(f"<tr><td><strong>Containers:</strong></td><td>{len(wizard.container_ids)}</td></tr>")
            
            if wizard.shredding_bin_ids:
                lines.append(f"<tr><td><strong>Shredding Bins:</strong></td><td>{len(wizard.shredding_bin_ids)}</td></tr>")
            
            if wizard.file_ids:
                lines.append(f"<tr><td><strong>Files:</strong></td><td>{len(wizard.file_ids)}</td></tr>")
            
            model_info = {
                'shredding': 'work.order.shredding',
                'retrieval': 'work.order.retrieval',
                'destruction': 'container.destruction.work.order',
                'access': 'container.access.work.order',
            }
            if wizard.work_order_type:
                lines.append(f"<tr><td><strong>Creates Model:</strong></td><td><code>{model_info.get(wizard.work_order_type)}</code></td></tr>")
            
            lines.append("</table>")
            wizard.preview_summary = ''.join(lines)

    # ============================================================================
    # NAVIGATION ACTIONS
    # ============================================================================
    def action_next(self):
        """Move to next wizard step."""
        self.ensure_one()
        state_order = ['type', 'customer', 'items', 'details', 'review']
        current_idx = state_order.index(self.state)
        
        self._validate_step()
        
        if current_idx < len(state_order) - 1:
            self.state = state_order[current_idx + 1]
        
        return self._reopen_wizard()
    
    def action_previous(self):
        """Move to previous wizard step."""
        self.ensure_one()
        state_order = ['type', 'customer', 'items', 'details', 'review']
        current_idx = state_order.index(self.state)
        
        if current_idx > 0:
            self.state = state_order[current_idx - 1]
        
        return self._reopen_wizard()
    
    def _validate_step(self):
        """Validate current step before allowing progression."""
        self.ensure_one()
        if self.state == 'type':
            if not self.work_order_type:
                raise ValidationError(_("Please select a work order type."))
        
        elif self.state == 'customer':
            if not self.partner_id:
                raise ValidationError(_("Please select a customer."))
        
        elif self.state == 'items':
            if self.work_order_type in ['retrieval', 'destruction']:
                if not self.container_ids:
                    raise ValidationError(_("Please select at least one container."))
            elif self.work_order_type == 'shredding':
                if not self.shredding_bin_ids:
                    raise ValidationError(_("Please select at least one shredding bin."))
    
    def _reopen_wizard(self):
        """Reopen the wizard at current step."""
        return {
            'name': _('Create Work Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'rm.work.order.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }

    # ============================================================================
    # CREATE WORK ORDER - Uses EXISTING Models
    # ============================================================================
    def action_create_work_order(self):
        """
        Create the work order using EXISTING work order models.
        
        This creates:
        - work.order.shredding for shredding
        - work.order.retrieval for retrieval  
        - container.destruction.work.order for destruction
        - container.access.work.order for access
        
        Optionally links to sale.order for native invoicing.
        """
        self.ensure_one()
        self._validate_step()
        
        # Create sale order if requested (for invoicing)
        sale_order = False
        if self.create_invoice:
            sale_order = self._create_sale_order()
        
        # Create the appropriate EXISTING work order model
        if self.work_order_type == 'shredding':
            work_order = self._create_shredding_work_order(sale_order)
            return self._return_to_work_order('work.order.shredding', work_order.id)
        
        elif self.work_order_type == 'retrieval':
            work_order = self._create_retrieval_work_order(sale_order)
            return self._return_to_work_order('work.order.retrieval', work_order.id)
        
        elif self.work_order_type == 'destruction':
            work_order = self._create_destruction_work_order(sale_order)
            return self._return_to_work_order('container.destruction.work.order', work_order.id)
        
        elif self.work_order_type == 'access':
            work_order = self._create_access_work_order(sale_order)
            return self._return_to_work_order('container.access.work.order', work_order.id)
    
    def _create_shredding_work_order(self, sale_order):
        """Create a work.order.shredding record."""
        vals = {
            'partner_id': self.partner_id.id,
            'scheduled_date': self.scheduled_date,
            'service_type': self.service_type,
            'notes': self.notes,
        }
        if sale_order:
            vals['sale_order_id'] = sale_order.id
        
        work_order = self.env['work.order.shredding'].create(vals)
        
        # Link bins to work order
        for bin_rec in self.shredding_bin_ids:
            bin_rec.current_work_order_id = work_order.id
        
        return work_order
    
    def _create_retrieval_work_order(self, sale_order):
        """Create a work.order.retrieval record."""
        vals = {
            'partner_id': self.partner_id.id,
            'scheduled_date': self.scheduled_date,
            'urgency_level': self.urgency_level,
            'notes': self.notes,
            'container_ids': [(6, 0, self.container_ids.ids)],
        }
        if sale_order:
            vals['sale_order_id'] = sale_order.id
        
        return self.env['work.order.retrieval'].create(vals)
    
    def _create_destruction_work_order(self, sale_order):
        """Create a container.destruction.work.order record."""
        vals = {
            'partner_id': self.partner_id.id,
            'scheduled_date': self.scheduled_date,
            'witness_required': self.witness_required,
            'notes': self.notes,
            'container_ids': [(6, 0, self.container_ids.ids)],
        }
        if sale_order:
            vals['sale_order_id'] = sale_order.id
        
        return self.env['container.destruction.work.order'].create(vals)
    
    def _create_access_work_order(self, sale_order):
        """Create a container.access.work.order record."""
        vals = {
            'partner_id': self.partner_id.id,
            'scheduled_date': self.scheduled_date,
            'notes': self.notes,
        }
        if self.file_ids:
            vals['file_ids'] = [(6, 0, self.file_ids.ids)]
        if sale_order:
            vals['sale_order_id'] = sale_order.id
        
        return self.env['container.access.work.order'].create(vals)
    
    def _create_sale_order(self):
        """Create a sale.order for invoicing."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'is_rm_work_order': True,
            'work_order_type': self.work_order_type,
        })
        return sale_order
    
    def _return_to_work_order(self, model, res_id):
        """Return to the created work order."""
        return {
            'name': _('Work Order'),
            'type': 'ir.actions.act_window',
            'res_model': model,
            'view_mode': 'form',
            'res_id': res_id,
            'target': 'current',
        }
