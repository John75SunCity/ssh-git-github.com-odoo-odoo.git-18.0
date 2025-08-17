# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CustomerNegotiatedRate(models.Model):
    """Customer Negotiated Rate"

        Manages customer-specific negotiated rates that override standard pricing.
    Supports container-type specific rates, service rates, and volume-based pricing.
        Integrates with billing profiles and rate management system.

    _name = 'customer.negotiated.rate'
    _description = 'Customer Negotiated Rate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'partner_id, rate_type, effective_date desc'

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string='Rate Name',
        required=True,
        tracking=True,
        help='Name for this negotiated rate':
            pass

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ,
    domain=[('is_company', '=', True)),
        tracking=True,
        help='Customer this negotiated rate applies to'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True

    user_id = fields.Many2one(
        'res.users',
        string='Account Manager',
        default=lambda self: self.env.user,
        tracking=True,
        help='Account manager who negotiated this rate'

    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Whether this negotiated rate is active'


        # ============================================================================
    # RATE CLASSIFICATION FIELDS
        # ============================================================================
    ,
    rate_type = fields.Selection([))
        ('storage', 'Storage Rate'),
        ('service', 'Service Rate'),
        ('volume_discount', 'Volume Discount'),
        ('custom', 'Custom Rate')


    container_type = fields.Selection([))
        ('type_01', 'TYPE 1 - Standard Box (1.2 CF)'),
        ('type_02', 'TYPE 2 - Legal/Banker Box (2.4 CF)'),
        ('type_03', 'TYPE 3 - Map Box (0.875 CF)'),
        ('type_04', 'TYPE 4 - Odd Size/Temp Box (5.0 CF)'),
        ('type_06', 'TYPE 6 - Pathology Box (0.42 CF)'),
        ('all', 'All Container Types')


    service_type = fields.Selection([))
        ('pickup', 'Pickup Service'),
        ('delivery', 'Delivery Service'),
        ('destruction', 'Destruction Service'),
        ('retrieval', 'Document Retrieval'),
        ('scanning', 'Document Scanning'),
        ('indexing', 'Document Indexing'),
        ('storage_move', 'Storage Location Move'),
        ('inventory_audit', 'Inventory Audit')


        # ============================================================================
    # RATE VALIDITY FIELDS
        # ============================================================================
    effective_date = fields.Date(
        string='Effective Date',
        default=fields.Date.today,
        required=True,
        tracking=True,
        help='Date this rate becomes effective'

    expiration_date = fields.Date(
        string='Expiration Date',
        tracking=True,
        ,
    help='Date this rate expires (leave blank for no expiration)':

    is_current = fields.Boolean(
        string='Currently Active',
        compute='_compute_is_current',
        store=True,
        help='Whether this rate is currently active'


        # ============================================================================
    # PRICING FIELDS
        # ============================================================================
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True


        # Storage rates
    monthly_rate = fields.Monetary(
        string='Monthly Rate',
        currency_field='currency_id',
        help='Monthly storage rate per container'

    annual_rate = fields.Monetary(
        string='Annual Rate',
        currency_field='currency_id',
        help='Annual storage rate per container'

    setup_fee = fields.Monetary(
        string='Setup Fee',
        currency_field='currency_id',
        help='One-time setup fee for new containers':


        # Service rates
    per_service_rate = fields.Monetary(
        string='Per Service Rate',
        currency_field='currency_id',
        help='Rate per service request'

    per_hour_rate = fields.Monetary(
        string='Per Hour Rate',
        currency_field='currency_id',
        help='Hourly rate for time-based services':

    per_document_rate = fields.Monetary(
        string='Per Document Rate',
        currency_field='currency_id',
        help='Rate per document for document services':


        # Volume-based pricing
    minimum_volume = fields.Integer(
        string='Minimum Volume',
        default=1,
        help='Minimum volume required for this rate':

    maximum_volume = fields.Integer(
        string='Maximum Volume',
        help='Maximum volume this rate applies to'

    discount_percentage = fields.Float(
        string='Discount Percentage',
        help='Percentage discount from base rate'


        # ============================================================================
    # CONTRACT FIELDS
        # ============================================================================
    contract_reference = fields.Char(
        string='Contract Reference',
        help='Reference to the contract where this rate was negotiated'

    approval_required = fields.Boolean(
        string='Requires Approval',
        default=True,
        help='Whether this rate requires management approval'

    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
        tracking=True,
        help='User who approved this rate'

    approval_date = fields.Datetime(
        string='Approval Date',
        tracking=True,
        help='Date this rate was approved'

    ,
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Approval'),:
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')


        # ============================================================================
    # BILLING INTEGRATION FIELDS
        # ============================================================================
    billing_profile_id = fields.Many2one(
        'customer.billing.profile',
        string='Billing Profile',
        ,
    domain="[('partner_id', '=', partner_id))",
        help='Billing profile this rate is associated with'

    auto_apply = fields.Boolean(
        string='Auto Apply',
        default=True,
        help='Automatically apply this rate when conditions are met'

    priority = fields.Integer(
        string='Priority',
        default=10,
        ,
    help='Priority order when multiple rates could apply (lower = higher priority)'


        # ============================================================================
    # COMPUTED FIELDS
        # ============================================================================
    base_rate_comparison = fields.Monetary(
        string='Base Rate',
        compute='_compute_rate_comparison',
        currency_field='currency_id',
        help='Corresponding base rate for comparison':

    savings_amount = fields.Monetary(
        string='Monthly Savings',
        compute='_compute_rate_comparison',
        currency_field='currency_id',
        help='Monthly savings compared to base rate'

    savings_percentage = fields.Float(
        string='Savings %',
        compute='_compute_rate_comparison',
        help='Percentage savings compared to base rate'


        # Statistics
    containers_using_rate = fields.Integer(
        string='Containers Using Rate',
        compute='_compute_usage_stats',
        help='Number of containers currently using this rate'

    monthly_revenue_impact = fields.Monetary(
        string='Monthly Revenue Impact',
        compute='_compute_usage_stats',
        currency_field='currency_id',
        ,
    help='Monthly revenue impact of this rate'


        # ============================================================================
    # MAIL FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance):
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        ,
    domain=lambda self: [("res_model", "=", self._name))


    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        ,
    domain=lambda self: [("res_model", "=", self._name))


    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        ,
    domain=lambda self: [("model", "=", self._name))

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('effective_date', 'expiration_date')
    def _compute_is_current(self):
        """Determine if rate is currently active""":
    today = fields.Date.today()
        for rate in self:
            if rate.effective_date > today:
                rate.is_current = False
            elif rate.expiration_date and rate.expiration_date < today:
                rate.is_current = False
            else:
                rate.is_current = rate.state in ['approved', 'active']

    @api.depends('monthly_rate', 'container_type', 'rate_type')
    def _compute_rate_comparison(self):
        """Compare negotiated rate to base rate"""
        for rate in self:
            if rate.rate_type != 'storage' or not rate.monthly_rate:
                rate.base_rate_comparison = 0.0
                rate.savings_amount = 0.0
                rate.savings_percentage = 0.0
                continue

            # Get base rate for comparison:
            base_rates = self.env['base.rate'].search([)]
                ('company_id', '=', rate.company_id.id),
                ('active', '=', True)


            if not base_rates:
                rate.base_rate_comparison = 0.0
                rate.savings_amount = 0.0
                rate.savings_percentage = 0.0
                continue

            # Get base rate based on container type
            if rate.container_type == 'type_01':
                base_rate = base_rates.standard_box_rate
            elif rate.container_type == 'type_02':
                base_rate = base_rates.legal_box_rate
            elif rate.container_type == 'type_03':
                base_rate = base_rates.map_box_rate
            elif rate.container_type == 'type_04':
                base_rate = base_rates.odd_size_rate
            elif rate.container_type == 'type_06':
                base_rate = base_rates.pathology_rate
            else:
                base_rate = base_rates.standard_box_rate

            rate.base_rate_comparison = base_rate
            rate.savings_amount = base_rate - rate.monthly_rate

            if base_rate > 0:
                rate.savings_percentage = ((base_rate - rate.monthly_rate) / base_rate) * 100
            else:
                rate.savings_percentage = 0.0

    @api.depends('partner_id', 'container_type', 'is_current')
    def _compute_usage_stats(self):
        """Compute usage statistics for this rate""":
        for rate in self:
            if not rate.partner_id or not rate.is_current:
                rate.containers_using_rate = 0
                rate.monthly_revenue_impact = 0.0
                continue

            # Count containers that would use this rate
            domain = [('partner_id', '=', rate.partner_id.id), ('active', '=', True)]
            if rate.container_type != 'all':
                domain.append(('container_type', '=', rate.container_type))

            containers = self.env['records.container'].search(domain)
            rate.containers_using_rate = len(containers)
            rate.monthly_revenue_impact = len(containers) * (rate.monthly_rate or 0.0)

    # ============================================================================
        # CONSTRAINT VALIDATIONS
    # ============================================================================
    @api.constrains('effective_date', 'expiration_date')
    def _check_date_validity(self):
        """Validate date range"""
        for rate in self:
            if rate.expiration_date and rate.effective_date > rate.expiration_date:
                raise ValidationError(_('Effective date cannot be after expiration date'))

    @api.constrains('minimum_volume', 'maximum_volume')
    def _check_volume_range(self):
        """Validate volume range"""
        for rate in self:
            if rate.maximum_volume and rate.minimum_volume > rate.maximum_volume:
                raise ValidationError(_('Minimum volume cannot be greater than maximum volume'))

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        """Validate discount percentage"""
        for rate in self:
            if rate.discount_percentage < 0 or rate.discount_percentage > 100:
                raise ValidationError(_('Discount percentage must be between 0 and 100'))

    @api.constrains('priority')
    def _check_priority(self):
        """Validate priority value"""
        for rate in self:
            if rate.priority < 0:
                raise ValidationError(_('Priority must be a positive number'))

    # ============================================================================
        # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update fields when customer changes"""
        if self.partner_id:
            # Set default name
            if not self.name or self.name == 'New':
                self.name = _('%s - Negotiated Rate', self.partner_id.name)

            # Look for existing billing profile:
            billing_profile = self.env['customer.billing.profile'].search([)]
                ('partner_id', '=', self.partner_id.id),
                ('active', '=', True)

            if billing_profile:
                self.billing_profile_id = billing_profile.id

    @api.onchange('rate_type')
    def _onchange_rate_type(self):
        """Clear irrelevant fields when rate type changes"""
        if self.rate_type == 'storage':
            self.service_type = False
            self.per_service_rate = 0.0
            self.per_hour_rate = 0.0
            self.per_document_rate = 0.0
        elif self.rate_type == 'service':
            self.container_type = False
            self.monthly_rate = 0.0
            self.annual_rate = 0.0
        elif self.rate_type == 'volume_discount':
            self.per_service_rate = 0.0
            self.per_hour_rate = 0.0
            self.per_document_rate = 0.0

    @api.onchange('monthly_rate')
    def _onchange_monthly_rate(self):
        """Calculate annual rate when monthly rate changes"""
        if self.monthly_rate:
            self.annual_rate = self.monthly_rate * 12

    @api.onchange('annual_rate')
    def _onchange_annual_rate(self):
        """Calculate monthly rate when annual rate changes"""
        if self.annual_rate:
            self.monthly_rate = self.annual_rate / 12

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_submit_for_approval(self):
        """Submit rate for management approval""":
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_('Only draft rates can be submitted for approval')):
        self.write({'state': 'submitted'})

        # Create activity for approver:
        self.activity_schedule()
            'mail.mail_activity_data_todo',
            summary=_('Rate Approval Required'),
            note=_('Negotiated rate for %s requires approval', self.partner_id.name),:
            user_id=self.env.user.id  # Could be dynamic based on approval workflow


        return {}
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {}
                'message': _('Rate submitted for approval'),:
                'type': 'success'



    def action_approve_rate(self):
        """Approve the negotiated rate"""
        self.ensure_one()
        if self.state != 'submitted':
            raise ValidationError(_('Only submitted rates can be approved'))

        self.write({)}
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now()


        # Activate if effective date has passed:
    if self.effective_date <= fields.Date.today():
            self.state = 'active'

        return {}
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {}
                'message': _('Rate approved successfully'),
                'type': 'success'



    def action_activate_rate(self):
        """Activate the rate (if approved and effective date reached)""":
        self.ensure_one()
        if self.state != 'approved':
            raise ValidationError(_('Rate must be approved before activation'))

        if self.effective_date > fields.Date.today():
            raise ValidationError(_('Cannot activate rate before effective date'))

        self.write({'state': 'active'})

        return {}
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {}
                'message': _('Rate activated successfully'),
                'type': 'success'



    def action_expire_rate(self):
        """Expire the rate"""
        self.ensure_one()
        self.write({'state': 'expired'})

        return {}
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {}
                'message': _('Rate expired'),
                'type': 'info'



    def action_view_containers(self):
        """View containers that use this rate"""
        self.ensure_one()

        domain = [('partner_id', '=', self.partner_id.id)]
        if self.container_type != 'all':
            domain.append(('container_type', '=', self.container_type))

        return {}
            'type': 'ir.actions.act_window',
            'name': _('Containers Using This Rate'),
            'res_model': 'records.container',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_partner_id': self.partner_id.id}


    def action_duplicate_rate(self):
        """Duplicate this rate for modification""":
        self.ensure_one()

        new_rate = self.copy({)}
            'name': _('%s (Copy)', self.name),
            'state': 'draft',
            'approved_by_id': False,
            'approval_date': False,
            'effective_date': fields.Date.today()


        return {}
            'type': 'ir.actions.act_window',
            'name': _('Negotiated Rate'),
            'res_model': 'customer.negotiated.rate',
            'res_id': new_rate.id,
            'view_mode': 'form',
            'target': 'current'


    # ============================================================================
        # CRON AND SCHEDULED METHODS
    # ============================================================================
    @api.model
    def cron_activate_rates(self):
        """Cron job to activate approved rates when effective date is reached"""
        rates_to_activate = self.search([)]
            ('state', '=', 'approved'),
            ('effective_date', '<=', fields.Date.today())


        for rate in rates_to_activate:
            rate.state = 'active'

        return True

    @api.model
    def cron_expire_rates(self):
        """Cron job to expire rates when expiration date is reached"""
        rates_to_expire = self.search([)]
            ('state', 'in', ['active', 'approved']),
            ('expiration_date', '<', fields.Date.today())


        for rate in rates_to_expire:
            rate.state = 'expired'

        return True

    """"))))))))))))))))))))))))
