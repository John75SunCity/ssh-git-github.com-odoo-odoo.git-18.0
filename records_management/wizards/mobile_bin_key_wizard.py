from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MobileBinKeyWizard(models.TransientModel):
    _name = "mobile.bin.key.wizard"
    _description = "Mobile Bin Key Management Wizard"

    # Core identification fields
    name = fields.Char(
        string="Wizard Reference", default="New Mobile Key Action"
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, required=True
    )

    # Action selection
    action_type = fields.Selection(
        [
            ("issue_new", "🆕 Issue New Key"),
            ("update_existing", "📝 Update Existing Assignment"),
            ("create_unlock_service", "🔓 Create Unlock Service"),
            ("quick_lookup", "🔍 Quick Key Holders Lookup"),
        ],
        string="Action Type",
        required=True,
    )

    # Customer and contact fields
    customer_company_id = fields.Many2one(
        "res.partner",
        string="Customer Company",
        domain=[("is_company", "=", True), ("customer_rank", ">", 0)],
    )
    contact_id = fields.Many2one(
        "res.partner",
        string="Contact",
        domain="[('parent_id', '=', customer_company_id), ('is_company', '=', False)]",
    )

    # New contact creation fields
    create_new_contact = fields.Boolean(
        string="Create New Contact", default=False
    )
    contact_name = fields.Char(string="Contact Name")
    contact_email = fields.Char(string="Email")
    contact_phone = fields.Char(string="Phone")
    contact_mobile = fields.Char(string="Mobile")
    contact_title = fields.Char(string="Job Title")

    # Key assignment fields
    issue_location = fields.Char(string="Issue Location")
    bin_locations = fields.Text(string="Bin Locations")
    emergency_contact = fields.Boolean(
        string="Emergency Contact Access", default=False
    )
    key_notes = fields.Text(string="Key Notes")

    # Unlock service fields
    unlock_reason = fields.Selection(
        [
            ("lost_key", "Lost Key"),
            ("locked_out", "Locked Out"),
            ("emergency_access", "Emergency Access"),
            ("maintenance", "Maintenance Required"),
            ("other", "Other Reason"),
        ],
        string="Unlock Reason",
    )
    unlock_reason_description = fields.Text(string="Reason Description")
    unlock_bin_location = fields.Char(string="Bin Location")
    items_retrieved = fields.Text(string="Items Retrieved")
    unlock_charge = fields.Monetary(
        string="Unlock Charge", currency_field="currency_id"
    )
    billable = fields.Boolean(string="Billable Service", default=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )

    # Service documentation
    photo_ids = fields.Many2many(
        "ir.attachment",
        string="Service Photos",
        help="Photos documenting the service",
    )
    service_notes = fields.Text(string="Service Notes")

    # Results and visibility controls
    key_lookup_results = fields.Html(
        string="Key Lookup Results", readonly=True
    )
    show_contact_creation = fields.Boolean(
        compute="_compute_visibility_controls"
    )
    show_key_assignment = fields.Boolean(
        compute="_compute_visibility_controls"
    )
    show_unlock_service = fields.Boolean(
        compute="_compute_visibility_controls"
    )
    show_lookup_results = fields.Boolean(
        compute="_compute_visibility_controls"
    )

    @api.depends("action_type", "customer_company_id", "create_new_contact")
    def _compute_visibility_controls(self):
        """Control form section visibility based on action type"""
        for record in self:
            record.show_contact_creation = (
                record.action_type == "issue_new"
                and record.customer_company_id
            )
            record.show_key_assignment = (
                record.action_type in ["issue_new", "update_existing"]
                and record.customer_company_id
            )
            record.show_unlock_service = (
                record.action_type == "create_unlock_service"
                and record.customer_company_id
            )
            record.show_lookup_results = (
                record.action_type == "quick_lookup"
                and record.customer_company_id
                and record.key_lookup_results
            )

    @api.onchange("customer_company_id")
    def _onchange_customer_company_id(self):
        """Update contact domain when customer company changes"""
        if self.customer_company_id:
            # Clear contact if it doesn't belong to the selected company
            if (
                self.contact_id
                and self.contact_id.parent_id != self.customer_company_id
            ):
                self.contact_id = False

            # If quick lookup, automatically perform lookup
            if self.action_type == "quick_lookup":
                self._perform_key_lookup()
        else:
            self.contact_id = False
            self.key_lookup_results = False

    @api.onchange('action_type')
    def _onchange_action_type(self):
        """Onchange handler (standard pattern _onchange_<field>).
        NOTE: This is NOT a user-triggered action; do not rename to action_*.
        """
        for wizard in self:
            wizard._apply_action_type_side_effects_internal()

    def action_apply_action_type(self):
        """Explicit action version of the onchange to satisfy UI button usage."""
        self.ensure_one()
        self._apply_action_type_side_effects_internal()
        return True

    def action_apply_action_type_side_effects_internal(self):
        """Apply side effects based on action type"""
        self.ensure_one()
        for wizard in self:
            if wizard.action_type != 'quick_lookup':
                wizard.key_lookup_results = False
            if wizard.action_type != 'issue_new':
                wizard.create_new_contact = False
                wizard.contact_name = False
                wizard.contact_email = False
                wizard.contact_phone = False
                wizard.contact_mobile = False
                wizard.contact_title = False

    def _perform_key_lookup(self):
        """Perform key lookup for the selected customer"""
        if not self.customer_company_id:
            return

        # Get existing bin keys for this customer
        existing_keys = self.env["bin.key"].search(
            [
                ("partner_id", "child_of", self.customer_company_id.id),
                ("active", "=", True),
            ]
        )

        if not existing_keys:
            # Fixed translation style: interpolation after _()
            self.key_lookup_results = _("<p class='text-muted'>No active keys found for %s</p>") % self.customer_company_id.name
            return

        # Build HTML results
        html_parts = [
            f"<h5>🔑 Active Keys for {self.customer_company_id.name}</h5>"
        ]
        html_parts.append("<table class='table table-sm'>")
        html_parts.append(
            "<thead><tr><th>Contact</th><th>Key ID</th><th>Status</th><th>Issue Date</th></tr></thead>"
        )
        html_parts.append("<tbody>")

        for key in existing_keys:
            status_icon = (
                "🟢"
                if key.state == "active"
                else "🟡" if key.state == "issued" else "🔴"
            )
            html_parts.append(
                f"""
                <tr>
                    <td>{key.partner_id.name or 'Unknown'}</td>
                    <td><strong>{key.name}</strong></td>
                    <td>{status_icon} {key.state.title()}</td>
                    <td>{key.issue_date.strftime('%m/%d/%Y') if key.issue_date else 'N/A'}</td>
                </tr>
            """
            )

        html_parts.append("</tbody></table>")
        self.key_lookup_results = "".join(html_parts)

    def action_execute(self):
        """Execute the selected action"""
        self.ensure_one()

        if self.action_type == "quick_lookup":
            self._perform_key_lookup()
            return {"type": "ir.actions.do_nothing"}

        # Validate required fields
        if not self.customer_company_id:
            raise ValidationError(_("Please select a customer company"))

        if self.action_type == "issue_new":
            return self.action_execute_issue_new()
        elif self.action_type == "update_existing":
            return self.action_execute_update_existing()
        elif self.action_type == "create_unlock_service":
            return self.action_execute_unlock_service()

        return {"type": "ir.actions.act_window_close"}

    def action_execute_issue_new(self):
        """Execute new key issuance"""
        self.ensure_one()
        # Create or get contact
        if self.create_new_contact:
            if not self.contact_name:
                raise ValidationError(
                    _("Contact name is required for new contact creation")
                )

            contact_vals = {
                "name": self.contact_name,
                "parent_id": self.customer_company_id.id,
                "is_company": False,
                "email": self.contact_email,
                "phone": self.contact_phone,
                "mobile": self.contact_mobile,
                "function": self.contact_title,
            }
            contact = self.env["res.partner"].create(contact_vals)
        else:
            if not self.contact_id:
                raise ValidationError(
                    _("Please select a contact or create a new one")
                )
            contact = self.contact_id

        # Create new bin key
        key_vals = {
            "partner_id": contact.id,
            "issue_location": self.issue_location,
            "bin_locations": self.bin_locations,
            "emergency_contact": self.emergency_contact,
            "notes": self.key_notes,
            "state": "issued",
            "issue_date": fields.Datetime.now(),
        }

        new_key = self.env["bin.key"].create(key_vals)

        return {
            "type": "ir.actions.act_window",
            "name": _("New Bin Key"),
            "res_model": "bin.key",
            "res_id": new_key.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_execute_update_existing(self):
        """Execute update of existing key data"""
        self.ensure_one()
        if not self.contact_id:
            raise ValidationError(_("Please select a contact to update"))

        # Get existing active key for contact
        existing_key = self.env["bin.key"].search(
            [
                ("partner_id", "=", self.contact_id.id),
                ("active", "=", True),
                ("state", "in", ["issued", "active"]),
            ],
            limit=1,
        )

        if not existing_key:
            raise ValidationError(
                _("No active key found for the selected contact")
            )

        # Update the key
        update_vals = {}
        if self.issue_location:
            update_vals["issue_location"] = self.issue_location
        if self.bin_locations:
            update_vals["bin_locations"] = self.bin_locations
        if self.key_notes:
            update_vals["notes"] = self.key_notes

        update_vals["emergency_contact"] = self.emergency_contact

        if update_vals:
            existing_key.write(update_vals)

        return {
            "type": "ir.actions.act_window",
            "name": _("Updated Bin Key"),
            "res_model": "bin.key",
            "res_id": existing_key.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_execute_unlock_service(self):
        """Execute unlock service creation"""
        self.ensure_one()
        if not self.contact_id:
            raise ValidationError(
                _("Please select a contact for the unlock service")
            )

        if not self.unlock_reason:
            raise ValidationError(_("Please specify the unlock reason"))

        if not self.unlock_bin_location:
            raise ValidationError(_("Please specify the bin location"))

        # Create unlock service record
        service_vals = {
            "name": _("Unlock Service - %s") % self.contact_id.name,  # fixed translation style
            "partner_id": self.contact_id.id,
            "unlock_reason": self.unlock_reason,
            "unlock_reason_description": self.unlock_reason_description,
            "unlock_bin_location": self.unlock_bin_location,
            "items_retrieved": self.items_retrieved,
            "unlock_charge": self.unlock_charge,
            "billable": self.billable,
            "service_notes": self.service_notes,
            "photo_ids": [(6, 0, self.photo_ids.ids)],
            "service_date": fields.Datetime.now(),
            "technician_id": self.user_id.id,
        }

        # Create the unlock service record using existing model
        unlock_service = self.env["bin.key.unlock.service"].create(
            service_vals
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Unlock Service"),
            "res_model": "bin.key.unlock.service",
            "res_id": unlock_service.id,
            "view_mode": "form",
            "target": "current",
        }
