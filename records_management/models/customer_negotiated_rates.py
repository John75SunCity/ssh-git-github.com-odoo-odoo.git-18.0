# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CustomerNegotiatedRates(models.Model):
    _name = "customer.negotiated.rates"
    _description = "Customer Negotiated Rates"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "partner_id, effective_date desc"
    _rec_name = "display_name"

    # Core fields
    name = fields.Char(string="Agreement Name", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("negotiating", "Under Negotiation"),
            ("approved", "Approved"),
            ("active", "Active"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Customer Information
    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    contract_reference = fields.Char(string="Contract Reference", tracking=True)

    # Base Rate Reference
    base_rate_id = fields.Many2one(
        "base.rates",
        string="Base Rate Set",
        required=True,
        tracking=True,
        help="Base rate set that these negotiated rates override",
    )

    # Date Management
    effective_date = fields.Date(string="Effective Date", required=True, tracking=True)
    expiry_date = fields.Date(string="Expiry Date", tracking=True)
    negotiation_date = fields.Date(
        string="Negotiation Date", default=lambda self: fields.Date.today()
    )
    approval_date = fields.Date(string="Approval Date", tracking=True)

    # Negotiated Service Rates (override base rates)
    external_per_bin_rate = fields.Float(
        string="Negotiated External Per Bin Rate",
        digits=(12, 2),
        tracking=True,
        help="Customer-specific rate per bin for external shredding services",
    )
    external_service_call_rate = fields.Float(
        string="Negotiated External Service Call Rate",
        digits=(12, 2),
        tracking=True,
        help="Customer-specific service call fee for external shredding",
    )

    managed_permanent_removal_rate = fields.Float(
        string="Negotiated Managed Permanent Removal Rate",
        digits=(12, 2),
        tracking=True,
        help="Customer-specific rate for permanent removal of managed records",
    )
    managed_retrieval_rate = fields.Float(
        string="Negotiated Managed Retrieval Rate",
        digits=(12, 2),
        tracking=True,
        help="Customer-specific rate for retrieving managed documents",
    )
    managed_service_call_rate = fields.Float(
        string="Negotiated Managed Service Call Rate",
        digits=(12, 2),
        tracking=True,
        help="Customer-specific service call fee for managed services",
    )
    managed_shredding_rate = fields.Float(
        string="Negotiated Managed Shredding Rate",
        digits=(12, 2),
        tracking=True,
        help="Customer-specific rate for shredding managed documents",
    )

    pickup_rate = fields.Float(
        string="Negotiated Pickup Rate",
        digits=(12, 2),
        tracking=True,
        help="Customer-specific rate for document pickup services",
    )
    storage_rate_monthly = fields.Float(
        string="Negotiated Monthly Storage Rate",
        digits=(12, 2),
        tracking=True,
        help="Customer-specific monthly rate for document storage",
    )

    # Discount Management
    global_discount_percent = fields.Float(
        string="Global Discount %",
        digits=(5, 2),
        tracking=True,
        help="Overall discount percentage applied to all services",
    )
    volume_discount_threshold = fields.Integer(
        string="Volume Discount Threshold",
        tracking=True,
        help="Minimum volume required for volume discounts",
    )
    volume_discount_percent = fields.Float(
        string="Volume Discount %",
        digits=(5, 2),
        tracking=True,
        help="Discount percentage for volume orders",
    )

    # Override Controls (which rates are customer-specific)
    override_external_rates = fields.Boolean(
        string="Override External Rates", default=False
    )
    override_managed_rates = fields.Boolean(
        string="Override Managed Rates", default=False
    )
    override_pickup_rates = fields.Boolean(
        string="Override Pickup Rates", default=False
    )
    override_storage_rates = fields.Boolean(
        string="Override Storage Rates", default=False
    )

    # Documentation
    description = fields.Text(string="Description")
    negotiation_notes = fields.Text(string="Negotiation Notes")
    approval_notes = fields.Text(string="Approval Notes")
    terms_conditions = fields.Text(string="Special Terms & Conditions")

    # Computed fields
    # The display_name field depends on partner_id, name, and effective_date.
    # If any of these fields change, the computation is triggered.
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    is_expired = fields.Boolean(
        string="Is Expired", compute="_compute_is_expired", store=True
    )
    days_until_expiry = fields.Integer(
        string="Days Until Expiry", compute="_compute_days_until_expiry", store=True
    )
    total_discount_percent = fields.Float(
        string="Total Discount %", compute="_compute_total_discount", store=True
    )

    rate_type = fields.Selection(
        [
            ("storage", "Storage Rate"),
            ("retrieval", "Retrieval Rate"),
            ("delivery", "Delivery Rate"),
            ("destruction", "Destruction Rate"),
            ("container_access", "Container Access Rate"),  # NEW
            ("not_found_search", "Not Found Search Rate"),  # NEW
            ("scanning", "Scanning Rate"),
            ("indexing", "Indexing Rate"),
            ("setup", "Setup Fee"),
            ("discount", "Volume Discount"),
            ("other", "Other Rate"),
        ],
        string="Rate Type",
        required=True,
    )

    @api.depends("partner_id", "name", "effective_date")
    def _compute_display_name(self):
        """
        Compute display_name based on partner_id, name, and effective_date.
        This ensures that any change to these fields triggers a recomputation.
        """
        for record in self:
            if record.partner_id and record.name:
                record.display_name = f"{record.partner_id.name} - {record.name}"
            elif record.partner_id:
                record.display_name = f"{record.partner_id.name} - Negotiated Rates"
            else:
                record.display_name = record.name or "New Negotiated Rates"

    @api.depends("expiry_date")
    def _compute_is_expired(self):
        """Check if negotiated rates have expired"""
        today = fields.Date.today()
        for record in self:
            record.is_expired = record.expiry_date and record.expiry_date < today

    @api.depends("expiry_date")
    def _compute_days_until_expiry(self):
        """Calculate days until expiry"""
        today = fields.Date.today()
        for record in self:
            if record.expiry_date:
                expiry_date_obj = fields.Date.from_string(record.expiry_date)
                today_obj = fields.Date.from_string(today)
                delta = expiry_date_obj - today_obj
                record.days_until_expiry = delta.days
            else:
                record.days_until_expiry = 0

    @api.depends("global_discount_percent", "volume_discount_percent")
    def _compute_total_discount(self):
        """Calculate total potential discount"""
        for record in self:
            record.total_discount_percent = (
                record.global_discount_percent + record.volume_discount_percent
            )

    @api.constrains("effective_date", "expiry_date")
    def _check_date_logic(self):
        """Ensure expiry date is after effective date"""
        for record in self:
            if (
                record.expiry_date
                and record.effective_date
                and record.expiry_date <= record.effective_date
            ):
                raise ValidationError(_("Expiry date must be after effective date"))

    @api.constrains("partner_id", "effective_date")
    def _check_unique_active_rates(self):
        """Ensure only one active rate set per customer at any time"""
        for record in self:
            if record.state == "active":
                existing = self.search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("state", "=", "active"),
                        ("id", "!=", record.id),
                    ]
                )
                if existing:
                    raise ValidationError(
                        _(
                            "Customer %s already has active negotiated rates. "
                            "Please expire existing rates before activating new ones."
                        )
                        % record.partner_id.name
                    )

    # Action methods
    def action_submit_for_negotiation(self):
        """Submit rates for negotiation"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Can only submit draft rates for negotiation"))
        self.write({"state": "negotiating"})

    def action_approve_rates(self):
        """Approve negotiated rates"""
        self.ensure_one()
        if self.state != "negotiating":
            raise UserError(_("Can only approve rates under negotiation"))
        self.write({"state": "approved", "approval_date": fields.Date.today()})

    def action_activate_rates(self):
        """Activate approved rates"""
        self.ensure_one()
        if self.state != "approved":
            raise UserError(_("Can only activate approved rates"))

        # Deactivate any existing active rates for this customer
        existing_active = self.search(
            [("partner_id", "=", self.partner_id.id), ("state", "=", "active")]
        )
        existing_active.write({"state": "expired"})

        self.write({"state": "active"})

    def action_expire_rates(self):
        """Mark rates as expired"""
        self.ensure_one()
        self.write({"state": "expired", "expiry_date": fields.Date.today()})

    def action_cancel_rates(self):
        """Cancel negotiated rates"""
        self.ensure_one()
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        """Reset to draft state"""
        self.ensure_one()
        self.write({"state": "draft", "approval_date": False})

    def action_duplicate_rates(self):
        """Create new version of negotiated rates"""
        self.ensure_one()
        return self.copy(
            {
                "name": f"{self.name} (Copy)",
                "state": "draft",
                "effective_date": fields.Date.today(),
                "approval_date": False,
            }
        )

    @api.model
    def get_customer_rates(self, partner_id, service_date=None):
        """Get active negotiated rates for customer"""
        if not service_date:
            service_date = fields.Date.today()

        return self.search(
            [
                ("partner_id", "=", partner_id),
                ("state", "=", "active"),
                ("effective_date", "<=", service_date),
                "|",
                ("expiry_date", "=", False),
                ("expiry_date", ">", service_date),
            ],
            limit=1,
        )

    def get_effective_rate(self, rate_type, fallback_base_rate=None):
        """Get effective rate with fallback to base rates"""
        self.ensure_one()

        # Check if this rate type is overridden
        override_field_map = {
            "external_per_bin_rate": "override_external_rates",
            "external_service_call_rate": "override_external_rates",
            "managed_permanent_removal_rate": "override_managed_rates",
            "managed_retrieval_rate": "override_managed_rates",
            "managed_service_call_rate": "override_managed_rates",
            "managed_shredding_rate": "override_managed_rates",
            "pickup_rate": "override_pickup_rates",
            "storage_rate_monthly": "override_storage_rates",
        }

        override_field = override_field_map.get(rate_type)
        if override_field and getattr(self, override_field, False):
            negotiated_rate = getattr(self, rate_type, 0.0)
            if negotiated_rate > 0:
                # Apply global discount
                if self.global_discount_percent > 0:
                    if self.global_discount_percent >= 100:
                        raise ValidationError(
                            _(
                                "Global discount percent cannot be 100 or more, as it would result in zero or negative rates."
                            )
                        )
                    negotiated_rate *= 1 - self.global_discount_percent / 100
                return negotiated_rate

        # Fallback to base rate
        base_rate = fallback_base_rate or self.base_rate_id
        if (
            base_rate
            and hasattr(base_rate, "get_rate")
            and callable(getattr(base_rate, "get_rate", None))
        ):
            return base_rate.get_rate(rate_type)

        return 0.0
