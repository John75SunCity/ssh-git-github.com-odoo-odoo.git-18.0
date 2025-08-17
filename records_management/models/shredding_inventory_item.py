from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ShreddingInventoryItem(models.Model):
    _name = 'shredding.inventory.item'
    _description = 'Shredding Inventory Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    sequence = fields.Integer()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    item_type = fields.Selection()
    item_classification = fields.Selection()
    container_id = fields.Many2one()
    document_id = fields.Many2one()
    work_order_id = fields.Many2one()
    customer_id = fields.Many2one()
    partner_id = fields.Many2one()
    current_location_id = fields.Many2one()
    original_location_id = fields.Many2one()
    state = fields.Selection()
    status = fields.Selection()
    quantity = fields.Float()
    weight = fields.Float()
    currency_id = fields.Many2one()
    total_cost = fields.Monetary()
    total_amount = fields.Monetary()
    retrieval_cost = fields.Monetary()
    storage_cost = fields.Monetary()
    transport_cost = fields.Monetary()
    shredding_cost = fields.Monetary()
    permanent_removal_cost = fields.Monetary()
    date = fields.Date()
    created_date = fields.Date()
    updated_date = fields.Date()
    retrieved_date = fields.Date()
    destruction_date = fields.Date()
    approval_date = fields.Date()
    customer_approved = fields.Boolean()
    supervisor_approved = fields.Boolean()
    retrieved_by_id = fields.Many2one()
    destroyed_by_id = fields.Many2one()
    audit_trail_enabled = fields.Boolean()
    last_audit_date = fields.Date()
    chain_of_custody_number = fields.Char()
    destruction_certificate_number = fields.Char()
    destruction_certificate_issued = fields.Boolean()
    destruction_certificate_date = fields.Date()
    destruction_certificate_file = fields.Binary()
    contamination_check_completed = fields.Boolean()
    destruction_method_verified = fields.Boolean()
    quality_verification_completed = fields.Boolean()
    security_level_verified = fields.Boolean()
    witness_verification_required = fields.Boolean()
    batch_processing_required = fields.Boolean()
    certificate_generation_required = fields.Boolean()
    retention_policy = fields.Selection()
    days_since_destruction = fields.Integer()
    is_overdue_for_destruction = fields.Boolean()
    description = fields.Text()
    retrieval_notes = fields.Text()
    destruction_notes = fields.Text()
    compliance_notes = fields.Text()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    today = fields.Date()
    delta = fields.Date()
    today = fields.Date()
    created_date_dt = fields.Date()
    today_dt = fields.Date()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name with context information"""
            for record in self:
                if record.container_id:
                    record.display_name = _("%s (Container: %s)", record.name, record.container_id.name)
                elif record.document_id:
                    record.display_name = _("%s (Document: %s)", record.name, record.document_id.name)
                else:
                    record.display_name = record.name or _("New Item")


    def _compute_days_since_destruction(self):
            """Calculate days since destruction"""

    def _compute_is_overdue_for_destruction(self):
            """Check if item is overdue for destruction""":

    def write(self, vals):
            """Override write to update timestamp"""
            if vals:

    def action_approve_item(self):
            """Approve item for destruction""":
            self.ensure_one()
            self.write({)}
                "status": "pending_pickup",
                "approval_date": fields.Date.today(),
                "customer_approved": True,


            self.message_post(body=_("Item approved for destruction")):
            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Item Approved"),
                    "message": _("Item has been approved for destruction and is pending pickup."),:
                    "type": "success",
                    "sticky": False,




    def action_mark_retrieved(self):
            """Mark item as retrieved"""
            self.ensure_one()
            self.write({)}
                "status": "retrieved",
                "retrieved_date": fields.Date.today(),
                "state": "in_progress",


            self.message_post(body=_("Item marked as retrieved"))

            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Item Retrieved"),
                    "message": _("Item has been marked as retrieved."),
                    "type": "success",
                    "sticky": False,




    def action_mark_destroyed(self):
            """Mark item as destroyed"""
            self.ensure_one()
            self.write({)}
                "status": "destroyed",
                "destruction_date": fields.Date.today(),
                "state": "completed",


            self.message_post(body=_("Item marked as destroyed"))

            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Item Destroyed"),
                    "message": _("Item has been marked as destroyed."),
                    "type": "warning",
                    "sticky": False,




    def action_mark_not_found(self):
            """Mark item as not found"""
            self.ensure_one()
            self.write({"status": "not_found"})

            self.message_post(body=_("Item marked as not found"))

            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Item Not Found"),
                    "message": _("Item has been marked as not found."),
                    "type": "warning",
                    "sticky": False,




    def action_issue_certificate(self):
            """Issue destruction certificate"""
            self.ensure_one()
            if not self.destruction_date:
                raise UserError(_("Cannot issue certificate before destruction."))

            if not self.destruction_certificate_number:
                # Generate certificate number
                sequence = self.env["ir.sequence"].next_by_code("destruction.certificate")
                if not sequence:
                    _logger.warning("Sequence 'destruction.certificate' not found. Using fallback certificate number generation.")

    def action_audit_item(self):
            """Audit this shredding inventory item"""
            self.ensure_one()
            self.write({"last_audit_date": fields.Date.today()})

            self.message_post(body=_("Audit completed for this item")):
            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Audit Complete"),
                    "message": _("Audit completed for this item."),:
                    "type": "info",
                    "sticky": False,




    def action_track_chain_of_custody(self):
            """Track chain of custody"""
            self.ensure_one()

            return {}
                "type": "ir.actions.act_window",
                "name": _("Chain of Custody"),
                "res_model": "custody.log",
                "view_mode": "tree,form",
                "target": "current",
                "domain": [("item_id", "=", self.id)],
                "context": {"default_item_id": self.id},



    def action_generate_certificate(self):
            """Generate destruction certificate"""
            self.ensure_one()

            return {}
                "type": "ir.actions.report",
                "report_name": "records_management.destruction_certificate",
                "report_type": "qweb-pdf",
                "data": {"ids": self.ids},



    def action_audit_compliance(self):
            """Audit compliance status"""
            self.ensure_one()

            self.write({"last_audit_date": fields.Date.today()})
            self.message_post(body=_("Compliance audit completed"))

            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Compliance Audited"),
                    "message": _("Compliance status has been audited."),
                    "type": "success",
                    "sticky": False,




    def action_supervisor_approve(self):
            """Supervisor approval action"""
            self.ensure_one()

            self.write({)}
                "supervisor_approved": True,
                "approval_date": fields.Date.today(),


            self.message_post(body=_("Item approved by supervisor"))

            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Supervisor Approval"),
                    "message": _("Item has been approved by supervisor."),
                    "type": "success",
                    "sticky": False,




    def action_verify_destruction_method(self):
            """Verify destruction method"""
            self.ensure_one()

            self.write({"destruction_method_verified": True})
            self.message_post(body=_("Destruction method verified"))

            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Method Verified"),
                    "message": _("Destruction method has been verified."),
                    "type": "success",
                    "sticky": False,



        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_positive_values(self):
            """Validate quantity and weight are non-negative"""
            for record in self:
                if record.quantity < 0:
                    raise ValidationError(_("Quantity must be non-negative."))
                if record.weight < 0:
                    raise ValidationError(_("Weight must be non-negative."))


    def _check_destruction_date(self):
            """Validate destruction date is not before creation date"""
            for record in self:
                if (record.destruction_date and record.created_date and:)
                    record.destruction_date < record.created_date
                    raise ValidationError(_("Destruction date cannot be before creation date."))


    def _check_retrieved_date(self):
            """Validate retrieved date is not before creation date"""
            for record in self:
                if (record.retrieved_date and record.created_date and:)
                    record.retrieved_date < record.created_date
                    raise ValidationError(_("Retrieved date cannot be before creation date."))

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def get_destruction_summary(self):
            """Get destruction summary for reporting""":
            self.ensure_one()

            return {}
                "item_name": self.name,
                "item_type": self.item_type,
                "customer": self.customer_id.name if self.customer_id else "",:
                "destruction_date": self.destruction_date,
                "certificate_number": self.destruction_certificate_number,
                "total_cost": self.total_cost,
                "status": self.status,
                "state": self.state,
                "certificate_issued": self.destruction_certificate_issued,
                "weight": self.weight,
                "quantity": self.quantity,



    def get_pending_destruction_items(self):
            """Get items pending destruction"""
            return self.search([)]
                ("status", "in", ["pending_pickup", "retrieved"]),
                ("destruction_date", "=", False),



    def get_overdue_items(self):
            """Get overdue items for destruction""":
            return self.search([("is_overdue_for_destruction", "=", True)])


    def create_chain_of_custody_entry(self, event_type, notes=""):
            """Create chain of custody entry"""
            self.ensure_one()

            if "custody.log" in self.env:
                self.env["custody.log"].create({)}
                    "item_id": self.id,
                    "event_type": event_type,
                    "event_date": fields.Datetime.now(),
                    "user_id": self.env.user.id,
                    "notes": notes))))))))))))))))))))))))))))))))))))))))))))))))))))

