# -*- coding: utf-8 -*-
"""
Container Content Module

Manages individual content items within a records container, such as files,
folders, or other physical media. Tracks metadata, lifecycle, and retention.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ContainerContent(models.Model):
    _name = 'container.content'
    _description = 'Container Contents'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION & RELATIONSHIPS
    # ============================================================================
    name = fields.Char(string='Content Name', required=True, tracking=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    container_id = fields.Many2one(
        'records.container',
        string='Container',
        required=True,
        ondelete='cascade',
        index=True
    )
    document_type_id = fields.Many2one('records.document.type', string='Document Type', tracking=True)
    partner_id = fields.Many2one(related='container_id.partner_id', string='Customer', store=True, comodel_name='res.partner')
    location_id = fields.Many2one(related='container_id.location_id', string='Location', store=True, comodel_name='stock.location')
    company_id = fields.Many2one(related='container_id.company_id', string='Company', store=True, comodel_name='res.company')
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    container_barcode = fields.Char(related='container_id.barcode', string='Container Barcode', store=True)

    # ============================================================================
    # WORKFLOW & STATE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('stored', 'In Storage'),
        ('retrieved', 'Retrieved'),
        ('destroyed', 'Destroyed')
    ], string='Status', default='draft', required=True, tracking=True)
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('secret', 'Top Secret')
    ], string='Confidentiality', default='internal', tracking=True)

    # ============================================================================
    # CONTENT DETAILS
    # ============================================================================
    description = fields.Text(string='Description')
    notes = fields.Text(string='Internal Notes')
    content_type = fields.Selection([
        ('file', 'File'),
        ('folder', 'Folder'),
        ('media', 'Media (Tape, Disk)'),
        ('other', 'Other')
    ], string='Content Type', default='file', required=True)
    document_count = fields.Integer(string='Document Count', default=1)
    estimated_pages = fields.Integer(string='Estimated Pages')
    weight_kg = fields.Float(string='Weight (kg)')

    # ============================================================================
    # LIFECYCLE & DATES
    # ============================================================================
    date_created = fields.Datetime(string='Creation Date', default=fields.Datetime.now, readonly=True)
    date_stored = fields.Datetime(string='Storage Date', readonly=True)
    date_retrieved = fields.Datetime(string='Retrieval Date', readonly=True)
    retention_until = fields.Date(string='Retain Until', tracking=True)
    is_overdue = fields.Boolean(string='Retention Overdue', compute='_compute_is_overdue', store=True)

    # ============================================================================
    # DESTRUCTION DETAILS
    # ============================================================================
    destruction_required = fields.Boolean(string='Destruction Required', default=True)
    destruction_method = fields.Selection([
        ('shred', 'Shredding'),
        ('incinerate', 'Incineration'),
        ('pulp', 'Pulping'),
        ('degauss', 'Degaussing (for media)')
    ], string='Destruction Method')

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('name_container_uniq', 'unique(name, container_id)', 'Content name must be unique within a container.')
    ]

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'container_id.name')
    def _compute_display_name(self):
        """Compute a descriptive display name for content items."""
        for record in self:
            if record.container_id and record.name:
                record.display_name = f"{record.container_id.name} / {record.name}"
            else:
                record.display_name = record.name or _("New Content")

    @api.depends('retention_until', 'state')
    def _compute_is_overdue(self):
        """Check if content is past its retention date and not yet processed."""
        for record in self:
            is_overdue = False
            if record.retention_until and record.state not in ['retrieved', 'destroyed']:
                if fields.Date.today() > record.retention_until:
                    is_overdue = True
            record.is_overdue = is_overdue

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('document_count', 'estimated_pages', 'weight_kg')
    def _check_positive_values(self):
        """Ensure numerical values are positive and reasonable."""
        for record in self:
            if record.document_count < 0:
                raise ValidationError(_("Document count cannot be negative."))
            if record.estimated_pages < 0:
                raise ValidationError(_("Estimated pages cannot be negative."))
            if record.weight_kg < 0:
                raise ValidationError(_("Weight cannot be negative."))
            if record.weight_kg > 1000:  # 1 ton limit
                raise ValidationError(_("Weight exceeds reasonable limit (1000kg)."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm content details."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft content can be confirmed."))
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Content details confirmed."))

    def action_store(self):
        """Mark content as stored."""
        self.ensure_one()
        if self.state not in ['confirmed', 'draft']:
            raise UserError(_("Cannot store content in its current state."))
        self.write({
            'state': 'stored',
            'date_stored': fields.Datetime.now()
        })
        self.message_post(body=_("Content stored in container %s.", self.container_id.name))

    def action_retrieve(self):
        """Mark content as retrieved."""
        self.ensure_one()
        if self.state != 'stored':
            raise UserError(_("Only stored content can be retrieved."))
        self.write({
            'state': 'retrieved',
            'date_retrieved': fields.Datetime.now()
        })
        self.message_post(body=_("Content retrieved from storage."))

    def action_mark_destroyed(self):
        """Mark content as destroyed."""
        self.ensure_one()
        if not self.destruction_required:
            raise UserError(_("This content is not marked for destruction."))
        if self.state == 'destroyed':
            raise UserError(_("This content has already been marked as destroyed."))
        self.write({'state': 'destroyed'})
        self.message_post(body=_("Content marked as destroyed."))

    def action_reset_to_draft(self):
        """Reset content to draft state."""
        self.ensure_one()
        if self.state == 'destroyed':
            raise UserError(_("Cannot reset destroyed content to draft."))
        self.write({'state': 'draft'})
        self.message_post(body=_("Content has been reset to draft."))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    @api.model
    def get_overdue_content(self):
        """Find all content items that are past their retention date."""
        return self.search([
            ('is_overdue', '=', True),
            ('state', '=', 'stored')
        ])
