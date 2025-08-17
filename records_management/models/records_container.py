from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RecordsContainer(models.Model):
    _name = 'records.container'
    _description = 'Records Container Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    code = fields.Char(string='Container Code')
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence')
    active = fields.Boolean(string='Active')
    currency_id = fields.Many2one()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    state = fields.Selection()
    partner_id = fields.Many2one()
    department_id = fields.Many2one('records.department')
    location_id = fields.Many2one()
    temp_inventory_id = fields.Many2one()
    customer_inventory_id = fields.Many2one()
    barcode_product_id = fields.Many2one()
    container_type_id = fields.Many2one()
    document_type_id = fields.Many2one()
    barcode = fields.Char(string='Barcode')
    dimensions = fields.Char(string='Dimensions')
    weight = fields.Float(string='Weight (lbs)')
    cubic_feet = fields.Float(string='Cubic Feet')
    document_ids = fields.One2many()
    document_count = fields.Integer()
    content_description = fields.Text(string='Content Description')
    is_full = fields.Boolean(string='Container Full')
    alpha_range_start = fields.Char()
    alpha_range_end = fields.Char()
    alpha_range_display = fields.Char()
    content_date_from = fields.Date()
    content_date_to = fields.Date()
    content_date_range_display = fields.Char()
    primary_content_type = fields.Selection()
    search_keywords = fields.Text()
    customer_sequence_start = fields.Char()
    customer_sequence_end = fields.Char()
    received_date = fields.Date()
    collection_date = fields.Date()
    service_date = fields.Date()
    storage_start_date = fields.Date(string='Storage Start Date')
    stored_date = fields.Date(string='Stored Date')
    last_access_date = fields.Date(string='Last Access Date')
    destruction_date = fields.Date(string='Destruction Date')
    from_location_id = fields.Many2one()
    to_location_id = fields.Many2one()
    movement_date = fields.Datetime()
    movement_type = fields.Selection()
    service_type = fields.Selection()
    access_level = fields.Selection()
    compliance_category = fields.Char()
    industry_category = fields.Selection()
    department_code = fields.Char()
    project_number = fields.Char()
    priority_level = fields.Selection()
    media_type = fields.Selection()
    language_codes = fields.Char()
    retention_category = fields.Char()
    special_dates = fields.Text()
    bale_weight = fields.Float()
    key = fields.Char()
    value = fields.Text()
    retention_policy_id = fields.Many2one()
    retention_years = fields.Integer(string='Retention Years')
    destruction_due_date = fields.Date()
    permanent_retention = fields.Boolean(string='Permanent Retention')
    billing_rate = fields.Float()
    service_level = fields.Selection()
    security_level = fields.Selection()
    access_restriction = fields.Text(string='Access Restrictions')
    authorized_user_ids = fields.Many2many('res.users')
    condition = fields.Selection()
    maintenance_notes = fields.Text(string='Maintenance Notes')
    last_inspection_date = fields.Date(string='Last Inspection Date')
    movement_ids = fields.One2many()
    current_movement_id = fields.Many2one()
    conversion_date = fields.Datetime()
    conversion_reason = fields.Text()
    converter_id = fields.Many2one()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    security_seal_number = fields.Char(string='Security Seal Number')
    last_inventory_date = fields.Date(string='Last Inventory Date')
    next_inspection_due = fields.Date(string='Next Inspection Due')
    temperature_controlled = fields.Boolean(string='Temperature Controlled')
    humidity_controlled = fields.Boolean(string='Humidity Controlled')
    fire_suppression = fields.Boolean(string='Fire Suppression Available')
    access_restrictions = fields.Text(string='Access Restrictions')
    insurance_value = fields.Monetary(string='Insurance Value')
    is_due_for_destruction = fields.Boolean()
    action_bulk_convert_container_type = fields.Selection(string='Action Bulk Convert Container Type')
    action_destroy_container = fields.Char(string='Action Destroy Container')
    action_generate_barcode = fields.Char(string='Action Generate Barcode')
    action_index_container = fields.Char(string='Action Index Container')
    action_retrieve_container = fields.Char(string='Action Retrieve Container')
    action_store_container = fields.Char(string='Action Store Container')
    action_view_documents = fields.Char(string='Action View Documents')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    context = fields.Char(string='Context')
    create_date = fields.Date(string='Create Date')
    destroyed = fields.Char(string='Destroyed')
    details = fields.Char(string='Details')
    documents = fields.Char(string='Documents')
    group_by_creation_date = fields.Date(string='Group By Creation Date')
    group_by_customer = fields.Char(string='Group By Customer')
    group_by_department = fields.Char(string='Group By Department')
    group_by_location = fields.Char(string='Group By Location')
    group_by_state = fields.Selection(string='Group By State')
    help = fields.Char(string='Help')
    indexed = fields.Char(string='Indexed')
    movements = fields.Char(string='Movements')
    near_destruction = fields.Char(string='Near Destruction')
    received = fields.Char(string='Received')
    res_model = fields.Char(string='Res Model')
    retrieved = fields.Char(string='Retrieved')
    search_view_id = fields.Many2one('search.view')
    stored = fields.Char(string='Stored')
    this_month = fields.Char(string='This Month')
    this_year = fields.Char(string='This Year')
    view_mode = fields.Char(string='View Mode')
    today = fields.Date()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_activate(self):
            """Activate container for storage""":
            self.ensure_one()
            if not self.partner_id:
                raise UserError(_("Customer must be specified before activation"))
            if not self.location_id:
                raise UserError(_("Storage location must be assigned"))

            self.write()
                {}
                    "state": "active",
                    "storage_start_date": fields.Date.today(),


            self.message_post(body=_("Container activated for storage")):

    def action_mark_full(self):
            """Mark container as full"""

            self.ensure_one()
            self.write({"is_full": True})
            self.message_post(body=_("Container marked as full"))


    def action_schedule_destruction(self):
            """Schedule container for destruction""":
            self.ensure_one()
            if self.permanent_retention:
                raise UserError()
                    _("Cannot schedule permanent retention containers for destruction"):


            self.write({"state": "pending_destruction"})
            self.message_post(body=_("Container scheduled for destruction")):

    def action_destroy(self):
            """Mark container as destroyed"""

            self.ensure_one()
            if self.state != "pending_destruction":
                raise UserError(_("Only containers pending destruction can be destroyed"))

            self.write()
                {}
                    "destruction_date": fields.Date.today(),


            self.message_post(body=_("Container destroyed"))


    def action_view_documents(self):
            """View all documents in this container"""

            self.ensure_one()
            return {}
                "name": _("Documents in Container %s", self.name),
                "type": "ir.actions.act_window",
                "res_model": "records.document",
                "view_mode": "tree,form",
                "domain": [("container_id", "=", self.id)],



    def action_generate_barcode(self):

            Generates a barcode if one doesn't exist and returns an action to print it.""":'""""
            This assumes a report with the external ID 'records_management.report_container_barcode' exists.


            self.ensure_one()
            if not self.barcode:
                # Generate barcode if not exists:
                self.barcode = (""")""""
                    self.env["ir.sequence"].next_by_code("records.container.barcode")
                    or self.name

            # Return a report action to print the barcode
            return self.env.ref("records_management.report_container_barcode").report_action(self)


    def action_index_container(self):
            """Index container - change state from received to indexed"""

            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Only draft containers can be indexed"))
            self.write({"state": "active"})
            self.message_post(body=_("Container indexed and activated"))


    def action_store_container(self):
            """Store container - change state from indexed to stored"""

            self.ensure_one()
            if self.state != "active":
                raise UserError(_("Only active containers can be stored"))
            if not self.location_id:
                raise UserError(_("Storage location must be assigned before storing"))
            vals = {"state": "stored"}
            if not self.storage_start_date:

    def action_retrieve_container(self):
            """Retrieve container from storage"""

            self.ensure_one()
            if self.state not in ["stored", "active"]:
                raise UserError(_("Only stored or active containers can be retrieved"))
            self.write({"state": "in_transit", "last_access_date": fields.Date.today()})
            self.message_post(body=_("Container retrieved from storage"))


    def action_destroy_container(self):
            """Prepare container for destruction""":
            self.ensure_one()
            if self.permanent_retention:
                raise UserError(_("Cannot destroy containers with permanent retention"))
            self.action_schedule_destruction()


    def action_bulk_convert_container_type(self):
            """Bulk convert container types"""

            self.ensure_one()
            return {}
                "name": _("Bulk Convert Container Types"),
                "type": "ir.actions.act_window",
                "res_model": "records.container.type.converter.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_container_ids": [(6, 0, self.ids)]},



    def create_movement_record(:):
            self, from_location_id, to_location_id, movement_type="transfer"

            """Create movement record for container""":
            self.ensure_one()
            movement_vals = {}
                "movement_date": fields.Date.today(),
                "from_location_id": from_location_id,
                "to_location_id": to_location_id,
                "movement_type": movement_type,
                "container_id": self.id,


            movement = self.env["records.container.movement"].create(movement_vals)
            self.current_movement_id = movement.id
            return movement

        # ============================================================================
            # COMPUTED FIELDS
        # ============================================================================


    def _compute_document_count(self):
            for container in self:
                container.document_count = len(container.document_ids)


    def _compute_destruction_due_date(self):
            for container in self:
                if container.permanent_retention or not container.storage_start_date:
                    container.destruction_due_date = False
                else:
                    container.destruction_due_date = ()
                        container.storage_start_date
                        + relativedelta(years=container.retention_years)



    def _compute_is_due_for_destruction(self):
        today = fields.Date.today()
            for container in self:
                container.is_due_for_destruction = ()
                    container.destruction_due_date
                    and container.destruction_due_date <= today
                    and not container.permanent_retention


        @api.depends("alpha_range_start", "alpha_range_end")
        def _compute_alpha_range_display(self):
            """Compute alphabetical range display for search purposes""":
            for container in self:
                if container.alpha_range_start and container.alpha_range_end:
                    container.alpha_range_display = ()
                        f"{container.alpha_range_start}-{container.alpha_range_end}"

                elif container.alpha_range_start:
                    container.alpha_range_display = f"{container.alpha_range_start}+"
                else:
                    container.alpha_range_display = ""

        @api.depends("content_date_from", "content_date_to")
        def _compute_date_range_display(self):
            """Compute date range display for search purposes""":
            for container in self:
                if container.content_date_from and container.content_date_to:
                    from_str = container.content_date_from.strftime("%m/%d/%Y")
                    to_str = container.content_date_to.strftime("%m/%d/%Y")
                    container.content_date_range_display = f"{from_str} - {to_str}"
                elif container.content_date_from:
                    from_str = container.content_date_from.strftime("%m/%d/%Y")
                    container.content_date_range_display = f"From {from_str}"
                elif container.content_date_to:
                    to_str = container.content_date_to.strftime("%m/%d/%Y")
                    container.content_date_range_display = f"Until {to_str}"
                else:
                    container.content_date_range_display = ""

        def _search_due_for_destruction(self, operator, value):
        today = fields.Date.today()
            if operator == "=" and value:
                # Due for destruction: due date is today or earlier, not permanent, not destroyed
                return []
                    ("destruction_due_date", "<=", today),
                    ("permanent_retention", "=", False),
                    ("state", "!=", "destroyed"),

            elif operator == "=" and not value:
                # Not due for destruction: due date is in future or permanent retention or destroyed
                return []
                    "|",
                    ("destruction_due_date", ">", today),
                    "|",
                    ("permanent_retention", "=", True),
                    ("state", "=", "destroyed"),

            elif operator == "!=" and value:
                # Not due for destruction:
                return []
                    "|",
                    ("destruction_due_date", ">", today),
                    "|",
                    ("permanent_retention", "=", True),
                    ("state", "=", "destroyed"),

            elif operator == "!=" and not value:
                # Due for destruction:
                return []
                    ("destruction_due_date", "<=", today),
                    ("permanent_retention", "=", False),
                    ("state", "!=", "destroyed"),

            else:
                return []

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

        @api.constrains("weight", "cubic_feet")
        def _check_positive_values(self):
            for record in self:
                if record.weight < 0 or record.cubic_feet < 0:
                    raise ValidationError()
                        _("Weight and cubic feet must be positive values")


        @api.constrains("retention_years")
        def _check_retention_years(self):
            for record in self:
                if record.retention_years < 0:
                    raise ValidationError(_("Retention years cannot be negative"))

        @api.constrains("received_date", "storage_start_date")
        def _check_date_consistency(self):
            for record in self:
                if (:)
                    record.received_date
                    and record.storage_start_date
                    and record.received_date > record.storage_start_date

                    raise ValidationError()
                        _("Storage start date cannot be before received date")


        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

        @api.model_create_multi
        def create(self, vals_list):
            for vals in vals_list:
                if not vals.get("name") or vals["name"] == "/":
                    vals["name"] = ()
                        self.env["ir.sequence"].next_by_code("records.container") or "NEW"

            return super().create(vals_list)

        def write(self, vals):
            # Update last access date only if location_id or state actually changes:
            if any(key in vals for key in ["location_id", "state"]):
                if "last_access_date" not in vals:
        vals["last_access_date"] = fields.Date.today()
            return super().write(vals)

        def unlink(self):
            for record in self:
                if record.state in ("active", "stored"):
                    raise UserError(_("Cannot delete active containers"))
                if record.document_ids:
                    raise UserError(_("Cannot delete containers with documents"))
            return super().unlink()

        def get_next_inspection_date(self):
            """Calculate next inspection date based on service level"""
            self.ensure_one()
            inspection_intervals = {}
                "standard": 12,
                "premium": 6,
                "climate_controlled": 4,
                "high_security": 3,

            interval = inspection_intervals.get(self.service_level, 12)
            base_date = self.last_inspection_date or fields.Date.today()
            return base_date + relativedelta(months=interval)

        # AUTO-GENERATED FIELDS (Batch 1)
            # ============================================================================


        """"))))))))))))))))))))))))))))))))))))))))))"""

