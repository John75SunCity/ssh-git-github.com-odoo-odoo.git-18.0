from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ContainerContent(models.Model):
    _name = 'container.content'
    _description = 'Container Contents'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    sequence = fields.Integer()
    active = fields.Boolean()
    description = fields.Text()
    notes = fields.Text()
    state = fields.Selection()
    container_id = fields.Many2one()
    document_type_id = fields.Many2one()
    partner_id = fields.Many2one()
    location_id = fields.Many2one()
    content_type = fields.Selection()
    document_count = fields.Integer()
    estimated_pages = fields.Integer()
    weight_kg = fields.Float()
    date_created = fields.Datetime()
    date_stored = fields.Datetime()
    date_retrieved = fields.Datetime()
    retention_until = fields.Date()
    confidentiality_level = fields.Selection()
    destruction_required = fields.Boolean()
    destruction_method = fields.Selection()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    display_name = fields.Char()
    is_overdue = fields.Boolean()
    container_barcode = fields.Char()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name for content items.""":
            for record in self:
                if record.container_id:
                    record.display_name = _("%(container)s - %(content)s",
                        container=record.container_id.name,
                        content=record.name
                    )
                else:
                    record.display_name = record.name or _("New Content")


    def _compute_is_overdue(self):
            """Check if content is past retention date.""":

    def _check_positive_values(self):
            """Ensure document counts are positive."""
            for record in self:
                if record.document_count < 0:
                    raise ValidationError(_("Document count cannot be negative"))
                if record.estimated_pages < 0:
                    raise ValidationError(_("Estimated pages cannot be negative"))


    def _check_weight_reasonable(self):
            """Validate weight is reasonable."""
            for record in self:
                if record.weight_kg < 0:
                    raise ValidationError(_("Weight cannot be negative"))
                if record.weight_kg > 1000:  # 1 ton limit
                    raise ValidationError(_("Weight exceeds reasonable limit (1000kg)"))

        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to set default values."""
            for vals in vals_list:
                if not vals.get("name"):
                    vals["name"] = _("New Content Item")
                if vals.get("state") == "stored" and not vals.get("date_stored"):

    def write(self, vals):
            """Override write to track state changes."""
            if "state" in vals:
                if vals["state"] == "stored" and not vals.get("date_stored"):

    def action_confirm(self):
            """Confirm content details."""
            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Only draft content can be confirmed"))
            self.write({"state": "confirmed"})
            self.message_post(body=_("Content details confirmed"))


    def action_store(self):
            """Mark content as stored."""
            self.ensure_one()
            if self.state not in ["confirmed", "draft"]:
                raise UserError(_("Cannot store content in current state"))
            if not self.container_id:
                raise UserError(_("Container must be assigned before storing"))
            self.write({
                "state": "stored",
                "date_stored": fields.Datetime.now()
            })
            self.message_post(body=_("Content stored in container %s", self.container_id.name))


    def action_retrieve(self):
            """Mark content as retrieved."""
            self.ensure_one()
            if self.state != "stored":
                raise UserError(_("Only stored content can be retrieved"))
            self.write({
                "state": "retrieved",
                "date_retrieved": fields.Datetime.now()
            })
            self.message_post(body=_("Content retrieved from storage"))


    def action_mark_destroyed(self):
            """Mark content as destroyed."""
            self.ensure_one()
            if not self.destruction_required:
                raise UserError(_("Content is not marked for destruction")):
            if self.state == "destroyed":
                raise UserError(_("Content is already destroyed"))
            self.write({"state": "destroyed"})
            self.message_post(body=_("Content marked as destroyed"))


    def action_reset_to_draft(self):
            """Reset content to draft state."""
            self.ensure_one()
            if self.state == "destroyed":
                raise UserError(_("Cannot reset destroyed content"))
            self.write({"state": "draft"})
            self.message_post(body=_("Content reset to draft"))

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def get_retention_status(self):
            """Get retention status information."""
            self.ensure_one()
            if not self.retention_until:
                return {"status": "no_policy", "message": _("No retention policy set")}

            days_remaining = (self.retention_until - fields.Date.today()).days

            if days_remaining < 0:
                return {
                    "status": "overdue",
                    "message": _("Overdue by %d days", abs(days_remaining))
                }
            elif days_remaining <= 30:
                return {
                    "status": "warning",
                    "message": _("%d days until retention expires", days_remaining)
                }
            else:
                return {
                    "status": "ok",
                    "message": _("%d days remaining", days_remaining)
                }


    def get_overdue_content(self):
            """Get all overdue content items."""
            return self.search([
                ("retention_until", "<", fields.Date.today()),
                ("state", "not in", ["destroyed", "retrieved"])
            ])
