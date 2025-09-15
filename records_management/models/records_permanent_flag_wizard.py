# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class RecordsPermanentFlagWizard(models.TransientModel):
    """
    Records Permanent Flag Wizard - Manages the flagging of records as permanent retention.
    Handles the workflow for identifying, reviewing, and flagging records that must be
    retained permanently for legal, historical, or compliance reasons.
    """
    _name = 'records.permanent.flag.wizard'
    _description = 'Records Permanent Flag Wizard'

    # Basic Information
    name = fields.Char(
        string='Permanent Flag Request',
        default='Records Permanent Flag Review',
        readonly=True
    )

    # Target Records Selection
    selection_method = fields.Selection([
        ('single_container', 'Single Container'),
        ('multiple_containers', 'Multiple Containers'),
        ('document_series', 'Document Series'),
        ('date_range', 'Date Range'),
        ('customer_all', 'All Customer Records'),
        ('category_based', 'Category Based'),
    ], string='Selection Method', required=True, default='single_container',
       help="Method for selecting records to flag as permanent")

    # Single Container Selection
    container_id = fields.Many2one(
        'records.container',
        string='Container',
        help="Single container to flag as permanent"
    )

    # Multiple Container Selection
    container_ids = fields.Many2many(
        'records.container',
        string='Containers',
        help="Multiple containers to flag as permanent"
    )

    # Document Series Selection
    document_series = fields.Char(
        string='Document Series',
        help="Document series identifier (e.g., 'INV-2023', 'CONTRACT-*')"
    )

    # Date Range Selection
    date_from = fields.Date(
        string='Date From',
        help="Start date for records to flag"
    )

    date_to = fields.Date(
        string='Date To',
        help="End date for records to flag"
    )

    # Customer and Category Selection
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain=[('is_company', '=', True)],
        help="Customer whose records should be flagged"
    )

    document_category = fields.Selection([
        ('legal', 'Legal Documents'),
        ('financial', 'Financial Records'),
        ('contracts', 'Contracts'),
        ('compliance', 'Compliance Records'),
        ('historical', 'Historical Documents'),
        ('intellectual_property', 'Intellectual Property'),
        ('regulatory', 'Regulatory Filings'),
        ('audit', 'Audit Documents'),
    ], string='Document Category', help="Category of documents to flag")

    # Permanent Flag Justification
    permanent_reason = fields.Selection([
        ('legal_requirement', 'Legal Requirement'),
        ('regulatory_compliance', 'Regulatory Compliance'),
        ('historical_significance', 'Historical Significance'),
        ('ongoing_litigation', 'Ongoing Litigation'),
        ('audit_requirement', 'Audit Requirement'),
        ('intellectual_property', 'Intellectual Property Protection'),
        ('contract_terms', 'Contract Terms Requirement'),
        ('customer_request', 'Customer Request'),
        ('other', 'Other (Specify in Notes)'),
    ], string='Permanent Retention Reason', required=True,
       help="Reason why these records must be retained permanently")

    legal_citation = fields.Text(
        string='Legal Citation/Reference',
        help="Legal statute, regulation, or requirement citation"
    )

    permanent_notes = fields.Text(
        string='Permanent Flag Notes',
        required=True,
        help="Detailed explanation for permanent retention requirement"
    )

    # Review and Approval
    requires_legal_review = fields.Boolean(
        string='Requires Legal Review',
        default=True,
        help="Whether legal department review is required"
    )

    legal_reviewer_id = fields.Many2one(
        'res.users',
        string='Legal Reviewer',
        help="Legal department reviewer"
    )

    compliance_reviewer_id = fields.Many2one(
        'res.users',
        string='Compliance Reviewer',
        help="Compliance department reviewer"
    )

    # Impact Analysis
    estimated_records_count = fields.Integer(
        string='Estimated Records Count',
        readonly=True,
        help="Estimated number of records that will be flagged"
    )

    estimated_storage_cost = fields.Monetary(
        string='Estimated Annual Storage Cost',
        currency_field='currency_id',
        readonly=True,
        help="Estimated additional annual storage cost"
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # Customer Communication
    notify_customer = fields.Boolean(
        string='Notify Customer',
        default=True,
        help="Notify customer about permanent retention status"
    )

    customer_notification_template = fields.Many2one(
        'mail.template',
        string='Customer Notification Template',
        domain=[('model', '=', 'res.partner')],
        help="Template for customer notification"
    )

    # Processing Options
    effective_date = fields.Date(
        string='Effective Date',
        default=fields.Date.today,
        required=True,
        help="Date when permanent flag becomes effective"
    )

    review_date = fields.Date(
        string='Next Review Date',
        help="Date for next review of permanent status (if applicable)"
    )

    auto_exempt_destruction = fields.Boolean(
        string='Auto-Exempt from Destruction',
        default=True,
        help="Automatically exempt flagged records from destruction schedules"
    )

    update_retention_policy = fields.Boolean(
        string='Update Retention Policy',
        default=True,
        help="Update retention policy to reflect permanent status"
    )

    # Approval Workflow
    approval_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending_legal', 'Pending Legal Review'),
        ('pending_compliance', 'Pending Compliance Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval Status', default='draft', readonly=True)

    legal_approval_date = fields.Datetime(
        string='Legal Approval Date',
        readonly=True
    )

    compliance_approval_date = fields.Datetime(
        string='Compliance Approval Date',
        readonly=True
    )

    legal_approval_notes = fields.Text(
        string='Legal Approval Notes',
        readonly=True
    )

    compliance_approval_notes = fields.Text(
        string='Compliance Approval Notes',
        readonly=True
    )

    # Processing Results
    processing_completed = fields.Boolean(
        string='Processing Completed',
        default=False,
        readonly=True
    )

    records_flagged_count = fields.Integer(
        string='Records Flagged Count',
        readonly=True,
        help="Actual number of records flagged as permanent"
    )

    processing_notes = fields.Text(
        string='Processing Notes',
        readonly=True,
        help="Notes about the processing results"
    )

    # State Management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('analysis', 'Impact Analysis'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', readonly=True)

    @api.onchange('selection_method')
    def _onchange_selection_method(self):
        """Clear related fields when selection method changes"""
        if self.selection_method != 'single_container':
            self.container_id = False
        if self.selection_method != 'multiple_containers':
            self.container_ids = [(5, 0, 0)]
        if self.selection_method != 'date_range':
            self.date_from = False
            self.date_to = False
        if self.selection_method not in ['customer_all', 'category_based']:
            self.customer_id = False
        if self.selection_method != 'category_based':
            self.document_category = False

    @api.onchange('container_id', 'container_ids', 'document_series', 'date_from', 'date_to', 'customer_id', 'document_category')
    def _onchange_selection_criteria(self):
        """Update estimated counts when selection criteria change"""
        self._compute_impact_analysis()

    def _compute_impact_analysis(self):
        """Compute impact analysis based on selection criteria"""
        if not self.selection_method:
            return

        # Simplified impact calculation - in real implementation would query actual data
        base_count = 0

        if self.selection_method == 'single_container' and self.container_id:
            base_count = 100  # Estimated documents per container
        elif self.selection_method == 'multiple_containers':
            base_count = len(self.container_ids) * 100
        elif self.selection_method == 'customer_all' and self.customer_id:
            base_count = 500  # Estimated total customer documents
        elif self.selection_method == 'date_range' and self.date_from and self.date_to:
            days = (self.date_to - self.date_from).days
            base_count = days * 10  # Estimated documents per day

        self.estimated_records_count = base_count
        self.estimated_storage_cost = base_count * 2.0  # $2 per record annually

    def action_analyze_impact(self):
        """Analyze the impact of permanent flagging"""
        self.ensure_one()

        if not self._validate_selection():
            return

        self._compute_impact_analysis()
        self.state = 'analysis'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Impact Analysis Complete'),
                'message': _('Estimated %s records will be flagged as permanent') % self.estimated_records_count,
                'type': 'info',
                'sticky': False,
            }
        }

    def action_submit_for_review(self):
        """Submit for legal and compliance review"""
        self.ensure_one()

        if self.state != 'analysis':
            raise UserError(_("Please complete impact analysis first"))

        if not self.permanent_notes:
            raise UserError(_("Please provide detailed notes for permanent retention"))

        if self.requires_legal_review:
            if not self.legal_reviewer_id:
                raise UserError(_("Please specify a legal reviewer"))
            self.approval_status = 'pending_legal'
            self._send_legal_review_notification()
        else:
            self.approval_status = 'approved'

        self.state = 'review'

        # Create audit log
        self._create_audit_log('submitted_for_review')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Submitted for Review'),
                'message': _('Permanent flag request submitted for review'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_legal_approve(self):
        """Legal department approval"""
        self.ensure_one()

        if self.approval_status != 'pending_legal':
            raise UserError(_("Only requests pending legal review can be approved"))

        if self.env.user != self.legal_reviewer_id:
            raise UserError(_("Only the designated legal reviewer can approve"))

        self.write({
            'legal_approval_date': fields.Datetime.now(),
            'approval_status': 'pending_compliance' if self.compliance_reviewer_id else 'approved',
        })

        if self.compliance_reviewer_id:
            self._send_compliance_review_notification()

        # Create audit log
        self._create_audit_log('legal_approved')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Legal Approval Granted'),
                'message': _('Legal review completed and approved'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_compliance_approve(self):
        """Compliance department approval"""
        self.ensure_one()

        if self.approval_status != 'pending_compliance':
            raise UserError(_("Only requests pending compliance review can be approved"))

        if self.env.user != self.compliance_reviewer_id:
            raise UserError(_("Only the designated compliance reviewer can approve"))

        self.write({
            'compliance_approval_date': fields.Datetime.now(),
            'approval_status': 'approved',
            'state': 'approved',
        })

        # Create audit log
        self._create_audit_log('compliance_approved')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Compliance Approval Granted'),
                'message': _('Compliance review completed and approved'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_process_permanent_flags(self):
        """Process the permanent flag assignments"""
        self.ensure_one()

        if self.approval_status != 'approved':
            raise UserError(_("Only approved requests can be processed"))

        if self.processing_completed:
            raise UserError(_("This request has already been processed"))

        self.state = 'processing'

        try:
            records_flagged = self._apply_permanent_flags()

            self.write({
                'processing_completed': True,
                'records_flagged_count': records_flagged,
                'state': 'completed',
                'processing_notes': _('Successfully flagged %s records as permanent on %s') % (
                    records_flagged, fields.Datetime.now()
                )
            })

            # Send customer notification if requested
            if self.notify_customer and self.customer_id:
                self._send_customer_notification()

            # Create audit log
            self._create_audit_log('processing_completed')

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Processing Complete'),
                    'message': _('%s records flagged as permanent') % records_flagged,
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            self.state = 'approved'
            raise UserError(_("Error during processing: %s") % str(e))

    def _validate_selection(self):
        """Validate the selection criteria"""
        if self.selection_method == 'single_container' and not self.container_id:
            raise UserError(_("Please select a container"))

        if self.selection_method == 'multiple_containers' and not self.container_ids:
            raise UserError(_("Please select containers"))

        if self.selection_method == 'date_range' and (not self.date_from or not self.date_to):
            raise UserError(_("Please specify date range"))

        if self.selection_method == 'date_range' and self.date_from > self.date_to:
            raise UserError(_("Date from must be before date to"))

        if self.selection_method in ['customer_all', 'category_based'] and not self.customer_id:
            raise UserError(_("Please select a customer"))

        if self.selection_method == 'category_based' and not self.document_category:
            raise UserError(_("Please select a document category"))

        return True

    def _apply_permanent_flags(self):
        """Apply permanent flags to selected records"""
        flagged_count = 0

        # Get target containers based on selection method
        containers = self._get_target_containers()

        for container in containers:
            # Flag container as permanent
            container.write({
                'retention_status': 'permanent',
                'permanent_flag_date': fields.Date.today(),
                'permanent_reason': self.permanent_reason,
                'permanent_notes': self.permanent_notes,
            })
            flagged_count += 1

            # Flag all documents in container
            documents = self.env['records.document'].search([
                ('container_id', '=', container.id)
            ])

            for document in documents:
                document.write({
                    'retention_status': 'permanent',
                    'permanent_flag_date': fields.Date.today(),
                    'permanent_reason': self.permanent_reason,
                })
                flagged_count += 1

        return flagged_count

    def _get_target_containers(self):
        """Get containers based on selection method"""
        if self.selection_method == 'single_container':
            return self.container_id
        elif self.selection_method == 'multiple_containers':
            return self.container_ids
        elif self.selection_method == 'customer_all':
            return self.env['records.container'].search([
                ('partner_id', '=', self.customer_id.id)
            ])
        elif self.selection_method == 'date_range':
            return self.env['records.container'].search([
                ('create_date', '>=', self.date_from),
                ('create_date', '<=', self.date_to)
            ])
        else:
            return self.env['records.container']

    def _send_legal_review_notification(self):
        """Send notification to legal reviewer"""
        if self.legal_reviewer_id:
            try:
                template = self.env.ref('records_management.permanent_flag_legal_review_template', False)
                if template:
                    template.send_mail(self.id)
            except Exception:
                pass

    def _send_compliance_review_notification(self):
        """Send notification to compliance reviewer"""
        if self.compliance_reviewer_id:
            try:
                template = self.env.ref('records_management.permanent_flag_compliance_review_template', False)
                if template:
                    template.send_mail(self.id)
            except Exception:
                pass

    def _send_customer_notification(self):
        """Send notification to customer"""
        if self.customer_notification_template and self.customer_id:
            try:
                self.customer_notification_template.send_mail(self.customer_id.id)
            except Exception:
                pass

    def _create_audit_log(self, action):
        """Create audit log entry"""
        try:
            self.env['naid.audit.log'].create({
                'name': _('Permanent Flag %s - %s') % (action.title(), self.permanent_reason),
                'action': 'permanent_flag_%s' % action,
                'user_id': self.env.user.id,
                'notes': _('Permanent flag processing: %s records affected') % self.estimated_records_count,
                'audit_date': fields.Datetime.now(),
            })
        except Exception:
            pass
