# -*- coding: utf-8 -*-
"""
Bale Weighing Wizard - Optimized for Technicians

This wizard provides a streamlined interface for technicians to:
1. See the current load they're working on
2. Enter bale weight and paper grade (WHT/MIX/OCC)
3. Sign and timestamp each bale
4. Print a receipt/tag for the bale
5. Track progress toward the 28-bale load goal
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BaleWeighingWizard(models.TransientModel):
    """Wizard to create and weigh paper bales with signature."""
    
    _name = 'bale.weighing.wizard'
    _description = 'Bale Weighing & Categorization Wizard'

    # ============================================================================
    # LOAD CONTEXT - Displayed at top for technician awareness
    # ============================================================================
    load_id = fields.Many2one(
        comodel_name='paper.bale.load',
        string='Current Load',
        required=True,
        domain="[('state', 'in', ['draft', 'loading'])]",
        default=lambda self: self._get_default_load(),
        help="The load this bale will be added to"
    )
    
    load_name = fields.Char(
        string='Load #',
        related='load_id.name',
        readonly=True
    )
    
    buyer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Buyer',
        related='load_id.buyer_id',
        readonly=True
    )
    
    current_bale_count = fields.Integer(
        string='Current Bale Count',
        related='load_id.total_bales',
        readonly=True
    )
    
    is_load_full = fields.Boolean(
        string='Load Full',
        related='load_id.is_load_full',
        readonly=True
    )
    
    load_progress = fields.Integer(
        string='Bales in Load',
        related='load_id.total_bales',
        readonly=True
    )
    
    load_progress_percent = fields.Float(
        string='Load Progress %',
        compute='_compute_load_progress_percent',
        help="Progress toward 28-bale load capacity"
    )
    
    bales_remaining = fields.Integer(
        string='Bales Remaining',
        compute='_compute_load_progress_percent',
        help="Number of bales needed to complete the load"
    )

    # ============================================================================
    # BALE INFORMATION
    # ============================================================================
    next_bale_number = fields.Char(
        string='Next Bale #',
        compute='_compute_next_bale_number',
        readonly=True,
        help="Auto-generated bale number from sequence"
    )
    
    weight = fields.Float(
        string='Bale Weight (lbs)',
        required=True,
        help="Enter the measured weight of the bale in pounds"
    )
    
    paper_grade = fields.Selection([
        ('wht', 'WHT - White Paper'),
        ('mix', 'MIX - Mixed Paper'),
        ('occ', 'OCC - Cardboard'),
    ], string='Paper Grade',
       required=True,
       default='mix',
       help="Paper grade classification:\n"
            "WHT = White office paper (highest value)\n"
            "MIX = Mixed paper grades (default)\n"
            "OCC = Cardboard/corrugated")
    
    source_type = fields.Selection([
        ('daily_route', 'Daily Route'),
        ('purge_project', 'Purge Project'),
        ('drop_off', 'Customer Drop-off'),
        ('internal', 'Internal'),
        ('other', 'Other'),
    ], string='Source',
       default='daily_route',
       help="Origin of the paper in this bale")
    
    location_id = fields.Many2one(
        comodel_name='records.location',
        string='Storage Location',
        help="Location where the bale is stored"
    )
    
    notes = fields.Text(
        string='Notes',
        help="Optional notes about this bale"
    )

    # ============================================================================
    # SIGNATURE & TIMESTAMP
    # ============================================================================
    technician_id = fields.Many2one(
        comodel_name='res.users',
        string='Technician',
        default=lambda self: self.env.user,
        required=True,
        readonly=True
    )
    
    technician_signature = fields.Binary(
        string='Technician Signature',
        required=True,
        help="Sign to confirm bale weight and classification"
    )
    
    weigh_datetime = fields.Datetime(
        string='Weigh Date/Time',
        default=fields.Datetime.now,
        required=True,
        readonly=True
    )

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    @api.model
    def _get_default_load(self):
        """Get the current active load (draft or loading state)."""
        # First check context for explicit load
        if self.env.context.get('default_load_id'):
            return self.env.context.get('default_load_id')
        
        # Find the most recent load in loading/draft state
        Load = self.env['paper.bale.load']
        load = Load.search([
            ('state', 'in', ['draft', 'loading']),
            ('company_id', '=', self.env.company.id)
        ], order='create_date desc', limit=1)
        
        return load.id if load else False

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('load_id', 'load_id.total_bales')
    def _compute_load_progress_percent(self):
        """Calculate progress toward 28-bale load capacity."""
        BALES_PER_LOAD = 28
        for wizard in self:
            if wizard.load_id:
                wizard.load_progress_percent = (wizard.load_id.total_bales / BALES_PER_LOAD) * 100
                wizard.bales_remaining = max(0, BALES_PER_LOAD - wizard.load_id.total_bales)
            else:
                wizard.load_progress_percent = 0
                wizard.bales_remaining = BALES_PER_LOAD

    @api.depends('load_id')
    def _compute_next_bale_number(self):
        """Preview the next bale number from sequence."""
        for wizard in self:
            # Get the next number from sequence without consuming it
            seq = self.env['ir.sequence'].search([
                ('code', '=', 'records_management.bale')
            ], limit=1)
            if seq:
                wizard.next_bale_number = seq.get_next_char(seq.number_next_actual)
            else:
                wizard.next_bale_number = 'BALE-NEW'

    # ============================================================================
    # VALIDATION
    # ============================================================================
    @api.constrains('weight')
    def _check_weight(self):
        """Ensure weight is positive and reasonable."""
        for wizard in self:
            if wizard.weight <= 0:
                raise ValidationError(_("Bale weight must be greater than zero."))
            if wizard.weight > 2000:  # Typical bale max ~1200 lbs
                raise ValidationError(_("Bale weight seems too high. Please verify."))

    @api.constrains('technician_signature')
    def _check_signature(self):
        """Ensure signature is provided."""
        for wizard in self:
            if not wizard.technician_signature:
                raise ValidationError(_("Please sign to confirm the bale weight."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm_and_create_bale(self):
        """Create the paper bale with signature and timestamp."""
        self.ensure_one()
        
        if not self.load_id:
            raise UserError(_("Please select a load for this bale."))
        
        if not self.technician_signature:
            raise UserError(_("Please sign to confirm the bale weight."))
        
        # Check if load is full (28 bales)
        if self.load_id.total_bales >= 28:
            raise UserError(_(
                "Load %s already has 28 bales and is full. "
                "Please create a new load or select a different one."
            ) % self.load_id.name)
        
        # Create the paper bale
        bale_vals = {
            'load_id': self.load_id.id,
            'weight': self.weight,
            'paper_grade': self.paper_grade,
            'source_type': self.source_type,
            'weigh_date': self.weigh_datetime,
            'notes': self.notes,
            'state': 'weighed',
            # Signature fields
            'technician_id': self.technician_id.id,
            'technician_signature': self.technician_signature,
            'signature_datetime': self.weigh_datetime,
        }
        
        bale = self.env['paper.bale'].create(bale_vals)
        
        # Update load state to 'loading' if it was draft
        if self.load_id.state == 'draft':
            self.load_id.write({'state': 'loading'})
        
        # Log the creation
        self.load_id.message_post(
            body=_("Bale %s added: %s lbs of %s paper by %s") % (
                bale.name,
                self.weight,
                dict(self._fields['paper_grade'].selection).get(self.paper_grade),
                self.technician_id.name
            )
        )
        
        # Return action to print the bale tag
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bale Created'),
            'res_model': 'paper.bale',
            'res_id': bale.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'show_print_tag': True,
            }
        }

    def action_confirm_and_print_tag(self):
        """Create bale and immediately print the tag."""
        self.ensure_one()
        
        # First create the bale
        if not self.load_id:
            raise UserError(_("Please select a load for this bale."))
        
        if not self.technician_signature:
            raise UserError(_("Please sign to confirm the bale weight."))
        
        if self.load_id.total_bales >= 28:
            raise UserError(_(
                "Load %s already has 28 bales and is full."
            ) % self.load_id.name)
        
        bale_vals = {
            'load_id': self.load_id.id,
            'weight': self.weight,
            'paper_grade': self.paper_grade,
            'source_type': self.source_type,
            'weigh_date': self.weigh_datetime,
            'notes': self.notes,
            'state': 'weighed',
            'technician_id': self.technician_id.id,
            'technician_signature': self.technician_signature,
            'signature_datetime': self.weigh_datetime,
        }
        
        bale = self.env['paper.bale'].create(bale_vals)
        
        if self.load_id.state == 'draft':
            self.load_id.write({'state': 'loading'})
        
        # Return print action for bale tag
        return self.env.ref('records_management.action_report_bale_tag').report_action(bale)

    def action_create_new_load(self):
        """Create a new load and set it as current."""
        self.ensure_one()
        
        new_load = self.env['paper.bale.load'].create({
            'state': 'draft',
        })
        
        self.load_id = new_load.id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("New Load Created"),
                'message': _("Load %s created and selected.") % new_load.name,
                'type': 'success',
                'sticky': False,
            }
        }
