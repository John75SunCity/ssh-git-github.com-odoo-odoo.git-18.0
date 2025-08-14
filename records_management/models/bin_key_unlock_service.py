from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BinKeyUnlockService(models.Model):
    _name = "bin.key.unlock.service"
    _description = "Bin Key Unlock Service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "service_date desc, name"
    _rec_name = "name"

    # Core identification fields
    name = fields.Char(
        string="Service Reference", required=True, tracking=True, index=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    active = fields.Boolean(string="Active", default=True)

    # Service details
    partner_id = fields.Many2one(
        "res.partner", string="Contact", required=True, tracking=True
    )
    customer_company_id = fields.Many2one(
        "res.partner",
        string="Customer Company",
        related="partner_id.parent_id",
        store=True,
    )

    # Service information
    service_date = fields.Datetime(
        string="Service Date", default=fields.Datetime.now, required=True
    )
    technician_id = fields.Many2one(
        "res.users",
        string="Technician",
        default=lambda self: self.env.user,
        required=True,
    )

    # Unlock details
    unlock_reason = fields.Selection(
        [
            ("lost_key", "Lost Key"),
            ("locked_out", "Locked Out"),
            ("emergency_access", "Emergency Access"),
            ("maintenance", "Maintenance Required"),
            ("other", "Other Reason"),
        ],
        string="Unlock Reason",
        required=True,
        tracking=True,
    )

    unlock_reason_description = fields.Text(string="Reason Description")
    unlock_bin_location = fields.Char(string="Bin Location", required=True)
    items_retrieved = fields.Text(string="Items Retrieved")

    # Financial fields
    unlock_charge = fields.Monetary(
        string="Unlock Charge", currency_field="currency_id"
    )
    billable = fields.Boolean(string="Billable Service", default=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )

    # Documentation
    photo_ids = fields.Many2many(
        "ir.attachment",
        "unlock_service_photo_rel",
        "service_id",
        "attachment_id",
        string="Service Photos",
        help="Photos documenting the unlock service",
    )
    service_notes = fields.Text(string="Service Notes")

    # State management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("completed", "Completed"),
            ("invoiced", "Invoiced"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Related bin key
    bin_key_id = fields.Many2one(
        "bin.key",
        string="Related Bin Key",
        compute="_compute_bin_key_id",
        store=True,
    )

    # Mail thread framework fields
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    @api.depends("partner_id")
    def _compute_bin_key_id(self):
        """Find the active bin key for the contact"""
        for record in self:
            if record.partner_id:
                bin_key = self.env["bin.key"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("active", "=", True),
                        ("state", "in", ["issued", "active"]),
                    ],
                    limit=1,
                )
                record.bin_key_id = bin_key.id if bin_key else False
            else:
                record.bin_key_id = False

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number for new services"""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "bin.key.unlock.service"
                    )
                    or "ULS-NEW"
                )
        return super().create(vals_list)

    def action_complete_service(self):
        """Mark service as completed"""
        for record in self:
            if record.state != "draft":
                raise ValidationError(
                    _("Only draft services can be completed")
                )

            record.write(
                {"state": "completed", "service_date": fields.Datetime.now()}
            )

            # Create audit log entry
            record._create_audit_log("service_completed")

    def action_create_invoice(self):
        """Create invoice for billable unlock service"""
        self.ensure_one()

        if not self.billable:
            raise ValidationError(_("This service is not marked as billable"))

        if self.state == "invoiced":
            raise ValidationError(_("This service has already been invoiced"))

        if not self.unlock_charge:
            raise ValidationError(
                _("Please set the unlock charge before creating invoice")
            )

        # Create invoice line data
        invoice_vals = {
            "partner_id": self.customer_company_id.id or self.partner_id.id,
            "move_type": "out_invoice",
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": _(
                            "Unlock Service - %s", self.unlock_bin_location
                        ),
                        "quantity": 1,
                        "price_unit": self.unlock_charge,
                    },
                )
            ],
        }

        invoice = self.env["account.move"].create(invoice_vals)

        self.write({"state": "invoiced"})

        return {
            "type": "ir.actions.act_window",
            "name": _("Invoice"),
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }

    def _create_audit_log(self, action):
        """Create audit log entry"""
        if not hasattr(self.env, "naid.audit.log"):
            return  # Skip if audit log model doesn't exist

        self.env["naid.audit.log"].create(
            {
                "name": _(
                    "Unlock Service: %s", action.replace("_", " ").title()
                ),
                "action_type": action,
                "model_name": self._name,
                "record_id": self.id,
                "user_id": self.env.user.id,
                "partner_id": self.partner_id.id,
                "details": _(
                    "Unlock service %s for %s at %s",
                    action.replace("_", " "),
                    self.partner_id.name,
                    self.unlock_bin_location,
                ),
            }
        )
