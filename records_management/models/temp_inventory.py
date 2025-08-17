from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class TempInventory(models.Model):
    _name = 'temp.inventory'
    _description = 'Temporary Inventory Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, date_created desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    description = fields.Text()
    sequence = fields.Integer()
    active = fields.Boolean()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    partner_id = fields.Many2one()
    state = fields.Selection()
    priority = fields.Selection()
    location_id = fields.Many2one()
    storage_type = fields.Selection()
    capacity_limit = fields.Integer()
    current_count = fields.Integer()
    available_capacity = fields.Integer()
    utilization_percent = fields.Float()
    document_ids = fields.One2many()
    container_ids = fields.One2many()
    document_count = fields.Integer()
    container_count = fields.Integer()
    date_created = fields.Datetime()
    date_modified = fields.Datetime()
    date_activated = fields.Datetime()
    date_archived = fields.Datetime()
    retention_period = fields.Integer()
    expiry_date = fields.Date()
    approval_required = fields.Boolean()
    approved_by_id = fields.Many2one()
    approval_date = fields.Datetime()
    rejection_reason = fields.Text()
    inventory_type = fields.Selection()
    access_level = fields.Selection()
    temperature_controlled = fields.Boolean()
    humidity_controlled = fields.Boolean()
    movement_ids = fields.One2many()
    last_movement_date = fields.Datetime()
    movement_count = fields.Integer()
    compliance_required = fields.Boolean()
    audit_trail_ids = fields.One2many()
    chain_of_custody_required = fields.Boolean()
    naid_compliant = fields.Boolean()
    currency_id = fields.Many2one()
    storage_cost = fields.Monetary()
    handling_cost = fields.Monetary()
    total_cost = fields.Monetary()
    display_name = fields.Char()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    retrieval_item_ids = fields.One2many()
    rate_id = fields.Many2one()
    inventory_id = fields.Many2one('records.inventory.dashboard')
    document_type_id = fields.Many2one('records.document.type')
    container_type = fields.Selection(string='Container Type')
    movement_type = fields.Selection()
    Inventories = fields.Char(string='Inventories')
    Movements = fields.Char(string='Movements')
    action_activate = fields.Char(string='Action Activate')
    action_approve = fields.Char(string='Action Approve')
    action_archive = fields.Char(string='Action Archive')
    action_check_capacity_status = fields.Selection(string='Action Check Capacity Status')
    action_deactivate = fields.Char(string='Action Deactivate')
    action_view_containers = fields.Char(string='Action View Containers')
    action_view_documents = fields.Char(string='Action View Documents')
    action_view_movements = fields.Char(string='Action View Movements')
    active_inventories = fields.Char(string='Active Inventories')
    button_box = fields.Char(string='Button Box')
    date = fields.Char(string='Date')
    full_inventories = fields.Char(string='Full Inventories')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    nearly_full = fields.Char(string='Nearly Full')
    quarantine = fields.Char(string='Quarantine')
    res_model = fields.Char(string='Res Model')
    staging = fields.Char(string='Staging')
    temporary = fields.Char(string='Temporary')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name"""
            for record in self:
                if record.name:
                    record.display_name = _("%s (%s items)", record.name, record.current_count)
                else:
                    record.display_name = _("New Temporary Inventory")


    def _compute_current_count(self):
            """Compute current count of items"""
            for record in self:
                record.current_count = len(record.document_ids) + len(record.container_ids)


    def _compute_available_capacity(self):
            """Compute available capacity"""
            for record in self:
                record.available_capacity = max()
                    0, record.capacity_limit - record.current_count



    def _compute_utilization_percent(self):
            """Compute utilization percentage"""
            for record in self:
                if record.capacity_limit > 0:
                    record.utilization_percent = ()
                        record.current_count / record.capacity_limit

                else:
                    record.utilization_percent = 0.0


    def _compute_document_count(self):
            """Compute document count"""
            for record in self:
                record.document_count = len(record.document_ids)


    def _compute_container_count(self):
            """Compute container count"""
            for record in self:
                record.container_count = len(record.container_ids)


    def _compute_expiry_date(self):
            """Compute expiry date based on activation and retention period"""
            for record in self:
                if record.date_activated and record.retention_period:
                    expiry_datetime = record.date_activated + timedelta()
                        days=record.retention_period

                    record.expiry_date = expiry_datetime.date()
                else:
                    record.expiry_date = False


    def _compute_last_movement_date(self):
            """Compute last movement date"""
            for record in self:
                if record.movement_ids:
                    record.last_movement_date = max(record.movement_ids.mapped("date"))
                else:
                    record.last_movement_date = False


    def _compute_movement_count(self):
            """Compute movement count"""
            for record in self:
                record.movement_count = len(record.movement_ids)


    def _compute_total_cost(self):
            """Compute total cost"""
            for record in self:
                record.total_cost = record.storage_cost + record.handling_cost

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_activate(self):
            """Activate the temporary inventory"""
            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Only draft inventories can be activated"))
            self.write()
                {}
                    "state": "active",
                    "date_activated": fields.Datetime.now(),


            self.message_post(body=_("Temporary inventory activated"))


    def action_deactivate(self):
            """Deactivate the temporary inventory"""
            self.ensure_one()
            if self.state not in ("active", "in_use"):
                raise UserError()
                    _("Only active or in-use inventories can be deactivated")

            self.write({"state": "archived"})
            self.message_post(body=_("Temporary inventory deactivated"))


    def action_archive(self):
            """Archive the temporary inventory"""
            self.ensure_one()
            if self.current_count > 0:
                raise UserError()
                    _()
                        "Cannot archive inventory with items. Please remove all items before archiving."


            self.write()
                {}
                    "state": "archived",
                    "active": False,
                    "date_archived": fields.Datetime.now(),


            self.message_post(body=_("Temporary inventory archived"))


    def action_approve(self):
            """Approve the temporary inventory"""
            self.ensure_one()
            if not self.approval_required:
                raise UserError(_("This inventory does not require approval"))
            self.write()
                {}
                    "approved_by_id": self.env.user.id,
                    "approval_date": fields.Datetime.now(),


            self.message_post(body=_("Temporary inventory approved"))


    def action_reject(self):
            """Reject the temporary inventory"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Reject Inventory"),
                "res_model": "temp.inventory.reject.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_inventory_id": self.id},



    def action_view_documents(self):
            """View associated documents"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Associated Documents"),
                "res_model": "records.document",
                "view_mode": "tree,form",
                "domain": [("temp_inventory_id", "=", self.id)],
                "context": {"default_temp_inventory_id": self.id},



    def action_view_containers(self):
            """View associated containers"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Associated Containers"),
                "res_model": "records.container",
                "view_mode": "tree,form",
                "domain": [("temp_inventory_id", "=", self.id)],
                "context": {"default_temp_inventory_id": self.id},



    def action_view_movements(self):
            """View inventory movements"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Inventory Movements"),
                "res_model": "temp.inventory.movement",
                "view_mode": "tree,form",
                "domain": [("inventory_id", "=", self.id)],
                "context": {"default_inventory_id": self.id},



    def action_create_movement(self):
            """Create new inventory movement"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Create Movement"),
                "res_model": "temp.inventory.movement",
                "view_mode": "form",
                "target": "new",
                "context": {}
                    "default_inventory_id": self.id,
                    "default_movement_type": "in",




    def action_check_capacity_status(self):
            """Check capacity status and update state if needed - Business method""":
            self.ensure_one()
            if self.utilization_percent >= 100:
                self.write({"state": "full"})
                message = _("Inventory is at full capacity")
                message_type = "warning"
            elif self.utilization_percent >= 90:
                utilization_rounded = round(self.utilization_percent, 1)
                message = _("Inventory is at %s%% capacity - nearly full", utilization_rounded)
                message_type = "warning"
            elif self.utilization_percent >= 75:
                utilization_rounded = round(self.utilization_percent, 1)
                message = _("Inventory is at %s%% capacity", utilization_rounded)
                message_type = "info"
            else:
                message = _("Inventory has %s available slots", self.available_capacity)
                message_type = "success"

            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Capacity Status"),
                    "message": message,
                    "type": message_type,
                    "sticky": False,



        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def get_expiry_status(self):
            """Get expiry status for business logic - Business method""":
            self.ensure_one()

    def get_inventory_summary(self):
            """Get inventory summary for reporting""":
            self.ensure_one()
            return {}
                "name": self.name,
                "type": self.inventory_type,
                "state": self.state,
                "current_count": self.current_count,
                "capacity_limit": self.capacity_limit,
                "utilization_percent": self.utilization_percent,
                "location": self.location_id.name if self.location_id else None,:
                "total_cost": self.total_cost,
                "expiry_status": self.get_expiry_status(),


        # ============================================================================
            # CONSTRAINT METHODS
        # ============================================================================

    def _check_capacity_limit(self):
            """Validate capacity limit"""
            for record in self:
                if record.capacity_limit <= 0:
                    raise ValidationError(_("Capacity limit must be greater than zero"))


    def _check_retention_period(self):
            """Validate retention period"""
            for record in self:
                if record.retention_period <= 0:
                    raise ValidationError(_("Retention period must be greater than zero"))


    def _check_costs(self):
            """Validate costs are non-negative"""
            for record in self:
                if record.storage_cost < 0 or record.handling_cost < 0:
                    raise ValidationError(_("Costs cannot be negative"))

        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to set default values and generate sequence"""
            for vals in vals_list:
                if not vals.get("name") or vals["name"] == "/":
                    vals["name") = (]
                        self.env["ir.sequence"].next_by_code("temp.inventory") or "TI-NEW"


    def write(self, vals):
            """Override write to update modification date and handle state changes"""

    def unlink(self):
            """Override unlink to prevent deletion with items"""
            for record in self:
                if record.current_count > 0:
                    raise UserError()
                        _()
                            "Cannot delete inventory '%s' because it contains %d items. Please remove all items before deleting.",
                            record.name,
                            record.current_count,


            return super().unlink()

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def get_expired_inventories(self):
            """Get all expired temporary inventories"""
            return self.search()
                []
                    ("expiry_date", "<=", fields.Date.today()),
                    ("state", "in", ["active", "in_use"]),




    def get_nearly_full_inventories(self, threshold=90):
            """Get inventories that are nearly full"""
            inventories = self.search([("state", "=", "active")])
            return inventories.filtered(lambda inv: inv.utilization_percent >= threshold)


    def cleanup_expired_inventories(self):
            """Cleanup expired inventories (automated method)"""
            expired_inventories = self.get_expired_inventories()
            for inventory in expired_inventories:
                if inventory.current_count == 0:
                    inventory.action_archive()
                else:
                    inventory.message_post()
                        body=_("Warning: Inventory has expired but still contains items")


