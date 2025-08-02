# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BaseRates(models.Model):
    _name = "base.rates"
    _description = "System Base Rates"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "effective_date desc, name"
    _rec_name = "name"

    # Core fields
    name = fields.Char(string="Rate Set Name", required=True, tracking=True)
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
            ("confirmed", "Active"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Standard message/activity fields
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages", auto_join=True
    )
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities", auto_join=True
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers", auto_join=True
    )

    # Date Management
    effective_date = fields.Date(string="Effective Date", required=True, tracking=True)
    expiry_date = fields.Date(string="Expiry Date", tracking=True)

    # Version Control
    version = fields.Char(string="Version", default="1.0", tracking=True)
    is_current = fields.Boolean(string="Current Rate Set", default=False, tracking=True)

    # External Service Rates
    external_per_bin_rate = fields.Float(
        string="External Per Bin Rate",
        digits=(12, 2),
        tracking=True,
        help="Rate charged per bin for external shredding services",
    )
    external_service_call_rate = fields.Float(
        string="External Service Call Rate",
        digits=(12, 2),
        tracking=True,
        help="Service call fee for external shredding services",
    )

    # Managed Service Rates
    managed_permanent_removal_rate = fields.Float(
        string="Managed Permanent Removal Rate",
        digits=(12, 2),
        tracking=True,
        help="Rate for permanent removal of managed records",
    )
    managed_retrieval_rate = fields.Float(
        string="Managed Retrieval Rate",
        digits=(12, 2),
        tracking=True,
        help="Rate for retrieving managed documents",
    )
    managed_service_call_rate = fields.Float(
        string="Managed Service Call Rate",
        digits=(12, 2),
        tracking=True,
        help="Service call fee for managed services",
    )
    managed_shredding_rate = fields.Float(
        string="Managed Shredding Rate",
        digits=(12, 2),
        tracking=True,
        help="Rate for shredding managed documents",
    )

    # Additional Service Rates
    pickup_rate = fields.Float(
        string="Pickup Rate",
        digits=(12, 2),
        tracking=True,
        help="Rate for document pickup services",
    )
    storage_rate_monthly = fields.Float(
        string="Monthly Storage Rate",
        digits=(12, 2),
        tracking=True,
        help="Monthly rate for document storage",
    )
    rush_service_multiplier = fields.Float(
        string="Rush Service Multiplier",
        default=1.5,
        tracking=True,
        help="Multiplier applied to rush services",
    )

    # Documentation
    description = fields.Text(string="Description")
    notes = fields.Text(string="Internal Notes")

    # Computed fields
    is_expired = fields.Boolean(
        string="Is Expired", compute="_compute_is_expired", store=True
    )
    days_until_expiry = fields.Integer(
        string="Days Until Expiry", compute="_compute_days_until_expiry"
    )

    @api.depends("expiry_date")
    def _compute_is_expired(self):
        """Check if rate set has expired"""
        today = fields.Date.today()
        for record in self:
            record.is_expired = record.expiry_date and record.expiry_date < today

    @api.depends("expiry_date")
    def _compute_days_until_expiry(self):
        """Calculate days until expiry"""
        today = fields.Date.today()
        for record in self:
            if record.expiry_date:
                delta = record.expiry_date - today
                record.days_until_expiry = delta.days
            else:
                record.days_until_expiry = 0

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

    @api.constrains("is_current")
    def _check_single_current(self):
        """Ensure only one current rate set per company"""
        for record in self:
            if record.is_current:
                existing = self.search(
                    [
                        ("is_current", "=", True),
                        ("company_id", "=", record.company_id.id),
                        ("id", "!=", record.id),
                    ]
                )
                if existing:
                    raise ValidationError(
                        _("Only one rate set can be marked as current per company")
                    )

    # Action methods
    def action_activate(self):
        """Activate rate set and make it current"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Can only activate draft rate sets"))

        # Deactivate other current rate sets
        current_rates = self.search(
            [("is_current", "=", True), ("company_id", "=", self.company_id.id)]
        )
        current_rates.write({"is_current": False})

        self.write({"state": "confirmed", "is_current": True})

    def action_expire(self):
        """Mark rate set as expired"""
        self.ensure_one()
        self.write(
            {
                "state": "expired",
                "is_current": False,
                "expiry_date": fields.Date.today(),
            }
        )

    def action_cancel(self):
        """Cancel rate set"""
        self.ensure_one()
        self.write({"state": "cancelled", "is_current": False})

    def action_reset_to_draft(self):
        """Reset to draft state"""
        self.ensure_one()
        self.write({"state": "draft", "is_current": False})

    def action_duplicate_rates(self):
        """Create new version of current rates"""
        self.ensure_one()
        new_version = float(self.version) + 0.1

        return self.copy(
            {
                "name": f"{self.name} v{new_version:.1f}",
                "version": f"{new_version:.1f}",
                "state": "draft",
                "is_current": False,
                "effective_date": fields.Date.today(),
            }
        )

    @api.model
    def get_current_rates(self, company_id=None):
        """Get current active rate set for company"""
        if not company_id:
            company_id = self.env.company.id

        return self.search(
            [
                ("is_current", "=", True),
                ("company_id", "=", company_id),
                ("state", "=", "confirmed"),
            ],
            limit=1,
        )

    def get_rate(self, rate_type):
        """Get specific rate value"""
        self.ensure_one()
        return getattr(self, rate_type, 0.0)
