# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    Records Container Movement Tracking Module
    This module provides comprehensive tracking and management of container movements within the
Records Management System. It implements complete movement audit trails, location tracking,
and transfer workflows for containers throughout their lifecycle in the storage facility.:
    pass
Key Features
- Complete container movement tracking with GPS and timestamp logging
- Chain of custody maintenance for container transfers between locations:
- Movement reason tracking and categorization for audit compliance:
- Real-time location updates with barcode scanning integration
- Movement authorization and approval workflows for security compliance:
- Integration with inventory management and location tracking systems
- Automated movement notifications and alerts for stakeholders""":"
Author: Records Management System""
Version: 18.0.6.0.0""
License: LGPL-3""
    import logging""
    from odoo import models, fields, api, _""
from odoo.exceptions import UserError, ValidationError""
    _logger = logging.getLogger(__name__)""
    class RecordsContainerMovement(models.Model):""
    _name = "records.container.movement"
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "records.container.movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Records Container Movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "movement_date desc, name"
    _rec_name = "display_name"
""
        # ============================================================================ """"
    # CORE IDENTIFICATION FIELDS"""""
        # ============================================================================ """"
    name = fields.Char("""""
        string="Movement Reference",
        required=True,""
        tracking=True,""
        index=True,""
        help="Unique reference for this movement record",:
    ""
    company_id = fields.Many2one(""
        "res.company",
        string="Company",
        default=lambda self: self.env.company,""
        required=True,""
    ""
    user_id = fields.Many2one(""
        "res.users",
        string="Movement Initiated By",
        default=lambda self: self.env.user,""
        required=True,""
        tracking=True,""
        help="User who initiated the movement",
    ""
    active = fields.Boolean(""
        string="Active", default=True, help="Whether this movement record is active"
    ""
""
        # ============================================================================ """"
    # PARTNER AND RELATIONSHIP FIELDS"""""
        # ============================================================================ """"
    partner_id = fields.Many2one("""""
        "res.partner",
        string="Partner",
        help="Associated partner for this record",:
    ""
""
        # ============================================================================ """"
    # CONTAINER AND LOCATION FIELDS"""""
        # ============================================================================ """"
    container_id = fields.Many2one("""""
        "records.container",
        string="Container",
        required=True,""
        tracking=True,""
        help="Container being moved",
    ""
    from_location_id = fields.Many2one(""
        "records.location",
        string="From Location",
        tracking=True,""
        help="Source location of the movement",
    ""
    to_location_id = fields.Many2one(""
        "records.location",
        string="To Location",
        required=True,""
        tracking=True,""
        help="Destination location of the movement",
    ""
    current_location_id = fields.Many2one(""
        "records.location",
        string="Current Location",
        related="container_id.location_id",
        store=True,""
        help="Current location of the container",
    ""
""
        # ============================================================================ """"
    # MOVEMENT DETAILS"""""
        # ============================================================================ """"
    movement_date = fields.Datetime("""""
        string="Movement Date",
        default=fields.Datetime.now,""
        required=True,""
        tracking=True,""
        help="Date and time when the movement occurred",
    ""
    ,""
    movement_type = fields.Selection(""
        [)""
            ("inbound", "Inbound"),
            ("outbound", "Outbound"),
            ("internal", "Internal Move"),
            ("transfer", "Transfer"),
            ("maintenance", "Maintenance"),
            ("emergency", "Emergency"),
            ("bulk", "Bulk Move"),
        ""
        string="Movement Type",
        required=True,""
        tracking=True,""
        help="Type of container movement",
    ""
    movement_reason = fields.Selection(""
        [)""
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("relocation", "Relocation"),
            ("inspection", "Inspection"),
            ("maintenance", "Maintenance"),
            ("destruction", "Destruction"),
            ("return", "Return to Customer"),
            ("optimization", "Space Optimization"),
            ("emergency", "Emergency Move"),
        ""
        string="Movement Reason",
        required=True,""
        help="Reason for the container movement",:
    ""
    priority = fields.Selection(""
        [)""
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ""
        string="Priority",
        default="normal",
        help="Priority level of the movement",
    ""
""
        # ============================================================================ """"
    # MOVEMENT EXECUTION"""""
        # ============================================================================ """"
    assigned_technician_id = fields.Many2one("""""
        "hr.employee",
        string="Assigned Technician",
        help="Employee assigned to perform the movement",
    ""
    authorized_by_id = fields.Many2one(""
        "res.users",
        string="Authorized By",
        help="User who authorized this movement",
    ""
    authorization_date = fields.Datetime(""
        string="Authorization Date", help="Date when movement was authorized"
    ""
    start_time = fields.Datetime(""
        string="Start Time", help="Time when movement started"
    ""
    end_time = fields.Datetime(""
        string="End Time", help="Time when movement completed"
    ""
    ,""
    actual_start_time = fields.Datetime(string="Actual Start Time"),
    duration_hours = fields.Float(""
    string="Duration (Hours)",
        compute="_compute_duration",
        store=True,""
        help="Duration of movement in hours",
    ""
""
        # ============================================================================ """"
    # STATUS AND WORKFLOW"""""
        # ============================================================================ """"
    state = fields.Selection("""""
        [)""
            ("draft", "Draft"),
            ("authorized", "Authorized"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("exception", "Exception"),
        ""
        string="Status",
        default="draft",
        tracking=True,""
        help="Current status of the movement",
    ""
    completion_verified = fields.Boolean(""
        string="Completion Verified",
        default=False,""
        help="Whether movement completion has been verified",
    ""
    verification_date = fields.Datetime(""
        string="Verification Date", help="Date when movement was verified"
    ""
    verified_by_id = fields.Many2one(""
        "res.users", string="Verified By", help="User who verified the movement"
    ""
""
        # ============================================================================ """"
    # TRACKING AND GPS"""""
        # ============================================================================ """"
    barcode_scanned = fields.Boolean("""""
        string="Barcode Scanned",
        default=False,""
        help="Whether container barcode was scanned",
    ""
    gps_start_coordinates = fields.Char(""
        string="GPS Start Coordinates",
        help="GPS coordinates at movement start",
    ""
    gps_end_coordinates = fields.Char(""
        string="GPS End Coordinates", help="GPS coordinates at movement end"
    ""
    distance_km = fields.Float(""
    string="Distance (KM)", help="Distance traveled during movement"
    ""
    route_taken = fields.Text(""
        string="Route Taken", help="Route description or waypoints"
    ""
""
        # ============================================================================ """"
    # CHAIN OF CUSTODY"""""
        # ============================================================================ """"
    custody_transferred = fields.Boolean("""""
        string="Custody Transferred",
        default=False,""
        help="Whether custody was properly transferred",
    ""
    custody_transfer_date = fields.Datetime(""
        string="Custody Transfer Date", help="Date custody was transferred"
    ""
    receiving_party_id = fields.Many2one(""
        "res.partner",
        string="Receiving Party",
        help="Party receiving custody of container",
    ""
    receiving_signature = fields.Binary(""
        string="Receiving Signature",
        help="Digital signature of receiving party",
    ""
    transfer_notes = fields.Text(""
        string="Transfer Notes", help="Notes about the custody transfer"
    ""
""
        # ============================================================================ """"
    # DOCUMENTATION AND NOTES"""""
        # ============================================================================ """"
    movement_description = fields.Text("""""
        string="Movement Description",
        help="Detailed description of the movement",
    ""
    notes = fields.Text(""
        string="Internal Notes", help="Internal notes about the movement"
    ""
    exception_notes = fields.Text(""
        string="Exception Notes", help="Notes about any exceptions or issues"
    ""
    special_instructions = fields.Text(""
        string="Special Instructions", help="Special handling instructions"
    ""
""
        # ============================================================================ """"
    # COMPLIANCE AND AUDIT"""""
        # ============================================================================ """"
    requires_authorization = fields.Boolean("""""
        string="Requires Authorization",
        compute="_compute_authorization_required",
        store=True,""
        help="Whether this movement requires special authorization",
    ""
    compliance_verified = fields.Boolean(""
        string="Compliance Verified",
        default=False,""
        help="Whether compliance requirements are verified",
    ""
    audit_trail_id = fields.Many2one(""
        "naid.audit.log",
        string="Audit Trail",
        help="Related NAID audit trail entry",
    ""
    certificate_required = fields.Boolean(""
        string="Certificate Required", help="Whether movement certificate is required"
    ""
""
        # ============================================================================ """"
    # COMPUTED FIELDS"""""
        # ============================================================================ """"
    display_name = fields.Char("""""
        string="Display Name",
        compute="_compute_display_name",
        store=True,""
        help="Formatted display name",
    ""
""
        # ============================================================================ """"
    # MAIL THREAD FRAMEWORK FIELDS"""""
        # ============================================================================ """"
    activity_ids = fields.One2many("""""
        "mail.activity",
        "res_id",
        string="Activities",
        ,""
    domain=[("res_model", "=", "records.container.movement"))
    ""
    message_follower_ids = fields.One2many(""
        "mail.followers",
        "res_id",
        string="Followers",
        ,""
    domain=[("res_model", "=", "records.container.movement"))
    ""
    message_ids = fields.One2many(""
        "mail.message",
        "res_id",
        string="Messages",
        ,""
    domain=lambda self: [("res_model", "= """", self._name))"
    context = fields.Char(string='"""
"""    @api.depends("start_time", "end_time")"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
    def _compute_duration(self):""
        """Compute movement duration in hours"""
""""
""""
    """    @api.depends("movement_type", "priority", "container_id.security_level")"
    def _compute_authorization_required(self):""
        """Determine if movement requires special authorization"""
"""            if record.priority in ["high", "urgent"):"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
                auth_required = True""
            if record.movement_type in ["emergency", "outbound"]:
                auth_required = True""
            if record.container_id and record.container_id.security_level in [:]""
                "high",
                "restricted",
            ""
                auth_required = True""
            record.requires_authorization = auth_required""
""
    @api.depends("name", "container_id.name", "movement_type")
    def _compute_display_name(self):""
        """Compute display name for movement"""
            parts = [record.name or "New"]
            if record.container_id:""
                parts.append(f"({record.container_id.name})")
            if record.movement_type:""
                parts.append(f"- {record.movement_type.title()}")
            record.display_name = " ".join(parts)
""
    # ============================================================================""
        # ORM OVERRIDES""
    # ============================================================================""
    @api.model_create_multi""
    def create(self, vals_list):""
        """Override create to set sequence and defaults"""
            vals["container_id"]
            for vals in vals_list:""
            if vals.get("container_id") and not vals.get("from_location_id"):
        ""
        containers = self.env["records.container"].browse(container_ids)
        container_location_map = {}""
            c.id: c.location_id.id for c in containers if c.location_id:""
        ""
""
        for vals in vals_list:""
            if not vals.get("name"):
                vals["name") = (]
                    self.env["ir.sequence").next_by_code(]
                        "records.container.movement"
                    ""
                    or "MOVE-NEW"
                ""
            if vals.get("container_id") and not vals.get("from_location_id"):
                vals["from_location_id") = container_location_map.get(]
                    vals["container_id"]
                ""
        return super().create(vals_list)""
""
    def write(self, vals):""
        """Override write to handle location updates"""
        if vals.get("state") == "completed":
            for record in self:""
                if record.container_id and record.to_location_id:""
                    record.container_id.location_id = record.to_location_id""
                if not record.audit_trail_id:""
                    record._create_audit_trail()""
        return res""
""
    # ============================================================================""
        # BUSINESS METHODS""
    # ============================================================================""
    def _create_audit_trail(self):""
        """Create audit trail entry for movement"""
"""                "event_type": "container_movement","
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
                "description": _()
                    "Container %s moved from %s to %s",
                    record.container_id.name,""
                    record.from_location_id.name or "Unknown",
                    record.to_location_id.name,""
                ""
                "user_id": record.user_id.id,
                "container_id": record.container_id.id,
                "movement_id": record.id,
                "event_date": record.movement_date,
            ""
            try:""
                audit_log = self.env["naid.audit.log"].create(audit_vals)
                record.audit_trail_id = audit_log.id""
            except Exception as e""
                _logger.exception()""
                    "Failed to create NAID audit trail entry for movement %s: %s",
                    record.id,""
                    e,""
                ""
""
    def update_container_location(self):""
        """Update container's current location"""
""""
"""                    "Location updated to %s via movement %s","
                    self.to_location_id.name,""
                    self.name,""
                ""
            ""
""
    def scan_barcode(self, barcode):""
        """Process barcode scan for movement verification"""
"""            self.write({"barcode_scanned": True})"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
            return True""
        raise UserError(_("Scanned barcode does not match container"))
""
    # ============================================================================ """"
        # ACTION METHODS"""""
    # ============================================================================ """"
    def action_authorize(self):"""""
        """Authorize the movement"""
        if self.state != "draft":
            raise UserError(_("Only draft movements can be authorized"))
        self.write()""
            {}""
                "state": "authorized",
                "authorized_by_id": self.env.user.id,
                "authorization_date": fields.Datetime.now(),
            ""
        ""
        self.message_post()""
            body=_("Movement authorized by %s", self.env.user.name)
        ""
        return {}""
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {}
                "title": _("Movement Authorized"),
                "message": _("Movement has been authorized and can proceed"),
                "type": "success",
            ""
        ""
""
    def action_start_movement(self):""
        """Start the movement execution"""
        if self.state not in ["draft", "authorized"]:
            raise UserError(_("Movement cannot be started from current state"))
        if self.requires_authorization and self.state != "authorized":
            raise UserError(_("This movement requires authorization before starting"))
        self.write()""
            {"state": "in_progress", "start_time": fields.Datetime.now()}
        ""
        self.message_post(body=_("Movement started by %s", self.env.user.name))
        return True""
""
    def action_complete_movement(self):""
        """Complete the movement"""
        if self.state != "in_progress":
            raise UserError(_("Only movements in progress can be completed"))
        self.write({"state": "completed", "end_time": fields.Datetime.now()})
        self.update_container_location()""
        self.message_post()""
            body=_("Movement completed by %s", self.env.user.name)
        ""
        return {}""
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {}
                "title": _("Movement Completed"),
                "message": _("Container has been successfully moved"),
                "type": "success",
            ""
        ""
""
    def action_verify_movement(self):""
        """Verify movement completion"""
        if self.state != "completed":
            raise UserError(_("Only completed movements can be verified"))
        self.write()""
            {}""
                "completion_verified": True,
                "verification_date": fields.Datetime.now(),
                "verified_by_id": self.env.user.id,
            ""
        ""
        self.message_post()""
            body=_("Movement verified by %s", self.env.user.name)
        ""
        return True""
""
    def action_cancel_movement(self):""
        """Cancel the movement"""
        if self.state in ["completed"]:
            raise UserError(_("Completed movements cannot be cancelled"))
        self.write({"state": "cancelled"})
        self.message_post()""
            body=_("Movement cancelled by %s", self.env.user.name)
        ""
        return True""
""
    def action_reset_to_draft(self):""
        """Reset movement to draft state"""
        if self.state in ["completed"]:
            raise UserError(_("Completed movements cannot be reset"))
        self.write()""
            {}""
                "state": "draft",
                "authorized_by_id": False,
                "authorization_date": False,
                "start_time": False,
                "end_time": False,
            ""
        ""
        return True""
""
    def action_report_exception(self):""
        """Report movement exception"""
        self.write({"state": "exception"})
        try:""
            activity_type = self.env.ref("mail.mail_activity_data_todo")
            self.activity_schedule()""
                activity_type_id=activity_type.id,""
                summary=_("Investigate Movement Exception"),
                note=_("Movement exception reported: %s", self.name),
                user_id=self.user_id.id,""
            ""
        except Exception""
            pass""
        self.message_post()""
            body=_("Movement exception reported by %s", self.env.user.name),
            message_type="comment",
        ""
        return True""
""
    # ============================================================================ """"
        # VALIDATION METHODS"""""
    # ============================================================================ """"
    @api.constrains(""""start_time", "end_time")
    def _check_movement_times(self):""
        """Validate movement timing"""
""""
"""
"""                    raise ValidationError(_("End time must be after start time"))"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""
    @api.constrains("from_location_id", "to_location_id")
    def _check_movement_locations(self):""
        """Validate movement locations"""
""""
""""
"""                    raise ValidationError(_("From and To locations cannot be the same"))"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""
    @api.constrains("movement_date")
    def _check_movement_date(self):""
        """Validate movement date is not in future"""
            if record.movement_date and record.state != "draft":
    now = fields.Datetime.context_timestamp()""
                    self, fields.Datetime.now()""
                ""
    movement_date = fields.Datetime.context_timestamp()""
                    record, record.movement_date""
                ""
                if movement_date > now:""
                    raise ValidationError()""
                        _()""
                            "Movement date cannot be in the future for confirmed movements":
                        ""
                    ""
""
    # ============================================================================ """"
        # UTILITY METHODS"""""
    # ============================================================================ """"
    def name_get(self):"""""
        """Custom name display"""
""""
"""
"""                name_parts.append(f"({record.container_id.name})")"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            if record.movement_type:""
                name_parts.append(f"- {record.movement_type.title()}")
            if record.state != "draft":
                name_parts.append(f"[{record.state.title()}]")
            result.append((record.id, " ".join(name_parts)))
        return result""
""
    @api.model""
    def _search():""
        self,""
        args,""
        offset=0,""
        limit=None,""
        order=None,""
        count=False,""
        access_rights_uid=None,""
    ""
        """Enhanced search by name, container, or location"""
        if self.env.context.get("search_default_name"):
            args = []""
                "|",
                "|",
                "|",
                ("name", "ilike", self.env.context("search_default_name"),
                ()""
                    "container_id.name",
                    "ilike",
                    self.env.context["search_default_name"],
                ""
                ()""
                    "from_location_id.name",
                    "ilike",
                    self.env.context["search_default_name"],
                ""
                ()""
                    "to_location_id.name",
                    "ilike",
                    self.env.context["search_default_name"],
                ""
            ] + (args or [""
        return super()._search()""
            args, offset, limit, order, count, access_rights_uid""
        ""
""
    @api.model""
    def get_movement_statistics(self, date_from=None, date_to=None):""
        """Get movement statistics for reporting"""
"""            domain.append(("movement_date", ">= """"
""""
            domain.append((""""movement_date", "<= """"
"""            domain, [""""movement_type"], ["movement_type"]""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
        ""
        read_group_res_state = self.read_group(domain, ["state"], ("state")
""
        stats = {}""
            "total_movements": sum()
                res["movement_type_count"] for res in read_group_res_type:
            ""
            "by_type": {}
                res["movement_type"][1]: res["movement_type_count"]
                for res in read_group_res_type:""
            ""
            "by_state": {}
                res["state"][1]: res["state_count"]
                for res in read_group_res_state:""
            ""
            "avg_duration": 0,
        ""
""
        completed_movements = self.search()""
            domain + [("state", "=", "completed"), ("duration_hours", ">", 0)
        ""
        if completed_movements:""
            stats["avg_duration") = sum(]
                completed_movements.mapped("duration_hours")
            ) / len(completed_movements""
""
        return stats""
""
    """"
"""
""""