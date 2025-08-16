# -*- coding: utf-8 -*-
"""
Document Search Attempt Model

Track individual search attempts for files during document retrieval operations.
Manages search history, success rates, and detailed tracking for NAID compliance
and operational efficiency in Records Management system.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DocumentSearchAttempt(models.Model):
    """
    Document Search Attempt Management

    Tracks individual search attempts during document retrieval operations,
    providing detailed audit trails, success metrics, and operational insights
    for Records Management compliance and efficiency optimization.
    """

    _name = "document.search.attempt"
    _description = "Document Search Attempt"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "search_date desc, id desc"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Search Reference",
        required=True,
        tracking=True,
        index=True,
        help="Reference number for this search attempt"
    )

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        store=True,
        help="Formatted display name for the search attempt"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        help='Company this record belongs to'
    )

    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who created this search record"
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to hide this record'
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    retrieval_item_id = fields.Many2one(
        "document.retrieval.item",
        string="Retrieval Item",
        required=True,
        ondelete="cascade",
        index=True,
        help="Related document retrieval item"
    )

    work_order_id = fields.Many2one(
        "file.retrieval.work.order",
        string="Work Order",
        related="retrieval_item_id.work_order_id",
        readonly=True,
        store=True,
        help="Related work order"
    )

    container_id = fields.Many2one(
        "records.container",
        string="Container Searched",
        required=True,
        index=True,
        help="Container that was searched"
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="retrieval_item_id.partner_id",
        readonly=True,
        store=True,
        help="Customer requesting the document"
    )

    location_id = fields.Many2one(
        "records.location",
        string="Search Location",
        related="container_id.location_id",
        readonly=True,
        store=True,
        help="Location where search was performed"
    )

    # ============================================================================
    # PERSONNEL TRACKING
    # ============================================================================
    searched_by_id = fields.Many2one(
        "res.users",
        string="Searched By",
        required=True,
        tracking=True,
        help="User who performed the search"
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        help="Employee who performed the search"
    )

    supervisor_id = fields.Many2one(
        "hr.employee",
        string="Supervisor",
        help="Supervising employee for this search"
    )

    # ============================================================================
    # SEARCH DETAILS
    # ============================================================================
    search_date = fields.Datetime(
        string="Search Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help="Date and time when search was performed"
    )

    search_duration_minutes = fields.Float(
        string="Search Duration (Minutes)",
        digits=(6, 2),
        help="Time spent searching this container"
    )

    search_method = fields.Selection([
        ('manual', 'Manual Search'),
        ('barcode', 'Barcode Scan'),
        ('electronic', 'Electronic Index'),
        ('systematic', 'Systematic Review'),
        ('random', 'Random Sampling')
    ], string="Search Method", default='manual', help="Method used for searching")

    search_thoroughness = fields.Selection([
        ('quick', 'Quick Scan'),
        ('standard', 'Standard Search'),
        ('thorough', 'Thorough Review'),
        ('complete', 'Complete Inventory')
    ], string="Search Thoroughness", default='standard', help="Level of search detail")

    # ============================================================================
    # SEARCH RESULTS
    # ============================================================================
    found = fields.Boolean(
        string="Document Found",
        default=False,
        tracking=True,
        help="Whether the requested document was found"
    )

    found_date = fields.Datetime(
        string="Found Date",
        help="Date and time when document was found"
    )

    document_condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], string="Document Condition", help="Condition of found document")

    retrieval_successful = fields.Boolean(
        string="Retrieval Successful",
        default=False,
        help="Whether document was successfully retrieved"
    )

    # ============================================================================
    # STATUS AND WORKFLOW
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)

    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string="Priority", default='medium', help="Search priority level")

    # ============================================================================
    # REFERENCE FIELDS
    # ============================================================================
    requested_file_name = fields.Char(
        related="retrieval_item_id.requested_file_name",
        string="Requested File",
        readonly=True,
        store=True,
        help="Name of requested file"
    )

    requested_file_description = fields.Text(
        related="retrieval_item_id.file_description",
        string="File Description",
        readonly=True,
        help="Description of requested file"
    )

    container_barcode = fields.Char(
        string="Container Barcode",
        related="container_id.barcode",
        readonly=True,
        store=True,
        help="Barcode of searched container"
    )

    container_type = fields.Selection(
        related="container_id.container_type_id.standard_type",
        readonly=True,
        store=True,
        string="Container Type",
        help="Type of container searched"
    )

    # ============================================================================
    # NOTES AND OBSERVATIONS
    # ============================================================================
    search_notes = fields.Text(
        string="Search Notes",
        help="Detailed notes about the search process"
    )

    findings = fields.Text(
        string="Search Findings",
        help="What was found during the search"
    )

    obstacles_encountered = fields.Text(
        string="Obstacles Encountered",
        help="Any issues or obstacles during search"
    )

    improvement_suggestions = fields.Text(
        string="Improvement Suggestions",
        help="Suggestions for improving search efficiency"
    )

    # ============================================================================
    # METRICS AND ANALYTICS
    # ============================================================================
    search_score = fields.Float(
        string="Search Score",
        compute='_compute_search_score',
        store=True,
        digits=(5, 2),
        help="Calculated search effectiveness score"
    )

    accuracy_rating = fields.Selection([
        ('1', 'Poor'),
        ('2', 'Fair'),
        ('3', 'Good'),
        ('4', 'Very Good'),
        ('5', 'Excellent')
    ], string="Search Accuracy", help="Rating of search accuracy")

    # ============================================================================
    # COMPLIANCE AND AUDIT
    # ============================================================================
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=True,
        help="Whether search meets NAID standards"
    )

    audit_trail_created = fields.Boolean(
        string="Audit Trail Created",
        default=False,
        help="Whether audit trail was created for this search"
    )

    quality_checked = fields.Boolean(
        string="Quality Checked",
        default=False,
        help="Whether search results were quality checked"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    )

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    )

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'requested_file_name', 'container_id', 'found')
    def _compute_display_name(self):
        """Compute display name with search details"""
        for attempt in self:
            parts = []
            if attempt.name:
                parts.append(attempt.name)
            if attempt.requested_file_name:
                parts.append(attempt.requested_file_name)
            if attempt.container_id:
                parts.append(_("in %s", attempt.container_id.name))

            status = _("Found") if attempt.found else _("Not Found")
            parts.append(_("[%s]", status))

            attempt.display_name = " - ".join(parts) if parts else _("New Search")

    @api.depends('found', 'search_duration_minutes', 'search_thoroughness', 'accuracy_rating')
    def _compute_search_score(self):
        """Calculate search effectiveness score"""
        for attempt in self:
            score = 0.0

            # Base score for finding the document
            if attempt.found:
                score += 50.0

            # Time efficiency bonus/penalty
            if attempt.search_duration_minutes:
                if attempt.search_duration_minutes <= 5:
                    score += 20.0  # Very fast
                elif attempt.search_duration_minutes <= 15:
                    score += 10.0  # Fast
                elif attempt.search_duration_minutes > 30:
                    score -= 10.0  # Slow

            # Thoroughness factor
            thoroughness_scores = {
                'quick': 5.0,
                'standard': 15.0,
                'thorough': 25.0,
                'complete': 35.0
            }
            score += thoroughness_scores.get(attempt.search_thoroughness, 15.0)

            # Accuracy rating
            if attempt.accuracy_rating:
                score += int(attempt.accuracy_rating) * 2

            attempt.search_score = min(score, 100.0)  # Cap at 100

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('found')
    def _onchange_found(self):
        """Update fields when found status changes"""
        if self.found and not self.found_date:
            self.found_date = fields.Datetime.now()
        elif not self.found:
            self.found_date = False
            self.document_condition = False
            self.retrieval_successful = False

    @api.onchange('searched_by_id')
    def _onchange_searched_by_id(self):
        """Update employee when user changes"""
        if self.searched_by_id and self.searched_by_id.employee_id:
            self.employee_id = self.searched_by_id.employee_id

    @api.onchange('container_id')
    def _onchange_container_id(self):
        """Update fields when container changes"""
        if self.container_id:
            # Auto-populate location
            self.location_id = self.container_id.location_id

            # Set default name if not set
            if not self.name and self.requested_file_name:
                self.name = _("Search %s in %s",
                             self.requested_file_name,
                             self.container_id.name)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_search(self):
        """Start the search process"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Can only start draft search attempts"))

        self.write({
            'state': 'in_progress',
            'search_date': fields.Datetime.now()
        })

        self._create_audit_log('search_started')
        self.message_post(body=_("Search started by %s", self.searched_by_id.name))

    def action_complete_search(self):
        """Complete the search process"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Can only complete searches in progress"))

        # Validate required information
        if not self.search_notes:
            raise UserError(_("Please provide search notes before completing"))

        self.write({
            'state': 'completed',
            'audit_trail_created': True
        })

        self._create_audit_log('search_completed')
        self.message_post(body=_(
            "Search completed. Document %s",
            _("found") if self.found else _("not found")
        ))

    def action_verify_search(self):
        """Verify search results"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Can only verify completed searches"))

        self.write({
            'state': 'verified',
            'quality_checked': True
        })

        self._create_audit_log('search_verified')
        self.message_post(body=_("Search results verified"))

    def action_cancel_search(self):
        """Cancel the search attempt"""
        self.ensure_one()
        if self.state in ['verified']:
            raise UserError(_("Cannot cancel verified search attempts"))

        self.write({'state': 'cancelled'})
        self._create_audit_log('search_cancelled')
        self.message_post(body=_("Search attempt cancelled"))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('search_duration_minutes')
    def _check_search_duration(self):
        """Validate search duration"""
        for attempt in self:
            if attempt.search_duration_minutes and attempt.search_duration_minutes < 0:
                raise ValidationError(_("Search duration cannot be negative"))
            if attempt.search_duration_minutes and attempt.search_duration_minutes > 480:  # 8 hours
                raise ValidationError(_(
                    "Search duration cannot exceed 8 hours. Please verify the time."
                ))

    @api.constrains('search_date', 'found_date')
    def _check_date_sequence(self):
        """Validate date sequence"""
        for attempt in self:
            if attempt.search_date and attempt.found_date:
                if attempt.search_date > attempt.found_date:
                    raise ValidationError(_(
                        "Search date cannot be after found date"
                    ))

    @api.constrains('found', 'document_condition')
    def _check_found_condition_consistency(self):
        """Validate found status and condition consistency"""
        for attempt in self:
            if attempt.found and not attempt.document_condition:
                raise ValidationError(_(
                    "Please specify document condition when document is found"
                ))

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def _create_audit_log(self, action_type):
        """Create NAID compliance audit log"""
        self.ensure_one()

        if 'naid.audit.log' in self.env:
            audit_vals = {
                'action_type': action_type,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
                'description': _("Search attempt %s: %s", self.name, action_type),
                'search_attempt_id': self.id,
                'container_id': self.container_id.id if self.container_id else False,
                'naid_compliant': self.naid_compliant,
            }
            return self.env['naid.audit.log'].create(audit_vals)

    def get_search_efficiency_metrics(self):
        """Calculate search efficiency metrics"""
        self.ensure_one()

        metrics = {
            'search_score': self.search_score,
            'time_efficiency': 'fast' if self.search_duration_minutes and self.search_duration_minutes <= 10 else 'standard',
            'success_rate': 100.0 if self.found else 0.0,
            'accuracy_score': int(self.accuracy_rating) * 20 if self.accuracy_rating else 60,
        }

        # Calculate overall efficiency
        total_score = (
            metrics['search_score'] * 0.4 +
            metrics['success_rate'] * 0.3 +
            metrics['accuracy_score'] * 0.3
        )
        metrics['overall_efficiency'] = round(total_score, 2)

        return metrics

    def get_history_summary(self):
        """Get summary of search attempt history"""
        self.ensure_one()
        return {
            "search_reference": self.name,
            "container": self.container_id.name if self.container_id else "Unknown",
            "customer": self.partner_id.name if self.partner_id else "Unknown",
            "requested_file": self.requested_file_name,
            "search_date": self.search_date,
            "searched_by": self.searched_by_id.name if self.searched_by_id else "Unknown",
            "duration_minutes": self.search_duration_minutes,
            "method": self.search_method,
            "thoroughness": self.search_thoroughness,
            "found": self.found,
            "document_condition": self.document_condition,
            "search_score": self.search_score,
            "notes": self.search_notes or "",
            "state": self.state,
        }

    @api.model
    def get_search_statistics(self, domain=None):
        """Get search attempt statistics"""
        if domain is None:
            domain = []

        attempts = self.search(domain)

        if not attempts:
            return {
                'total_attempts': 0,
                'success_rate': 0.0,
                'average_duration': 0.0,
                'by_method': {},
                'by_container_type': {}
            }

        stats = {
            'total_attempts': len(attempts),
            'successful_attempts': len(attempts.filtered('found')),
            'success_rate': (len(attempts.filtered('found')) / len(attempts)) * 100,
            'average_duration': sum(attempts.mapped('search_duration_minutes')) / len(attempts),
            'average_score': sum(attempts.mapped('search_score')) / len(attempts),
        }

        # Group by method
        methods = attempts.mapped('search_method')
        stats['by_method'] = {}
        for method in methods:
            method_attempts = attempts.filtered(lambda a: a.search_method == method)
            stats['by_method'][method] = {
                'count': len(method_attempts),
                'success_rate': (len(method_attempts.filtered('found')) / len(method_attempts)) * 100
            }

        # Group by container type
        container_types = attempts.mapped('container_type')
        stats['by_container_type'] = {}
        for container_type in container_types:
            type_attempts = attempts.filtered(lambda a: a.container_type == container_type)
            if type_attempts:
                stats['by_container_type'][container_type] = {
                    'count': len(type_attempts),
                    'success_rate': (len(type_attempts.filtered('found')) / len(type_attempts)) * 100
                }

        return stats

    # ============================================================================
    # REPORTING METHODS
    # ============================================================================
    def generate_search_report(self):
        """Generate detailed search attempt report"""
        self.ensure_one()

        metrics = self.get_search_efficiency_metrics()

        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.document_search_attempt_report',
            'report_type': 'qweb-pdf',
            'data': {
                'search_attempt_id': self.id,
                'metrics': metrics,
                'include_details': True,
                'include_recommendations': True
            },
            'context': self.env.context
        }

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set defaults"""
        for vals in vals_list:
            if not vals.get('name'):
                sequence = self.env['ir.sequence'].next_by_code('document.search.attempt')
                vals['name'] = sequence or _('New Search')

            # Set default searched_by if not specified
            if not vals.get('searched_by_id'):
                vals['searched_by_id'] = self.env.user.id

        return super().create(vals_list)

    def write(self, vals):
        """Override write for status tracking"""
        result = super().write(vals)

        if 'state' in vals:
            for attempt in self:
                state_label = dict(attempt._fields['state'].selection)[attempt.state]
                attempt.message_post(body=_("Status changed to %s", state_label))

        return result

    def name_get(self):
        """Custom name display"""
        result = []
        for attempt in self:
            name = attempt.display_name or attempt.name
            result.append((attempt.id, name))
        return result

    # ============================================================================
    # INTEGRATION METHODS
    # ============================================================================
    def action_view_container(self):
        """View the searched container"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Container Details'),
            'res_model': 'records.container',
            'res_id': self.container_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_retrieval_item(self):
        """View the related retrieval item"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Retrieval Item'),
            'res_model': 'document.retrieval.item',
            'res_id': self.retrieval_item_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_follow_up_search(self):
        """Create a follow-up search attempt"""
        self.ensure_one()

        follow_up_vals = {
            'name': _("Follow-up: %s", self.name),
            'retrieval_item_id': self.retrieval_item_id.id,
            'container_id': self.container_id.id,
            'searched_by_id': self.env.user.id,
            'priority': 'high',
            'search_notes': _("Follow-up search based on attempt %s", self.name),
        }

        follow_up = self.create(follow_up_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Follow-up Search'),
            'res_model': 'document.search.attempt',
            'res_id': follow_up.id,
            'view_mode': 'form',
            'target': 'current',
        }
