from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsContainer(models.Model):
    # === AUDIT: MISSING FIELDS ===
    access_level = fields.Char(string='Access Level')
    alpha_range_end = fields.Char(string='Alpha Range End')
    alpha_range_start = fields.Char(string='Alpha Range Start')
    bale_weight = fields.Char(string='Bale Weight')
    code = fields.Char(string='Code')
    collection_date = fields.Date(string='Collection Date')
    compliance_category = fields.Char(string='Compliance Category')
    content_date_from = fields.Char(string='Content Date From')
    content_date_to = fields.Char(string='Content Date To')
    customer_sequence_end = fields.Char(string='Customer Sequence End')
    customer_sequence_start = fields.Char(string='Customer Sequence Start')
    department_code = fields.Char(string='Department Code')
    industry_category = fields.Char(string='Industry Category')
    key = fields.Char(string='Key')
    language_codes = fields.Char(string='Language Codes')
    media_type = fields.Char(string='Media Type')
    primary_content_type = fields.Char(string='Primary Content Type')
    priority_level = fields.Char(string='Priority Level')
    project_number = fields.Char(string='Project Number')
    retention_category = fields.Char(string='Retention Category')
    search_keywords = fields.Char(string='Search Keywords')
    service_date = fields.Date(string='Service Date')
    service_type = fields.Char(string='Service Type')
    special_dates = fields.Char(string='Special Dates')
    value = fields.Char(string='Value')
    _name = 'records.container'
    _description = 'Records Container Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Container Name", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)
    barcode = fields.Char(string='Barcode', copy=False, index=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    department_id = fields.Many2one('records.department', string="Department", domain="[('partner_id', '=', partner_id)]", tracking=True)
    location_id = fields.Many2one('records.location', string="Current Location", tracking=True, domain="[('usage', '=', 'internal')]")
    container_type_id = fields.Many2one('records.container.type', string="Container Type", required=True)
    retention_policy_id = fields.Many2one('records.retention.policy', string="Retention Policy")
    temp_inventory_id = fields.Many2one('temp.inventory', string="Temporary Inventory")
    document_type_id = fields.Many2one('records.document.type', string="Document Type")

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active/Indexed'),
        ('stored', 'In Storage'),
        ('in_transit', 'In Transit'),
        ('retrieved', 'Retrieved'),
        ('pending_destruction', 'Pending Destruction'),
        ('destroyed', 'Destroyed'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # PHYSICAL & CONTENT DETAILS
    # ============================================================================
    description = fields.Text(string='Description')
    content_description = fields.Text(string='Content Description')
    dimensions = fields.Char(string='Dimensions', related='container_type_id.dimensions', readonly=True)
    weight = fields.Float(string='Weight (lbs)')
    cubic_feet = fields.Float(string='Cubic Feet', related='container_type_id.cubic_feet', readonly=True)
    is_full = fields.Boolean(string='Container Full', default=False)
    document_ids = fields.One2many('records.document', 'container_id', string="Documents")
    document_count = fields.Integer(compute='_compute_document_count', string="Document Count", store=True)

    # ============================================================================
    # DATES & RETENTION
    # ============================================================================
    storage_start_date = fields.Date(string='Storage Start Date', tracking=True)
    last_access_date = fields.Date(string='Last Access Date', readonly=True)
    destruction_due_date = fields.Date(string='Destruction Due Date', compute='_compute_destruction_due_date', store=True)
    destruction_date = fields.Date(string='Actual Destruction Date', readonly=True)
    permanent_retention = fields.Boolean(string='Permanent Retention', default=False)
    is_due_for_destruction = fields.Boolean(string="Due for Destruction", compute='_compute_is_due_for_destruction', search='_search_due_for_destruction')

    # ============================================================================
    # MOVEMENT & SECURITY
    # ============================================================================
    movement_ids = fields.One2many('records.container.movement', 'container_id', string="Movement History")
    security_level = fields.Selection([('1', 'Standard'), ('2', 'Confidential'), ('3', 'High Security')], string="Security Level", default='1')
    access_restrictions = fields.Text(string='Access Restrictions')

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('barcode_company_uniq', 'unique(barcode, company_id)', 'The barcode must be unique per company.'),
    ]

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.container') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        if any(key in vals for key in ['location_id', 'state']) and 'last_access_date' not in vals:
            vals['last_access_date'] = fields.Date.today()
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.state not in ('draft', 'destroyed'):
                raise UserError(_("You can only delete containers that are in 'Draft' or 'Destroyed' state."))
            if record.document_ids:
                raise UserError(_("Cannot delete a container that has documents linked to it."))
        return super().unlink()

    # ============================================================================
    # COMPUTE & SEARCH METHODS
    # ============================================================================
    @api.depends('document_ids')
    def _compute_document_count(self):
        for container in self:
            container.document_count = len(container.document_ids)

    @api.depends('storage_start_date', 'retention_policy_id.retention_years', 'permanent_retention')
    def _compute_destruction_due_date(self):
        for container in self:
            if container.permanent_retention or not container.storage_start_date or not container.retention_policy_id:
                container.destruction_due_date = False
            else:
                retention_years = container.retention_policy_id.retention_years
                container.destruction_due_date = container.storage_start_date + relativedelta(years=retention_years)

    @api.depends('destruction_due_date', 'permanent_retention', 'state')
    def _compute_is_due_for_destruction(self):
        today = fields.Date.today()
        for container in self:
            container.is_due_for_destruction = bool(
                container.destruction_due_date
                and container.destruction_due_date <= today
                and not container.permanent_retention
                and container.state != 'destroyed'
            )

    def _search_due_for_destruction(self, operator, value):
        today = fields.Date.today()
        domain = [
            ('destruction_due_date', '<=', today),
            ('permanent_retention', '=', False),
            ('state', '!=', 'destroyed'),
        ]
        if (operator == '=' and value) or (operator == '!=' and not value):
            return domain

        # This handles the inverse case: (operator == '!=' and value) or (operator == '=' and not value)
        # which means we are searching for containers NOT due for destruction.
        inverse_domain = [
            '|',
                ('destruction_due_date', '>', today),
            '|',
                ('permanent_retention', '=', True),
                ('state', '=', 'destroyed'),
        ]
        return inverse_domain

    # ============================================================================
    # BUTTON ACTIONS
    # ============================================================================
    def action_activate(self):
        """Activate container for storage"""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Customer must be specified before activation"))

        self.write({
            "state": "active",
        })
        self.message_post(body=_("Container activated and ready for storage."))

    def action_mark_full(self):
        """Mark container as full"""
        self.ensure_one()
        self.write({"is_full": True})
        self.message_post(body=_("Container marked as full"))

    def action_schedule_destruction(self):
        """Schedule container for destruction"""
        self.ensure_one()
        if self.permanent_retention:
            raise UserError(_("Cannot schedule permanent retention containers for destruction"))
        if not self.is_due_for_destruction:
            raise UserError(_("This container is not yet due for destruction."))

        self.write({"state": "pending_destruction"})
        self.message_post(body=_("Container scheduled for destruction"))

    def action_destroy(self):
        """Mark container as destroyed"""
        self.ensure_one()
        if self.state != "pending_destruction":
            raise UserError(_("Only containers pending destruction can be destroyed"))

        self.write({
            "state": "destroyed",
            "destruction_date": fields.Date.today(),
            "active": False,
        })
        self.message_post(body=_("Container destroyed"))

    def action_view_documents(self):
        """View all documents in this container"""
        self.ensure_one()
        return {
            "name": _("Documents in Container %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("container_id", "=", self.id)],
            "context": {"default_container_id": self.id}
        }

    def action_generate_barcode(self):
        """
        Generates a barcode if one doesn't exist and returns an action to print it.
        This assumes a report with the external ID 'records_management.report_container_barcode' exists.
        """
        self.ensure_one()
        if not self.barcode:
            self.barcode = self.env["ir.sequence"].next_by_code("records.container.barcode") or self.name
        return self.env.ref("records_management.report_container_barcode").report_action(self)

    def action_store_container(self):
        """Store container - change state from indexed to stored"""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active containers can be stored"))
        if not self.location_id:
            raise UserError(_("Storage location must be assigned before storing"))
        vals = {"state": "stored"}
        if not self.storage_start_date:
            vals['storage_start_date'] = fields.Date.today()
        self.write(vals)
        self.message_post(body=_("Container has been stored."))

    def action_retrieve_container(self):
        """Retrieve container from storage"""
        self.ensure_one()
        if self.state not in ["stored", "active"]:
            raise UserError(_("Only stored or active containers can be retrieved"))
        self.write({"state": "in_transit", "last_access_date": fields.Date.today()})
        self.message_post(body=_("Container retrieved from storage"))

    def action_bulk_convert_container_type(self):
        """Bulk convert container types"""
        return {
            "name": _("Bulk Convert Container Types"),
            "type": "ir.actions.act_window",
            "res_model": "records.container.type.converter",
            "view_mode": "form",
            "target": "new",
            "context": {"default_container_ids": [(6, 0, self.ids)]},
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('partner_id', 'department_id')
    def _check_department_partner(self):
        """Ensure department belongs to the same partner"""
        for record in self:
            if record.department_id and record.department_id.partner_id != record.partner_id:
                raise ValidationError(_("Department must belong to the selected customer."))

    @api.constrains("weight")
    def _check_positive_values(self):
        for record in self:
            if record.weight and record.weight < 0:
                raise ValidationError(_("Weight must be a positive value."))

    @api.constrains("storage_start_date", "destruction_due_date")
    def _check_date_consistency(self):
        for record in self:
            if (
                record.storage_start_date
                and record.destruction_due_date
                and record.storage_start_date > record.destruction_due_date
            ):
                raise ValidationError(_("Destruction date cannot be before storage start date"))

