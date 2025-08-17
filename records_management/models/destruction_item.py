# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DestructionItem(models.Model):
    _name = 'destruction.item'
    _description = 'Destruction Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "sequence, create_date desc"
    _rec_name = "item_description"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(string="Name", compute="_compute_name",,
    store=True),
    item_description = fields.Char(
        string="Item Description", required=True, tracking=True

    sequence = fields.Integer(string="Sequence",,
    default=10),
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True

    active = fields.Boolean(string="Active",,
    default=True)

        # ============================================================================
    # BUSINESS SPECIFIC FIELDS
        # ============================================================================
    quantity = fields.Float(string="Quantity", default=1.0,,
    digits=(12, 3))
    weight = fields.Float(string="Weight (lbs)", digits=(12, 2))
    container_type = fields.Selection(
        [)
            ("type_01", "Standard Box (1.2 CF)"),
            ("type_02", "Legal/Banker Box (2.4 CF)"),
            ("type_03", "Map Box (0.875 CF)"),
            ("type_04", "Odd Size/Temp Box (5.0 CF)"),
            ("type_06", "Pathology Box (0.42 CF)"),
            ("hard_drive", "Hard Drive"),
            ("media", "Media/Tapes"),
            ("other", "Other"),

        string="Container Type",


    destruction_status = fields.Selection(
        [)
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("destroyed", "Destroyed"),
            ("verified", "Verified"),

        string="Destruction Status",
        default="pending",
        tracking=True,


        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        help="Customer associated with this destruction item",


    shredding_service_id = fields.Many2one(
        "shredding.service", string="Shredding Service", ondelete="cascade"


    records_destruction_id = fields.Many2one(
        "records.destruction",
        string="Records Destruction",
        help="Associated records destruction record",


    naid_certificate_id = fields.Many2one(
        "naid.certificate",
        string="NAID Certificate",
        help="Associated NAID destruction certificate",


    certificate_id = fields.Many2one(
        "shredding.certificate",
        string="Shredding Certificate",
        help="Associated shredding certificate for this destruction item",:
            pass
        ondelete="set null"


    destruction_record_id = fields.Many2one(
        "naid.destruction.record",
        string="Destruction Record",
        help="Associated NAID destruction record",
        ,
    ondelete="set null"


        # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance):
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"

    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"

    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages")

        # ============================================================================
    # TIMESTAMPS & AUDIT
        # ============================================================================
    date_created = fields.Datetime(
        string="Created Date", default=fields.Datetime.now, readonly=True

    ,
    date_destroyed = fields.Datetime(string="Destruction Date"),
    date_verified = fields.Datetime(string="Verification Date")

        # Workflow state management
    state = fields.Selection([))
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('cancelled', 'Cancelled'),

        help='Current status of the record'

    # ============================================================================
        # COMPUTE METHODS
    # ============================================================================
    @api.depends("item_description", "sequence")
    def _compute_name(self):
        """Compute name from description and sequence"""
        for record in self:
            if record.item_description:
                record.name = record.item_description
            else:
                record.name = _("Item #%s", record.sequence)

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_mark_destroyed(self):
        """Mark item as destroyed with timestamp"""
        self.ensure_one()
        if self.destruction_status in ["destroyed", "verified"]:
            raise UserError(_("Item is already marked as destroyed"))

        self.write()
            {}
                "destruction_status": "destroyed",
                "date_destroyed": fields.Datetime.now(),



        # Create audit log
        self.message_post(body=_("Item marked as destroyed"))

    def action_verify_destruction(self):
        """Verify destruction completion"""
        self.ensure_one()
        if self.destruction_status != "destroyed":
            raise UserError(_("Can only verify items that are destroyed"))

        self.write()
            {}
                "destruction_status": "verified",
                "date_verified": fields.Datetime.now(),



        self.message_post(body=_("Destruction verified"))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create with proper batch handling"""
        for vals in vals_list:
            # Auto-generate sequence if not provided:
            if not vals.get("sequence"):
                vals["sequence"] = ()
                    self.env["ir.sequence"].next_by_code("destruction.item")
                    or 10


        return super().create(vals_list)

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains("quantity", "weight")
    def _check_positive_values(self):
        """Validate positive values for quantity and weight""":
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero"))
            if record.weight < 0:
                raise ValidationError(_("Weight cannot be negative"))

    @api.constrains("destruction_status", "date_destroyed", "date_verified")
    def _check_destruction_dates(self):
        """Validate destruction and verification dates"""
        for record in self:
            if (:)
                record.destruction_status == "destroyed"
                and not record.date_destroyed

                raise ValidationError()
                    _("Destruction date is required for destroyed items"):

            if (:)
                record.destruction_status == "verified"
                and not record.date_verified

                raise ValidationError()
                    _("Verification date is required for verified items"):

))))))))))
