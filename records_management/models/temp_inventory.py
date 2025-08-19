from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class TempInventory(models.Model):
    _name = 'temp.inventory'
    _description = 'Temporary Inventory Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, date_created desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Inventory Name", required=True, copy=False, default=lambda self: _('New'))
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer/Owner", help="Optional: Link this inventory to a specific customer.")

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('in_use', 'In Use'),
        ('full', 'Full'),
        ('archived', 'Archived'),
    ], string="Status", default='draft', required=True, tracking=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
    ], string='Priority', default='0')

    # ============================================================================
    # LOCATION & CAPACITY
    # ============================================================================
    location_id = fields.Many2one('stock.location', string="Physical Location")
    capacity_limit = fields.Integer(string="Capacity Limit (Items)", default=100)
    current_count = fields.Integer(string="Current Item Count", compute='_compute_current_count', store=True)
    available_capacity = fields.Integer(string="Available Capacity", compute='_compute_capacity_metrics', store=True)
    utilization_percent = fields.Float(string="Utilization (%)", compute='_compute_capacity_metrics', store=True, aggregator="avg")

    # ============================================================================
    # CONTENTS
    # ============================================================================
    document_ids = fields.One2many('records.document', 'temp_inventory_id', string="Documents")
    container_ids = fields.One2many('records.container', 'temp_inventory_id', string="Containers")
    document_count = fields.Integer(compute='_compute_content_counts', store=True)
    container_count = fields.Integer(compute='_compute_content_counts', store=True)

    # ============================================================================
    # DATES & RETENTION
    # ============================================================================
    date_created = fields.Datetime(string="Created On", default=fields.Datetime.now, readonly=True)
    date_activated = fields.Datetime(string="Activated On", readonly=True)
    date_archived = fields.Datetime(string="Archived On", readonly=True)
    retention_period = fields.Integer(string="Retention Period (Days)", help="How long items can stay here.")
    expiry_date = fields.Date(string="Expiry Date", compute='_compute_expiry_date', store=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('document_ids', 'container_ids')
    def _compute_current_count(self):
        for record in self:
            record.current_count = len(record.document_ids) + len(record.container_ids)

    @api.depends('current_count', 'capacity_limit')
    def _compute_capacity_metrics(self):
        for record in self:
            record.available_capacity = max(0, record.capacity_limit - record.current_count)
            if record.capacity_limit > 0:
                record.utilization_percent = (record.current_count / record.capacity_limit) * 100
            else:
                record.utilization_percent = 0.0

    @api.depends('document_ids')
    def _compute_content_counts(self):
        for record in self:
            record.document_count = len(record.document_ids)
            record.container_count = len(record.container_ids)

    @api.depends('date_activated', 'retention_period')
    def _compute_expiry_date(self):
        for record in self:
            if record.date_activated and record.retention_period > 0:
                expiry_datetime = record.date_activated + timedelta(days=record.retention_period)
                record.expiry_date = expiry_datetime.date()
            else:
                record.expiry_date = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft inventories can be activated."))
        self.write({
            "state": "active",
            "date_activated": fields.Datetime.now(),
        })
        self.message_post(body=_("Temporary inventory activated by %s.", self.env.user.name))

    def action_archive(self):
        for record in self:
            if record.current_count > 0:
                raise UserError(_("Cannot archive inventory '%s' because it still contains %d items.", record.name, record.current_count))
            record.write({
                "state": "archived",
                "active": False,
                "date_archived": fields.Datetime.now(),
            })
            record.message_post(body=_("Temporary inventory archived by %s.", self.env.user.name))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('temp.inventory') or _('New')
        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.current_count > 0:
                raise UserError(_("Cannot delete inventory '%s' because it contains %d items. Please remove all items before deleting.", record.name, record.current_count))
        return super().unlink()

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('capacity_limit')
    def _check_capacity_limit(self):
        for record in self:
            if record.capacity_limit < 0:
                raise ValidationError(_("Capacity limit cannot be negative."))

    @api.constrains('retention_period')
    def _check_retention_period(self):
        for record in self:
            if record.retention_period < 0:
                raise ValidationError(_("Retention period cannot be negative."))


