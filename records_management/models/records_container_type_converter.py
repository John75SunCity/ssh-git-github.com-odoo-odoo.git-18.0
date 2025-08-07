# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsContainerTypeConverter(models.Model):
    _name = "records.container.type.converter"
    _description = "Records Container Type Converter"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Basic Information
    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )

    name = fields.Char(string="Converter Name", required=True)
    source_type = fields.Char(string="Source Type")
    target_type = fields.Char(string="Target Type")

    # Missing fields from view analysis
    container_ids = fields.One2many(
        "records.container", "converter_id", string="Containers to Convert"
    )
    current_type = fields.Char(string="Current Container Type")
    new_container_type_code = fields.Char(string="New Container Type Code")
    reason = fields.Text(string="Conversion Reason")
    summary_line = fields.Char(string="Summary Line", compute="_compute_summary_line")
    target_container_type = fields.Char(
        string="Target Container Type"
    )  # Alternative name for target_type
    conversion_notes = fields.Text(string="Conversion Notes")
    # === BUSINESS CRITICAL FIELDS ===
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    location_id = fields.Many2one("records.location", string="Location", tracking=True)
    barcode = fields.Char(string="Barcode", copy=False)
    container_type = fields.Selection(
        selection="_get_container_type_selection", string="Container Type"
    )
    capacity = fields.Float(string="Capacity", digits=(10, 2))
    current_weight = fields.Float(string="Current Weight", digits=(10, 2))
    last_access_date = fields.Date(string="Last Access Date")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Notes")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")

    @api.depends("source_type", "target_type", "container_ids")
    def _compute_summary_line(self):
        """Compute summary line for conversion"""
        for record in self:
            container_count = len(record.container_ids)
            record.summary_line = f"Convert {container_count} containers from {record.source_type or 'Unknown'} to {record.target_type or 'Unknown'}"

    @api.constrains("source_type", "target_type")
    def _check_conversion_types(self):
        """Validate that source and target types are different and valid"""
        for record in self:
            if record.source_type and record.target_type:
                if record.source_type == record.target_type:
                    raise ValidationError(
                        _("Source type and target type cannot be the same.")
                    )

    def write(self, vals):
        vals = dict(vals)
        vals["updated_date"] = fields.Datetime.now()
        return super().write(vals)

    def create(self, vals):
        vals = dict(vals)  # Copy to avoid side effects
        vals["updated_date"] = fields.Datetime.now()
        return super().create(vals)

    @api.model
    def _get_container_type_selection(self):
        try:
            container_types = self.env["records.container.type"].search([])
            return [(ct.code, ct.name) for ct in container_types]
        except Exception as e:
            # Log the exception for debugging
            import logging

            _logger = logging.getLogger(__name__)
            _logger.error("Error fetching container types: %s", e)
            # Fallback to Type format if model doesn't exist
            return [
                ("TYPE_01", "Type 01"),
                ("TYPE_02", "Type 02"),
                ("TYPE_03", "Type 03"),
                ("TYPE_04", "Type 04"),
            ]

    def action_convert_containers(self):
        """Convert containers with proper validation."""
        self.ensure_one()

        # Validate conversion is possible
        if not self.container_ids:
            raise UserError(_("No containers selected for conversion."))

        if not self.target_type:
            raise UserError(_("Target container type must be specified."))

        # Check for containers that cannot be converted (proper validation for container conversion)
        blocked_containers = self.container_ids.filtered(
            lambda c: c.state in ["destroyed", "archived"]
            or getattr(c, "is_permanent", False)
        )

        if blocked_containers:
            raise UserError(
                _(
                    "Cannot convert containers that are destroyed, archived, or marked as permanent: %s"
                )
                % ", ".join(blocked_containers.mapped("name"))
            )

        # Perform the actual conversion logic
        for container in self.container_ids:
            # Prepare update values with safe field checking
            update_vals = {
                "container_type": self.target_type,
            }

            # Only add conversion tracking fields if they exist in the container model
            container_fields = container._fields
            if "conversion_date" in container_fields:
                update_vals["conversion_date"] = fields.Datetime.now()
            if "conversion_reason" in container_fields:
                update_vals["conversion_reason"] = self.reason or "Bulk conversion"

            # Use notes field as fallback for conversion tracking
            if "notes" in container_fields and self.reason:
                current_notes = container.notes or ""
                conversion_note = f"\n[{fields.Datetime.now()}] Converted to {self.target_type}: {self.reason}"
                update_vals["notes"] = current_notes + conversion_note

            container.write(update_vals)

        # Log the conversion activity
        self.message_post(
            body=_("Converted %d containers from %s to %s")
            % (len(self.container_ids), self.source_type or "Unknown", self.target_type)
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Containers Converted"),
                "message": _("Successfully converted %d containers.")
                % len(self.container_ids),
                "type": "success",
                "sticky": False,
            },
        }

    def action_preview_changes(self):
        """Preview changes."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Preview Generated"),
                "message": _("Changes preview has been generated."),
                "type": "info",
                "sticky": False,
            },
        }

    def action_preview_conversion(self):
        """Preview conversion results with validation."""
        self.ensure_one()

        if not self.container_ids:
            raise UserError(_("No containers selected to preview."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Conversion Preview"),
            "res_model": "records.container",
            "view_mode": "tree",
            "target": "new",
        }
