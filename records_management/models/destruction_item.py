from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class DestructionItem(models.Model):
    _name = 'destruction.item'
    _description = 'Destruction Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, create_date desc'
    _rec_name = 'item_description'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name')
    item_description = fields.Char()
    sequence = fields.Integer(string='Sequence')
    company_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    quantity = fields.Float(string='Quantity')
    weight = fields.Float(string='Weight (lbs)')
    container_type = fields.Selection()
    destruction_status = fields.Selection()
    partner_id = fields.Many2one()
    shredding_service_id = fields.Many2one()
    records_destruction_id = fields.Many2one()
    naid_certificate_id = fields.Many2one()
    certificate_id = fields.Many2one()
    destruction_record_id = fields.Many2one()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    date_created = fields.Datetime()
    date_destroyed = fields.Datetime(string='Destruction Date')
    date_verified = fields.Datetime(string='Verification Date')
    state = fields.Selection()

    # ============================================================================
    # METHODS
    # ============================================================================
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

    def _check_positive_values(self):
            """Validate positive values for quantity and weight""":
            for record in self:
                if record.quantity <= 0:
                    raise ValidationError(_("Quantity must be greater than zero"))
                if record.weight < 0:
                    raise ValidationError(_("Weight cannot be negative"))


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

