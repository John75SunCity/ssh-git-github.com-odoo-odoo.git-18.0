from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsBillingConfigAudit(models.Model):
    _name = 'records.billing.config.audit'
    _description = 'Records Billing Config Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Audit Entry", compute='_compute_name', store=True)
    config_id = fields.Many2one('records.billing.config', string="Billing Configuration", required=True, ondelete='cascade', readonly=True)
    user_id = fields.Many2one('res.users', string="Changed By", required=True, readonly=True, default=lambda self: self.env.user)
    audit_date = fields.Datetime(string="Change Date", required=True, readonly=True, default=fields.Datetime.now)
    company_id = fields.Many2one(related='config_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)

    # ============================================================================
    # CHANGE DETAILS
    # ============================================================================
    action_type = fields.Selection([
        ('create', 'Create'),
        ('write', 'Update'),
        ('archive', 'Archive'),
    ], string="Action", required=True, readonly=True)

    field_changed = fields.Char(string="Field Changed", readonly=True)
    old_value = fields.Text(string="Old Value", readonly=True)
    new_value = fields.Text(string="New Value", readonly=True)
    change_reason = fields.Text(string="Reason for Change")

    # ============================================================================
    # APPROVAL & IMPACT
    # ============================================================================
    requires_approval = fields.Boolean(string="Requires Approval", readonly=True)
    approval_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Approval Status", default='pending', tracking=True)

    approved_by_id = fields.Many2one('res.users', string="Approved By", readonly=True)
    approval_date = fields.Datetime(string="Approval Date", readonly=True)

    impact_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string="Impact Level", readonly=True)

    # ============================================================================
    # TECHNICAL DETAILS
    # ============================================================================
    ip_address = fields.Char(string="IP Address", readonly=True)
    user_agent = fields.Text(string="User Agent", readonly=True)

    # New Fields from analysis
    partner_id = fields.Many2one('res.partner', string='Customer')
    billing_profile_id = fields.Many2one('records.billing.profile', string='Billing Profile')
    billing_contact_id = fields.Many2one('records.billing.contact', string='Billing Contact')
    billing_address_id = fields.Many2one('res.partner', string='Billing Address')
    shipping_address_id = fields.Many2one('res.partner', string='Shipping Address')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    payment_method_id = fields.Many2one('account.payment.method', 'Payment Method')
    journal_id = fields.Many2one('account.journal', string='Journal')
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')
    tax_id = fields.Many2one('account.tax', string='Tax')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    product_id = fields.Many2one('product.product', string='Product')
    product_template_id = fields.Many2one('product.template', string='Product Template')
    product_category_id = fields.Many2one('product.category', string='Product Category')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    pricelist_item_id = fields.Many2one('product.pricelist.item', string='Pricelist Item')
    discount = fields.Float(string='Discount (%)')
    price_unit = fields.Float(string='Unit Price')
    price_subtotal = fields.Monetary(string='Subtotal')
    price_total = fields.Monetary(string='Total')
    price_tax = fields.Float(string='Tax Amount')
    price_before_discount = fields.Monetary(string='Price Before Discount')
    price_after_discount = fields.Monetary(string='Price After Discount')
    quantity = fields.Float(string='Quantity')
    is_recurring = fields.Boolean(string='Is Recurring')
    recurring_interval = fields.Integer(string='Recurring Interval')
    recurring_rule_type = fields.Selection([('daily', 'Day(s)'), ('weekly', 'Week(s)'), ('monthly', 'Month(s)'), ('yearly', 'Year(s)')], string='Recurrency')
    recurring_next_date = fields.Date(string='Next Billing Date')
    recurring_last_date = fields.Date(string='Last Billing Date')
    is_prepaid = fields.Boolean(string='Is Prepaid')
    prepaid_amount = fields.Monetary(string='Prepaid Amount')
    prepaid_balance = fields.Monetary(string='Prepaid Balance')
    is_postpaid = fields.Boolean(string='Is Postpaid')
    postpaid_amount = fields.Monetary(string='Postpaid Amount')
    postpaid_balance = fields.Monetary(string='Postpaid Balance')
    is_billed = fields.Boolean(string='Is Billed')
    billed_date = fields.Date(string='Billed Date')
    is_paid = fields.Boolean(string='Is Paid')
    paid_date = fields.Date(string='Paid Date')
    is_cancelled = fields.Boolean(string='Is Cancelled')
    cancelled_date = fields.Date(string='Cancelled Date')
    is_suspended = fields.Boolean(string='Is Suspended')
    suspended_date = fields.Date(string='Suspended Date')
    is_active = fields.Boolean(string='Is Active')
    active_date = fields.Date(string='Active Date')
    is_trial = fields.Boolean(string='Is Trial')
    trial_start_date = fields.Date(string='Trial Start Date')
    trial_end_date = fields.Date(string='Trial End Date')
    is_expired = fields.Boolean(string='Is Expired')
    expiration_date = fields.Date(string='Expiration Date')
    is_upgraded = fields.Boolean(string='Is Upgraded')
    upgraded_date = fields.Date(string='Upgraded Date')
    is_downgraded = fields.Boolean(string='Is Downgraded')
    downgraded_date = fields.Date(string='Downgraded Date')
    is_renewed = fields.Boolean(string='Is Renewed')
    renewed_date = fields.Date(string='Renewed Date')
    is_auto_renew = fields.Boolean(string='Auto Renew')
    is_manual_renew = fields.Boolean(string='Manual Renew')
    is_on_hold = fields.Boolean(string='On Hold')
    on_hold_date = fields.Date(string='On Hold Date')
    is_off_hold = fields.Boolean(string='Off Hold')
    off_hold_date = fields.Date(string='Off Hold Date')
    is_in_grace_period = fields.Boolean(string='In Grace Period')
    grace_period_start_date = fields.Date(string='Grace Period Start Date')
    grace_period_end_date = fields.Date(string='Grace Period End Date')
    is_in_dunning = fields.Boolean(string='In Dunning')
    dunning_start_date = fields.Date(string='Dunning Start Date')
    dunning_end_date = fields.Date(string='Dunning End Date')
    is_in_collections = fields.Boolean(string='In Collections')
    collections_start_date = fields.Date(string='Collections Start Date')
    collections_end_date = fields.Date(string='Collections End Date')
    is_in_litigation = fields.Boolean(string='In Litigation')
    litigation_start_date = fields.Date(string='Litigation Start Date')
    litigation_end_date = fields.Date(string='Litigation End Date')
    is_in_bankruptcy = fields.Boolean(string='In Bankruptcy')
    bankruptcy_start_date = fields.Date(string='Bankruptcy Start Date')
    bankruptcy_end_date = fields.Date(string='Bankruptcy End Date')
    is_in_receivership = fields.Boolean(string='In Receivership')
    receivership_start_date = fields.Date(string='Receivership Start Date')
    receivership_end_date = fields.Date(string='Receivership End Date')
    is_in_probate = fields.Boolean(string='In Probate')
    probate_start_date = fields.Date(string='Probate Start Date')
    probate_end_date = fields.Date(string='Probate End Date')
    is_in_foreclosure = fields.Boolean(string='In Foreclosure')
    foreclosure_start_date = fields.Date(string='Foreclosure Start Date')
    foreclosure_end_date = fields.Date(string='Foreclosure End Date')
    is_in_repossession = fields.Boolean(string='In Repossession')
    repossession_start_date = fields.Date(string='Repossession Start Date')
    repossession_end_date = fields.Date(string='Repossession End Date')
    is_in_charge_off = fields.Boolean(string='In Charge Off')
    charge_off_date = fields.Date(string='Charge Off Date')
    is_in_write_off = fields.Boolean(string='In Write Off')
    write_off_date = fields.Date(string='Write Off Date')
    is_in_settlement = fields.Boolean(string='In Settlement')
    settlement_date = fields.Date(string='Settlement Date')
    is_in_dispute = fields.Boolean(string='In Dispute')
    dispute_date = fields.Date(string='Dispute Date')
    is_in_fraud = fields.Boolean(string='In Fraud')
    fraud_date = fields.Date(string='Fraud Date')
    is_in_identity_theft = fields.Boolean(string='In Identity Theft')
    identity_theft_date = fields.Date(string='Identity Theft Date')
    is_in_deceased = fields.Boolean(string='In Deceased')
    deceased_date = fields.Date(string='Deceased Date')
    is_in_unclaimed = fields.Boolean(string='In Unclaimed')
    unclaimed_date = fields.Date(string='Unclaimed Date')
    is_in_escheatment = fields.Boolean(string='In Escheatment')
    escheatment_date = fields.Date(string='Escheatment Date')
    is_in_abandonment = fields.Boolean(string='In Abandonment')
    abandonment_date = fields.Date(string='Abandonment Date')
    is_in_liquidation = fields.Boolean(string='In Liquidation')
    liquidation_date = fields.Date(string='Liquidation Date')
    is_in_dissolution = fields.Boolean(string='In Dissolution')
    dissolution_date = fields.Date(string='Dissolution Date')
    is_in_merger = fields.Boolean(string='In Merger')
    merger_date = fields.Date(string='Merger Date')
    is_in_acquisition = fields.Boolean(string='In Acquisition')
    acquisition_date = fields.Date(string='Acquisition Date')
    is_in_divestiture = fields.Boolean(string='In Divestiture')
    divestiture_date = fields.Date(string='Divestiture Date')
    is_in_spinoff = fields.Boolean(string='In Spinoff')
    spinoff_date = fields.Date(string='Spinoff Date')
    is_in_joint_venture = fields.Boolean(string='In Joint Venture')
    joint_venture_date = fields.Date(string='Joint Venture Date')
    is_in_partnership = fields.Boolean(string='In Partnership')
    partnership_date = fields.Date(string='Partnership Date')
    is_in_sole_proprietorship = fields.Boolean(string='In Sole Proprietorship')
    sole_proprietorship_date = fields.Date(string='Sole Proprietorship Date')
    is_in_corporation = fields.Boolean(string='In Corporation')
    corporation_date = fields.Date(string='Corporation Date')
    is_in_llc = fields.Boolean(string='In LLC')
    llc_date = fields.Date(string='LLC Date')
    is_in_non_profit = fields.Boolean(string='In Non Profit')
    non_profit_date = fields.Date(string='Non Profit Date')
    is_in_government = fields.Boolean(string='In Government')
    government_date = fields.Date(string='Government Date')
    is_in_education = fields.Boolean(string='In Education')
    education_date = fields.Date(string='Education Date')
    is_in_religious = fields.Boolean(string='In Religious')
    religious_date = fields.Date(string='Religious Date')
    is_in_other = fields.Boolean(string='In Other')
    other_date = fields.Date(string='Other Date')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('action_type', 'field_changed', 'audit_date')
    def _compute_name(self):
        for record in self:
            parts = []
            if record.action_type:
                action_dict = dict(record._fields['action_type'].selection)
                parts.append(action_dict.get(record.action_type, record.action_type))
            if record.field_changed:
                parts.append(f"({record.field_changed})")
            if record.audit_date:
                parts.append(f"on {record.audit_date.strftime('%Y-%m-%d')}")
            record.name = " ".join(parts) if parts else _("New Audit Entry")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_approve_change(self):
        self.ensure_one()
        if not self.requires_approval:
            raise UserError(_('This change does not require approval.'))
        if self.approval_status == 'approved':
            raise UserError(_('This change has already been approved.'))

        self.write({
            'approval_status': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Change approved by %s', self.env.user.name))

    def action_reject_change(self):
        self.ensure_one()
        if not self.requires_approval:
            raise UserError(_('This change does not require approval.'))

        self.write({
            'approval_status': 'rejected',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Change rejected by %s', self.env.user.name))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    @api.model
    def log_change(self, config, action_type, changes):
        """
        Utility method to create audit log entries for one or more field changes.
        :param config: The records.billing.config recordset.
        :param action_type: The type of action ('write', 'create', etc.).
        :param changes: A dictionary of changes, e.g., {'field_name': {'old': old_val, 'new': new_val}}.
        """
        request = self.env.context.get('request')
        ip = request.httprequest.remote_addr if request else ''
        ua = request.httprequest.user_agent.string if request else ''

        for field, values in changes.items():
            audit_vals = {
                'config_id': config.id,
                'action_type': action_type,
                'field_changed': field,
                'old_value': str(values.get('old')),
                'new_value': str(values.get('new')),
                'user_id': self.env.user.id,
                'ip_address': ip,
                'user_agent': ua,
            }

            # Determine impact and approval requirements
            if field in ['unit_price', 'recurring_interval']:
                audit_vals.update({
                    'impact_level': 'high',
                    'requires_approval': True,
                    'approval_status': 'pending',
                })
            elif field in ['active', 'billing_type']:
                audit_vals.update({'impact_level': 'medium'})
            else:
                audit_vals.update({'impact_level': 'low'})

            audit_entry = self.create(audit_vals)
            if audit_vals.get('requires_approval'):
                # Create activity for manager if one is configured
                manager_group = self.env.ref('records_management.group_records_manager', raise_if_not_found=False)
                if manager_group:
                    audit_entry.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary=_('Review High-Impact Billing Change'),
                        note=_('Please review and approve the change to "%s" on billing config "%s"', field, config.name),
                        user_id=manager_group.users[0].id if manager_group.users else self.env.user.company_id.partner_id.user_ids[0].id if self.env.user.company_id.partner_id.user_ids else None
                    )
        return True

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('old_value', 'new_value', 'action_type')
    def _check_values_different(self):
        for record in self:
            if record.action_type == 'write' and record.old_value == record.new_value:
                raise ValidationError(_('Old and new values must be different for an update action.'))

    @api.constrains('approval_status', 'approved_by_id')
    def _check_approval_consistency(self):
        for record in self:
            if record.approval_status in ['approved', 'rejected'] and not record.approved_by_id:
                raise ValidationError(_('Approved or rejected entries must have a processing user.'))
