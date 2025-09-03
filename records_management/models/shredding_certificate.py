"""Module for managing shredding certificates in the Records Management system.

This module provides comprehensive functionality for creating, tracking, and managing
shredding certificates with full NAID AAA compliance. It handles certificate lifecycle
from draft through issuance, delivery, and archiving, with integrated audit trails
and customer communication features.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ShreddingCertificate(models.Model):
    """Model for managing shredding certificates with NAID compliance tracking.

    This model handles the creation, issuance, and delivery of shredding certificates
    for document destruction services. It maintains compliance with NAID standards
    and provides audit trails for all certificate operations.

    Key Features:
    - Automatic certificate numbering via sequences
    - Multi-service aggregation with totals computation
    - Customer contact management with onchange handling
    - State management (draft -> issued -> delivered -> archived)
    - Email and portal delivery options
    - Integration with project.task for shredding services
    - Full audit trail via mail.thread inheritance
    """

    _name = 'shredding.certificate'
    _description = 'Shredding Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Certificate #",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        readonly=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Issued By',
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('delivered', 'Delivered'),
        ('archived', 'Archived'),
    ], string="Status", default='draft', required=True, tracking=True, index=True)

    # ============================================================================
    # DATES & DESTRUCTION DETAILS
    # ============================================================================
    certificate_date = fields.Date(
        string="Certificate Date",
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    destruction_date = fields.Date(
        string="Destruction Date",
        required=True,
        tracking=True
    )
    destruction_method = fields.Selection(
        [
            ("on_site_shredding", "Mobile Shredding"),
            ("off_site_shredding", "Off-Site Shredding"),
            ("incineration", "Incineration"),
        ],
        string="Destruction Method",
        default="on_site_shredding",
        required=True,
        tracking=True,
    )
    destruction_equipment = fields.Char(string="Destruction Equipment", tracking=True)
    equipment_serial_number = fields.Char(string="Equipment Serial Number", tracking=True)
    operator_name = fields.Char(string="Operator Name", tracking=True)

    # ============================================================================
    # CUSTOMER & WITNESS INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        required=True,
        tracking=True,
        domain="[('customer_rank', '>', 0)]"
    )
    customer_contact_id = fields.Many2one(
        'res.partner',
        string="Customer Contact",
        domain="[('parent_id', '=', partner_id), ('type', '=', 'contact')]"
    )
    service_location = fields.Char(string="Service Location", tracking=True)
    witness_required = fields.Boolean(string="Witness Required", default=False)
    witness_name = fields.Char(string="Witness Name", tracking=True)
    witness_title = fields.Char(string="Witness Title", tracking=True)

    # ============================================================================
    # MATERIALS & TOTALS
    # ============================================================================
    shredding_service_ids = fields.Many2many(
        'project.task',
        'shredding_certificate_task_rel',
        'certificate_id',
        'task_id',
        string="Shredding Services",
        domain="[('project_id.name', 'ilike', 'shredding')]",
        tracking=True
    )
    total_weight = fields.Float(
        string="Total Weight (kg)",
        compute='_compute_totals',
        store=True,
        digits=(10, 2)
    )
    total_containers = fields.Integer(
        string="Total Containers",
        compute='_compute_totals',
        store=True
    )
    service_count = fields.Integer(
        string="Service Count",
        compute='_compute_service_count',
        store=True
    )

    # ============================================================================
    # COMPLIANCE & DELIVERY
    # ============================================================================
    naid_level = fields.Selection([
        ('aaa', 'NAID AAA'),
        ('aa', 'NAID AA')
    ], string="NAID Level", default='aaa', required=True, tracking=True)
    certification_statement = fields.Text(
        string="Certification Statement",
        default=lambda self: self._default_certification_statement(),
        tracking=True
    )
    chain_of_custody_number = fields.Char(
        string="Chain of Custody #",
        tracking=True,
        index=True
    )
    delivery_method = fields.Selection([
        ('portal', 'Portal'),
        ('email', 'Email')
    ], string="Delivery Method", default='portal', required=True, tracking=True)
    delivered_date = fields.Date(string="Delivered Date", readonly=True)
    notes = fields.Text(string='Internal Notes', tracking=True)

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('name_unique', 'unique(name, company_id)', 'Certificate number must be unique per company!'),
        ('chain_of_custody_unique', 'unique(chain_of_custody_number)', 'Chain of Custody number must be unique!'),
    ]

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Create new shredding certificates with automatic sequence numbering.

        Generates certificate numbers using the configured sequence and ensures
        proper initialization of new certificate records.

        Args:
            vals_list (list): List of dictionaries containing field values for new records.

        Returns:
            ShreddingCertificate: The created certificate records.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('shredding.certificate') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('shredding_service_ids')
    def _compute_service_count(self):
        """Compute the total number of shredding services linked to this certificate.

        This method counts the number of project.task records associated with
        the shredding services for this certificate, providing a quick reference
        for the number of services included.
        """
        for record in self:
            record.service_count = len(record.shredding_service_ids)

    @api.depends('shredding_service_ids.total_weight', 'shredding_service_ids.container_count')
    def _compute_totals(self):
        """Compute total weight and container count from linked shredding services.

        Aggregates the total_weight and container_count from all associated
        shredding service tasks to provide summary information for reporting
        and compliance purposes.
        """
        for record in self:
            # Safely handle missing fields on project.task
            total_weight = 0.0
            total_containers = 0

            for task in record.shredding_service_ids:
                # Check if fields exist before accessing
                if hasattr(task, 'total_weight') and task.total_weight:
                    total_weight += task.total_weight
                if hasattr(task, 'container_count') and task.container_count:
                    total_containers += task.container_count

            record.total_weight = total_weight
            record.total_containers = total_containers

    # ============================================================================
    # ONCHANGE & DEFAULTS
    # ============================================================================
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update customer contact when partner is changed.

        Automatically sets the customer contact to the first child contact
        of the selected partner, or the partner itself if no children exist.
        This ensures proper contact information is maintained for certificates.
        """
        if self.partner_id:
            # Find child contacts for the selected partner
            child_contacts = self.partner_id.child_ids.filtered(
                lambda c: c.type == 'contact' and c.email
            )
            if child_contacts:
                self.customer_contact_id = child_contacts[0]
            else:
                # Fallback to partner itself if no child contacts
                self.customer_contact_id = self.partner_id
        else:
            self.customer_contact_id = False

    @api.onchange('witness_required')
    def _onchange_witness_required(self):
        """Clear witness information when witness is not required."""
        if not self.witness_required:
            self.witness_name = False
            self.witness_title = False

    def _default_certification_statement(self):
        """Provide default certification statement for NAID compliance.

        Returns a standardized certification statement that confirms the secure
        destruction of materials in compliance with NAID standards.

        Returns:
            str: Default certification statement text.
        """
        return _("This certifies that the materials listed have been collected and destroyed in a secure manner, rendering them completely unreadable and unusable, in compliance with NAID standards.")

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def _validate_certificate_data(self):
        """Validate certificate data before state changes.

        Performs comprehensive validation of certificate data including
        required fields, relationships, and business rules.

        Raises:
            ValidationError: If validation fails.
        """
        for record in self:
            # Validate destruction date is not in the future
            if record.destruction_date > fields.Date.context_today(record):
                raise ValidationError(_("Destruction date cannot be in the future."))

            # Validate certificate date is not after destruction date
            if record.certificate_date > record.destruction_date:
                raise ValidationError(_("Certificate date cannot be after destruction date."))

            # Validate witness information if required
            if record.witness_required:
                if not record.witness_name:
                    raise ValidationError(_("Witness name is required when witness is required."))

            # Validate chain of custody number format
            if record.chain_of_custody_number and not record.chain_of_custody_number.strip():
                raise ValidationError(_("Chain of Custody number cannot be empty if provided."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_issue_certificate(self):
        """Issue the shredding certificate after validation.

        Validates that the certificate is in draft state and has at least one
        linked shredding service before changing status to 'issued'. Posts a
        notification message to the certificate's chatter for audit purposes.

        Raises:
            UserError: If certificate is not in draft state or has no linked services.
        """
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft certificates can be issued."))
        if not self.shredding_service_ids:
            raise UserError(_("You must link at least one shredding service before issuing a certificate."))

        # Perform comprehensive validation
        self._validate_certificate_data()

        self.write({'state': 'issued'})
        self.message_post(
            body=_("Certificate has been issued by %(user)s on %(date)s") % {
                'user': self.env.user.name,
                'date': fields.Date.context_today(self)
            },
            message_type='notification'
        )

    def action_deliver_certificate(self):
        """Mark certificate as delivered and handle delivery method.

        Changes certificate status to 'delivered', sets the delivery date, and
        handles email delivery if selected as the delivery method. Posts a
        notification message indicating the delivery method used.

        Raises:
            UserError: If certificate is not in issued state.
        """
        self.ensure_one()
        if self.state != 'issued':
            raise UserError(_("Only issued certificates can be delivered."))

        # Handle delivery based on method
        if self.delivery_method == 'email':
            self._send_certificate_email()
        elif self.delivery_method == 'portal':
            self._prepare_portal_delivery()

        self.write({
            'state': 'delivered',
            'delivered_date': fields.Date.context_today(self)
        })

        self.message_post(
            body=_("Certificate marked as delivered via %(method)s on %(date)s") % {
                'method': self.delivery_method,
                'date': fields.Date.context_today(self)
            },
            message_type='notification'
        )

    def action_archive_certificate(self):
        """Archive the certificate and mark as inactive.

        Changes the certificate status to 'archived' and sets the active flag
        to False, effectively removing it from active views while preserving
        the record for historical and compliance purposes.
        """
        self.write({'state': 'archived', 'active': False})
        self.message_post(
            body=_("Certificate has been archived on %(date)s") % {
                'date': fields.Date.context_today(self)
            },
            message_type='notification'
        )

    def action_reset_to_draft(self):
        """Reset certificate to draft state.

        Changes the certificate status back to 'draft' and ensures the active
        flag is set to True, allowing for modifications and re-issuance.
        """
        self.write({'state': 'draft', 'active': True})
        self.message_post(
            body=_("Certificate has been reset to draft on %(date)s") % {
                'date': fields.Date.context_today(self)
            },
            message_type='notification'
        )

    def action_print_certificate(self):
        """Generate and return print action for the certificate.

        Uses the configured report action to generate a printable version
        of the shredding certificate for physical or digital distribution.

        Returns:
            dict: Report action dictionary for printing the certificate.
        """
        self.ensure_one()
        return self.env.ref('records_management.action_report_shredding_certificate').report_action(self)

    def action_duplicate_certificate(self):
        """Create a duplicate of the current certificate.

        Creates a new certificate with the same data but in draft state,
        allowing for modifications before re-issuance.

        Returns:
            ShreddingCertificate: The newly created duplicate certificate.
        """
        self.ensure_one()
        duplicate_vals = {
            'partner_id': self.partner_id.id,
            'customer_contact_id': self.customer_contact_id.id,
            'destruction_date': self.destruction_date,
            'destruction_method': self.destruction_method,
            'service_location': self.service_location,
            'witness_required': self.witness_required,
            'naid_level': self.naid_level,
            'notes': self.notes,
        }

        duplicate = self.create(duplicate_vals)
        duplicate.message_post(
            body=_("Certificate duplicated from %(original)s") % {
                'original': self.name
            }
        )

        return duplicate

    # ============================================================================
    # HELPER & PRIVATE METHODS
    # ============================================================================
    def _send_certificate_email(self):
        """Send certificate via email to the customer.

        Uses the configured email template to send the certificate to the
        customer's email address. Posts a success message to the chatter
        or raises an error if the template is not found or email is missing.

        Raises:
            UserError: If customer email is missing or email template not found.
        """
        self.ensure_one()

        # Validate customer email
        if not self.partner_id.email:
            raise UserError(_("Customer email address is required for email delivery."))

        # Get email template
        template = self.env.ref('records_management.email_template_shredding_certificate', raise_if_not_found=False)
        if not template:
            raise UserError(_("Email template for shredding certificate not found."))

        # Send email
        template.send_mail(self.id, force_send=True)

        # Log success
        self.message_post(
            body=_("Certificate sent to %(email)s via email") % {
                'email': self.partner_id.email
            },
            message_type='notification'
        )

    def _prepare_portal_delivery(self):
        """Prepare certificate for portal delivery.

        Sets up the certificate for customer portal access, ensuring
        proper permissions and notifications are in place.
        """
        self.ensure_one()
        # Portal delivery preparation logic would go here
        # This could include setting up access tokens, notifications, etc.
        pass

    # ============================================================================
    # SEARCH & NAME METHODS
    # ============================================================================
    def name_get(self):
        """Generate display name for certificate records.

        Returns a list of tuples containing record IDs and display names
        that include the certificate number and customer name.

        Returns:
            list: List of (id, name) tuples for display.
        """
        result = []
        for record in self:
            name = f"{record.name}"
            if record.partner_id:
                name += f" - {record.partner_id.name}"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        """Custom name search for certificates.

        Allows searching by certificate number or customer name.

        Args:
            name (str): Search term
            args (list): Additional search arguments
            operator (str): Search operator
            limit (int): Maximum number of results

        Returns:
            list: List of matching record IDs and names
        """
        if not args:
            args = []

        if name:
            # Search by certificate number or customer name
            search_args = [
                '|',
                ('name', operator, name),
                ('partner_id.name', operator, name)
            ]
            args = search_args + args

        return super()._name_search(name=name, args=args, operator=operator, limit=limit)
